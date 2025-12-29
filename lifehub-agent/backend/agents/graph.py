"""Multi-agent LangGraph graph with planner → worker → explainer flow."""

import json
import logging
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from backend.models import get_model_client
from backend.tools.weather import get_weather
from backend.tools.tasks import add_task
from backend.tools.notes import search_notes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the tools available to the worker
TOOLS = [get_weather, add_task, search_notes]
TOOL_MAP = {tool.name: tool for tool in TOOLS}


class PlanStep(TypedDict):
    """A single step in the execution plan."""
    step: int
    description: str
    tool: str | None
    tool_input: dict | None


class ContextLogEntry(TypedDict):
    """A single entry in the context log."""
    step: int
    action: str
    result: str


class MultiAgentState(TypedDict):
    """State for the multi-agent graph."""
    messages: Annotated[list[AnyMessage], add_messages]
    plan: list[PlanStep] | None
    current_step: int
    context_log: list[ContextLogEntry]
    final_answer: str | None


# System prompts for each agent
PLANNER_SYSTEM_PROMPT = """You are a planning agent for LifeHub. Your job is to analyze the user's request and create a structured execution plan.

Available tools:
- get_weather(city: str): Get weather information for a city
- add_task(task: str): Add a task to the user's task list
- search_notes(query: str): Search the user's personal notes (fitness plans, recipes, etc.)

Analyze the user's message and output a JSON plan with this exact format:
{
  "plan": [
    {"step": 1, "description": "Brief description of what to do", "tool": "tool_name or null", "tool_input": {"param": "value"} or null},
    {"step": 2, "description": "...", "tool": "...", "tool_input": {...}}
  ]
}

Guidelines:
- If the user asks about their notes, fitness, recipes, or personal information, use search_notes
- If the user asks about weather, use get_weather
- If the user wants to add/create a task or reminder, use add_task
- You can have multiple steps that use different tools
- Steps without tools are for reasoning/synthesis (set tool to null)
- Always end with a synthesis step (tool: null) to combine results

Output ONLY valid JSON, nothing else."""

WORKER_SYSTEM_PROMPT = """You are a worker agent executing a plan step. You have access to tools.

Based on the current step, call the appropriate tool if specified. If no tool is needed, just acknowledge the step.

Be precise and follow the plan exactly."""

EXPLAINER_SYSTEM_PROMPT = """You are an explainer agent for LifeHub. Your job is to produce the final user-friendly response.

You will receive:
1. The original user messages
2. The execution plan that was created
3. The context log with results from each step

Your response should:
1. Briefly mention what you did (1-2 sentences max)
2. Provide the main answer/information the user requested
3. If tasks were added, confirm them
4. If notes were consulted, you may cite the source

Be helpful, concise, and natural. Do not output JSON or technical details."""


def create_multi_agent_graph(provider: str = "openai"):
    """Create and compile the multi-agent LangGraph graph.
    
    Args:
        provider: Model provider to use ("openai" or "ollama")
    """
    # Get model clients for each agent role
    planner_model = get_model_client(provider=provider, streaming=False, temperature=0.3)
    worker_model = get_model_client(provider=provider, streaming=False, temperature=0.2)
    worker_model_with_tools = worker_model.bind_tools(TOOLS)
    explainer_model = get_model_client(provider=provider, streaming=True, temperature=0.7)
    
    def planner_node(state: MultiAgentState) -> dict:
        """Planner agent: analyzes request and creates execution plan."""
        logger.info("=== PLANNER NODE ===")
        
        messages = state["messages"]
        
        # Build planner prompt
        planner_messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=f"User request: {messages[-1].content if messages else 'No message'}")
        ]
        
        response = planner_model.invoke(planner_messages)
        logger.info(f"Planner raw response: {response.content}")
        
        # Parse the plan from JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            content = response.content.strip()
            if content.startswith("```"):
                # Remove markdown code block
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            
            plan_data = json.loads(content)
            plan = plan_data.get("plan", [])
            
            # Validate and normalize plan
            normalized_plan = []
            for i, step in enumerate(plan):
                normalized_plan.append({
                    "step": step.get("step", i + 1),
                    "description": step.get("description", ""),
                    "tool": step.get("tool"),
                    "tool_input": step.get("tool_input"),
                })
            
            logger.info(f"Parsed plan: {json.dumps(normalized_plan, indent=2)}")
            
            return {
                "plan": normalized_plan,
                "current_step": 0,
                "context_log": [],
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan JSON: {e}")
            # Fallback: create a simple direct response plan
            return {
                "plan": [{"step": 1, "description": "Respond directly to user", "tool": None, "tool_input": None}],
                "current_step": 0,
                "context_log": [],
            }
    
    def worker_node(state: MultiAgentState) -> dict:
        """Worker agent: executes all plan steps by directly invoking tools."""
        logger.info("=== WORKER NODE ===")
        
        plan = state.get("plan", [])
        context_log = list(state.get("context_log", []))
        
        # Execute all steps in the plan
        for step in plan:
            step_num = step["step"]
            description = step["description"]
            tool_name = step.get("tool")
            tool_input = step.get("tool_input") or {}
            
            logger.info(f"Executing step {step_num}: {description}")
            
            if tool_name and tool_name in TOOL_MAP:
                # Directly invoke the tool
                try:
                    tool = TOOL_MAP[tool_name]
                    result = tool.invoke(tool_input)
                    
                    # Convert result to string
                    if isinstance(result, dict):
                        result_str = json.dumps(result)
                    elif isinstance(result, list):
                        result_str = json.dumps(result)
                    else:
                        result_str = str(result)
                    
                    logger.info(f"Tool {tool_name} returned: {result_str[:200]}...")
                    
                    context_log.append({
                        "step": step_num,
                        "action": f"{tool_name}({json.dumps(tool_input)})",
                        "result": result_str[:1000],  # Truncate long results
                    })
                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {e}")
                    context_log.append({
                        "step": step_num,
                        "action": f"{tool_name}({json.dumps(tool_input)})",
                        "result": f"Error: {str(e)}",
                    })
            else:
                # No tool needed, just log the reasoning step
                context_log.append({
                    "step": step_num,
                    "action": description,
                    "result": "Reasoning/synthesis step completed",
                })
        
        logger.info(f"Worker completed {len(plan)} steps")
        
        return {
            "context_log": context_log,
        }
    
    def explainer_node(state: MultiAgentState) -> dict:
        """Explainer agent: produces final user-friendly response."""
        logger.info("=== EXPLAINER NODE ===")
        
        messages = state["messages"]
        plan = state.get("plan", [])
        context_log = state.get("context_log", [])
        
        # Build context for explainer
        user_request = messages[-1].content if messages else "No request"
        
        plan_summary = "\n".join([
            f"- Step {s['step']}: {s['description']}" + (f" (tool: {s['tool']})" if s.get('tool') else "")
            for s in plan
        ])
        
        context_summary = "\n".join([
            f"- Step {c['step']}: {c['action']}\n  Result: {c['result']}"
            for c in context_log
        ])
        
        explainer_prompt = f"""User request: {user_request}

Execution plan:
{plan_summary}

Results from execution:
{context_summary}

Now provide a helpful, natural response to the user based on the above information."""
        
        explainer_messages = [
            SystemMessage(content=EXPLAINER_SYSTEM_PROMPT),
            HumanMessage(content=explainer_prompt),
        ]
        
        response = explainer_model.invoke(explainer_messages)
        logger.info(f"Explainer response generated")
        
        return {
            "final_answer": response.content,
            "messages": [AIMessage(content=response.content)],
        }
    
    # Create the graph
    graph = StateGraph(MultiAgentState)
    
    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("worker", worker_node)
    graph.add_node("explainer", explainer_node)
    
    # Add edges: simple linear flow
    # START → planner → worker → explainer → END
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "worker")
    graph.add_edge("worker", "explainer")
    graph.add_edge("explainer", END)
    
    # Compile and return
    return graph.compile()


# Lazy initialization - graphs cached per provider
_multi_agent_graphs: dict[str, Any] = {}


def get_multi_agent_graph(provider: str = "openai"):
    """Get or create the multi-agent graph (lazy initialization).
    
    Args:
        provider: Model provider to use ("openai" or "ollama")
    """
    global _multi_agent_graphs
    if provider not in _multi_agent_graphs:
        _multi_agent_graphs[provider] = create_multi_agent_graph(provider=provider)
    return _multi_agent_graphs[provider]


# Alias for backward compatibility
def get_agent_graph(provider: str = "openai"):
    """Alias for get_multi_agent_graph for backward compatibility."""
    return get_multi_agent_graph(provider=provider)
