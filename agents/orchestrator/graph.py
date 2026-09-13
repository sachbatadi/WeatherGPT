from langgraph.graph import StateGraph, START, END

from .state import WeatherState
from .nodes import run_sentinel, run_strategist
from .router import threat_router


def build_graph():

    # Create the graph using our shared WeatherState
    graph = StateGraph(WeatherState)

    # Add our agent nodes
    graph.add_node("sentinel", run_sentinel)
    graph.add_node("strategist", run_strategist)

    # Workflow starts with Sentinel
    graph.add_edge(START, "sentinel")

    # Sentinel decides where to go next
    graph.add_conditional_edges(
        "sentinel",
        threat_router,
        {
            "strategist": "strategist",
            "monitor": END
        }
    )

    # For now, Strategist ends the workflow
    graph.add_edge("strategist", END)

    return graph.compile()