"""
Test script to check which Claude models are available with current API key.
"""
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# List of model identifiers to test
models_to_test = [
    # Claude 3.5 models
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
    "claude-3-5-haiku-20241022",

    # Claude 3 models (older)
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307",

    # Claude 4 models (if available)
    "claude-4-sonnet-20250514",
    "claude-sonnet-4-5-20250929",
    "claude-4.5-sonnet",

    # Alternative naming conventions
    "claude-sonnet-3.5",
    "claude-3.5-sonnet",
]

print("Testing Claude API model availability...\n")
print("=" * 80)

for model in models_to_test:
    try:
        # Try a minimal API call
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print(f"OK SUCCESS: {model}")
        print(f"   Response: {response.content[0].text}")
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not_found" in error_msg:
            print(f"ERROR 404: {model} - Model not found")
        elif "401" in error_msg or "authentication" in error_msg.lower():
            print(f"ERROR 401: {model} - Authentication failed")
        elif "403" in error_msg or "permission" in error_msg.lower():
            print(f"ERROR 403: {model} - No permission to access this model")
        else:
            print(f"ERROR: {model} - {error_msg[:100]}")
    print()

print("=" * 80)
print("\nCheck complete. Use models marked as 'OK SUCCESS' in your application.")
