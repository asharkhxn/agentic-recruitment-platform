---
version: "1.0.0"
name: "safety_warning"
description: "Safety warning message for blocked operations"
---

# Safety Warning Prompt

## Purpose
Provides a clear, professional warning message when users attempt dangerous operations.

## Output Format
Returns a friendly but firm message explaining why the operation is blocked.

## Prompt Template

```
I understand you'd like to {operation}, but I cannot perform delete, update, modify, or any data modification operations through the chatbot for security reasons.

For data modification operations, please use the admin dashboard or contact your system administrator.

I can help you with:
- Creating new job postings
- Searching and viewing jobs
- Viewing applicants
- Ranking candidates with ATS
- Getting statistics

Is there something else I can help you with?
```

