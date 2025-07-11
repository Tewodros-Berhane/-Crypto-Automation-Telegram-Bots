#!/usr/bin/env python3
import os
import asyncio
import logging
from datetime import datetime, timezone

import aiohttp
import feedparser
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
import uvicorn
from tweepy.asynchronous import AsyncStreamingClient, StreamRule
import dateutil.parser
import humanize

# ─── CONFIG VIA ENV ─────────────────────────────────────────────────────────────
# TW_BEARER_TOKEN : Twitter API v2 Bearer Token
# IG_VERIFY_TOKEN : your chosen verify token for IG webhook
# IG_TOKEN        : Instagram Graph API User Access Token
# TG_TOKEN        : Telegram Bot Token
# TG_CHAT_ID      : Telegram chat_id to post into
# Adjust keywords/accounts as you like below:

TWITTER_KEYWORDS = ["Solana", "Ethereum"]
TWITTER_ACCOUNTS = ["elonmusk", "michelson"]  # no '@'

TRUTH_ACCOUNT     = "realDonaldTrump"
WH_FEED_URL       = "https://www.whitehouse.gov/presidential-actions/feed/"

# ─── GLOBAL HTTP SESSION FOR TELEGRAM ───────────────────────────────────────────
_telegram_session: aiohttp.ClientSession | None = None

async def send_to_telegram(html: str):
    global _telegram_session
    if _telegram_session is None:
        _telegram_session = aiohttp.ClientSession()
    url = f"https://api.telegram.org/bot{os.getenv('TG_TOKEN')}/sendMessage"
    await _telegram_session.post(url, json={
        "chat_id": os.getenv("TG_CHAT_ID"),
        "text": html,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    })

# ─── FORMATTERS ────────────────────────────────────────────────────────────────
def relative_time(timestamp: str) -> str:
    dt = dateutil.parser.isoparse(timestamp)
    return humanize.naturaltime(datetime.now(timezone.utc) - dt)

def format_twitter(tweet, user) -> str:
    rt = relative_time(tweet.created_at)
    return (
        f"<b>{user.name}</b> <a href=\"https://twitter.com/{user.username}\">@{user.username}</a> &#183; {rt}\n"
        f"{tweet.text}\n"
        f"https://twitter.com/{user.username}/status/{tweet.id}"
    )

def format_instagram(media: dict) -> str:
    rt = relative_time(media["timestamp"])
    cap = media.get("caption", "")
    return (
        f"<b>{media['username']}</b> &#183; {rt}\n"
        f"{cap}\n"
        f"{media['permalink']}"
    )

def format_truth(account: str, text: str, timestamp: str, permalink: str) -> str:
    rt = relative_time(timestamp)
    return (
        f"<b>{account}</b> &#183; {rt}\n"
        f"{text}\n"
        f"{permalink}"
    )

def format_whitehouse(entry) -> str:
    rt = humanize.naturaltime(datetime.now(timezone.utc) - dateutil.parser.parse(entry.published))
    return (
        f"<b>White House</b> &#183; {rt}\n"
        f"{entry.title}\n"
        f"{entry.link}"
    )

# ─── TWITTER STREAM ────────────────────────────────────────────────────────────
class TwitterListener(AsyncStreamingClient):
    async def on_tweet(self, tweet):
        user_resp = await self.get_user(tweet.author_id, user_fields=["username","name"])
        user = user_resp.data
        formatted = format_twitter(tweet, user)
        await send_to_telegram(formatted)

async def start_twitter(keywords: list[str], accounts: list[str]):
    client = TwitterListener(os.getenv("TW_BEARER_TOKEN"), wait_on_rate_limit=True)
    # clear old rules
    existing = await client.get_rules()
    if existing.data:
        await client.delete_rules([r.id for r in existing.data])
    # add new
    for kw in keywords:
        await client.add_rules(StreamRule(f"{kw} lang:en"))
    for acct in accounts:
        await client.add_rules(StreamRule(f"from:{acct}"))
    await client.filter(threaded=True)

# ─── INSTAGRAM WEBHOOK ─────────────────────────────────────────────────────────
app = FastAPI()

@app.get("/ig_webhook")
def verify(hub_challenge: str = None, hub_verify_token: str = None):
    if hub_verify_token == os.getenv("IG_VERIFY_TOKEN"):
        return int(hub_challenge)
    return "Invalid verify token"

@app.post("/ig_webhook")
async def ig_webhook(req: Request):
    data = await req.json()
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            media_id = change.get("value", {}).get("media_id")
            if media_id:
                media = await fetch_instagram_media(media_id)
                formatted = format_instagram(media)
                await send_to_telegram(formatted)
    return {"success": True}

async def fetch_instagram_media(media_id: str) -> dict:
    token = os.getenv("IG_TOKEN")
    url = (
        f"https://graph.facebook.com/v15.0/{media_id}"
        f"?fields=id,caption,media_url,permalink,username,timestamp"
        f"&access_token={token}"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            return await r.json()

# ─── TRUTH SOCIAL POLLING ───────────────────────────────────────────────────────
async def poll_truth(account: str, seen: set[str]):
    session = aiohttp.ClientSession()
    try:
        while True:
            url = f"https://truthsocial.com/{account}"
            async with session.get(url) as r:
                html = await r.text()
            soup = BeautifulSoup(html, "html.parser")
            # adjust selectors if Truth Social markup changes
            for post in soup.select("article"):
                pid = post.get("data-post-id") or post.get("id")
                if not pid or pid in seen:
                    continue
                seen.add(pid)
                text = "".join(post.select_one("p").stripped_strings)
                ts = post.find("time")["datetime"]
                link = post.find("a", href=True)["href"]
                formatted = format_truth(account, text, ts, link)
                await send_to_telegram(formatted)
            await asyncio.sleep(2)
    finally:
        await session.close()

# ─── WHITE HOUSE RSS POLLING ───────────────────────────────────────────────────
async def poll_whitehouse(feed_url: str, seen: set[str]):
    while True:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            if entry.id not in seen:
                seen.add(entry.id)
                formatted = format_whitehouse(entry)
                await send_to_telegram(formatted)
        await asyncio.sleep(2)

# ─── MAIN ENTRYPOINT ───────────────────────────────────────────────────────────
async def main():
    logging.info("Starting News Tracker…")
    seen_truth = set()
    seen_wh    = set()

    # fire up Uvicorn for FastAPI Instagram webhooks
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)

    await asyncio.gather(
        start_twitter(TWITTER_KEYWORDS, TWITTER_ACCOUNTS),
        poll_truth(TRUTH_ACCOUNT, seen_truth),
        poll_whitehouse(WH_FEED_URL, seen_wh),
        server.serve(),
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
