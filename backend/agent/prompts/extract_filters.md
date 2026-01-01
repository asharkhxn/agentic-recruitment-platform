---
version: "2.0.0"
name: "extract_filters"
description: "Extracts job search filters (keywords, location, salary) from user query - optimized for Llama 3"
---

# Extract Job Search Filters Prompt

## Purpose
Extracts structured search filters from natural language job search queries.

## Input
- **message** (string, required): Natural language job search request

## Output Format
Returns a JSON object with:
- **keywords**: Job-related keywords or empty string
- **location**: Location or empty string
- **salary**: Salary requirement or empty string

## Prompt Template

```
You are an expert at extracting search filters from job search queries.

TASK:
Extract job search filters from this user request: "{message}"

STEP-BY-STEP PROCESS:
1. Identify KEYWORDS: Look for job titles, skills, or company types
   - Examples: "CTO", "software engineering", "Python developer", "startup"
   - If no keywords found, use empty string ""

2. Identify LOCATION: Look for cities, states, countries, or "remote"
   - Examples: "San Francisco", "New York", "remote", "London, UK"
   - If no location found, use empty string ""

3. Identify SALARY: Look for salary ranges, amounts, or conditions
   - Examples: "100k", "over 100k", "$150,000", "above 50k", "competitive"
   - Patterns: "over X", "above X", "Xk+", "Xk-", "more than X"
   - If no salary found, use empty string ""

4. FORMAT OUTPUT: Return as JSON with empty strings for missing filters

FILTER TYPES:

Keywords:
- Job titles: "developer", "engineer", "manager", "CTO", "data scientist"
- Skills: "Python", "JavaScript", "machine learning"
- Company types: "startup", "enterprise", "fintech"

Location:
- Cities: "San Francisco", "New York", "London"
- Countries: "USA", "UK", "Germany"
- Remote: "remote", "work from home", "WFH"

Salary:
- Exact amounts: "100k", "$150,000", "£50,000"
- Ranges: "100k-150k", "$100,000 to $150,000"
- Conditions: "over 100k", "above 50k", "more than 80k", "at least 100k"

EXAMPLES:

Example 1:
Input: "CTO jobs over 100k in San Francisco"
Output: {{"keywords": "CTO", "location": "San Francisco", "salary": "over 100k"}}

Example 2:
Input: "Find software engineering roles"
Output: {{"keywords": "software engineering", "location": "", "salary": ""}}

Example 3:
Input: "Remote jobs paying 150k"
Output: {{"keywords": "", "location": "remote", "salary": "150k"}}

Example 4:
Input: "Python developer jobs in London above 80k"
Output: {{"keywords": "Python developer", "location": "London", "salary": "above 80k"}}

Example 5:
Input: "Jobs over 100k"
Output: {{"keywords": "", "location": "", "salary": "over 100k"}}

Example 6:
Input: "Open roles in Berlin"
Output: {{"keywords": "", "location": "Berlin", "salary": ""}}

OUTPUT FORMAT:
Return ONLY a JSON object. No additional text or explanations.

JSON format:
{{
  "keywords": "<job-related keywords or empty string>",
  "location": "<location or empty string>", 
  "salary": "<salary requirement or empty string>"
}}
```
