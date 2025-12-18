from app.services.session import get_session_events, update_session_summary
from app.services.llm import generate_summary
from datetime import datetime
import asyncio

async def process_session_summary(session_id: str, start_time: datetime):
    """
    Background task to summarize the session.
    """
    try:
        # Calculate duration
        end_time = datetime.now()
        duration = (end_time - start_time).seconds
        
        # Fetch all events
        events = await get_session_events(session_id)
        
        # Filter for chat messages to send to LLM
        messages = []
        for event in events:
            if event["event_type"] in ["user_message", "assistant_message", "tool_call", "tool_result"]:
                # We might need to format this better for the LLM
                messages.append({
                    "role": "user" if event["event_type"] == "user_message" else "assistant",
                    "content": str(event["payload"])
                })
        
        if not messages:
            return

        # Generate summary
        summary = await generate_summary(messages)
        
        # Update DB
        await update_session_summary(session_id, summary, duration)
        
        print(f"Session {session_id} summarized successfully.")
        
    except Exception as e:
        print(f"Error processing session summary for {session_id}: {e}")
