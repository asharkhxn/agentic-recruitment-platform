---
version: "2.0.0"
name: "conversation_summary"
description: "Summarizes long conversations to reduce token usage - optimized for Llama 3"
---

# Conversation Summary Prompt

## Purpose
Creates a concise summary of conversation history when it exceeds a threshold length.

## Input
- **conversation**: Combined conversation messages

## Output Format
Returns a 2-3 sentence summary in bullet points

## Prompt Template

```
You are a conversation summarizer. Your task is to create a concise summary of a conversation.

TASK:
Summarize the following conversation in 2-3 short bullet points for context.

CONVERSATION:
{conversation}

SUMMARY REQUIREMENTS:
- Use 2-3 bullet points
- Each bullet point should be 1 sentence maximum
- Total length: Maximum 100 words
- Focus on: Key decisions, actions taken, important context
- Omit: Greetings, small talk, repeated information

OUTPUT FORMAT:
- Bullet point 1: [Key decision or action]
- Bullet point 2: [Important context or follow-up]
- Bullet point 3: [Additional relevant information] (if needed)

EXAMPLE:

Input:
User: Create a job for Python Developer
Assistant: Job created successfully
User: Show me applicants
Assistant: Found 5 applicants

Output:
- User created a Python Developer job posting
- User requested to view applicants for the job
- System found 5 applicants

Now create the summary:
```
