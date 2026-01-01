"""Safety utilities for blocking dangerous operations."""
import re
from typing import List


# Dangerous SQL keywords that should be blocked
DANGEROUS_SQL_KEYWORDS = [
    "DELETE", "UPDATE", "INSERT", "DROP", "TRUNCATE", "ALTER", 
    "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "MERGE"
]

# Dangerous operation keywords in user messages
DANGEROUS_OPERATION_KEYWORDS = [
    "delete", "remove", "update", "modify", "change", "edit",
    "drop", "truncate", "alter", "clear", "wipe", "erase"
]


def contains_dangerous_keywords(message: str) -> bool:
    """Check if message contains dangerous operation keywords."""
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in DANGEROUS_OPERATION_KEYWORDS)


def is_dangerous_sql_query(query: str) -> bool:
    """Check if SQL query contains dangerous operations."""
    query_upper = query.upper().strip()
    
    # Check for dangerous keywords
    for keyword in DANGEROUS_SQL_KEYWORDS:
        # Use word boundaries to avoid false positives
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, query_upper):
            return True
    
    return False


def sanitize_sql_query(query: str) -> tuple[bool, str]:
    """Sanitize and validate SQL query. Returns (is_safe, error_message)."""
    query_upper = query.upper().strip()
    
    # Only allow SELECT queries
    if not query_upper.startswith('SELECT'):
        return False, "Only SELECT queries are allowed for security reasons."
    
    # Check for dangerous keywords
    if is_dangerous_sql_query(query):
        return False, "This query contains dangerous operations (DELETE, UPDATE, etc.) which are not allowed."
    
    # Check for SQL injection patterns
    dangerous_patterns = [
        r';\s*(DELETE|UPDATE|DROP|INSERT)',
        r'--',  # SQL comments
        r'/\*.*\*/',  # Multi-line comments
        r'UNION.*SELECT',  # SQL injection
        r'EXEC\s*\(',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, query_upper, re.IGNORECASE):
            return False, "Query contains potentially dangerous patterns."
    
    return True, ""

