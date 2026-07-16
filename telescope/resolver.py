import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.types import (
    User, Chat, Channel, ChatForbidden, ChannelForbidden,
    ChannelFull, UserFull
)
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest
from telethon.tl.functions.messages import CheckChatInviteRequest, ImportChatInviteRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import ChatInviteAlready, ChatInvite, ChatInvitePeek
from telethon.errors import (
    FloodWaitError, RPCError, InviteHashExpiredError, InviteHashInvalidError,
    UsernameInvalidError, UsernameNotOccupiedError, UserAlreadyParticipantError
)
from .models import IOCResult, EntityType
from .utils import random_delay
from .parser import classify_and_extract
from .config import MAX_RETRIES

async def resolve_ioc(client: TelegramClient, url: str, join: bool = False) -> IOCResult:
    result = IOCResult(original_ioc=url, normalized_url=url)
    
    is_invite, identifier = classify_and_extract(url)
    if not identifier:
        result.status = "Failed"
        result.error_message = "Invalid or unsupported Telegram URL format"
        return result
        
    result.invite_hash = identifier if is_invite else None
    result.username = identifier if not is_invite else None
    
    retries = 0
    while retries <= MAX_RETRIES:
        try:
            await random_delay()
            
            if is_invite:
                # Resolve invite link
                invite_details = await client(CheckChatInviteRequest(hash=identifier))
                
                if isinstance(invite_details, (ChatInviteAlready, ChatInvitePeek)):
                    entity = invite_details.chat
                    if join and isinstance(invite_details, ChatInviteAlready):
                        result.action_status = "Joined"
                elif isinstance(invite_details, ChatInvite):
                    result.entity_type = EntityType.CHANNEL.value if getattr(invite_details, 'channel', False) else EntityType.BASIC_GROUP.value
                    if getattr(invite_details, 'megagroup', False):
                        result.entity_type = EntityType.SUPERGROUP.value
                        
                    result.display_name = getattr(invite_details, 'title', None)
                    result.members = getattr(invite_details, 'participants_count', None)
                    result.description = getattr(invite_details, 'about', None)
                    result.verified = getattr(invite_details, 'verified', False)
                    result.scam = getattr(invite_details, 'scam', False)
                    result.fake = getattr(invite_details, 'fake', False)
                    
                    if join:
                        try:
                            await client(ImportChatInviteRequest(hash=identifier))
                            result.action_status = "Joined"
                        except UserAlreadyParticipantError:
                            result.action_status = "Joined"
                        except Exception as e:
                            logging.debug(f"Action failed for {url}: {e}")
                            
                    result.status = "Success"
                    return result
                else:
                    result.status = "Failed"
                    result.error_message = "Unknown invite response"
                    return result
            else:
                # Resolve public username
                entity = await client.get_entity(identifier)
            
            # Extract data
            if isinstance(entity, User):
                result.entity_type = EntityType.BOT.value if entity.bot else EntityType.USER.value
                result.display_name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                result.username = entity.username
                result.telegram_id = entity.id
                result.verified = getattr(entity, 'verified', False)
                result.scam = getattr(entity, 'scam', False)
                result.fake = getattr(entity, 'fake', False)
                result.restricted = getattr(entity, 'restricted', False)
                
                try:
                    full_user = await client(GetFullUserRequest(id=entity))
                    result.description = full_user.full_user.about
                except Exception as e:
                    logging.debug(f"Could not fetch full user for {identifier}: {e}")
                
            elif isinstance(entity, Channel):
                result.entity_type = EntityType.SUPERGROUP.value if entity.megagroup else EntityType.CHANNEL.value
                result.display_name = entity.title
                result.username = entity.username
                result.telegram_id = entity.id
                result.verified = getattr(entity, 'verified', False)
                result.scam = getattr(entity, 'scam', False)
                result.fake = getattr(entity, 'fake', False)
                result.restricted = getattr(entity, 'restricted', False)
                
                try:
                    full_channel = await client(GetFullChannelRequest(channel=entity))
                    result.description = full_channel.full_chat.about
                    result.members = full_channel.full_chat.participants_count
                except Exception as e:
                    logging.debug(f"Could not fetch full channel for {identifier}: {e}")
                
            elif isinstance(entity, Chat):
                result.entity_type = EntityType.BASIC_GROUP.value
                result.display_name = entity.title
                result.telegram_id = entity.id
                result.members = entity.participants_count
                
            elif isinstance(entity, (ChatForbidden, ChannelForbidden)):
                result.entity_type = EntityType.UNKNOWN.value
                result.display_name = getattr(entity, 'title', None)
                result.telegram_id = entity.id
                result.status = "Failed"
                result.error_message = "Access to the chat/channel is forbidden"
                return result
                
            else:
                result.entity_type = EntityType.UNKNOWN.value
                result.status = "Failed"
                result.error_message = f"Unsupported entity type: {type(entity)}"
                return result

            if join:
                try:
                    if result.entity_type == EntityType.BOT.value:
                        await client.send_message(entity, '/start')
                        result.action_status = "Requested"
                    elif result.entity_type in (EntityType.CHANNEL.value, EntityType.SUPERGROUP.value):
                        await client(JoinChannelRequest(entity))
                        result.action_status = "Joined"
                except UserAlreadyParticipantError:
                    result.action_status = "Joined"
                except Exception as e:
                    logging.debug(f"Action failed for {url}: {e}")

            result.status = "Success"
            return result
            
        except FloodWaitError as e:
            logging.warning(f"FloodWaitError: Waiting for {e.seconds} seconds before retrying {identifier}")
            await asyncio.sleep(e.seconds)
            retries += 1
            
        except UsernameInvalidError:
            result.status = "Failed"
            result.error_message = "Invalid username format"
            return result
            
        except UsernameNotOccupiedError:
            result.status = "Failed"
            result.error_message = "Username not occupied"
            return result
            
        except (InviteHashExpiredError, InviteHashInvalidError):
            result.status = "Failed"
            result.error_message = "Invite link is invalid or expired"
            return result
            
        except RPCError as e:
            result.status = "Failed"
            result.error_message = f"RPC Error: {str(e)}"
            return result
            
        except Exception as e:
            if "No user has" in str(e) or "Cannot find any entity" in str(e):
                result.status = "Failed"
                result.error_message = "Entity not found (could be deleted or private)"
                return result
            
            logging.error(f"Unexpected error resolving {url}: {e}", exc_info=True)
            if retries == MAX_RETRIES:
                result.status = "Failed"
                result.error_message = f"Unexpected error: {str(e)}"
                return result
            retries += 1
            await random_delay()

    result.status = "Failed"
    result.error_message = "Max retries exceeded"
    return result
