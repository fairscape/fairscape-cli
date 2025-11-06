import os
import json
import re
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod


DESCRIPTION_PROMPT_TEMPLATE = """ROLE: Research data management expert specializing in FAIR metadata

TASK: Generate concise, technical descriptions for a computational workflow

INPUT FORMAT:
- Software code that was executed
- Input datasets with samples (first 5 rows)
- Output datasets with samples (first 5 rows)

OUTPUT FORMAT: JSON object with these keys:
{{
  "software_description": "What this code does technically",
  "computation_description": "What this computation accomplishes",
  "input_datasets": {{
    "filename": "Description of this input's role and content"
  }},
  "output_datasets": {{
    "filename": "Description of this output's content and meaning"
  }}
}}

REQUIREMENTS:
- Software description: 1-2 sentences, focus on operations performed
- Computation description: 1-2 sentences, focus on scientific/analytical goal
- Dataset descriptions: 1 sentence each, describe content type and role in workflow
- Be technical but clear, assume scientific audience
- No markdown formatting, just plain JSON

SOFTWARE CODE:
```python
{code}
```

INPUT DATASETS:
{input_samples}

OUTPUT DATASETS:
{output_samples}

Generate the JSON now:"""


class MetadataGenerator(ABC):
    """Abstract base class for generating metadata descriptions."""
    
    @abstractmethod
    def generate_descriptions(
        self, 
        code: str, 
        input_samples: str, 
        output_samples: str
    ) -> Optional[Dict[str, Any]]:
        """Generate descriptions for code and datasets."""
        pass


class GeminiMetadataGenerator(MetadataGenerator):
    """Generate metadata using Google Gemini."""
    
    def __init__(self, api_key: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 2048):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or provided")
    
    def _build_prompt(self, code: str, input_samples: str, output_samples: str) -> str:
        """Build the prompt for the LLM."""
        return DESCRIPTION_PROMPT_TEMPLATE.format(
            code=code,
            input_samples=input_samples,
            output_samples=output_samples
        )
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling various formats."""
        response_text = response_text.strip()
        
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        else:
            code_match = re.search(r'```\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if code_match:
                response_text = code_match.group(1)
            elif not (response_text.startswith('{') and response_text.endswith('}')):
                json_search = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_search:
                    response_text = json_search.group(0)
                    
        return json.loads(response_text)
    
    def generate_descriptions(
        self, 
        code: str, 
        input_samples: str, 
        output_samples: str
    ) -> Optional[Dict[str, Any]]:
        """Generate descriptions using Gemini."""
        import google.generativeai as genai
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = self._build_prompt(code, input_samples, output_samples)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
        )
        
        return self._parse_llm_response(response.text)


class FallbackMetadataGenerator(MetadataGenerator):
    """Generate simple timestamp-based descriptions without LLM."""
    
    def __init__(self, timestamp: str):
        self.timestamp = timestamp
    
    def generate_descriptions(
        self, 
        code: str, 
        input_samples: str, 
        output_samples: str
    ) -> Dict[str, Any]:
        """Generate simple fallback descriptions."""
        return {
            "software_description": f"Code executed at {self.timestamp}",
            "computation_description": f"Computation executed at {self.timestamp}",
            "input_datasets": {},
            "output_datasets": {}
        }


class MockMetadataGenerator(MetadataGenerator):
    """Mock generator for testing."""
    
    def __init__(self, mock_response: Dict[str, Any]):
        self.mock_response = mock_response
    
    def generate_descriptions(
        self, 
        code: str, 
        input_samples: str, 
        output_samples: str
    ) -> Dict[str, Any]:
        """Return mock response."""
        return self.mock_response


def create_metadata_generator(
    provider: str = "gemini",
    api_key: Optional[str] = None,
    **kwargs
) -> MetadataGenerator:
    """Factory function to create appropriate metadata generator."""
    
    if provider == "gemini":
        try:
            gemini_kwargs = {k: v for k, v in kwargs.items() if k in ['temperature', 'max_tokens']}
            return GeminiMetadataGenerator(api_key=api_key, **gemini_kwargs)
        except ValueError:
            print("WARNING: GEMINI_API_KEY not found, using fallback descriptions")
            timestamp = kwargs.get('timestamp', 'unknown')
            return FallbackMetadataGenerator(timestamp=timestamp)
    elif provider == "fallback":
        timestamp = kwargs.get('timestamp', 'unknown')
        return FallbackMetadataGenerator(timestamp=timestamp)
    elif provider == "mock":
        return MockMetadataGenerator(kwargs.get('mock_response', {}))
    else:
        raise ValueError(f"Unknown metadata generator provider: {provider}")