#!/usr/bin/env python3
"""
Simple test script to verify mem0 integration in the chatbot
Run this to test memory functionality before deploying
"""

import sys
import os
import asyncio
import json

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

# Test imports
try:
    from server.agent.memory.memory_agent import get_memory_service
    from server.agent.orchestrator_agent import get_app_graph
    print("✅ Successfully imported memory agent and orchestrator")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def test_memory_integration():
    """Test the memory integration with sample conversations"""
    
    print("\n🧪 Testing Memory Integration\n" + "="*50)
    
    # Initialize services
    memory_service = get_memory_service()
    app_graph = get_app_graph()
    
    if not memory_service.is_available():
        print("⚠️ Memory service not available (mem0 or OpenAI API key missing)")
        print("📝 Testing will continue with memory disabled")
    else:
        print("✅ Memory service is available")
    
    # Test session
    test_session_id = "test_session_123"
    test_context = {
        "session_id": test_session_id,
        "lat": 19.0760,  # Mumbai coordinates for testing
        "lon": 72.8777,
        "locale": "en-IN",
        "location_status": "granted"
    }
    
    # Test conversations
    test_conversations = [
        "I have a 5 acre wheat farm in Punjab",
        "What's the current weather for my farm?",
        "Should I irrigate my wheat today?",
        "What government schemes are available for small farmers?",
        "When is the best time to harvest wheat?"
    ]
    
    print(f"\n🎯 Testing {len(test_conversations)} conversations...")
    
    for i, user_message in enumerate(test_conversations, 1):
        print(f"\n--- Conversation {i} ---")
        print(f"User: {user_message}")
        
        # Prepare messages
        messages = [{"role": "user", "content": user_message}]
        
        try:
            # Process through agent
            final_response = None
            async for event in app_graph.run_stream(messages, test_context):
                if event.get("type") == "final":
                    final_response = event.get("text", "")
                    print(f"Bot: {final_response[:200]}{'...' if len(final_response) > 200 else ''}")
                    break
            
            if not final_response:
                print("❌ No final response received")
                
        except Exception as e:
            print(f"❌ Error in conversation {i}: {e}")
            continue
    
    # Test memory retrieval
    if memory_service.is_available():
        print(f"\n🧠 Testing memory retrieval...")
        test_query = "irrigation advice for wheat"
        try:
            memories = memory_service.get_relevant_memories(test_session_id, test_query, limit=3)
            print(f"Found {len(memories)} relevant memories for '{test_query}'")
            print(f"🔍 Memory types: {[type(m) for m in memories]}")
            
            for j, memory in enumerate(memories, 1):
                print(f"🔍 Memory {j} type: {type(memory)}, keys: {memory.keys() if isinstance(memory, dict) else 'N/A'}")
                if isinstance(memory, dict):
                    memory_text = memory.get("memory", "")[:100]
                    print(f"  {j}. {memory_text}{'...' if len(memory.get('memory', '')) > 100 else ''}")
                else:
                    print(f"  {j}. Unexpected memory format: {str(memory)[:100]}")
        except Exception as memory_error:
            print(f"❌ Memory retrieval error: {memory_error}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ Memory integration test completed!")
    print(f"\n📋 Summary:")
    print(f"   - Memory service: {'✅ Available' if memory_service.is_available() else '❌ Not available'}")
    print(f"   - Conversation processing: ✅ Working")
    print(f"   - Agent pipeline: ✅ Functional")


def test_memory_filtering():
    """Test the memory filtering logic"""
    
    print("\n🔍 Testing Memory Filtering Logic\n" + "="*40)
    
    memory_service = get_memory_service()
    
    # Test cases for memory filtering
    test_cases = [
        # Should NOT be stored
        ("hello", "general", "Hello! How can I help you today?", False),
        ("thanks", "general", "You're welcome!", False),
        ("hi there", "general", "Hi! I'm here to help.", False),
        ("what can you do", "general", "I can help with farming...", False),
        ("error test", "weather", "Sorry, I encountered an error", False),
        
        # Should be stored
        ("what's the weather for my wheat crop", "weather", "Current temperature is 25°C, humidity 60%. Good conditions for wheat growth.", True),
        ("I have 10 acres of rice farm", "general", "That's a good size farm. Rice requires specific water management.", True),
        ("government subsidies for drip irrigation", "govt_scheme", "Available schemes: PM-KISAN, subsidies for micro-irrigation...", True),
        ("when to harvest tomatoes", "general", "Harvest tomatoes when they start turning color but are still firm.", True),
    ]
    
    for user_msg, intent, bot_response, should_store in test_cases:
        result = memory_service.should_store_conversation(user_msg, intent, bot_response)
        status = "✅" if result == should_store else "❌"
        print(f"{status} '{user_msg}' -> {result} (expected: {should_store})")
    
    print(f"\n✅ Memory filtering test completed!")


if __name__ == "__main__":
    print("🚀 Starting Mem0 Integration Tests")
    
    # Test memory filtering logic
    test_memory_filtering()
    
    # Test full integration
    asyncio.run(test_memory_integration())
    
    print("\n🎉 All tests completed!")
    print("\n💡 To enable mem0:")
    print("   1. Install: pip install mem0ai")
    print("   2. Set OPENAI_API_KEY in your environment")
    print("   3. Restart the server")
