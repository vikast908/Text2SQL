"""LLM client for OpenAI interactions."""

import os
from typing import Optional, Dict, Any, List
from openai import OpenAI
from openai._exceptions import APIError, APIConnectionError, RateLimitError

from src.settings import settings
from src.utils.logging import get_logger
from .exceptions import LLMClientException

logger = get_logger(__name__)


class LLMClient:
    """Client for interacting with OpenAI."""
    
    def __init__(self):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Model name (defaults to settings)
        """
        self.api_key = settings.openai.api_key
        self.model = settings.openai.model

        self._client: Optional[OpenAI] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the OpenAI client."""
        try:
            # Validate required parameters before attempting to create client
            if not self.api_key:
                raise LLMClientException(
                    "Missing required environment variable: OPENAI_API_KEY",
                    details={"missing_variables": ["OPENAI_API_KEY"]},
                )
            
            self._client = OpenAI(
                api_key=self.api_key,
            )
            logger.debug("OpenAI client initialized successfully")
        
        except LLMClientException:
            # Re-raise our custom exceptions as-is
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise LLMClientException(
                f"Failed to initialize OpenAI client: {str(e)}",
                details={"error_type": type(e).__name__},
            ) from e
    
    def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a completion using the LLM.
        
        Args:
            system_prompt: System prompt for the conversation
            user_prompt: User prompt/question
            model: Model name to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
            
        Raises:
            LLMClientException: If generation fails
        """
        if not self._client:
            raise LLMClientException("LLM client not initialized")
        
        try:
            logger.debug(f"Generating completion with model: {model}, temperature: {temperature}")
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            
            # Use the model from parameter or default to settings model
            model_to_use = model if model else self.model
            
            response = self._client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            result = response.choices[0].message.content
            if not result:
                raise LLMClientException("Empty response from LLM")
            
            logger.debug("Successfully generated completion")
            return result.strip()
        
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise LLMClientException(
                "Rate limit exceeded. Please try again later.",
                details={"error_type": "rate_limit"},
            ) from e
        
        except APIConnectionError as e:
            logger.error(f"API connection error: {e}")
            raise LLMClientException(
                "Failed to connect to OpenAI service.",
                details={"error_type": "connection_error"},
            ) from e
        
        except APIError as e:
            logger.error(f"API error: {e}")
            raise LLMClientException(
                f"OpenAI API error: {str(e)}",
                details={"error_type": "api_error", "status_code": getattr(e, "status_code", None)},
            ) from e
        
        except Exception as e:
            logger.error(f"Unexpected error during completion generation: {e}")
            raise LLMClientException(
                f"Unexpected error during completion generation: {str(e)}",
                details={"error_type": type(e).__name__},
            ) from e
    
    @property
    def client(self) -> OpenAI:
        """Get the underlying OpenAI client."""
        if not self._client:
            raise LLMClientException("LLM client not initialized")
        return self._client

