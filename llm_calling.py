import os
import json
import datetime
import logging
import tiktoken
import time
from typing import Optional
from datetime import datetime as dt, timedelta
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

# Force load environment variables
load_dotenv()

# --- 1. CONFIGURATION & LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- 2. RATE LIMITER CLASS ---
from rate_limiter import get_rate_limiter

# Get global thread-safe rate limiter
rate_limiter = get_rate_limiter()


# --- 3. GLOBAL CLIENTS (Initialize once) ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    logger.error("❌ OPENROUTER_API_KEY not found in environment!")
    logger.error("Check your .env file or export OPENROUTER_API_KEY='your-key'")
    raise ValueError("OPENROUTER_API_KEY is required")

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    timeout=60.0
)

# --- 3. UTILITY FUNCTIONS ---
def number_of_tokens(text):
    """Returns the number of tokens in a text string."""
    try:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        num_tokens = len(encoding.encode(text))
        return num_tokens
    except Exception as e:
        logger.error(f"Token counting failed: {e}")
        return 0

# --- 4. CORE LLM FUNCTIONS ---

# local machine
def call_llm_local(user_prompt, system_prompt):
    """Call local LLM instance for testing."""
    client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
    
    model_path = "/Users/harshitbudhraja/Documents/research/dataset_curation/models/qwen_coder_3b"

    try:
        resp = client.chat.completions.create(
            model=model_path,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"Local LLM call failed: {e}")
        return None

# --- OpenRouter with Retry Logic ---
@retry(
    stop=stop_after_attempt(4),  # Increased retries
    wait=wait_exponential(multiplier=2, min=6, max=30),  # Longer waits
    retry=retry_if_exception_type(Exception)
)
def _call_openrouter_with_retry(model, messages, max_tokens, temperature, top_p):
    """Inner function to handle the actual API call with retries."""
    if not openrouter_client:
        raise ValueError("OpenRouter client is not initialized.")
    
    # CRITICAL: Acquire rate limit token (thread-safe)
    rate_limiter.acquire()
    
    # Fix 1: Explicitly disable streaming and stop at special tokens
    completion = openrouter_client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        stream=False,  # Must be False
        stop=["<|file_sep|>", "<|fim_prefix|>", "<|fim_suffix|>", "<|fim_middle|>", "<|endoftext|>"]  # Stop at Qwen special tokens
    )
    
    # Validate response
    if not completion.choices:
        raise RuntimeError("No choices returned from OpenRouter")
    
    response_content = completion.choices[0].message.content
    if not response_content or response_content.strip() == "":
        logger.warning("Empty response - triggering retry")
        raise ValueError("Empty response from provider")
    
    return completion

# cloud
def call_llm_openrouter(
    user_prompt: str, 
    system_prompt: str, 
    model: str, 
    max_tokens: int = 1000, 
    temperature: float = 0.7,  # Increased for better creativity
    top_p: float = 0.9  # Increased for better diversity
) -> Optional[str]:
    """
    Call OpenRouter API with automatic retry logic and rate limiting.
    
    Args:
        user_prompt: The user's message
        system_prompt: The system prompt to set behavior
        model: Model identifier (e.g., "qwen/qwen3-235b-a22b-2507")
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter
        
    Returns:
        Generated text or None if failed after retries
    """
    
    # Apply rate limiting is now handled inside _call_openrouter_with_retry
    
    # Use standard message format (system + user separate)
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    try:
        # Call with retry logic
        completion = _call_openrouter_with_retry(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )

        # Fix 2: Treat empty output as HARD failure
        if not completion.choices:
            raise RuntimeError("No choices returned from OpenRouter")
        
        msg = completion.choices[0].message
        if not msg or not msg.content or not msg.content.strip():
            raise RuntimeError("Empty response from OpenRouter")

        return msg.content.strip()

    except Exception as e:
        logger.error(f"Final failure for model {model}: {e}")
        _log_error_to_file(model, str(e), None)
        return None


def _log_error_to_file(model, error_msg, completion_obj):
    """Helper to log errors to error_logs.json"""
    try:
        with open('error_logs.json', 'a') as error_file:
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "model": model,
                "error": error_msg
            }
            if completion_obj:
                try:
                    log_entry["completion"] = completion_obj.model_dump()
                except:
                    pass
            json.dump(log_entry, error_file, indent=2)
            error_file.write("\n")
    except IOError as e:
        logger.error(f"Failed to write error log: {e}")
