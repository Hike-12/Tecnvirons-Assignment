from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks
from app.services.session import create_session, log_event
from app.services.llm import stream_chat_response, AVAILABLE_TOOLS
from app.services.background import process_session_summary
from datetime import datetime
import json
import asyncio

router = APIRouter()

@router.websocket("/ws/session/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    
    # Initialize Session
    session_id = await create_session(user_id=client_id)
    start_time = datetime.now()
    
    # Local conversation history for the LLM context
    conversation_history = [
        {"role": "system", "content": "You are a helpful AI assistant. You can fetch user profiles using the fetch_user_profile tool."}
    ]
    
    try:
        while True:
            # 1. Receive User Message
            data = await websocket.receive_text()
            
            # Update history and DB
            conversation_history.append({"role": "user", "content": data})
            await log_event(session_id, "user_message", {"content": data})
            
            # 2. Stream LLM Response
            assistant_content = ""
            tool_calls_buffer = []
            
            # We need a loop to handle potential multiple turns (tool calls)
            # For simplicity, we'll handle one level of tool calls here
            
            async for chunk in stream_chat_response(conversation_history):
                if chunk["type"] == "content":
                    content = chunk["content"]
                    if content:
                        assistant_content += content
                        await websocket.send_text(json.dumps({"type": "token", "content": content}))
                
                elif chunk["type"] == "tool_calls":
                    tool_calls_buffer = chunk["tool_calls"]
                
                elif chunk["type"] == "error":
                    await websocket.send_text(json.dumps({"type": "error", "content": chunk["content"]}))

            # 3. Handle Tool Calls if any
            if tool_calls_buffer:
                # Notify client we are executing tools
                await websocket.send_text(json.dumps({"type": "info", "content": "Executing tools..."}))
                
                # Add the assistant's tool call message to history
                # Groq expects tool_calls to include 'type' field
                formatted_tool_calls = []
                for tc in tool_calls_buffer:
                    formatted_tool_calls.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": tc["function"]
                    })
                
                conversation_history.append({
                    "role": "assistant",
                    "content": assistant_content if assistant_content else None,
                    "tool_calls": formatted_tool_calls
                })
                await log_event(session_id, "tool_call", {"tool_calls": formatted_tool_calls})

                # Execute tools
                for tool_call in tool_calls_buffer:
                    function_name = tool_call["function"]["name"]
                    arguments = json.loads(tool_call["function"]["arguments"])
                    tool_call_id = tool_call["id"]
                    
                    if function_name in AVAILABLE_TOOLS:
                        # Execute
                        result = await AVAILABLE_TOOLS[function_name](**arguments)
                        
                        # Add result to history
                        conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": function_name,
                            "content": result
                        })
                        await log_event(session_id, "tool_result", {"name": function_name, "result": result})
                
                # 4. Get final response after tool execution
                # Stream again
                final_content = ""
                async for chunk in stream_chat_response(conversation_history):
                    if chunk["type"] == "content":
                        content = chunk["content"]
                        if content:
                            final_content += content
                            await websocket.send_text(json.dumps({"type": "token", "content": content}))
                
                assistant_content = final_content

            # Finalize Assistant Message
            if assistant_content:
                if conversation_history[-1]["role"] != "assistant":
                     conversation_history.append({"role": "assistant", "content": assistant_content})
                await log_event(session_id, "assistant_message", {"content": assistant_content})
            
            # End of turn signal
            await websocket.send_text(json.dumps({"type": "end_turn"}))

    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
        # Trigger background task
        # Note: We can't use BackgroundTasks here because the request is done.
        # We need to schedule it on the event loop.
        asyncio.create_task(process_session_summary(session_id, start_time))
        
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()
