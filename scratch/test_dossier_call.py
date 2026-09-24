import sys
sys.path.insert(0, ".")
from backend.ai_engine import call_groq_api, resolve_api_key

key = resolve_api_key("groq")

# Test with 2048 max_tokens
print("Testing with max_tokens=2048...")
res1 = call_groq_api(
    prompt="Generate a 1-sentence risk summary for target employee Sjoerd Sikkema.",
    system_instruction="You are a cyber intelligence analyst. Return brief text.",
    api_key=key,
    model="qwen/qwen3.8-27b"
)
print("res1 (2048 tokens):", res1.get("success"), res1.get("error"))

# Test with max_tokens=600
print("\nTesting with max_tokens=600...")
# (Let's see what happens when we parameterize max_tokens)
