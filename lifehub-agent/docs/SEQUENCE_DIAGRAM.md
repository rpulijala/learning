# LifeHub Agent - Detailed Request Flow Sequence Diagram

This document shows the complete back-and-forth calls between all entities during an end-to-end request lifecycle.

## Entities

| Entity | Description |
|--------|-------------|
| **User** | End user interacting via browser |
| **Frontend** | Next.js React app |
| **FastAPI** | Backend API server |
| **LangGraph** | Orchestration framework |
| **Planner Agent** | Creates execution plan |
| **Worker Agent** | Executes tools |
| **Explainer Agent** | Generates final response |
| **LLM (OpenAI/Ollama)** | Language model API |
| **Tools** | Built-in tools (weather, tasks, notes) |
| **MCP Server** | External MCP servers (Brave Search) |
| **ChromaDB** | Vector database for RAG |
| **Embeddings API** | OpenAI/Ollama embeddings |

---

## Example Query

```
"What's in my notes about running? Also search the web for marathon training tips."
```

---

## Full Sequence Diagram

```
┌──────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌────────┐ ┌───────────┐ ┌─────┐ ┌───────┐ ┌────────────┐ ┌──────────┐ ┌────────────────┐
│ User │ │ Frontend │ │ FastAPI │ │ LangGraph│ │ Planner │ │ Worker │ │ Explainer │ │ LLM │ │ Tools │ │ MCP Server │ │ ChromaDB │ │ Embeddings API │
└──┬───┘ └────┬─────┘ └────┬────┘ └────┬─────┘ └────┬────┘ └───┬────┘ └─────┬─────┘ └──┬──┘ └───┬───┘ └─────┬──────┘ └────┬─────┘ └───────┬────────┘
   │          │            │           │            │          │            │          │        │           │             │              │
   │ 1. Type message       │           │            │          │            │          │        │           │             │              │
   │─────────>│            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │ 2. POST /chat          │            │          │            │          │        │           │             │              │
   │          │ {messages, provider}   │            │          │            │          │        │           │             │              │
   │          │───────────>│           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │ 3. SSE: {"type":"start"}            │          │            │          │        │           │             │              │
   │          │<───────────│           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │ 4. astream_events()    │          │            │          │        │           │             │              │
   │          │            │──────────>│            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │ 5. START → planner    │            │          │        │           │             │              │
   │          │            │           │───────────>│          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
```

### Phase 1: Planning (Planner Agent → LLM)

```
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │ 6. Build planner prompt           │        │           │             │              │
   │          │            │           │            │ [SystemMessage: "You are a        │        │           │             │              │
   │          │            │           │            │  planning agent... Available      │        │           │             │              │
   │          │            │           │            │  tools: search_notes, get_weather,│        │           │             │              │
   │          │            │           │            │  add_task, brave_web_search..."]  │        │           │             │              │
   │          │            │           │            │ [HumanMessage: "User request:     │        │           │             │              │
   │          │            │           │            │  What's in my notes about         │        │           │             │              │
   │          │            │           │            │  running?..."]                    │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │ 7. planner_model.invoke(messages) │        │           │             │              │
   │          │            │           │            │─────────────────────────────────────────>│           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │   ┌──────┴──────┐ │           │             │              │
   │          │            │           │            │          │            │   │ LLM thinks: │ │           │             │              │
   │          │            │           │            │          │            │   │ - User wants│ │           │             │              │
   │          │            │           │            │          │            │   │   notes     │ │           │             │              │
   │          │            │           │            │          │            │   │ - User wants│ │           │             │              │
   │          │            │           │            │          │            │   │   web search│ │           │             │              │
   │          │            │           │            │          │            │   │ - Need 3    │ │           │             │              │
   │          │            │           │            │          │            │   │   steps     │ │           │             │              │
   │          │            │           │            │          │            │   └──────┬──────┘ │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │ 8. LLM Response (JSON plan)       │        │           │             │              │
   │          │            │           │            │<─────────────────────────────────────────│           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │ Response:│            │          │        │           │             │              │
   │          │            │           │            │ {        │            │          │        │           │             │              │
   │          │            │           │            │   "plan": [           │          │        │           │             │              │
   │          │            │           │            │     {"step": 1, "tool": "search_notes",   │           │             │              │
   │          │            │           │            │      "tool_input": {"query": "running"}}, │           │             │              │
   │          │            │           │            │     {"step": 2, "tool": "brave_web_search",│          │             │              │
   │          │            │           │            │      "tool_input": {"query": "marathon    │           │             │              │
   │          │            │           │            │       training tips"}},           │        │           │             │              │
   │          │            │           │            │     {"step": 3, "tool": null,     │        │           │             │              │
   │          │            │           │            │      "description": "Synthesize"} │        │           │             │              │
   │          │            │           │            │   ]      │            │          │        │           │             │              │
   │          │            │           │            │ }        │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │ 9. Return plan to state            │          │        │           │             │              │
   │          │            │           │<──────────│          │            │          │        │           │             │              │
   │          │            │           │           │            │          │            │          │        │           │             │              │
   │          │ 10. SSE: {"type":"plan", "plan":[...]}         │            │          │        │           │             │              │
   │          │<───────────│           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
```

### Phase 2: Execution (Worker Agent → Tools)

```
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │ 11. planner → worker  │            │          │        │           │             │              │
   │          │            │           │────────────────────────>          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │ ┌────────┴────────┐   │          │        │           │             │              │
   │          │            │           │            │ │ Worker iterates │   │          │        │           │             │              │
   │          │            │           │            │ │ through plan    │   │          │        │           │             │              │
   │          │            │           │            │ └────────┬────────┘   │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
```

#### Step 1: search_notes (RAG Flow)

```
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │ 12. SSE: {"type":"tool_start", "name":"search_notes", "input":{...}}   │        │           │             │              │
   │          │<───────────│           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │ 13. tool.invoke({"query":"running"})      │             │              │
   │          │            │           │            │          │───────────────────────────────>│           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │ 14. get_single_embedding("running")    │
   │          │            │           │            │          │            │          │        │───────────────────────────────────────>│
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │   ┌──────────┴──────────┐
   │          │            │           │            │          │            │          │        │           │             │   │ OpenAI/Ollama       │
   │          │            │           │            │          │            │          │        │           │             │   │ embeddings.create() │
   │          │            │           │            │          │            │          │        │           │             │   │ model: text-embed-  │
   │          │            │           │            │          │            │          │        │           │             │   │ ding-3-small        │
   │          │            │           │            │          │            │          │        │           │             │   └──────────┬──────────┘
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │ 15. Return embedding vector [0.023, -0.156, ...]  │
   │          │            │           │            │          │            │          │        │<───────────────────────────────────────│
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │ 16. collection.query(embedding, n=5)  │              │
   │          │            │           │            │          │            │          │        │──────────────────────────>│              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │  ┌──────────┴──────────┐   │
   │          │            │           │            │          │            │          │        │           │  │ ChromaDB:           │   │
   │          │            │           │            │          │            │          │        │           │  │ - Cosine similarity │   │
   │          │            │           │            │          │            │          │        │           │  │ - Find top 5 chunks │   │
   │          │            │           │            │          │            │          │        │           │  └──────────┬──────────┘   │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │ 17. Return matching chunks             │
   │          │            │           │            │          │            │          │        │ [{content: "My running plan: Mon 3mi...", source: "fitness.md"}]
   │          │            │           │            │          │            │          │        │<──────────────────────────│              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │ 18. Return formatted results  │           │             │              │
   │          │            │           │            │          │<──────────────────────────────│           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │ 19. SSE: {"type":"tool_end", "name":"search_notes", "output":[...]}    │        │           │             │              │
   │          │<───────────│           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │ 20. Append to context_log:    │           │             │              │
   │          │            │           │            │          │ {step:1, action:"search_notes({query:'running'})",      │              │
   │          │            │           │            │          │  result:"[{content:'My running plan...'}]"}│             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
```

#### Step 2: brave_web_search (MCP Flow)

```
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │ 21. SSE: {"type":"tool_start", "name":"brave_web_search", "input":{...}}       │           │             │              │
   │          │<───────────│           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │ 22. tool.invoke({"query":"marathon training tips"})     │              │
   │          │            │           │            │          │────────────────────────────────────────────>│             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │    ┌──────┴──────┐      │              │
   │          │            │           │            │          │            │          │        │    │ MCP Client: │      │              │
   │          │            │           │            │          │            │          │        │    │ 1. stdio_   │      │              │
   │          │            │           │            │          │            │          │        │    │    client() │      │              │
   │          │            │           │            │          │            │          │        │    │ 2. session. │      │              │
   │          │            │           │            │          │            │          │        │    │    init()   │      │              │
   │          │            │           │            │          │            │          │        │    │ 3. call_    │      │              │
   │          │            │           │            │          │            │          │        │    │    tool()   │      │              │
   │          │            │           │            │          │            │          │        │    └──────┬──────┘      │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │ 23. Brave Search API call
   │          │            │           │            │          │            │          │        │           │ (via npx brave-search-mcp)
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │ 24. Return search results     │           │             │              │
   │          │            │           │            │          │ "1. Marathon Training Guide... 2. Beginner tips..."     │              │
   │          │            │           │            │          │<────────────────────────────────────────────│             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │ 25. SSE: {"type":"tool_end", "name":"brave_web_search", "output":"..."}        │           │             │              │
   │          │<───────────│           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │ 26. Append to context_log:    │           │             │              │
   │          │            │           │            │          │ {step:2, action:"brave_web_search(...)",   │             │              │
   │          │            │           │            │          │  result:"1. Marathon Training Guide..."}   │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
```

#### Step 3: Synthesis (No Tool)

```
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │ 27. Append to context_log:    │           │             │              │
   │          │            │           │            │          │ {step:3, action:"Synthesize results",      │             │              │
   │          │            │           │            │          │  result:"Reasoning/synthesis step completed"}            │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │ 28. Return context_log to state    │          │        │           │             │              │
   │          │            │           │<───────────────────────│            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │ 29. SSE: {"type":"context_log", "log":[...]}   │            │          │        │           │             │              │
   │          │<───────────│           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
```

### Phase 3: Explanation (Explainer Agent → LLM with Streaming)

```
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │ 30. worker → explainer│            │          │        │           │             │              │
   │          │            │           │─────────────────────────────────────>          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │ 31. Build explainer prompt     │             │              │
   │          │            │           │            │          │            │ [SystemMessage: "You are an   │             │              │
   │          │            │           │            │          │            │  explainer agent... Be helpful,│             │              │
   │          │            │           │            │          │            │  concise, natural..."]        │             │              │
   │          │            │           │            │          │            │ [HumanMessage:                │             │              │
   │          │            │           │            │          │            │  "User request: What's in my  │             │              │
   │          │            │           │            │          │            │   notes about running?...     │             │              │
   │          │            │           │            │          │            │                               │             │              │
   │          │            │           │            │          │            │   Execution plan:             │             │              │
   │          │            │           │            │          │            │   - Step 1: search_notes      │             │              │
   │          │            │           │            │          │            │   - Step 2: brave_web_search  │             │              │
   │          │            │           │            │          │            │   - Step 3: Synthesize        │             │              │
   │          │            │           │            │          │            │                               │             │              │
   │          │            │           │            │          │            │   Results from execution:     │             │              │
   │          │            │           │            │          │            │   - Step 1: search_notes...   │             │              │
   │          │            │           │            │          │            │     Result: [{content:...}]   │             │              │
   │          │            │           │            │          │            │   - Step 2: brave_web_search..│             │              │
   │          │            │           │            │          │            │     Result: 1. Marathon...    │             │              │
   │          │            │           │            │          │            │   ..."]                       │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │ 32. explainer_model.invoke(messages) ──────>│             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │  ┌─────┴─────┐     │             │              │
   │          │            │           │            │          │            │          │  │ LLM       │     │             │              │
   │          │            │           │            │          │            │          │  │ generates │     │             │              │
   │          │            │           │            │          │            │          │  │ response  │     │             │              │
   │          │            │           │            │          │            │          │  │ STREAMING │     │             │              │
   │          │            │           │            │          │            │          │  └─────┬─────┘     │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │ 33. Stream token: "Based"     │             │              │
   │          │            │           │            │          │            │<─────────────────│           │             │              │
   │          │ 34. SSE: {"type":"token", "content":"Based"}   │            │          │        │           │             │              │
   │          │<───────────│           │            │          │            │          │        │           │             │              │
   │ 35. Show │            │           │            │          │            │          │        │           │             │              │
   │ "Based"  │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │ 36. Stream token: " on"       │             │              │
   │          │            │           │            │          │            │<─────────────────│           │             │              │
   │          │ 37. SSE: {"type":"token", "content":" on"}     │            │          │        │           │             │              │
   │          │<───────────│           │            │          │            │          │        │           │             │              │
   │ 38. Show │            │           │            │          │            │          │        │           │             │              │
   │ "Based on"            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │ ... (continues streaming)     │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │ 39. Final token + done        │             │              │
   │          │            │           │            │          │            │<─────────────────│           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │ 40. Return final_answer to state   │          │        │           │             │              │
   │          │            │           │<────────────────────────────────────│          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
```

### Phase 4: Completion

```
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │ 41. explainer → END   │            │          │        │           │             │              │
   │          │            │           │───────────>│          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │          │ 42. SSE: {"type":"end"}│            │          │            │          │        │           │             │              │
   │          │<───────────│           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
   │ 43. Show │            │           │            │          │            │          │        │           │             │              │
   │ complete │            │           │            │          │            │          │        │           │             │              │
   │ response │            │           │            │          │            │          │        │           │             │              │
   │          │            │           │            │          │            │          │        │           │             │              │
```

---

## Summary: When Data Goes to LLM

| Phase | LLM Call | Input | Output | Streaming? |
|-------|----------|-------|--------|------------|
| **1. Planning** | `planner_model.invoke()` | System prompt + user message | JSON execution plan | No |
| **2. Execution** | None (tools only) | - | - | - |
| **3. Explanation** | `explainer_model.invoke()` | System prompt + plan + context_log | Final user response | **Yes** |

### Key Points:

1. **LLM is called exactly 2 times** per request:
   - Once for planning (non-streaming)
   - Once for explanation (streaming)

2. **Worker does NOT call LLM** - it directly invokes tools

3. **RAG flow** (search_notes):
   - Calls Embeddings API to vectorize query
   - Queries ChromaDB for similar chunks
   - Returns raw results (no LLM involved)

4. **MCP flow** (brave_web_search):
   - Spawns MCP server process via stdio
   - Sends JSON-RPC call to MCP server
   - MCP server calls external API (Brave)
   - Returns results (no LLM involved)

5. **Streaming** only happens in the Explainer phase

---

## Data Flow Summary

```
User Message
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                     PLANNER (LLM Call #1)                   │
│  Input: "What's in my notes about running? Also search..."  │
│  Output: JSON plan with 3 steps                             │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                     WORKER (No LLM)                         │
│                                                             │
│  Step 1: search_notes ──► Embeddings API ──► ChromaDB      │
│          └── Returns: note chunks                           │
│                                                             │
│  Step 2: brave_web_search ──► MCP Server ──► Brave API     │
│          └── Returns: web results                           │
│                                                             │
│  Step 3: (synthesis placeholder)                            │
│                                                             │
│  Output: context_log with all results                       │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXPLAINER (LLM Call #2)                   │
│  Input: user request + plan + context_log                   │
│  Output: Streamed natural language response                 │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
User sees streaming response
```

---

## SSE Event Types

| Event Type | When Sent | Contains |
|------------|-----------|----------|
| `start` | Stream begins | - |
| `plan` | After planner (debug mode) | Execution plan array |
| `tool_start` | Before each tool call | Tool name, input |
| `tool_end` | After each tool call | Tool name, output |
| `context_log` | After worker (debug mode) | Full context log |
| `token` | During explainer streaming | Single token string |
| `end` | Stream complete | - |
| `error` | On any error | Error message |
