import time
from collections import defaultdict

# Rate limiting store and settings
RATE_LIMIT_STORE: defaultdict[str, list] = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 50  # requests per hour
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds


def check_rate_limit(user_id: str) -> bool:
    """Check if user is within rate limits. Returns True if allowed, False if blocked."""
    now = time.time()
    user_requests = RATE_LIMIT_STORE[user_id]
    # Remove old requests outside the window
    user_requests[:] = [req_time for req_time in user_requests if now - req_time < RATE_LIMIT_WINDOW]
    if len(user_requests) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    user_requests.append(now)
    return True

