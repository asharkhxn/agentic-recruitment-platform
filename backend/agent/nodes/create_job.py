from agent.state import AgentState
from agent.utils.llm import llm
from agent.prompts.loader import format_prompt
from agent.tools.job_tools import create_job
import json
import re


async def create_job_node(state: AgentState) -> AgentState:
    """Handle job creation using heuristic extraction (more reliable than LLM)."""
    try:
        # Use heuristic extraction as PRIMARY method (more reliable than LLM)
        # LLM extraction is unreliable as it generates conversational text instead of JSON
        raw = state.get("message", "")
        # Remove any context summary prefix added earlier
        raw = re.sub(r"CONTEXT_SUMMARY:\n.*?\n\nUser:\s*", "", raw, flags=re.DOTALL)

        def extract_between(text, lefts, rights=None):
            for l in lefts:
                m = re.search(rf"{re.escape(l)}\s*(.*?)($|\\.|;|,|\n)", text, re.IGNORECASE)
                if m:
                    return m.group(1).strip()
            if rights:
                for r in rights:
                    m = re.search(rf"(.*)\s*{re.escape(r)}", text, re.IGNORECASE)
                    if m:
                        return m.group(1).strip()
            return None

        title = None
        location = None
            
        # Pattern 1: "Create a job for [Title] position" or "Create a job for [Title]"
        # Handles: "Create a job for Lead/Senior Frontend Developer position"
        # Stop at: position, role, in, based, with, or end of sentence
        m1 = re.search(r"(?:create|post|add)\s+(?:a\s+)?job\s+for\s+(?:a\s+)?([A-Za-z][\w\s\-\+\.,/()]+?)(?:\s+position|\s+role|\s+in\s+[A-Z]|\s+based|\s+with\s+salary|\s+with\s+a|\.|,|$)", raw, re.IGNORECASE)
        if m1:
            title = m1.group(1).strip()
            # Clean up: remove common prefixes that might have been captured
            title = re.sub(r'^(role\s+for\s+a|a\s+role\s+for|for\s+a\s+role|role\s+posting\s+for|posting\s+for)\s+', '', title, flags=re.IGNORECASE).strip()
        
        # Pattern 2: "I need to add a role posting for [Title]" or similar variations
        if not title:
            m2a = re.search(r"(?:i\s+need\s+to\s+add|i\s+want\s+to\s+create|we\s+need\s+to\s+post)\s+(?:a\s+)?(?:role\s+posting\s+for|job\s+posting\s+for|job\s+for|role\s+for)\s+(?:a\s+)?([A-Za-z][\w\s\-\+\.,/()]+?)(?:\s+position|\s+role|\s+in\s+[A-Z]|\s+based|\.|,|$)", raw, re.IGNORECASE)
            if m2a:
                title = m2a.group(1).strip()
                title = re.sub(r'^(role\s+for\s+a|a\s+role)\s+', '', title, flags=re.IGNORECASE).strip()
        
        # Pattern 3: "Create a [Title] job" or "Post a [Title] position"
        if not title:
            m2 = re.search(r"(?:create|post|add)\s+(?:a\s+)?([A-Za-z][\w\s\-\+\.,/()]+?)(?:\s+job|\s+position|\s+role)(?:\s+in|\s+based|\.|,|$)", raw, re.IGNORECASE)
            if m2:
                title = m2.group(1).strip()
        
        # Pattern 4: Look for job title patterns (Senior/Lead/Junior + Role)
        # Handles: "Lead/Senior Frontend Developer" or "Senior Python Developer" or "DevOps Engineer"
        if not title:
            title_match = re.search(r"((?:Senior|Lead|Junior|Mid-level|Principal|DevOps|Frontend|Backend|Full.?stack)[/\s]*(?:Senior|Lead|Junior|Mid-level|Principal)?\s*)?([A-Za-z][\w\s]+?\s+(?:Developer|Engineer|Designer|Manager|Analyst|Scientist|Architect|Frontend|Backend|Full.?stack|DevOps))", raw, re.IGNORECASE)
            if title_match:
                title = title_match.group(0).strip()
        
        # Pattern 5: Fallback - extract just the job role keywords if nothing else matched
        if not title:
            # Look for common job role patterns anywhere in the text
            role_match = re.search(r"((?:Senior|Lead|Junior|Principal|DevOps|Frontend|Backend|Full.?stack)\s+)?([A-Za-z]+?\s+(?:Developer|Engineer|Designer|Manager|Analyst|Scientist|Architect|Recruiter|Product|Data))", raw, re.IGNORECASE)
            if role_match:
                title = role_match.group(0).strip()
        
        # Clean up title: capitalize properly and remove extra words
        if title:
            # Remove common prefixes that might have been captured
            title = re.sub(r'^(role\s+for\s+a|a\s+role\s+for|for\s+a\s+role|role\s+posting\s+for|posting\s+for|i\s+need\s+to\s+add|i\s+want\s+to\s+create)\s+', '', title, flags=re.IGNORECASE).strip()
            # Capitalize first letter of each word (title case)
            title = ' '.join(word.capitalize() for word in title.split())

        # Location extraction - multiple patterns
        # Pattern 1: "in [Location]" or "based in [Location]"
        loc_match1 = re.search(r"(?:in|based in|located in)\s+([A-Z][\w\s,()]+?)(?:,|\.|$|with|paying)", raw, re.IGNORECASE)
        if loc_match1:
            location = loc_match1.group(1).strip()
        
        # Pattern 2: "Location is [Location]"
        if not location:
            loc_match2 = re.search(r"location\s+is\s+([A-Z][\w\s,()]+?)(?:,|\.|$|with|paying)", raw, re.IGNORECASE)
            if loc_match2:
                location = loc_match2.group(1).strip()
        
        # Pattern 3: Look for common location patterns (City, Country)
        if not location:
            loc_match3 = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z]{2,3}|[A-Z][a-z]+)", raw)
            if loc_match3:
                location = loc_match3.group(0).strip()

        # Salary extraction - handle multiple formats (£, $, €, and ranges)
        salary = None
        # Pattern 1: £80,000 to £100,000 or £80k to £100k
        sal_match1 = re.search(r"([£$€])\s?(\d{1,3}(?:,\d{3})?)\s?(?:k|000)?\s*[–\-to]+\s*([£$€]?\s?\d{1,3}(?:,\d{3})?)\s?(?:k|000)?", raw, re.IGNORECASE)
        if sal_match1:
            currency = sal_match1.group(1)
            amount1 = sal_match1.group(2).replace(',', '')
            amount2 = sal_match1.group(3).replace(',', '').replace(currency, '').strip()
            # Format nicely
            if int(amount1) < 1000:
                salary = f"{currency}{amount1}k–{currency}{amount2}k"
            else:
                salary = f"{currency}{amount1:,}–{currency}{amount2:,}"
        else:
            # Pattern 2: £80k-£100k or 80k-100k
            sal_match2 = re.search(r"([£$€]?)\s?(\d{2,3})\s?k\s*[–\-to]+\s*([£$€]?)\s?(\d{2,3})\s?k", raw, re.IGNORECASE)
            if sal_match2:
                currency = sal_match2.group(1) or sal_match2.group(3) or "£"
                a = sal_match2.group(2)
                b = sal_match2.group(4)
                salary = f"{currency}{a}k–{currency}{b}k"
            else:
                # Pattern 3: Single salary mention
                sal_simple = re.search(r"([£$€])\s?(\d{1,3}(?:,\d{3})?)\s?(?:k|000)?\s*(?:per year|annually|salary)", raw, re.IGNORECASE)
                if sal_simple:
                    currency = sal_simple.group(1)
                    amount = sal_simple.group(2).replace(',', '')
                    if int(amount) < 1000:
                        salary = f"{currency}{amount}k"
                    else:
                        salary = f"{currency}{amount:,}"

        # Requirements extraction: look for 'requires', 'must have', 'looking for', 'need', or skills mentioned
        req_text = None
        # Pattern 1: "looking for someone with X" - capture everything until "The role" or end
        req_match1 = re.search(r"looking for (?:someone with|a candidate with|someone who has)?\s*(.+?)(?:\.|$|The role|role involves)", raw, re.IGNORECASE | re.DOTALL)
        if req_match1:
            req_text = req_match1.group(1).strip()
            # Clean up - remove trailing periods and trim
            req_text = req_text.rstrip('.,').strip()
        else:
            # Pattern 2: "requires" or "must have" or "need"
            req_match2 = re.search(r"(?:requires|require|must have|must include|role requires|the role requires|need)[:\s]+(.+?)(?:\.|$|The role|role involves)", raw, re.IGNORECASE | re.DOTALL)
            if req_match2:
                req_text = req_match2.group(1).strip()
                req_text = req_text.rstrip('.,').strip()
            else:
                # Pattern 3: Extract skills/technologies mentioned - "5+ years of React experience, TypeScript, and..."
                skills_pattern = r"(\d+\+?\s*years?\s+of\s+)?([A-Za-z0-9\s,+\-/]+?)(?:\s+experience|\s+knowledge|\s+skills|\.|,|$|and|The role)"
                skills_match = re.search(skills_pattern, raw, re.IGNORECASE)
                if skills_match:
                    # Try to get more context - look for comma-separated lists
                    extended_match = re.search(r"(\d+\+?\s*years?\s+of\s+)?([A-Za-z0-9\s,+\-/]+?)(?:,|and|\.|$|The role)", raw, re.IGNORECASE)
                    if extended_match:
                        req_text = extended_match.group(0).strip()
                        req_text = req_text.rstrip('.,').strip()
                else:
                    # Pattern 4: Look for common tech stack mentions
                    tech_stack = re.search(r"(\d+\+?\s*years?\s+)?(?:of\s+)?([A-Za-z\s,+\-/]+?)(?:experience|knowledge|skills|frameworks)(?:,|\.|$|and)", raw, re.IGNORECASE)
                    if tech_stack:
                        req_text = tech_stack.group(0).strip()
                        req_text = req_text.rstrip('.,').strip()

        # Description extraction: look for role description, responsibilities, or generate from context
        desc = None
        # Pattern 1: "The role involves" or "role involves" - capture full sentence
        desc_match1 = re.search(r"(?:The role|role|position|job)(?:\s+involves|\s+will|\s+requires)?\s*(.+?)(?:\.|$|We're|We are|The job)", raw, re.IGNORECASE | re.DOTALL)
        if desc_match1:
            desc_text = desc_match1.group(1).strip()
            # Clean up - take first sentence or up to 300 chars
            if len(desc_text) > 300:
                desc = desc_text[:300].rsplit('.', 1)[0] + '.'
            else:
                desc = desc_text
        else:
            # Pattern 2: "Responsibilities" or "will work" or "involves"
            desc_match2 = re.search(r"(?:Responsibilities|will work|will be|involves)[:\s]*(.+?)(?:\.|$|Requirements|We're)", raw, re.IGNORECASE | re.DOTALL)
            if desc_match2:
                desc_text = desc_match2.group(1).strip()
                if len(desc_text) > 300:
                    desc = desc_text[:300].rsplit('.', 1)[0] + '.'
                else:
                    desc = desc_text
            else:
                # Pattern 3: Generate description from title and requirements if available
                if title and req_text:
                    desc = f"We are seeking a {title} to join our team. The ideal candidate will have {req_text}."
                elif title:
                    desc = f"We are seeking a {title} to join our team."
                else:
                    # Last resort: use relevant part of the message
                    desc = raw[:200].strip() if len(raw) > 50 else raw.strip()

        job_data = {
            "title": title,
            "description": desc,
            "requirements": req_text,
            "location": location,
            "salary": salary
        }

        # Validate: Check if this is actually about creating a job
        # If all fields are null, it might not be a job creation request
        all_null = all(
            job_data.get(field) is None or 
            (isinstance(job_data.get(field), str) and job_data.get(field).strip().lower() in ["null", "none", "", "tbd", "n/a", "na", "unspecified"])
            for field in ["title", "description", "requirements", "location"]
        )
        
        if all_null:
            # This might not be a job creation request - route to general response
            state["response"] = (
                "I didn't detect job creation details in your message. "
                "To create a job, please provide: job title, description, requirements, and location.\n\n"
                "Example: 'Create a Senior Python Developer job in London paying £60k-£80k with requirements for Django and React experience.'\n\n"
                "If you need help with something else, I can assist with searching jobs, viewing applicants, or ranking candidates."
            )
            return state

        # Check for missing required fields and generate defaults if needed
        # Title is critical - if missing, we can't proceed
        if not job_data.get("title") or job_data.get("title", "").strip().lower() in ["null", "none", "", "tbd", "n/a", "na", "unspecified"]:
            state["response"] = (
                "I need a job title to create this posting. Please provide a job title.\n\n"
                "Example: 'Create a Senior Python Developer job in London paying £60k-£80k with requirements for Django and React experience.'"
            )
            return state

        # Generate defaults for missing fields if we have enough context
        if not job_data.get("description") or job_data.get("description", "").strip().lower() in ["null", "none", "", "tbd", "n/a", "na", "unspecified"]:
            # Generate a basic description from title and requirements
            title = job_data.get("title", "")
            reqs = job_data.get("requirements", "")
            if reqs:
                job_data["description"] = f"We are seeking a {title} to join our team. The ideal candidate will have {reqs}."
            else:
                job_data["description"] = f"We are seeking a {title} to join our team."

        if not job_data.get("requirements") or job_data.get("requirements", "").strip().lower() in ["null", "none", "", "tbd", "n/a", "na", "unspecified"]:
            # If no requirements, set a generic one
            job_data["requirements"] = "Relevant experience and skills for the role"

        if not job_data.get("location") or job_data.get("location", "").strip().lower() in ["null", "none", "", "tbd", "n/a", "na", "unspecified"]:
            # If no location, we need to ask
            state["response"] = (
                f"I need a location for the {job_data.get('title')} position. Please provide the work location (e.g., 'London, UK' or 'Remote')."
            )
            return state

        # Final title cleanup - remove any remaining unwanted prefixes
        if job_data.get("title"):
            title_clean = job_data["title"]
            # Remove common unwanted prefixes
            title_clean = re.sub(r'^(role\s+for\s+a|a\s+role\s+for|for\s+a\s+role|role\s+posting\s+for|posting\s+for|i\s+need\s+to\s+add|i\s+want\s+to\s+create|we\s+need\s+to\s+post|add\s+a\s+role)\s+', '', title_clean, flags=re.IGNORECASE).strip()
            # Remove if it's too long (likely captured the whole query)
            if len(title_clean) > 80:
                # Try to extract just the job role part
                role_extract = re.search(r'((?:Senior|Lead|Junior|Principal|DevOps|Frontend|Backend|Full.?stack)\s+)?([A-Za-z]+?\s+(?:Developer|Engineer|Designer|Manager|Analyst|Scientist|Architect|Recruiter|Product|Data))', title_clean, re.IGNORECASE)
                if role_extract:
                    title_clean = role_extract.group(0).strip()
            # Capitalize properly (title case)
            title_clean = ' '.join(word.capitalize() for word in title_clean.split())
            job_data["title"] = title_clean

        # Validate extracted data quality
        if not job_data.get("title") or len(job_data["title"]) < 3:
            state["response"] = "I couldn't extract a valid job title from your message. Please provide a clear job title.\n\nExample: 'Create a Senior Python Developer job in London.'"
            return state

        if len(job_data["description"]) < 10:
            # Regenerate if too short
            title = job_data.get("title", "")
            reqs = job_data.get("requirements", "")
            job_data["description"] = f"We are seeking a {title} to join our team. {reqs}."

        # Create job - populate tool information for LangSmith tracking
        tool_args = {
            "title": job_data["title"],
            "description": job_data["description"],
            "requirements": job_data["requirements"],
            "location": job_data["location"],
            "salary": job_data.get("salary"),
            "user_id": state["user_id"]
        }
        
        state["tool_name"] = "create_job"
        state["tool_args"] = tool_args
        
        try:
            result = await create_job(
                title=job_data["title"],
                description=job_data["description"],
                requirements=job_data["requirements"],
                location=job_data["location"],
                salary=job_data.get("salary"),
                user_id=state["user_id"]
            )
            # Store tool result for LangSmith
            if isinstance(result, dict):
                state["tool_result"] = str(result)
            else:
                state["tool_result"] = f"Job created successfully: {result.get('id', 'N/A') if isinstance(result, dict) else 'Success'}"
        except Exception as e:
            result = {"error": str(e)}
            state["tool_result"] = f"Error: {str(e)}"

        if isinstance(result, dict) and result.get("error"):
            # If persistence failed (missing Supabase or other error), return a clear payload the caller can POST
            payload = {
                "title": job_data.get("title"),
                "description": job_data.get("description"),
                "requirements": job_data.get("requirements"),
                "location": job_data.get("location"),
                "salary": job_data.get("salary")
            }
            state["response"] = (
                "I parsed the job details but couldn't persist the job to the database. "
                f"Error: {result.get('error')}\n\n"
                "You can create the job manually by POSTing the following JSON to the /jobs endpoint as a recruiter:\n\n"
                f"{json.dumps(payload, indent=2)}"
            )
        else:
            # User-friendly response
            salary_info = f" with salary {job_data.get('salary')}" if job_data.get('salary') else ""
            state["response"] = (
                f"✅ **Job Created Successfully!**\n\n"
                f"📋 **{job_data['title']}**\n"
                f"📍 **Location:** {job_data['location']}{salary_info}\n\n"
                f"**Job Description:**\n{job_data['description']}\n\n"
                f"**Requirements:** {job_data['requirements']}\n\n"
                "The job is now live and ready for applications! 🎉"
            )
    except json.JSONDecodeError:
        state["response"] = "I had trouble parsing the job details. Please try rephrasing your request with clear job information."
    except Exception as e:
        state["response"] = f"I encountered an issue while creating the job posting. Please try again."

    return state

