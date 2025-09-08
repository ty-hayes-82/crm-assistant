"""
Centralized Model Provider for Phase 9.

This module provides a single provider for gemini-2.5-flash model client initialization
to ensure consistent settings and simplify mocking for tests.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    import google.generativeai as genai
    from google.generativeai import GenerativeModel
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GenerativeModel = None
    GENAI_AVAILABLE = False


@dataclass
class ModelConfig:
    """Configuration for model initialization."""
    model_name: str = "gemini-2.5-flash"
    temperature: float = 0.1
    top_p: float = 0.8
    top_k: int = 40
    max_output_tokens: int = 8192
    safety_settings: Optional[Dict[str, Any]] = None


class ModelProvider:
    """Centralized provider for AI model clients."""
    
    def __init__(self):
        self._model_cache: Dict[str, Any] = {}
        self._default_config = ModelConfig()
        
        # Set up default safety settings
        if GENAI_AVAILABLE:
            self._default_config.safety_settings = {
                genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
    
    def get_model(self, config: Optional[ModelConfig] = None) -> Any:
        """
        Get a configured model instance.
        
        Args:
            config: Optional model configuration. Uses default if not provided.
            
        Returns:
            Configured model instance
            
        Raises:
            ImportError: If google-generativeai is not available
            ValueError: If API key is not configured
        """
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-generativeai not available. Install with: pip install google-generativeai"
            )
        
        config = config or self._default_config
        cache_key = self._get_cache_key(config)
        
        if cache_key in self._model_cache:
            return self._model_cache[cache_key]
        
        # Configure API key
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                "Google API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable."
            )
        
        genai.configure(api_key=api_key)
        
        # Create generation config
        generation_config = genai.types.GenerationConfig(
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            max_output_tokens=config.max_output_tokens,
        )
        
        # Create model
        model = GenerativeModel(
            model_name=config.model_name,
            generation_config=generation_config,
            safety_settings=config.safety_settings
        )
        
        # Cache the model
        self._model_cache[cache_key] = model
        
        return model
    
    def _get_cache_key(self, config: ModelConfig) -> str:
        """Generate a cache key for the model configuration."""
        return f"{config.model_name}_{config.temperature}_{config.top_p}_{config.top_k}_{config.max_output_tokens}"
    
    def clear_cache(self) -> None:
        """Clear the model cache."""
        self._model_cache.clear()
    
    def get_default_config(self) -> ModelConfig:
        """Get the default model configuration."""
        return self._default_config
    
    def set_default_config(self, config: ModelConfig) -> None:
        """Set the default model configuration."""
        self._default_config = config
        # Clear cache to force recreation with new defaults
        self.clear_cache()


# Global model provider instance
_model_provider = None


def get_model_provider() -> ModelProvider:
    """Get the global model provider instance."""
    global _model_provider
    if _model_provider is None:
        _model_provider = ModelProvider()
    return _model_provider


def get_model(config: Optional[ModelConfig] = None) -> Any:
    """
    Convenience function to get a configured model instance.
    
    Args:
        config: Optional model configuration
        
    Returns:
        Configured model instance
    """
    return get_model_provider().get_model(config)


def create_agent_model_config(agent_name: str) -> ModelConfig:
    """
    Create a model configuration optimized for a specific agent.
    
    Args:
        agent_name: Name of the agent (for future customization)
        
    Returns:
        ModelConfig optimized for the agent
    """
    # Base configuration for all CRM agents
    config = ModelConfig(
        model_name="gemini-2.5-flash",
        temperature=0.1,  # Low temperature for consistent, factual responses
        top_p=0.8,
        top_k=40,
        max_output_tokens=8192
    )
    
    # Agent-specific customizations
    if agent_name.lower() in ["lead_scoring", "crm_updater"]:
        # More deterministic for scoring and updates
        config.temperature = 0.05
    elif agent_name.lower() in ["outreach_personalizer"]:
        # Slightly more creative for personalization
        config.temperature = 0.2
        config.max_output_tokens = 4096  # Outreach content is typically shorter
    elif agent_name.lower() in ["company_intelligence", "contact_intelligence"]:
        # Balanced for analysis tasks
        config.temperature = 0.1
        config.max_output_tokens = 6144
    
    return config


# Mock model for testing
class MockModel:
    """Mock model for testing purposes."""
    
    def __init__(self, responses: Optional[Dict[str, str]] = None):
        self.responses = responses or {}
        self.call_count = 0
        self.last_prompt = None
    
    def generate_content(self, prompt: str) -> Any:
        """Mock generate_content method."""
        self.call_count += 1
        self.last_prompt = prompt
        
        # Return mock response
        mock_response = type('MockResponse', (), {
            'text': self.responses.get(prompt, "Mock response"),
            'candidates': [type('MockCandidate', (), {
                'content': type('MockContent', (), {
                    'parts': [type('MockPart', (), {'text': self.responses.get(prompt, "Mock response")})]
                })
            })]
        })()
        
        return mock_response


def get_mock_model(responses: Optional[Dict[str, str]] = None) -> MockModel:
    """
    Get a mock model for testing.
    
    Args:
        responses: Dictionary mapping prompts to responses
        
    Returns:
        MockModel instance
    """
    return MockModel(responses)