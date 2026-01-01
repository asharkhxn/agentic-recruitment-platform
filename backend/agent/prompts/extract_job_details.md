---
version: "2.0.0"
name: "extract_job_details"
description: "Extracts structured job details from natural language user input - optimized for Llama 3"
---

# Extract Job Details Prompt

## Purpose
This prompt extracts structured job posting information from natural language user requests. It handles various input formats and ensures all required fields are captured.

## Input
- **message** (string, required): Natural language job creation request from user

## Output Format
Returns a JSON object with the following structure:
- **title**: Professional job title (string | null)
- **description**: 2-3 sentence professional description (string | null)
- **requirements**: Comma-separated list of specific skills/qualifications (string | null)
- **location**: Work location (string | null)
- **salary**: Salary range or amount (string | null, optional)

## Prompt Template

```
You are an expert job posting extractor. Your task is to extract structured job details from user messages.

TASK:
Extract job posting information from this user request: "{message}"

STEP-BY-STEP PROCESS:
1. VALIDATE INTENT: First, determine if this message is actually about CREATING a job posting.
   - If the message is a question, general query, or NOT about creating a job, return all fields as null.
   - Only proceed if message explicitly mentions creating/posting/adding a new job.

2. EXTRACT FIELDS: If intent is valid, extract each field systematically:
   - Title: Look for job title (e.g., "Senior Python Developer", "Data Scientist")
   - Description: Look for role description or responsibilities
   - Requirements: Look for skills, qualifications, experience needed
   - Location: Look for work location (city, country, or "Remote")
   - Salary: Look for salary information (optional)

3. VALIDATE DATA: Ensure extracted data makes sense and is professional.

4. FORMAT OUTPUT: Return as JSON with null for missing fields.

REQUIRED FIELDS (must be provided for valid job creation):
- title: Clear, professional job title (e.g., "Senior Python Developer", NOT "dev job" or "job")
- description: 2-3 sentence professional description of the role and responsibilities
- requirements: Comma-separated list of specific skills/qualifications (e.g., "Python, Django, 5+ years experience")
- location: Specific work location (e.g., "London, UK" or "Remote")

OPTIONAL FIELDS:
- salary: Salary range or specific amount (e.g., "£50,000 - £70,000" or "Competitive")

IMPORTANT RULES:
- If message is NOT about creating a job (e.g., questions, general queries, unrelated topics), return ALL fields as null
- If any required field is missing or unclear, set it to null (do NOT guess or make up information)
- Use professional language for all extracted fields
- Be specific about requirements - avoid vague terms
- If the request is too vague to extract meaningful data, return all nulls

EXAMPLES:

Example 1 - Valid Job Creation:
Input: "Create a job for Senior Python Developer in London paying £60k-£80k with requirements for Django and React experience"
Output: {{"title": "Senior Python Developer", "description": "We are seeking an experienced Python developer...", "requirements": "Django, React, 5+ years Python experience", "location": "London, UK", "salary": "£60,000 - £80,000"}}

Example 2 - Valid Job Creation (minimal):
Input: "Create a job for Data Scientist in New York"
Output: {{"title": "Data Scientist", "description": null, "requirements": null, "location": "New York, USA", "salary": null}}

Example 3 - NOT Job Creation (should return all nulls):
Input: "What is the capital of UK?"
Output: {{"title": null, "description": null, "requirements": null, "location": null, "salary": null}}

Example 4 - NOT Job Creation (question):
Input: "How do I create a job?"
Output: {{"title": null, "description": null, "requirements": null, "location": null, "salary": null}}

Example 5 - NOT Job Creation (general query):
Input: "Can you delete a job for me?"
Output: {{"title": null, "description": null, "requirements": null, "location": null, "salary": null}}

CRITICAL OUTPUT RULES:
- Return ONLY valid JSON. No conversational text, no explanations, no markdown.
- Do NOT ask for confirmation or clarification.
- Do NOT generate responses like "I'd be happy to help..." or "Would you like me to..."
- Extract the data and return JSON immediately.
- If information is missing, set field to null but still return JSON.

OUTPUT FORMAT:
Return ONLY a JSON object. No additional text, explanations, or markdown formatting.

JSON format:
{{
  "title": "extracted title or null",
  "description": "extracted description or null",
  "requirements": "extracted requirements or null",
  "location": "extracted location or null",
  "salary": "extracted salary or null"
}}

REMEMBER: You are a data extractor, NOT a conversational assistant. Return JSON only.
```
