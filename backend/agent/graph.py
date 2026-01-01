from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.router import route_query
from agent.nodes.create_job import create_job_node
from agent.nodes.search_jobs import search_jobs_node
from agent.nodes.get_applicants import get_applicants_node
from agent.nodes.rank_applicants import rank_applicants_node
from agent.nodes.sql_query import sql_query_node
from agent.nodes.general_response import general_response_node
from agent.nodes.safety_block import safety_block_node


# Build the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("create_job_tool", create_job_node)
workflow.add_node("get_applicants_tool", get_applicants_node)
workflow.add_node("search_jobs_tool", search_jobs_node)
workflow.add_node("rank_tool", rank_applicants_node)
workflow.add_node("sql_tool", sql_query_node)
workflow.add_node("general_response", general_response_node)
workflow.add_node("safety_block", safety_block_node)

# Set conditional entry point based on routing
workflow.set_conditional_entry_point(
    route_query,
    {
        "create_job_tool": "create_job_tool",
        "get_applicants_tool": "get_applicants_tool",
        "rank_tool": "rank_tool",
        "sql_tool": "sql_tool",
        "general_response": "general_response",
        "search_jobs_tool": "search_jobs_tool",
        "safety_block": "safety_block"
    }
)

# All tools end after execution
workflow.add_edge("create_job_tool", END)
workflow.add_edge("get_applicants_tool", END)
workflow.add_edge("rank_tool", END)
workflow.add_edge("sql_tool", END)
workflow.add_edge("general_response", END)
workflow.add_edge("search_jobs_tool", END)
workflow.add_edge("safety_block", END)

# Compile the graph
agent_graph = workflow.compile()
