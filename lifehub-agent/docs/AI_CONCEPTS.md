# AI Concepts Explained (ELI5)

A beginner-friendly guide to the AI concepts used in LifeHub Agent.

---

## Table of Contents

1. [Large Language Models (LLMs)](#1-large-language-models-llms)
2. [Embeddings](#2-embeddings)
3. [Vector Databases](#3-vector-databases)
4. [RAG (Retrieval-Augmented Generation)](#4-rag-retrieval-augmented-generation)
5. [Tool Calling / Function Calling](#5-tool-calling--function-calling)
6. [LangGraph](#6-langgraph)
7. [Multi-Agent Architecture](#7-multi-agent-architecture)
8. [Streaming (SSE)](#8-streaming-sse)
9. [MCP (Model Context Protocol)](#9-mcp-model-context-protocol)
10. [Putting It All Together](#10-putting-it-all-together)

---

## 1. Large Language Models (LLMs)

### What is it?
An LLM is like a super-smart autocomplete. It predicts the next word based on everything it learned from reading billions of documents.

### ELI5
Imagine you read every book, website, and article ever written. Now someone asks you a question, and you answer based on patterns you remember. That's an LLM.

### In LifeHub Agent
```
┌─────────────────────────────────────────────────────┐
│                   LLM Providers                      │
├─────────────────────────────────────────────────────┤
│  OpenAI (Cloud)          │  Ollama (Local)          │
│  • GPT-4o-mini           │  • Llama 3.2             │
│  • Fast, high quality    │  • Free, private         │
│  • Requires API key      │  • Runs on your machine  │
└─────────────────────────────────────────────────────┘
```

**Code location**: `backend/models.py`

---

## 2. Embeddings

### What is it?
Embeddings convert text into numbers (vectors) that capture meaning. Similar meanings = similar numbers.

### ELI5
Imagine every word/sentence has a GPS coordinate. "Happy" and "Joyful" are close together. "Happy" and "Refrigerator" are far apart.

### Visual Example
```
Text                    →  Embedding (simplified)
─────────────────────────────────────────────────
"I love running"        →  [0.8, 0.2, 0.9, ...]
"I enjoy jogging"       →  [0.7, 0.3, 0.9, ...]  ← Similar!
"Buy groceries"         →  [0.1, 0.9, 0.2, ...]  ← Different!
```

### Why does this matter?
- **Keyword search**: "running" only matches "running"
- **Semantic search**: "running" also matches "jogging", "marathon", "cardio"

### In LifeHub Agent
```python
# backend/rag/embeddings.py
# Supports both OpenAI and Ollama embeddings

EMBEDDING_PROVIDER=openai  →  text-embedding-3-small (1536 dimensions)
EMBEDDING_PROVIDER=ollama  →  nomic-embed-text (768 dimensions)
```

---

## 3. Vector Databases

### What is it?
A database optimized for storing and searching embeddings (vectors). Instead of "find exact match", it finds "find similar".

### ELI5
Regular database: "Find all books titled 'Harry Potter'"
Vector database: "Find all books *similar to* Harry Potter" (returns fantasy, magic, coming-of-age stories)

### How it works
```
┌─────────────────────────────────────────────────────────────┐
│                     Vector Database                          │
├─────────────────────────────────────────────────────────────┤
│  ID        │  Text                    │  Vector              │
├────────────┼──────────────────────────┼──────────────────────┤
│  note_1    │  "Monday: 3 mile run"    │  [0.8, 0.2, 0.9...]  │
│  note_2    │  "Pasta recipe..."       │  [0.1, 0.7, 0.3...]  │
│  note_3    │  "Wednesday: tempo run"  │  [0.7, 0.3, 0.8...]  │
└─────────────────────────────────────────────────────────────┘

Query: "What's my running schedule?"
Query Vector: [0.75, 0.25, 0.85...]

Result: note_1 and note_3 (closest vectors)
```

### In LifeHub Agent
We use **ChromaDB** - an embedded vector database that stores data as files on disk.

```
backend/state/chroma/     ← Vector database files
├── chroma.sqlite3        ← Metadata
└── [uuid]/               ← Vector data (parquet files)
```

**No external database server needed!** It's just files.

---

## 4. RAG (Retrieval-Augmented Generation)

### What is it?
RAG = "Look it up, then answer"

LLMs only know what they were trained on. RAG lets them access YOUR data by:
1. **Retrieving** relevant information from a knowledge base
2. **Augmenting** the LLM's prompt with that information
3. **Generating** a response using both

### ELI5
It's like an open-book exam. Instead of memorizing everything, you can look up answers in your notes before responding.

### The Problem RAG Solves
```
Without RAG:
User: "What's my running schedule?"
LLM: "I don't have access to your personal schedule."

With RAG:
User: "What's my running schedule?"
System: [Searches notes, finds running plan]
LLM: "Based on your notes, you run Mon/Wed/Fri..."
```

### RAG Pipeline
```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION (one-time setup)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Markdown     Split into      Embed each       Store in        │
│   Files    →   Chunks      →   Chunk        →   ChromaDB        │
│                (500 chars)     (vectors)        (persist)        │
│                                                                  │
│   fitness.md   ["Monday: 3     [0.8, 0.2...]   ID: fitness_0    │
│                 mile run",     [0.7, 0.3...]   ID: fitness_1    │
│                 "Wednesday:                                      │
│                 tempo..."]                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL (at query time)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Query    Embed         Search           Return Top       │
│              →  Query     →   ChromaDB     →   Matching Chunks  │
│                                                                  │
│   "running      [0.75,        Find similar     "Monday: 3 mile  │
│    schedule"    0.25...]      vectors           run...",        │
│                                                 "Wednesday:      │
│                                                  tempo..."       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    GENERATION (final step)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   LLM Prompt:                                                    │
│   "User asked: What's my running schedule?                       │
│                                                                  │
│    Context from notes:                                           │
│    - Monday: 3 mile easy run                                     │
│    - Wednesday: 5 mile tempo run                                 │
│    - Friday: recovery run                                        │
│                                                                  │
│    Please answer based on this context."                         │
│                                                                  │
│   LLM Response: "Your running schedule is..."                    │
└─────────────────────────────────────────────────────────────────┘
```

### In LifeHub Agent
```
backend/rag/
├── embeddings.py      # Convert text ↔ vectors (OpenAI or Ollama)
├── store.py           # ChromaDB setup
└── ingest_notes.py    # Ingestion script

backend/tools/
└── notes.py           # search_notes tool (retrieval)

backend/notes/
├── fitness_example.md # Your notes go here
└── recipes_example.md
```

---

## 5. Tool Calling / Function Calling

### What is it?
LLMs can't actually DO things - they can only generate text. Tool calling lets them request actions by outputting structured function calls.

### ELI5
The LLM is like a manager who can't use a computer. It writes instructions on paper: "Please look up the weather for Tokyo." A helper (your code) reads the paper, does the task, and reports back.

### How it works
```
┌─────────────────────────────────────────────────────────────────┐
│  User: "What's the weather in Tokyo?"                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LLM thinks: "I need to call the weather tool"                   │
│                                                                  │
│  LLM outputs: {                                                  │
│    "tool": "get_weather",                                        │
│    "arguments": {"city": "Tokyo"}                                │
│  }                                                               │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  Your code:                                                      │
│  1. Parses the tool call                                         │
│  2. Executes get_weather("Tokyo")                                │
│  3. Gets result: {"temp": "45°F", "conditions": "cloudy"}        │
│  4. Sends result back to LLM                                     │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  LLM generates final response:                                   │
│  "The weather in Tokyo is 45°F and cloudy."                      │
└─────────────────────────────────────────────────────────────────┘
```

### In LifeHub Agent
```
backend/tools/
├── weather.py    # get_weather - calls Open-Meteo API
├── tasks.py      # add_task - writes to tasks.json
└── notes.py      # search_notes - RAG search
```

Tools are defined with the `@tool` decorator:
```python
@tool
def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    # ... API call ...
    return {"city": city, "temp": "45°F", ...}
```

---

## 6. LangGraph

### What is it?
LangGraph is a framework for building multi-step LLM applications as state machines (graphs).

### ELI5
Think of it like a flowchart for your AI:
- **Nodes** = Things to do (call LLM, run tool, etc.)
- **Edges** = What happens next
- **State** = Data that flows through

### Why use it?
```
Without LangGraph:              With LangGraph:
─────────────────────           ─────────────────────
if user_wants_weather:          graph.add_node("planner", ...)
    plan = make_plan()          graph.add_node("worker", ...)
    if plan.has_tools:          graph.add_edge("planner", "worker")
        for tool in plan:       
            result = run(tool)  # Clean, modular, debuggable
            if error:           
                handle_error()  
    response = explain()        
```

### Visual
```
        ┌─────────┐
        │  START  │
        └────┬────┘
             │
             ▼
        ┌─────────┐
        │ PLANNER │  ← Creates execution plan
        └────┬────┘
             │
             ▼
        ┌─────────┐
        │ WORKER  │  ← Executes tools
        └────┬────┘
             │
             ▼
       ┌──────────┐
       │ EXPLAINER│  ← Generates response
       └────┬─────┘
            │
            ▼
        ┌─────────┐
        │   END   │
        └─────────┘
```

### State flows through
```python
class MultiAgentState(TypedDict):
    messages: list          # Conversation history
    plan: list[PlanStep]    # From Planner
    context_log: list       # Tool results from Worker
    final_answer: str       # From Explainer
```

### In LifeHub Agent
**Code location**: `backend/agents/graph.py`

---

## 7. Multi-Agent Architecture

### What is it?
Instead of one LLM doing everything, multiple specialized "agents" work together, each with a specific role.

### ELI5
It's like a restaurant:
- **Planner** = Manager who takes orders and assigns tasks
- **Worker** = Kitchen staff who actually cook
- **Explainer** = Waiter who presents the food nicely

### Why multiple agents?
| Single Agent | Multi-Agent |
|--------------|-------------|
| One prompt does everything | Specialized prompts |
| Hard to debug | Clear responsibility |
| Inconsistent output | Structured flow |
| Can't easily add features | Modular, extensible |

### LifeHub's Three Agents

```
┌─────────────────────────────────────────────────────────────────┐
│                         PLANNER                                  │
├─────────────────────────────────────────────────────────────────┤
│  Role: Analyze request, create structured plan                   │
│  Temperature: 0.3 (more deterministic)                           │
│  Output: JSON array of steps                                     │
│                                                                  │
│  Example output:                                                 │
│  [                                                               │
│    {"step": 1, "tool": "search_notes", "input": {...}},         │
│    {"step": 2, "tool": "add_task", "input": {...}},             │
│    {"step": 3, "tool": null, "description": "Synthesize"}       │
│  ]                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         WORKER                                   │
├─────────────────────────────────────────────────────────────────┤
│  Role: Execute each step in the plan                             │
│  Temperature: 0.2 (very deterministic)                           │
│  Actions: Call tools, log results                                │
│                                                                  │
│  For each step:                                                  │
│  1. If step has tool → execute it                                │
│  2. Log result to context_log                                    │
│  3. Move to next step                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        EXPLAINER                                 │
├─────────────────────────────────────────────────────────────────┤
│  Role: Generate user-friendly response                           │
│  Temperature: 0.7 (more creative)                                │
│  Input: messages + plan + context_log                            │
│  Output: Natural language response (streamed)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Streaming (SSE)

### What is it?
Server-Sent Events (SSE) allow the server to push data to the client in real-time, token by token.

### ELI5
Without streaming: You wait 10 seconds, then see the entire response at once.
With streaming: You see each word appear as it's generated, like watching someone type.

### How it works
```
┌─────────────────────────────────────────────────────────────────┐
│  Without Streaming                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Client ──────────────────────────────────────────► Server       │
│         │  POST /chat                              │             │
│         │                                          │             │
│         │         (waiting... 5 seconds)           │             │
│         │                                          │             │
│         ◄──────────────────────────────────────────│             │
│           "The weather in Tokyo is 45°F..."        │             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  With Streaming (SSE)                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Client ──────────────────────────────────────────► Server       │
│         │  POST /chat                              │             │
│         ◄─ data: {"token": "The"}                  │             │
│         ◄─ data: {"token": " weather"}             │             │
│         ◄─ data: {"token": " in"}                  │             │
│         ◄─ data: {"token": " Tokyo"}               │             │
│         ◄─ data: {"token": " is"}                  │             │
│         ◄─ data: {"token": " 45°F"}                │             │
│         ◄─ data: [DONE]                            │             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### In LifeHub Agent
**Backend** (`main.py`):
```python
async def stream_response(...):
    async for event in graph.astream_events(...):
        if event["event"] == "on_chat_model_stream":
            token = event["data"]["chunk"].content
            yield f"data: {json.dumps({'token': token})}\n\n"
```

**Frontend** (`page.tsx`):
```typescript
const reader = response.body.getReader();
while (true) {
    const { done, value } = await reader.read();
    // Parse SSE data, append token to UI
}
```

---

## 9. MCP (Model Context Protocol)

### What is it?
MCP is an open protocol that lets AI applications connect to external tools and data sources in a standardized way. Think of it as a "USB for AI" - any MCP-compatible tool can plug into any MCP-compatible AI app.

### ELI5
Imagine every AI assistant speaks a different language. MCP is like a universal translator - it lets your AI talk to any tool (web search, databases, file systems) without writing custom code for each one.

### The Problem MCP Solves
```
Without MCP:
┌─────────────────────────────────────────────────────────────────┐
│  Your AI App                                                     │
│  ├── Custom code for Google Search API                          │
│  ├── Custom code for GitHub API                                 │
│  ├── Custom code for Slack API                                  │
│  └── Custom code for every new tool...  😫                      │
└─────────────────────────────────────────────────────────────────┘

With MCP:
┌─────────────────────────────────────────────────────────────────┐
│  Your AI App (MCP Client)                                        │
│  └── One MCP client that connects to ANY MCP server             │
└─────────────────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ Search  │   │ GitHub  │   │  Slack  │
    │ Server  │   │ Server  │   │ Server  │
    └─────────┘   └─────────┘   └─────────┘
```

### How MCP Works
```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Architecture                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │  MCP Client  │ ◄─────► │  MCP Server  │                      │
│  │  (Your App)  │  JSON   │  (External)  │                      │
│  └──────────────┘         └──────────────┘                      │
│                                                                  │
│  Client actions:           Server provides:                      │
│  • list_tools()            • Tool definitions                   │
│  • call_tool(name, args)   • Tool execution                     │
│  • list_resources()        • Data resources                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### MCP vs Regular APIs

| Aspect | Regular API | MCP |
|--------|-------------|-----|
| Discovery | Read docs, write code | `list_tools()` returns schema |
| Integration | Custom per API | One client for all servers |
| Schema | Varies wildly | Standardized JSON Schema |
| AI-friendly | Not designed for LLMs | Built for AI tool calling |

### In LifeHub Agent

We use MCP as a **client** to connect to external MCP servers like Brave Search:

```
┌─────────────────────────────────────────────────────────────────┐
│                    LifeHub Agent                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Built-in Tools                              │    │
│  │  • get_weather    • add_task    • search_notes          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              +                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              MCP Client                                  │    │
│  │  Dynamically loads tools from MCP servers                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │  Brave Search    │
                    │  MCP Server      │
                    │  ────────────    │
                    │  • brave_web_search
                    │  • brave_news_search
                    │  • brave_image_search
                    │  • brave_video_search
                    └──────────────────┘
```

### How LifeHub Integrates MCP

**1. On Startup** - Load tools from configured MCP servers:
```python
# backend/mcp/client.py
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()  # Get available tools
```

**2. Convert to LangChain** - Wrap MCP tools for our agent:
```python
# MCP tool schema → LangChain StructuredTool
StructuredTool.from_function(
    func=sync_call_mcp_tool,
    name="brave_web_search",
    description="Search the web...",
    args_schema=BraveWebSearchArgs,  # Built from MCP schema
)
```

**3. Agent Uses Them** - Planner can now include MCP tools in plans:
```json
{
  "plan": [
    {"step": 1, "tool": "brave_web_search", "tool_input": {"query": "Python 3.13 features"}},
    {"step": 2, "tool": null, "description": "Summarize results"}
  ]
}
```

### Code Structure
```
backend/mcp/
├── __init__.py      # Package exports
├── config.py        # Server configurations (which MCP servers to connect to)
└── client.py        # MCP client wrapper (connects, lists tools, calls tools)
```

### Configuration
MCP servers are enabled via environment variables:
```bash
# Enable Brave Search MCP
export BRAVE_API_KEY="your-api-key"

# On startup, LifeHub will:
# 1. Detect BRAVE_API_KEY is set
# 2. Connect to Brave Search MCP server
# 3. Load 6 tools (web_search, news_search, etc.)
# 4. Make them available to the agent
```

### Available MCP Servers
| Server | What it provides | API Key? |
|--------|------------------|----------|
| **Brave Search** | Web, news, image, video search | Yes (free tier) |
| **GitHub** | Repos, issues, PRs | Yes |
| **Filesystem** | Read/write local files | No |
| **Postgres** | Database queries | No |

---

## 10. Putting It All Together

### Complete Request Flow

```
User: "Based on my notes, what's my running plan? Also add a task to buy shoes."

┌─────────────────────────────────────────────────────────────────┐
│ 1. FRONTEND                                                      │
│    • User types message                                          │
│    • POST /chat with {messages, provider: "openai"}              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. API LAYER (FastAPI)                                           │
│    • Receives request                                            │
│    • Converts to LangChain messages                              │
│    • Invokes LangGraph                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. PLANNER AGENT                                                 │
│    • Analyzes: "User wants running info + add task"              │
│    • Creates plan:                                               │
│      [                                                           │
│        {step: 1, tool: "search_notes", input: {query: "running"}}│
│        {step: 2, tool: "add_task", input: {task: "buy shoes"}}   │
│        {step: 3, tool: null, desc: "Synthesize response"}        │
│      ]                                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. WORKER AGENT                                                  │
│                                                                  │
│    Step 1: search_notes("running")                               │
│    ├─ Embed query → [0.75, 0.25, ...]                            │
│    ├─ Search ChromaDB for similar vectors                        │
│    └─ Return: ["Monday: 3 mile run", "Wednesday: tempo..."]      │
│                                                                  │
│    Step 2: add_task("buy shoes")                                 │
│    └─ Write to tasks.json → Return: "Task added successfully"    │
│                                                                  │
│    Step 3: (no tool, just logged)                                │
│                                                                  │
│    context_log now contains all results                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. EXPLAINER AGENT                                               │
│    • Receives: messages + plan + context_log                     │
│    • Calls LLM with all context                                  │
│    • Streams response token by token                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (SSE Stream)
┌─────────────────────────────────────────────────────────────────┐
│ 6. FRONTEND                                                      │
│    • Receives tokens in real-time                                │
│    • Displays: "Based on your notes, here's your running plan:   │
│      • Monday: 3 mile easy run                                   │
│      • Wednesday: 5 mile tempo run                               │
│      ...                                                         │
│      I've also added 'buy shoes' to your task list!"             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference

| Concept | One-liner |
|---------|-----------|
| **LLM** | AI that predicts text based on patterns |
| **Embeddings** | Text → Numbers that capture meaning |
| **Vector DB** | Database for similarity search |
| **RAG** | Look up info, then answer |
| **Tool Calling** | LLM requests actions, code executes them |
| **LangGraph** | Flowchart framework for LLM apps |
| **Multi-Agent** | Specialized LLMs working together |
| **Streaming** | Real-time token-by-token delivery |
| **MCP** | Universal protocol for AI tool integration |

---

## Further Reading

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [RAG Explained (LangChain)](https://python.langchain.com/docs/tutorials/rag/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Brave Search MCP Server](https://github.com/brave/brave-search-mcp-server)
