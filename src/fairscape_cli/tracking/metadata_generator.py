import os
import json
import re
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod


DESCRIPTION_PROMPT_TEMPLATE = """ROLE: Research data management expert specializing in FAIR metadata

TASK: Generate concise, technical descriptions for a computational workflow

INPUT FORMAT:
- Software code that was executed
- Input datasets/files (may include tabular data samples or image files)
- Output datasets/files (may include tabular data samples or image files)

OUTPUT FORMAT: Return ONLY a valid JSON object with these keys:
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
- For images: Generate figure legend-style descriptions that describe what is shown in the image scientifically
- Be technical but clear, assume scientific audience
- CRITICAL: Return ONLY valid JSON, no markdown code blocks, no explanations, no trailing commas
- Ensure all string values properly escape quotes and special characters

SOFTWARE CODE:
```python
{code}
```

INPUT FILES:
{input_info}

OUTPUT FILES:
{output_info}

Return the JSON object now (no code blocks, no additional text):"""


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

    def __init__(self, api_key: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 2048, max_images: int = 5):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_images = max_images

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or provided")
    
    def _is_image_file(self, filepath: str) -> bool:
        """Check if file is an image."""
        from pathlib import Path
        suffix = Path(filepath).suffix.lower()
        return suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp']

    def _build_prompt(self, code: str, input_info: str, output_info: str) -> str:
        """Build the prompt for the LLM."""
        return DESCRIPTION_PROMPT_TEMPLATE.format(
            code=code,
            input_info=input_info,
            output_info=output_info
        )

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling various formats."""
        response_text = response_text.strip()

        # Try to extract JSON from markdown code blocks
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

        # Clean common JSON formatting issues
        response_text = response_text.strip()

        # Remove trailing commas before closing braces/brackets
        response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)

        # Try to parse
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            # If parsing fails, try to provide helpful debug info
            print(f"DEBUG: Failed to parse LLM response. Error: {e}", file=__import__('sys').stderr)
            print(f"DEBUG: Response text (first 500 chars):\n{response_text[:500]}", file=__import__('sys').stderr)
            print(f"DEBUG: Response text (last 500 chars):\n{response_text[-500:]}", file=__import__('sys').stderr)

            # Try one more aggressive cleanup: find the largest valid JSON object
            # by matching braces more carefully
            brace_count = 0
            start_idx = response_text.find('{')
            if start_idx == -1:
                raise ValueError("No JSON object found in LLM response") from e

            for i in range(start_idx, len(response_text)):
                if response_text[i] == '{':
                    brace_count += 1
                elif response_text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Found matching closing brace
                        candidate = response_text[start_idx:i+1]
                        # Clean and try again
                        candidate = re.sub(r',(\s*[}\]])', r'\1', candidate)
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            pass

            # If all else fails, re-raise original error
            raise

    def generate_descriptions(
        self,
        code: str,
        input_files: Dict[str, str],
        output_files: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Generate descriptions using Gemini with support for images.

        Args:
            code: The source code
            input_files: Dict mapping filename to filepath
            output_files: Dict mapping filename to filepath
        """
        import google.generativeai as genai
        from pathlib import Path
        from PIL import Image

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Separate image files from other files
        input_images = {k: v for k, v in input_files.items() if self._is_image_file(v)}
        output_images = {k: v for k, v in output_files.items() if self._is_image_file(v)}

        # Limit total images to avoid Gemini safety filters
        # Reserve 2 for inputs, rest for outputs (CAM visualizations are more important)
        total_image_budget = self.max_images
        max_input_images = min(2, len(input_images))
        max_output_images = min(total_image_budget - max_input_images, len(output_images))

        input_images = dict(list(input_images.items())[:max_input_images])
        output_images = dict(list(output_images.items())[:max_output_images])

        # Build text descriptions for files
        input_info_parts = []
        for filename in input_files.keys():
            if filename in input_images:
                input_info_parts.append(f"- {filename} (image - see attached)")
            else:
                input_info_parts.append(f"- {filename}")

        output_info_parts = []
        for filename in output_files.keys():
            if filename in output_images:
                output_info_parts.append(f"- {filename} (image - see attached)")
            else:
                output_info_parts.append(f"- {filename}")

        input_info = "\n".join(input_info_parts) if input_info_parts else "None"
        output_info = "\n".join(output_info_parts) if output_info_parts else "None"

        prompt = self._build_prompt(code, input_info, output_info)

        # Build content list with prompt and images
        content = [prompt]

        # Add input images
        for filename, filepath in input_images.items():
            try:
                img = Image.open(filepath)
                content.append(img)
                content.append(f"Input image: {filename}")
            except Exception as e:
                print(f"WARNING: Could not load input image {filename}: {e}", file=__import__('sys').stderr)

        # Add output images
        for filename, filepath in output_images.items():
            try:
                img = Image.open(filepath)
                content.append(img)
                content.append(f"Output image: {filename}")
            except Exception as e:
                print(f"WARNING: Could not load output image {filename}: {e}", file=__import__('sys').stderr)

        response = model.generate_content(
            content,
            generation_config=genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                response_mime_type="application/json",
            )
        )

        # Check if response was blocked by safety filters
        if not response.candidates or not response.candidates[0].content.parts:
            finish_reason = response.candidates[0].finish_reason if response.candidates else None
            raise ValueError(
                f"Gemini blocked the response (finish_reason={finish_reason}). "
                f"This usually means too many images were sent. "
                f"Sent {len(input_images)} input images + {len(output_images)} output images. "
                f"Try reducing max_images parameter (currently {self.max_images})."
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
            gemini_kwargs = {k: v for k, v in kwargs.items() if k in ['temperature', 'max_tokens', 'max_images']}
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