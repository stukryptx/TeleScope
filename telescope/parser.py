import re
from typing import List, Tuple
import aiofiles
import logging

def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = f"https://{url}"
    return url

def classify_and_extract(url: str) -> Tuple[bool, str]:
    """
    Returns (is_invite, identifier)
    """
    # Invite links like t.me/+hash or t.me/joinchat/hash
    invite_match = re.search(r'(?:t\.me|telegram\.me|telegram\.dog)/(?:joinchat/|\+)([\w-]+)', url, re.IGNORECASE)
    if invite_match:
        return True, invite_match.group(1)
        
    # Public usernames
    public_match = re.search(r'(?:t\.me|telegram\.me|telegram\.dog)/([\w_]+)', url, re.IGNORECASE)
    if public_match:
        return False, public_match.group(1)
        
    return False, ""

async def parse_iocs(filepath: str) -> List[str]:
    """
    Reads the file, normalizes, removes duplicates while preserving order.
    """
    seen = set()
    iocs = []
    try:
        async with aiofiles.open(filepath, mode='r', encoding='utf-8') as f:
            async for line in f:
                url = line.strip()
                if not url:
                    continue
                url = normalize_url(url)
                if url not in seen:
                    seen.add(url)
                    iocs.append(url)
    except FileNotFoundError:
        logging.error(f"Input file not found: {filepath}")
    except Exception as e:
        logging.error(f"Error reading {filepath}: {e}")
    return iocs
