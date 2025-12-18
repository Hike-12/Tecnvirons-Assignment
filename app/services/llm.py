import json
from typing import List, AsyncGenerator, Any, Dict
from groq import AsyncGroq
from app.config import settings
from app.models import ChatMessage

client = AsyncGroq(api_key=settings.GROQ_API_KEY)

# --- Tool Definitions ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_user_profile",
            "description": "Get the user's profile information including name and preferences.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The ID of the user to fetch.",
                    }
                },
                "required": ["user_id"],
            },
        },
    }
]

async def fetch_user_profile(user_id: str) -> str:
    """Simulated tool implementation."""
    # In a real app, this would query a database
    return json.dumps({
        "user_id": user_id,
        "name": "Alex Johnson",
        "preferences": {"theme": "dark", "notifications": True},
        "subscription": "premium"
    })

AVAILABLE_TOOLS = {
    "fetch_user_profile": fetch_user_profile
}

# --- LLM Interaction ---

async def stream_chat_response(messages: List[Dict[str, Any]]) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Streams the LLM response. Handles tool calls internally if possible, 
    but for this architecture, we'll yield chunks and let the caller handle the flow 
    or we can handle the tool execution loop here.
    
    To keep it simple and robust for the WebSocket, we will yield:
    - Content chunks
    - Tool call requests
    """
    
    try:
        stream = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            stream=True,
        )

        tool_calls = []
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            
            # Handle content
            if delta.content:
                yield {"type": "content", "content": delta.content}
            
            # Handle tool calls (accumulate them)
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if len(tool_calls) <= tc.index:
                        tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                    
                    if tc.id:
                        tool_calls[tc.index]["id"] = tc.id
                    if tc.function.name:
                        tool_calls[tc.index]["function"]["name"] = tc.function.name
                    if tc.function.arguments:
                        tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments

        # If we collected tool calls, yield them
        if tool_calls:
            yield {"type": "tool_calls", "tool_calls": tool_calls}

    except Exception as e:
        yield {"type": "error", "content": str(e)}

async def generate_summary(messages: List[Dict[str, Any]]) -> str:
    """Generates a concise summary of the conversation."""
    try:
        summary_prompt = [
            {"role": "system", "content": "Summarize the following conversation concisely in 2-3 sentences."},
            {"role": "user", "content": json.dumps(messages)}
        ]
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=summary_prompt,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating summary: {str(e)}"
