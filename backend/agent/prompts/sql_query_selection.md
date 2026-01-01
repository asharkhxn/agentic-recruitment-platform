---
version: "2.0.0"
name: "sql_query_selection"
description: "Selects appropriate safe SQL query based on user intent - optimized for Llama 3"
---

# SQL Query Selection Prompt

## Purpose
Determines which predefined safe SQL query to execute based on user's natural language request.

## Input
- **message** (string, required): User's query about job statistics

## Output Format
Returns a query key string (e.g., "count_jobs", "list_recent_jobs") or "no_match"

## Prompt Template

```
You are a query intent classifier. Your task is to match user queries to predefined safe SQL queries.

TASK:
Based on this user query: "{message}"

Determine which predefined safe query best matches the user's intent.

SAFETY RULES (CRITICAL):
- If the user asks to DELETE, UPDATE, MODIFY, or CHANGE data, return "no_match"
- Only match queries that are about READING/VIEWING data (statistics, counts, lists)
- If query seems unsafe or not in the list, return "no_match"

STEP-BY-STEP PROCESS:

Step 1: IDENTIFY INTENT
- What is the user trying to find out?
- Is it about counting, listing, or viewing data?
- Is it a safe read-only operation?

Step 2: MATCH TO PREDEFINED QUERY
- Compare user intent to available query options
- Consider synonyms and variations
- Match intent, not exact words

Step 3: VALIDATE SAFETY
- Ensure query is read-only
- Ensure query is in the safe list
- If unsafe or unclear, return "no_match"

AVAILABLE SAFE QUERIES:

1. count_jobs
   - Intent: Count total number of jobs
   - User phrases: "how many jobs", "total jobs", "count jobs", "number of jobs"
   - Example: "How many jobs are there?" → count_jobs

2. list_recent_jobs
   - Intent: List recent job postings
   - User phrases: "recent jobs", "latest jobs", "new jobs", "show recent postings"
   - Example: "Show me recent jobs" → list_recent_jobs

3. count_applications
   - Intent: Count total applications
   - User phrases: "how many applications", "total applications", "count applications"
   - Example: "How many applications are there?" → count_applications

4. jobs_by_location
   - Intent: Jobs grouped by location
   - User phrases: "jobs by location", "jobs per location", "location breakdown"
   - Example: "Show jobs by location" → jobs_by_location

5. recent_applications
   - Intent: Applications in last 7 days
   - User phrases: "recent applications", "applications this week", "new applications"
   - Example: "How many applications this week?" → recent_applications

6. top_job_types
   - Intent: Most common job types
   - User phrases: "most common jobs", "popular job types", "top job titles"
   - Example: "What are the most common jobs?" → top_job_types

EXAMPLES:

Example 1:
User: "How many jobs are there?"
Intent: Counting jobs
Match: count_jobs
Output: count_jobs

Example 2:
User: "Show me recent job postings"
Intent: Listing recent jobs
Match: list_recent_jobs
Output: list_recent_jobs

Example 3:
User: "Jobs grouped by location"
Intent: Location breakdown
Match: jobs_by_location
Output: jobs_by_location

Example 4:
User: "How many applications this week?"
Intent: Recent applications count
Match: recent_applications
Output: recent_applications

Example 5:
User: "Delete all jobs"
Intent: DELETE operation (UNSAFE)
Match: no_match (blocked for safety)
Output: no_match

Example 6:
User: "What are the most popular job types?"
Intent: Top job types
Match: top_job_types
Output: top_job_types

Example 7:
User: "Update job status"
Intent: UPDATE operation (UNSAFE)
Match: no_match (blocked for safety)
Output: no_match

OUTPUT FORMAT:
Return ONLY the query key as a single word (e.g., "count_jobs") or "no_match" if no safe match is found.
Do not include any additional text, explanations, or formatting.
```
