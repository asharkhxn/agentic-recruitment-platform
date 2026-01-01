import re
from pathlib import Path
from typing import Dict, Optional

class PromptLoader:
    """Loads and parses markdown prompt files."""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, str] = {}
    
    def load_prompt_template(self, prompt_file: str) -> str:
        """Load prompt template from markdown file.
        
        Args:
            prompt_file: Name of the markdown file (e.g., 'extract_job_details.md')
        
        Returns:
            The prompt template string
        """
        cache_key = prompt_file
        
        if cache_key not in self._cache:
            file_path = self.prompts_dir / prompt_file
            
            if not file_path.exists():
                raise FileNotFoundError(f"Prompt file not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract template from code block (between ``` markers)
            match = re.search(r'```\n(.*?)\n```', content, re.DOTALL)
            if match:
                template = match.group(1).strip()
            else:
                # Fallback: look for content after "## Prompt Template"
                match = re.search(r'## Prompt Template\s*\n\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
                template = match.group(1).strip() if match else content.strip()
            
            self._cache[cache_key] = template
        
        return self._cache[cache_key]
    
    def format_prompt(self, prompt_file: str, **kwargs) -> str:
        """Load and format a prompt with variables."""
        template = self.load_prompt_template(prompt_file)
        return template.format(**kwargs)


# Global loader instance
_loader: Optional[PromptLoader] = None

def get_loader() -> PromptLoader:
    """Get or create the global prompt loader."""
    global _loader
    if _loader is None:
        _loader = PromptLoader()
    return _loader

def load_prompt(prompt_file: str) -> str:
    """Convenience function to load a prompt template."""
    return get_loader().load_prompt_template(prompt_file)

def format_prompt(prompt_file: str, **kwargs) -> str:
    """Convenience function to format a prompt."""
    return get_loader().format_prompt(prompt_file, **kwargs)

