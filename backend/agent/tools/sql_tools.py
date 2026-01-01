from typing import Dict, List, Any
from core.config import get_supabase_client
from agent.utils.safety import sanitize_sql_query
import re


async def run_sql_query(query: str) -> List[Dict[str, Any]]:
    """Execute SQL SELECT query against Supabase database."""
    try:
        # Enhanced safety check
        is_safe, error_message = sanitize_sql_query(query)
        if not is_safe:
            return {"error": error_message}
        
        supabase = get_supabase_client()
        
        # Parse table name from query
        table_match = re.search(r'from\s+(\w+)', query.lower())
        if not table_match:
            return {"error": "Could not parse table name"}
        
        table_name = table_match.group(1)
        
        # Additional validation: only allow known safe tables
        safe_tables = ["jobs", "applications", "users", "chat_messages"]
        if table_name not in safe_tables:
            return {"error": f"Access to table '{table_name}' is not allowed for security reasons."}
        
        response = supabase.table(table_name).select("*").execute()
        return response.data
    except Exception as e:
        return {"error": f"Query execution failed: {str(e)}"}

