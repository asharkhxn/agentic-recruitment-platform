from agent.utils.llm import llm


async def summarize_cv(cv_text: str) -> str:
    """Summarize CV using LLM."""
    try:
        prompt = f"""Summarize the following CV in 2-3 sentences, highlighting key skills and experience:

{cv_text}

Summary:"""
        
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error summarizing CV: {str(e)}"


async def generate_job_description(title: str, key_requirements: str) -> str:
    """Generate a job description using LLM."""
    try:
        prompt = f"""Generate a professional job description for the following position:

Title: {title}
Key Requirements: {key_requirements}

Create a compelling job description including:
- Role overview
- Key responsibilities
- Required qualifications
- Desired skills

Job Description:"""
        
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error generating job description: {str(e)}"

