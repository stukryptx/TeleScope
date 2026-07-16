import asyncio
import logging
import json
import sys
import hashlib
import os
import argparse
from time import time
from dataclasses import asdict
from tqdm.asyncio import tqdm
from telethon import TelegramClient
import telethon.network.mtprotostate

# Monkeypatch telethon to prevent hanging on time sync issues
telethon.network.mtprotostate.MSG_TOO_NEW_DELTA = 99999999
telethon.network.mtprotostate.MSG_TOO_OLD_DELTA = 99999999

from config import API_ID, API_HASH, SESSION_NAME
from utils import setup_logging
from parser import parse_iocs
from resolver import resolve_ioc
from writer import init_report, append_ioc_to_report, finalize_report
from models import IOCResult

def get_file_hash(filepath: str) -> str:
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
    except FileNotFoundError:
        return ""
    return hasher.hexdigest()

async def main():
    parser = argparse.ArgumentParser(description="Telegram IOC Resolver - Asynchronous MTProto OSINT tool")
    parser.add_argument("--file", "-f", type=str, default="Cleaned_IOC.txt", help="Path to the IOC text file (default: Cleaned_IOC.txt)")
    parser.add_argument("--join", action="store_true", help="Automatically join groups/channels and start bots")
    args = parser.parse_args()

    setup_logging()
    logging.info("Starting Telegram IOC Resolver")
    start_time = time()
    
    file_path = args.file
    iocs = await parse_iocs(file_path)
    if not iocs:
        logging.error(f"No valid IOCs found in {file_path} or file is missing.")
        return
        
    logging.info(f"Loaded {len(iocs)} unique IOCs")
    
    current_hash = get_file_hash(file_path)
    results = []
    
    # State handling
    state_file = ".resolver_state.jsonl"
    processed_count = 0
    try:
        with open(state_file, "r") as f:
            first_line = f.readline()
            if first_line:
                state_meta = json.loads(first_line)
                if state_meta.get("file_hash") == current_hash:
                    for line in f:
                        data = json.loads(line)
                        results.append(IOCResult(**data))
                        processed_count += 1
                    logging.info(f"Resuming from previous state. {processed_count} IOCs already processed.")
                else:
                    logging.info("Input file changed. Starting from scratch.")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Initialize Telethon Client
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    logging.info("Connecting to Telegram...")
    await client.start()
    logging.info("Logged in successfully!")
    
    success_count = sum(1 for r in results if r.status == "Success")
    fail_count = processed_count - success_count
    
    pbar = tqdm(total=len(iocs), initial=processed_count, desc="Resolving IOCs")
    
    stop_requested = False

    async def listen_for_pause():
        nonlocal stop_requested
        loop = asyncio.get_event_loop()
        while not stop_requested and processed_count < len(iocs):
            # sys.stdin.readline is blocking, we run it in executor
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if line.strip().lower() == 'p':
                print("\nPause requested. Do you want to pause and exit? (yes/no): ", end='', flush=True)
                confirm = await loop.run_in_executor(None, sys.stdin.readline)
                if confirm.strip().lower() == 'yes':
                    stop_requested = True
                    break

    listen_task = asyncio.create_task(listen_for_pause())

    # Re-initialize the report as a table and write already processed results
    await init_report(overwrite=True)
    for r in results:
        await append_ioc_to_report(r)
    
    # Open state file in append mode or write mode
    mode = "a" if processed_count > 0 else "w"
    
    with open(state_file, mode) as sf:
        if mode == "w":
            sf.write(json.dumps({"file_hash": current_hash}) + "\n")
            sf.flush()
            
        for ioc in iocs[processed_count:]:
            if stop_requested:
                logging.info("Pausing the script as requested...")
                break
                
            pbar.set_description(f"Resolving: {ioc[:30]}...")
            
            result = await resolve_ioc(client, ioc, join=args.join)
            results.append(result)
            sf.write(json.dumps(asdict(result)) + "\n")
            sf.flush()
            
            if result.status == "Success":
                success_count += 1
                await append_ioc_to_report(result)
                
                # Format: [+] Telegram [Channel,Group,User,BOT] [Resolved, Unavaliable] [Name of That] [Joined , Requested]
                action_str = f" [{result.action_status}]" if result.action_status else ""
                log_msg = f"[+] Telegram [{result.entity_type}] [Resolved] [{result.display_name or ioc}]{action_str}"
                tqdm.write(log_msg)
            else:
                fail_count += 1
                log_msg = f"[-] Telegram [{result.entity_type}] [Unavailable] [{ioc}] [{result.error_message}]"
                tqdm.write(log_msg)
                
            pbar.set_postfix({"Success": success_count, "Failed": fail_count})
            pbar.update(1)
            
    pbar.close()
    if not listen_task.done():
        listen_task.cancel()
        
    await client.disconnect()
    
    if stop_requested:
        logging.info("Script paused. You can restart it later to resume.")
        # Do not generate markdown report yet since we are pausing
        return
        
    runtime = time() - start_time
    
    logging.info("Appending final statistics to markdown report...")
    await finalize_report(results, runtime)
    
    # After generating report, delete the state file
    try:
        os.remove(state_file)
    except FileNotFoundError:
        pass
        
    logging.info(f"Finished processing {len(iocs)} IOCs in {runtime:.2f}s")
    logging.info("Report saved to Telegram_IOCs.md")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
    except Exception as e:
        logging.critical(f"Critical error: {e}", exc_info=True)
