from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class SessionCreate(BaseModel):
    user_id: Optional[str] = "anonymous"

class SessionEvent(BaseModel):
    session_id: str
    event_type: str
    payload: Dict[str, Any]
    created_at: datetime = datetime.now()

class ChatMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
