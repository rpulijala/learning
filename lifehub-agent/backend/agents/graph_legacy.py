"""LangGraph single-agent graph with tool support."""

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from backend.models import get_model_client
from backend.tools.weather import get_weather
from backend.tools.tasks import add_task
from backend.tools.notes import search_notes


# Define the tools available to the agent
TOOLS = [get_weather, add_task, search_notes]

# System prompt for the agent
SYSTEM_PROMPT = """You are a helpful AI assistant called LifeHub Agent. You can help users with:

1. Weather information - Use the get_weather tool to check weather for any city
2. Task management - Use the add_task tool to add tasks to the user's task list
3. Personal notes - Use the search_notes tool to search the user's personal notes and documents

When the user asks about weather, use the get_weather tool.
When the user wants to add or create a task, use the add_task tool.
When the user asks about their notes, personal information, fitness plans, recipes, or anything they might have written down, use the search_notes tool.
For other questions, respond directly without using tools.

When using search_notes results, incorporate the relevant information naturally into your response and cite the source file when helpful.

Be concise and helpful in your responses."""


class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Annotated[list[AnyMessage], add_messages]


def create_agent_graph(provider: str = "openai"):
    """Create and compile the LangGraph agent graph.
    
    Args:
        provider: Model provider to use ("openai" or "ollama")
    """
    # Get the model client with tools bound
    model = get_model_client(provider=provider, streaming=True)
    model_with_tools = model.bind_tools(TOOLS)
    
    def should_continue(state: AgentState) -> str:
        """Determine if we should continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If there are tool calls, route to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        # Otherwise, end
        return END
    
    def call_model(state: AgentState) -> dict:
        """Call the model with the current state."""
        messages = state["messages"]
        
        # Add system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # Create the graph
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(TOOLS))
    
    # Add edges
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, ["tools", END])
    graph.add_edge("tools", "agent")
    
    # Compile and return
    return graph.compile()


# Lazy initialization - graphs cached per provider
_agent_graphs: dict[str, any] = {}


def get_agent_graph(provider: str = "openai"):
    """Get or create the agent graph (lazy initialization).
    
    Args:
        provider: Model provider to use ("openai" or "ollama")
    """
    global _agent_graphs
    if provider not in _agent_graphs:
        _agent_graphs[provider] = create_agent_graph(provider=provider)
    return _agent_graphs[provider]
