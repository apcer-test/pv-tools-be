"""LLM Gateway - Vendor-agnostic LLM API calls"""
import time
import logging
from typing import Dict, Any
from decimal import Decimal

import litellm
from litellm.exceptions import AuthenticationError, Timeout, RateLimitError

from apps.ai_extraction.schemas.response import LLMCallResult
from apps.ai_extraction.exceptions import ProviderError
from constants.llm import (
    PROVIDER_OPENAI, PROVIDER_ANTHROPIC, PROVIDER_GOOGLE, 
    PROVIDER_META, PROVIDER_MISTRAL, PROVIDER_UNKNOWN,
    OPENAI_PREFIXES, ANTHROPIC_PREFIXES, GOOGLE_PREFIX,
    META_PREFIX, MISTRAL_PREFIX, DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P, DEFAULT_TIMEOUT, DEFAULT_MAX_TOKENS
)


class LLMGateway:
    """Gateway for vendor-agnostic LLM API calls using LiteLLM."""
    
    _logger = logging.getLogger(__name__)

    @staticmethod
    async def call(*,
        provider: str,
        model: str,
        prompt: str | list,  # Update type hint to allow list
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        credential,
        timeout: int = DEFAULT_TIMEOUT
    ) -> LLMCallResult:
        """Make a vendor-agnostic call via LiteLLM.
        
        Args:
            model: Model identifier (e.g., "gpt-4", "claude-3-sonnet")
            prompt: The prompt text or list of content parts with file references
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 2.0)
            top_p: Nucleus sampling parameter (0.0 to 1.0)
            credential: Credential object with api_key and base_url
            timeout: Request timeout in seconds
            
        Returns:
            LLMCallResult with response and metadata
            
        Raises:
            ProviderError: On authentication, timeout, or other API errors
        """
        start_time = time.time()
        
        # Log call start
        LLMGateway._logger.info(f"LLM call started - Provider: {provider}, Model: {model}, MaxTokens: {max_tokens}, Temperature: {temperature}")
        
        try:
            # Prepare the call parameters
            call_params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "timeout": timeout,
                "custom_llm_provider": provider,
            }

            # Handle different prompt types
            if isinstance(prompt, list):
                # If prompt is a list of content parts, use it directly
                call_params["messages"] = [{"role": "user", "content": prompt}]
                LLMGateway._logger.debug(f"Using content parts prompt - Provider: {provider}, Model: {model}, Parts: {len(prompt)}")
            else:
                # If prompt is a string, wrap it in a message
                call_params["messages"] = [{"role": "user", "content": prompt}]
                LLMGateway._logger.debug(f"Using text prompt - Provider: {provider}, Model: {model}, Length: {len(prompt)}")
            
            # Add credentials if available
            if hasattr(credential, 'api_key') and credential.api_key:
                call_params["api_key"] = credential.api_key
                LLMGateway._logger.debug(f"Added API key for provider: {provider}")
            else:
                LLMGateway._logger.warning(f"No API key provided for provider: {provider}")
            
            # Make the API call
            LLMGateway._logger.info(f"Making API call to {provider} - Model: {model}")
            response = await litellm.acompletion(**call_params)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract response data
            message_content = response.choices[0].message.content
            usage = response.usage
            
            # Calculate cost (litellm provides cost calculation)
            cost_usd = Decimal(str(litellm.completion_cost(response) or 0.0))
            
            # Log successful call
            LLMGateway._logger.info(f"LLM call successful - Provider: {provider}, Model: {model}, Tokens: {usage.prompt_tokens}/{usage.completion_tokens}, Cost: ${cost_usd}, Latency: {latency_ms}ms")
            
            return LLMCallResult(
                response_text=message_content,
                model_used=model,
                tokens_prompt=usage.prompt_tokens,
                tokens_completion=usage.completion_tokens,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                provider=provider
            )
            
        except AuthenticationError as e:
            error_msg = f"Authentication failed: {str(e)}"
            LLMGateway._logger.error(f"Authentication error - Provider: {provider}, Model: {model}, Error: {error_msg}")
            raise ProviderError("AUTH_FAIL", error_msg)
        except Timeout as e:
            error_msg = f"Request timeout: {str(e)}"
            LLMGateway._logger.error(f"Timeout error - Provider: {provider}, Model: {model}, Error: {error_msg}")
            raise ProviderError("TIMEOUT", error_msg)
        except RateLimitError as e:
            error_msg = f"Rate limit exceeded: {str(e)}"
            LLMGateway._logger.error(f"Rate limit error - Provider: {provider}, Model: {model}, Error: {error_msg}")
            raise ProviderError("RATE_LIMIT", error_msg)
        except Exception as e:
            error_msg = f"LLM API call failed: {str(e)}"
            LLMGateway._logger.error(f"API call error - Provider: {provider}, Model: {model}, Error: {error_msg}", exc_info=True)
            raise ProviderError("API_ERROR", error_msg)

    @staticmethod
    def _get_provider_from_model(model: str) -> str:
        """Determine provider from model name.
        
        Args:
            model: Model identifier
            
        Returns:
            Provider name
        """
        model_lower = model.lower()
        
        if any(prefix in model_lower for prefix in OPENAI_PREFIXES):
            return PROVIDER_OPENAI
        elif any(prefix in model_lower for prefix in ANTHROPIC_PREFIXES):
            return PROVIDER_ANTHROPIC
        elif GOOGLE_PREFIX in model_lower:
            return PROVIDER_GOOGLE
        elif META_PREFIX in model_lower:
            return PROVIDER_META
        elif MISTRAL_PREFIX in model_lower:
            return PROVIDER_MISTRAL
        else:
            return PROVIDER_UNKNOWN
