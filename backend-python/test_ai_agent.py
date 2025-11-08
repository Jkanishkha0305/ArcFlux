"""
Quick test script for AI agent
"""
import sys
sys.path.insert(0, '.')

from ai_agent import ai_agent

# Test parse intent
test_input = "Pay 10 USDC to 0xfc45b45245ca0045b208a955f619949eed194f02"

print(f"Testing AI agent with input: {test_input}")
print("=" * 50)

try:
    result = ai_agent.parse_payment_intent(test_input)
    print("✅ SUCCESS!")
    print(f"Result: {result}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
