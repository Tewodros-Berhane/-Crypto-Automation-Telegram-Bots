# Crypto Automation & Telegram Bots

A collection of Python automation tools and Telegram bots for the crypto space. These scripts demonstrate real-world automation skills—wallet monitoring, news aggregation, and message forwarding—using blockchain and Telegram APIs.

---

## Table of Contents

- [Overview](#overview)
- [Scripts](#scripts)
  - [solana_multi_wallet_monitor.py](#solana_multi_wallet_monitorpy)
  - [solana_single_wallet_alert.py](#solana_single_wallet_alertpy)
  - [telegram_signal_filter.py](#telegram_signal_filterpy)
  - [telegram_keyword_forwarder.py](#telegram_keyword_forwarderpy)
  - [crypto_news_aggregator.py](#crypto_news_aggregatorpy)
- [Requirements](#requirements)
- [Setup & Usage](#setup--usage)
- [Customization](#customization)
- [License](#license)

---

## Overview

Each script leverages modern Python libraries and public APIs to automate critical crypto/Telegram tasks:

- **Monitor Solana wallets for on-chain events (airdrops, buys)**
- **Forward and filter Telegram trading signals**
- **Aggregate and broadcast crypto news/alpha from social and official sources**
- **Automate crypto intelligence with robust, real-world Python bots**

---

## Scripts

### 1. `solana_multi_wallet_monitor.py`
**Multi-Wallet Solana Tracker & Alert Bot**  
Monitors a list of Solana wallets for outgoing transactions to fresh addresses (potential airdrop/token buy activity). If two or more tracked wallets interact with the same destination, it triggers a Telegram alert.

---

### 2. `solana_single_wallet_alert.py`
**Single Wallet Outgoing Transaction Watcher**  
Monitors one Solana wallet for outgoing transfers to addresses with no prior transactions. Sends a Telegram message if such an event occurs (e.g., a new wallet is funded).

---

### 3. `telegram_signal_filter.py`
**Exchange Signal Telegram Bot**  
Forwards messages from a source Telegram channel to a target group if they match custom criteria (e.g., “From: KuCoin” and balance above 65.99). Built for filtering exchange signals or alpha drops.

---

### 4. `telegram_keyword_forwarder.py`
**Keyword-Based Telegram Forwarder**  
Listens for messages in a source channel and forwards those containing a specific keyword (in text or URL) to a destination group. Easy to configure for any keyword or signal.

---

### 5. `crypto_news_aggregator.py`
**Crypto News & Social Alpha Aggregator**  
Tracks specified keywords and accounts across Twitter, Truth Social, White House RSS, and Instagram. Sends formatted, real-time news and social media alpha to a Telegram channel. Includes a FastAPI server for Instagram webhooks.

---

## Requirements

- Python 3.9+
- [Telethon](https://github.com/LonamiWebs/Telethon)
- [requests](https://pypi.org/project/requests/)
- [aiohttp](https://docs.aiohttp.org/en/stable/)
- [feedparser](https://pypi.org/project/feedparser/)
- [fastapi](https://fastapi.tiangolo.com/)
- [uvicorn](https://www.uvicorn.org/)
- [tweepy](https://www.tweepy.org/)
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/)
- [humanize](https://pypi.org/project/humanize/)
- API credentials: Telegram, Twitter, Solana RPC, Instagram, etc.

---

## Setup & Usage

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/Tewodros-Berhane/Crypto-Automation---Telegram-Bots.git
    cd crypto-automation-bots
    ```

2. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure Credentials:**  
   - Edit each script and add your API keys, tokens, channel names, wallet addresses, and keywords at the top.

4. **Run Any Script:**
    ```bash
    python solana_multi_wallet_monitor.py
    # or
    python solana_single_wallet_alert.py
    # etc.
    ```

---

## Customization

- Easily adjust wallet lists, Telegram groups, keywords, or endpoints by modifying the top section of each script.
- For running multiple bots: consider [pm2](https://pm2.keymetrics.io/) or Docker.

---

## License

MIT License. Fork, adapt, and use these tools for your own crypto and automation projects.
