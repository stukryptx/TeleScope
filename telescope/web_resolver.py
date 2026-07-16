import aiohttp
from bs4 import BeautifulSoup
import logging
import re
from .models import IOCResult, EntityType
from .parser import classify_and_extract

async def web_resolve(url: str) -> IOCResult:
    result = IOCResult(original_ioc=url, normalized_url=url)
    is_invite, identifier = classify_and_extract(url)
    
    if not identifier:
        result.status = "Failed"
        result.error_message = "Invalid URL"
        return result

    result.invite_hash = identifier if is_invite else None
    result.username = identifier if not is_invite else None

    # Construct the t.me URL cleanly
    target_url = f"https://t.me/{identifier}" if not is_invite else f"https://t.me/+{identifier}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(target_url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status != 200:
                    result.status = "Failed"
                    result.error_message = f"HTTP {response.status}"
                    return result
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Check if it's an actual preview page by looking for the title
                title_elem = soup.find('div', {'class': 'tgme_page_title'})
                desc_elem = soup.find('div', {'class': 'tgme_page_description'})
                
                if not title_elem:
                    # Check if it's a hidden user profile
                    if desc_elem and "contact @" in desc_elem.text.lower():
                        result.entity_type = "User (Unconfirmed)"
                        result.status = "Success"
                        result.description = "Private User Account (No Public Web Preview)"
                        result.display_name = identifier
                        return result
                        
                    # Otherwise, it's truly invalid or unavailable
                    result.status = "Failed"
                    result.error_message = "No preview available (Invalid or Private)"
                    return result
                
                title_text = title_elem.text.strip()
                result.verified = "✔" in title_text or "✅" in title_text
                # Remove verified badges and zero-width spaces for the display name
                clean_name = title_text.replace("✔", "").replace("✅", "").strip()
                result.display_name = clean_name if clean_name else identifier

                extra_elem = soup.find('div', {'class': 'tgme_page_extra'})
                extra_text = extra_elem.text.lower() if extra_elem else ""

                # Determine entity type based on extra text
                if "bot" in extra_text:
                    result.entity_type = EntityType.BOT.value
                elif "subscribers" in extra_text:
                    result.entity_type = EntityType.CHANNEL.value
                elif "members" in extra_text:
                    result.entity_type = EntityType.BASIC_GROUP.value 
                else:
                    result.entity_type = EntityType.USER.value

                # Extract member count if available
                mem_match = re.search(r'([\d\s]+)', extra_text)
                if mem_match and result.entity_type != EntityType.USER.value:
                    try:
                        result.members = int(mem_match.group(1).replace(" ", ""))
                    except ValueError:
                        pass

                # Description (if not already extracted)
                if desc_elem and not result.description:
                    result.description = desc_elem.text.strip()

                # Action/Warning label checks (Scam)
                action_elem = soup.find('div', {'class': 'tgme_page_action'})
                if action_elem and "scam" in action_elem.text.lower():
                    result.scam = True

                result.status = "Success"
                return result

    except Exception as e:
        logging.debug(f"Web resolve failed for {url}: {e}")
        result.status = "Failed"
        result.error_message = f"Web scrape error: {e}"
        return result
