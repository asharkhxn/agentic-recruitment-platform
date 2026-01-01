from typing import Dict, List, Any, Optional
from core.config import get_supabase_client
import re


async def create_job(title: str, description: str, requirements: str, location: str, salary: Optional[str], user_id: str) -> Dict[str, Any]:
    """Create a new job posting."""
    try:
        # Validate required fields and return clear prompt if missing
        required_map = {
            "title": title,
            "description": description,
            "requirements": requirements,
            "location": location,
        }
        missing = [k for k, v in required_map.items() if not v or str(v).strip() == ""]
        if missing:
            return {
                "error": "Missing required fields",
                "missing_fields": missing,
                "message": f"Please provide the following fields to create the job: {', '.join(missing)}"
            }

        # Minimal normalization (trim strings)
        title = str(title).strip()
        description = str(description).strip()
        requirements = str(requirements).strip()
        location = str(location).strip() if location else None
        salary = str(salary).strip() if salary else None

        supabase = get_supabase_client()
        try:
            response = supabase.table("jobs").insert({
                "title": title,
                "description": description,
                "requirements": requirements,
                "location": location,
                "salary": salary,
                "created_by": user_id
            }).execute()
            return response.data[0]
        except Exception as e:
            # If the created_by value is not a valid UUID (e.g., during local testing with placeholder user_id),
            # retry inserting without the created_by foreign key to allow creating a job record.
            msg = str(e)
            if 'invalid input syntax for type uuid' in msg or 'invalid input syntax for type uuid' in msg.lower():
                try:
                    response = supabase.table("jobs").insert({
                        "title": title,
                        "description": description,
                        "requirements": requirements,
                        "location": location,
                        "salary": salary
                    }).execute()
                    return response.data[0]
                except Exception as e2:
                    return {"error": str(e2)}
            return {"error": msg}
    except ValueError as e:
        return {"error": f"Invalid input: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


async def search_jobs(keywords: Optional[str] = None, location: Optional[str] = None, salary: Optional[str] = None) -> List[Dict[str, Any]] | Dict[str, Any]:
    """Search jobs by keyword, location, or salary phrase."""
    try:
        supabase = get_supabase_client()

        # Get all jobs first (we'll filter in Python for more flexibility)
        response = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
        all_jobs = response.data

        # Filter by location
        if location and location.strip():
            location_filter = location.strip().lower()
            all_jobs = [job for job in all_jobs if job.get('location', '').lower().find(location_filter) != -1]

        # Filter by salary with better parsing
        if salary and salary.strip():
            salary_filter = salary.strip().lower()
            filtered_jobs = []

            for job in all_jobs:
                job_salary = job.get('salary', '').lower()
                if not job_salary:
                    continue

                # Check if salary filter matches
                if _salary_matches(job_salary, salary_filter):
                    filtered_jobs.append(job)

            all_jobs = filtered_jobs

        # Filter by keywords in Python
        if keywords and keywords.strip():
            keyword_list = [kw.strip().lower() for kw in keywords.split(',') if kw.strip()]
            if keyword_list:
                filtered_jobs = []
                for job in all_jobs:
                    job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')}".lower()
                    if any(keyword in job_text for keyword in keyword_list):
                        filtered_jobs.append(job)
                all_jobs = filtered_jobs

        return all_jobs
    except Exception as e:
        return {"error": str(e)}


def _salary_matches(job_salary: str, salary_filter: str) -> bool:
    """Check if job salary matches the salary filter."""
    # Normalize both strings
    job_salary = job_salary.lower().strip()
    salary_filter = salary_filter.lower().strip()

    # Extract meaningful salary numbers (handle formats like "100k", "$100,000", "100k-150k")
    clean_salary = re.sub(r'[$,]', '', job_salary)
    # split on dash, the word 'to', or whitespace
    salary_parts = re.split(r'\s*-\s*|\s+to\s+|\s+', clean_salary)

    job_nums = []
    for part in salary_parts:
        part = part.strip()
        if not part:
            continue

        # find first number in the part
        num_match = re.search(r'(\d+)', part)
        if not num_match:
            continue

        try:
            num_int = int(num_match.group(1))
        except ValueError:
            continue

        # apply suffix multipliers if present (k=thousand, m=million)
        if re.search(r'k\b', part, re.IGNORECASE):
            num_int *= 1000
        elif re.search(r'm\b', part, re.IGNORECASE):
            num_int *= 1000000

        # If number looks like '100' from '100k' we've multiplied above; accept any positive integer
        if num_int > 0:
            job_nums.append(num_int)

    if not job_nums:
        # If no numbers found, fall back to text matching
        return salary_filter in job_salary

    # Handle different filter patterns
    if 'over' in salary_filter or 'above' in salary_filter or 'more than' in salary_filter or 'greater than' in salary_filter:
        # Extract number from filter
        filter_nums = re.findall(r'\d+', salary_filter)
        if filter_nums:
            filter_num = int(filter_nums[0])
            # Convert k to thousands
            if 'k' in salary_filter and filter_num < 1000:
                filter_num *= 1000
            # Check if any job salary is >= filter
            return any(num >= filter_num for num in job_nums)

    elif 'under' in salary_filter or 'below' in salary_filter or 'less than' in salary_filter:
        # Extract number from filter
        filter_nums = re.findall(r'\d+', salary_filter)
        if filter_nums:
            filter_num = int(filter_nums[0])
            # Convert k to thousands
            if 'k' in salary_filter and filter_num < 1000:
                filter_num *= 1000
            # Check if any job salary is <= filter
            return any(num <= filter_num for num in job_nums)

    elif 'k' in salary_filter:
        # Handle "100k" format - assume they want jobs at or above this amount
        filter_nums = re.findall(r'\d+', salary_filter)
        if filter_nums:
            filter_num = int(filter_nums[0])
            if filter_num < 1000:  # Assume it's in thousands
                filter_num *= 1000
            return any(num >= filter_num for num in job_nums)

    else:
        # Default: check if filter number appears anywhere in job salary
        filter_nums = re.findall(r'\d+', salary_filter)
        if filter_nums:
            filter_num = int(filter_nums[0])
            if 'k' in salary_filter and filter_num < 1000:
                filter_num *= 1000
            return any(num >= filter_num for num in job_nums)

    # Fallback: simple text matching
    return salary_filter in job_salary

