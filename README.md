# Telegram IOC Resolver

A production-ready Python 3.12 application that uses the Telegram MTProto API (Telethon) to resolve a list of Telegram IOCs (Indicators of Compromise).

## Features

- Asynchronous processing of Telegram links (public usernames and private invite links).
- Extracts metadata: Entity Type, Display Name, Telegram ID, Verification/Scam/Fake/Restricted flags, Members count, and Bio/Description.
- Graceful handling of Telegram rate limits (FloodWait), invalid usernames, deleted accounts, and network errors.
- Export results to a detailed Markdown report (`Telegram_IOCs.md`).
- Real-time logging to `logs/resolver.log` and a CLI progress bar.

## Setup

1. **Install Python 3.12** if you haven't already.
2. **Clone the repository** and navigate to the project directory.
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configuration:**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and fill in your `API_ID` and `API_HASH`. You can obtain these from [my.telegram.org](https://my.telegram.org).

## Usage

1. Create a text file named `Cleaned_IOC.txt` in the project root directory.
2. Add one Telegram URL per line:
   ```text
   https://t.me/example
   https://telegram.me/example
   https://t.me/+InviteHash
   ```
3. Run the script:
   ```bash
   python main.py
   ```
4. The first time you run it, you will be prompted to log in to your Telegram account and enter the 2FA code if enabled. A session file will be created locally.
5. Once completed, review `Telegram_IOCs.md` for the results.
