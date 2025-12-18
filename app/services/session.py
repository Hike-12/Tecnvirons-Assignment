from app.database import get_supabase
from app.models import SessionCreate
from typing import List, Dict, Any
import uuid

async def create_session(user_id: str) -> str:
    supabase = get_supabase()
    data = {"user_id": user_id}
    response = supabase.table("sessions").insert(data).execute()
    return response.data[0]["session_id"]

async def log_event(session_id: str, event_type: str, payload: Dict[str, Any]):
    supabase = get_supabase()
    data = {
        "session_id": session_id,
        "event_type": event_type,
        "payload": payload
    }
    
    supabase.table("session_events").insert(data).execute()

async def get_session_events(session_id: str) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    response = supabase.table("session_events").select("*").eq("session_id", session_id).order("created_at").execute()
    return response.data

async def update_session_summary(session_id: str, summary: str, duration: int):
    supabase = get_supabase()
    data = {
        "summary": summary,
        "duration_seconds": duration,
        "end_time": "now()"
    }
    supabase.table("sessions").update(data).eq("session_id", session_id).execute()
