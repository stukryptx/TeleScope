import asyncio
import logging
import random
from pathlib import Path
from rich.logging import RichHandler
from .config import MIN_DELAY, MAX_DELAY

def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="[%Y-%m-%d %H:%M:%S]",
        handlers=[
            RichHandler(rich_tracebacks=True, markup=True),
            logging.FileHandler(log_dir / "resolver.log", encoding="utf-8")
        ]
    )
    
    # Set telethon logs to WARNING to reduce noise
    logging.getLogger("telethon").setLevel(logging.WARNING)

async def random_delay():
    """Sleeps for a random duration between MIN_DELAY and MAX_DELAY"""
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    await asyncio.sleep(delay)
