<h1 align="center">Telegram IOC Resolver</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Telethon-Async-orange.svg" alt="Telethon">
  <img src="https://img.shields.io/badge/OSINT-Threat%20Intelligence-red.svg" alt="OSINT">
</p>

<p align="center">
  <strong>A production-ready, highly resilient asynchronous Python tool built on the MTProto API (Telethon) to resolve, classify, and extract metadata from massive lists of Telegram Indicators of Compromise (IOCs).</strong>
</p>

---

## ⚡ Features

- **Asynchronous Engine**: Leverages pure `asyncio` and `Telethon` to quickly parse massive lists of domains safely.
- **Deep Metadata Extraction**: Resolves Entity Type (User, Bot, Channel, Supergroup), Display Name, Telegram ID, Members count, Bio/Description, and Security Flags (Verified/Scam/Fake/Restricted).
- **Anti-Ban Architecture**: Intelligent handling of Telegram rate limits (`FloodWait`), invalid usernames, deleted accounts, network errors, and session state persistence.
- **Streaming Table Output**: Results are continuously streamed into a clean, formatted Markdown table as they are successfully resolved.
- **Smart Resume**: Built-in state tracking allows you to pause processing and resume exactly where you left off later without losing data.

## ⚙️ Setup

### Prerequisites
- Python 3.12+
- Telegram API ID and Hash (obtainable via [my.telegram.org](https://my.telegram.org))

### Installation
1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd TG-Resolver
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the Environment**:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in your `API_ID` and `API_HASH`. 

## 🚀 Usage

By default, the script looks for a file named `Cleaned_IOC.txt` in the root directory.

### Basic Run
```bash
python main.py
```

### Custom IOC File
You can specify any text file containing newline-separated Telegram URLs using the `--file` or `-f` argument:
```bash
python main.py --file path/to/your/iocs.txt
```

### Authentication
On the first run, the script will interactively prompt you for your Telegram phone number and 2FA code. This generates a persistent `.session` file locally.

### Interactive Pausing
While the script is running, you can safely pause it:
1. Type `p` and press **Enter**.
2. Type `yes` to confirm.
3. The script will safely shut down and save its exact state. Run `python main.py` again to immediately resume!

---
*Disclaimer: Use responsibly and strictly adhere to Telegram's Terms of Service to avoid account bans.*
