"""Constants for LLM providers and models"""

# Provider names
PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_GOOGLE = "gemini"
PROVIDER_META = "meta"
PROVIDER_MISTRAL = "mistral"
PROVIDER_UNKNOWN = "unknown"

# Model prefixes
OPENAI_PREFIXES = ["gpt", "openai"]
ANTHROPIC_PREFIXES = ["claude", "anthropic"]
GOOGLE_PREFIX = "gemini"
META_PREFIX = "llama"
MISTRAL_PREFIX = "mistral"

# Default values
DEFAULT_TEMPERATURE = 0.0
DEFAULT_TOP_P = 1.0
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_TOKENS = 1024
