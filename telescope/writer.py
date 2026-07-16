import os
from datetime import datetime
import aiofiles
from typing import List
from .models import IOCResult, EntityType

async def init_report(output_file: str = "Telegram_IOCs.md", overwrite: bool = False):
    mode = 'w' if overwrite or not os.path.exists(output_file) else 'a'
    if mode == 'w':
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await f.write(f"# Telegram IOC Resolution Report\n\n")
            await f.write(f"Generated timestamp: {timestamp}\n\n")
            await f.write("| Original URL | Entity Type | Display Name | Username | Telegram ID | Members | Verified | Scam | Fake | Description |\n")
            await f.write("|---|---|---|---|---|---|---|---|---|---|\n")

async def append_ioc_to_report(r: IOCResult, output_file: str = "Telegram_IOCs.md"):
    if r.status != "Success":
        return
        
    async with aiofiles.open(output_file, 'a', encoding='utf-8') as f:
        url = r.original_ioc
        etype = r.entity_type
        name = (r.display_name or "").replace("|", "\\|").replace("\n", " ")
        uname = (r.username or "").replace("|", "\\|")
        tid = r.telegram_id or ""
        members = r.members if r.members is not None else ""
        verified = "✅" if r.verified else ""
        scam = "⚠️" if r.scam else ""
        fake = "❌" if r.fake else ""
        desc = (r.description or "").replace("|", "\\|").replace("\n", " ").strip()
        
        # Keep description manageable
        if len(desc) > 200:
            desc = desc[:197] + "..."
            
        await f.write(f"| {url} | {etype} | {name} | {uname} | {tid} | {members} | {verified} | {scam} | {fake} | {desc} |\n")

async def finalize_report(results: List[IOCResult], runtime: float, output_file: str = "Telegram_IOCs.md"):
    total = len(results)
    success = sum(1 for r in results if r.status == "Success")
    failed = total - success
    
    users = sum(1 for r in results if r.entity_type == EntityType.USER.value)
    bots = sum(1 for r in results if r.entity_type == EntityType.BOT.value)
    channels = sum(1 for r in results if r.entity_type == EntityType.CHANNEL.value)
    supergroups = sum(1 for r in results if r.entity_type == EntityType.SUPERGROUP.value)
    groups = sum(1 for r in results if r.entity_type == EntityType.BASIC_GROUP.value)
    invalid = sum(1 for r in results if r.entity_type == EntityType.UNKNOWN.value)
    
    async with aiofiles.open(output_file, 'a', encoding='utf-8') as f:
        await f.write("\n## Final Statistics\n\n")
        await f.write(f"- **Runtime:** {runtime:.2f} seconds\n")
        await f.write(f"- **Total processed:** {total}\n")
        await f.write(f"- **Successful:** {success}\n")
        await f.write(f"- **Failed:** {failed}\n")
        await f.write(f"- **Users:** {users}\n")
        await f.write(f"- **Bots:** {bots}\n")
        await f.write(f"- **Channels:** {channels}\n")
        await f.write(f"- **Supergroups:** {supergroups}\n")
        await f.write(f"- **Groups:** {groups}\n")
        await f.write(f"- **Invalid:** {invalid}\n")
