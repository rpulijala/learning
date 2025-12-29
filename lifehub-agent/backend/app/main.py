"""FastAPI application with /chat endpoint using multi-agent LangGraph."""

import json
import logging
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel

from backend.agents.graph import get_multi_agent_graph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="LifeHub Agent API",
    description="AI assistant with LangGraph orchestration",
    version="0.1.0",
)

# Add CORS middleware for frontend
# Allow all origins in production (Vercel URLs vary)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Render."""
    return {"status": "ok"}


class Message(BaseModel):
    """A single message in the conversation."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Request body for /chat endpoint."""
    messages: list[Message]
    provider: str = "openai"  # "openai" or "ollama"
    debug: bool = False  # If true, include plan and context_log in response


def convert_messages(messages: list[Message]) -> list:
    """Convert API messages to LangChain message format."""
    lc_messages = []
    for msg in messages:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))
        # Skip system messages for now - handled in graph
    return lc_messages


async def stream_response(
    messages: list[Message], 
    provider: str = "openai",
    debug: bool = False,
) -> AsyncGenerator[str, None]:
    """Stream the multi-agent response using Server-Sent Events (SSE).
    
    Event types:
    - {"type": "start"}: Stream started
    - {"type": "plan", "plan": [...]}: Execution plan (debug mode)
    - {"type": "step", "step": int, "action": str}: Step execution (debug mode)
    - {"type": "token", "content": "..."}: Token from model
    - {"type": "tool_start", "name": "...", "input": {...}}: Tool execution started
    - {"type": "tool_end", "name": "...", "output": {...}}: Tool execution completed
    - {"type": "context_log", "log": [...]}: Context log (debug mode)
    - {"type": "end"}: Stream completed
    - {"type": "error", "message": "..."}: Error occurred
    """
    lc_messages = convert_messages(messages)
    
    try:
        agent_graph = get_multi_agent_graph(provider=provider)
    except Exception as e:
        logger.error(f"Failed to get agent graph: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        return
    
    # Signal stream start
    yield f"data: {json.dumps({'type': 'start'})}\n\n"
    
    plan_sent = False
    context_log_sent = False
    
    try:
        # Stream events from the graph
        async for event in agent_graph.astream_events(
            {
                "messages": lc_messages,
                "plan": None,
                "current_step": 0,
                "context_log": [],
                "final_answer": None,
            },
            version="v2",
        ):
            kind = event["event"]
            
            # Debug: send plan after planner completes
            if debug and kind == "on_chain_end" and not plan_sent:
                output = event.get("data", {}).get("output", {})
                if isinstance(output, dict) and "plan" in output and output["plan"]:
                    yield f"data: {json.dumps({'type': 'plan', 'plan': output['plan']})}\n\n"
                    plan_sent = True
            
            # Debug: send context log updates
            if debug and kind == "on_chain_end" and not context_log_sent:
                output = event.get("data", {}).get("output", {})
                if isinstance(output, dict) and "context_log" in output and output["context_log"]:
                    # Only send if we have new entries
                    yield f"data: {json.dumps({'type': 'context_log', 'log': output['context_log']})}\n\n"
            
            # Stream tokens from the model (explainer output)
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = chunk.content
                if content:
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            
            # Notify about tool calls starting
            elif kind == "on_tool_start":
                tool_name = event["name"]
                tool_input = event["data"].get("input", {})
                logger.info(f"Tool start: {tool_name} with input {tool_input}")
                yield f"data: {json.dumps({'type': 'tool_start', 'name': tool_name, 'input': tool_input})}\n\n"
            
            # Notify about tool calls completing
            elif kind == "on_tool_end":
                tool_name = event["name"]
                tool_output = event["data"].get("output")
                # Convert to serializable format if it's a LangChain message
                if hasattr(tool_output, "content"):
                    tool_output = tool_output.content
                elif not isinstance(tool_output, (dict, list, str, int, float, bool, type(None))):
                    tool_output = str(tool_output)
                logger.info(f"Tool end: {tool_name}")
                yield f"data: {json.dumps({'type': 'tool_end', 'name': tool_name, 'output': tool_output})}\n\n"
    
    except Exception as e:
        logger.error(f"Stream error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        return
    
    # Signal stream end
    yield f"data: {json.dumps({'type': 'end'})}\n\n"


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "lifehub-agent"}


@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint that streams responses from the multi-agent system.
    
    Accepts a list of messages and returns a streaming response
    with the agent's reply.
    
    Set debug=true in request body to include plan and context_log in stream.
    """
    logger.info(f"Chat request: {len(request.messages)} messages, provider={request.provider}, debug={request.debug}")
    return StreamingResponse(
        stream_response(request.messages, provider=request.provider, debug=request.debug),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/chat/sync")
async def chat_sync(request: ChatRequest):
    """Non-streaming chat endpoint for simpler testing.
    
    Returns the final response as JSON.
    Set debug=true to include plan and context_log in response.
    """
    logger.info(f"Sync chat request: {len(request.messages)} messages, provider={request.provider}, debug={request.debug}")
    
    lc_messages = convert_messages(request.messages)
    agent_graph = get_multi_agent_graph(provider=request.provider)
    
    # Run the graph to completion
    result = await agent_graph.ainvoke({
        "messages": lc_messages,
        "plan": None,
        "current_step": 0,
        "context_log": [],
        "final_answer": None,
    })
    
    # Get the final answer
    final_answer = result.get("final_answer", "")
    if not final_answer and result.get("messages"):
        final_answer = result["messages"][-1].content
    
    # Build response
    response = {
        "role": "assistant",
        "content": final_answer,
    }
    
    # Include debug info if requested
    if request.debug:
        response["plan"] = result.get("plan", [])
        response["context_log"] = result.get("context_log", [])
    
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
