import re

# Simple synonym map for recruiter queries
SYNONYMS = {
    "role": ["job", "position", "opening", "vacancy"],
    "applicant": ["candidate", "person"]
}


def normalize_synonyms(text: str) -> str:
    """Replace simple synonyms with canonical terms to help routing and tooling."""
    lower = text.lower()
    for canonical, variants in SYNONYMS.items():
        for v in variants:
            lower = re.sub(rf"\b{re.escape(v)}\b", canonical, lower)
    return lower

