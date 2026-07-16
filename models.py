from dataclasses import dataclass
from enum import Enum
from typing import Optional

class EntityType(Enum):
    USER = "User"
    BOT = "Bot"
    CHANNEL = "Channel"
    SUPERGROUP = "Supergroup"
    BASIC_GROUP = "Basic Group"
    UNKNOWN = "Unknown"

@dataclass
class IOCResult:
    original_ioc: str
    normalized_url: str
    entity_type: str = EntityType.UNKNOWN.value
    display_name: Optional[str] = None
    username: Optional[str] = None
    telegram_id: Optional[int] = None
    invite_hash: Optional[str] = None
    verified: bool = False
    scam: bool = False
    fake: bool = False
    restricted: bool = False
    members: Optional[int] = None
    description: Optional[str] = None
    status: str = "Pending"
    error_message: Optional[str] = None
    action_status: str = ""
