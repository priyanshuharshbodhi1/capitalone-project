from __future__ import annotations
import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Tuple

from .state import AgentState, TurnMessage
from .delegating_agent import route_intent
from .composer_agent import compose_answer, compose_enhanced_answer
from .agents.weather_agent import weather_agent
from .agents.market_agent import fetch_market
from .agents.govt_scheme_agent import govt_scheme_agent
from .agents.agronomist_agent import agronomist_agent
from .memory.checkpointer import RedisCheckpointer
from .memory.memory_agent import get_memory_service
from ..infra.settings import settings

# Groq tool calling setup
try:
    from groq import Groq
    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False

_checkpointer = RedisCheckpointer()

# Weather tool definitions moved inline to _get_gemini_client()

def _get_groq_client():
    """Get configured Groq client"""
    if not settings.groq_api_key or not _GROQ_AVAILABLE:
        print("⚠️ Groq client unavailable: missing API key or import failed")
        return None
    
    try:
        client = Groq(api_key=settings.groq_api_key)
        print("✅ Groq client initialized successfully")
        return client
        
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")
        return None

def _get_weather_tools():
    """Get weather tool definitions in OpenAI/Groq format"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get real-time weather conditions including soil parameters for immediate farm decisions like irrigation and pesticide application",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lat": {
                            "type": "number",
                            "description": "Latitude coordinate"
                        },
                        "lon": {
                            "type": "number", 
                            "description": "Longitude coordinate"
                        }
                    },
                    "required": ["lat", "lon"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_future_weather",
                "description": "Get weather forecast for crop planning, planting timing, and harvest scheduling",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lat": {
                            "type": "number",
                            "description": "Latitude coordinate"
                        },
                        "lon": {
                            "type": "number",
                            "description": "Longitude coordinate"
                        },
                        "days": {
                            "type": "number",
                            "description": "Number of forecast days (1-16)"
                        }
                    },
                    "required": ["lat", "lon"]
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "get_historical_weather",
                "description": "Get historical weather patterns for crop selection and seasonal analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lat": {
                            "type": "number",
                            "description": "Latitude coordinate"
                        },
                        "lon": {
                            "type": "number",
                            "description": "Longitude coordinate"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format"
                        },
                        "end_date": {
                            "type": "string", 
                            "description": "End date in YYYY-MM-DD format"
                        }
                    },
                    "required": ["lat", "lon", "start_date", "end_date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_weather_alerts",
                "description": "Get weather alerts and warnings for crop protection and emergency planning",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lat": {
                            "type": "number",
                            "description": "Latitude coordinate"
                        },
                        "lon": {
                            "type": "number",
                            "description": "Longitude coordinate"
                        }
                    },
                    "required": ["lat", "lon"]
                }
            }
        }
    ]

def _execute_tool_call(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the actual tool call based on name and parameters"""
    print(f"🔧 Executing tool: {tool_name} with parameters: {parameters}")
    
    try:
        if tool_name == "get_current_weather":
            result = weather_agent.get_current_weather(parameters["lat"], parameters["lon"])
            print(f"✅ Tool {tool_name} executed successfully: {result}")
            return result
        elif tool_name == "get_future_weather":
            days = parameters.get("days", 7)
            result = weather_agent.get_future_weather(parameters["lat"], parameters["lon"], days)
            print(f"✅ Tool {tool_name} executed successfully: {result}")
            return result
        elif tool_name == "get_historical_weather":
            result = weather_agent.get_historical_weather(
                parameters["lat"], parameters["lon"], 
                parameters["start_date"], parameters["end_date"]
            )
            print(f"✅ Tool {tool_name} executed successfully: {result}")
            return result
        elif tool_name == "get_weather_alerts":
            result = weather_agent.get_weather_alerts(parameters["lat"], parameters["lon"])
            print(f"✅ Tool {tool_name} executed successfully: {result}")
            return result
        else:
            error_msg = f"Unknown tool: {tool_name}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Error executing tool {tool_name}: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}


def _groq_tool_execution(user_text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Groq-style tool calling: LLM decides which tools to call with parameters"""
    print(f"🤖 Starting tool execution for query: {user_text[:100]}...")
    print(f"📍 Context: {context}")
    
    client = _get_groq_client()
    if not client:
        print("❌ No Groq client available, skipping tool execution")
        return []
    
    lat = context.get("lat")
    lon = context.get("lon")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        print(f"❌ Invalid coordinates: lat={lat}, lon={lon}")
        return []
    
    print(f"✅ Valid coordinates: lat={lat}, lon={lon}")
    
    # Prompt for tool selection
    prompt = f"""You are an agricultural AI assistant helping Indian farmers.

Farmer's location: {lat}, {lon}
Farmer's question: "{user_text}"

Based on their question, determine which weather tools would be most helpful. You can call multiple tools if needed.

Available tools:
1. get_current_weather(lat, lon) - for immediate decisions like irrigation, spraying
2. get_future_weather(lat, lon, days) - for planning activities, harvest timing  
3. get_historical_weather(lat, lon, start_date, end_date) - for comparing patterns
4. get_weather_alerts(lat, lon) - for emergency planning, crop protection

Call the appropriate tools to provide comprehensive agricultural guidance."""
    
    try:
        tools = _get_weather_tools()
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Will update to llama-4-scout when available
            messages=[{"role": "user", "content": prompt}],
            tools=tools,
            tool_choice="auto",
            temperature=0.1,
            max_tokens=1000
        )
        
        tools_executed = []
        
        # Check if the model decided to call tools
        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    parameters = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    print(f"❌ Failed to parse tool arguments: {tool_call.function.arguments}")
                    continue
                
                # Inject location automatically if not provided
                parameters.setdefault('lat', lat)
                parameters.setdefault('lon', lon)
                
                # Execute tool
                result = _execute_tool_call(tool_name, parameters)
                
                tools_executed.append({
                    "name": tool_name,
                    "input": parameters,
                    "output": result,
                    "ok": result.get("success", False),
                    "error": result.get("error") if not result.get("success", False) else None,
                    "execution_type": "groq_function_call"
                })
        else:
            # If no tools were called, provide helpful message
            print(f"ℹ️ No tools called for query: {user_text}")
            return [{
                "name": "no_tool_selected",
                "input": {"query": user_text},
                "output": {
                    "success": False,
                    "message": "I couldn't determine the specific weather information you need. Please try asking about current weather, weather forecast, historical weather patterns, or weather alerts with more details.",
                    "suggestions": [
                        "Ask about current weather conditions",
                        "Request a weather forecast for specific days",
                        "Inquire about historical weather patterns",
                        "Check for weather alerts in your area"
                    ]
                },
                "ok": False,
                "error": "Could not determine appropriate tool - please provide more specific details about what weather information you need"
            }]
        
        return tools_executed
        
    except Exception as e:
        print(f"❌ Groq tool execution error: {e}")
        return [{
            "name": "execution_error",
            "input": {"query": user_text},
            "output": {
                "success": False, 
                "message": "I encountered an error while processing your request. Please try rephrasing your question or check your connection.",
                "error": str(e)
            },
            "ok": False,
            "error": f"Tool execution failed: {str(e)}"
        }]

def _execute_multiple_tools_parallel(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Execute multiple tools in parallel (LangGraph ToolNode behavior)"""
    results = []
    
    # In real LangGraph, this would use asyncio for true parallel execution
    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        parameters = tool_call.get("parameters", {})
        
        result = _execute_tool_call(tool_name, parameters)
        results.append({
            "name": tool_name,
            "input": parameters,
            "output": result,
            "ok": result.get("success", False),
            "error": result.get("error") if not result.get("success", False) else None
        })
    
    return results


class AppGraph:
    def __init__(self) -> None:
        pass

    async def run_stream(self, messages: List[Dict[str, Any]], context: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        # Build state
        state = AgentState(messages=[TurnMessage(**m) for m in messages], context=context)
        user_text = state.last_user() or ""
        
        # Get memory service
        memory_service = get_memory_service()
        session_id = context.get("session_id", "default")
        
        # Step 1: Retrieve relevant memories before processing
        if memory_service.is_available() and user_text:
            try:
                print(f"🧠 Retrieving memories for session: {session_id}")
                relevant_memories = memory_service.get_relevant_memories(session_id, user_text, limit=3)
                print(f"🧠 Retrieved {len(relevant_memories)} memories, types: {[type(m) for m in relevant_memories]}")
                
                state.memory_context = relevant_memories
                
                # Extract user preferences from memories
                for i, memory in enumerate(relevant_memories):
                    try:
                        if isinstance(memory, dict) and memory.get("metadata", {}).get("type") == "farming_context":
                            state.user_preferences.update(memory.get("metadata", {}))
                    except Exception as mem_error:
                        print(f"❌ Error processing memory {i}: {mem_error}")
                        continue
                
                # Add memory context to enhance the query
                if relevant_memories:
                    try:
                        memory_context_text = "\n".join([
                            f"- {memory.get('memory', '') if isinstance(memory, dict) else str(memory)}" 
                            for memory in relevant_memories
                        ])
                        print(f"🧠 Found {len(relevant_memories)} relevant memories")
                        context["memory_context"] = memory_context_text
                    except Exception as context_error:
                        print(f"❌ Error building memory context: {context_error}")
                
                # Store farming context if this is the first time we see location/context
                if context.get("lat") and context.get("lon"):
                    memory_service.add_farming_context(session_id, context)
                    
            except Exception as memory_error:
                print(f"❌ Memory processing error: {memory_error}")
                # Continue without memory if there's an error
                state.memory_context = []
        
        # Step 2: Route intent with enhanced context
        intents = route_intent(user_text, context)

        # Weather intent path using Gemini tool calling
        if "weather" in intents:
            # First message: Show detected intents
            yield {
                "type": "intents", 
                "text": f"Detected intents: {', '.join(intents)}",
                "intents": intents
            }
            
            lat = context.get("lat")
            lon = context.get("lon")
            
            if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                yield {
                    "type": "final",
                    "text": "I need your location to provide weather information. Please enable location access in your browser.",
                    "intents": intents,
                    "citations": []
                }
                return
            
            # Use Groq tool calling: LLM decides which tools to execute
            tools_used = _groq_tool_execution(user_text, context)
            
            if not tools_used:
                yield {
                    "type": "final",
                    "text": "I couldn't determine the appropriate weather tool for your query. Please try rephrasing your question.",
                    "intents": intents,
                    "citations": []
                }
                return
            
            # Second message: Enhanced composed answer after tool execution
            memory_context = getattr(state, 'memory_context', []) if state else []
            
            # Convert messages to format expected by enhanced composer
            chat_history = [{"role": msg.role, "content": msg.content} for msg in state.messages] if state else []
            
            composed = compose_enhanced_answer(
                original_query=user_text,
                chat_history=chat_history,
                agent_responses=tools_used,
                intent="weather",
                context=context,
                memory_context=memory_context
            )
            final_response = composed.get("text", "")
            
            # Store conversation in memory if relevant
            if memory_service.is_available():
                memory_service.add_conversation_memory(session_id, user_text, final_response, "weather")
            
            yield {
                "type": "final",
                "text": final_response,
                "intents": intents,
                "citations": composed.get("citations", []),
            }
            return

        # Government Scheme intent path using Perplexity Sonar
        if "govt_scheme" in intents:
            yield {
                "type": "intents",
                "text": f"Detected intents: {', '.join(intents)}",
                "intents": intents
            }
            
            # Extract context for policy search
            state = context.get("state")
            farmer_type = context.get("farmer_type")
            
            # Search government schemes using Perplexity Sonar
            scheme_result = govt_scheme_agent.search_schemes(user_text, state, farmer_type)
            
            tools_used = [{
                "name": "search_schemes",
                "input": {"query": user_text, "state": state, "farmer_type": farmer_type},
                "output": scheme_result,
                "ok": scheme_result.get("success", False),
                "error": scheme_result.get("error") if not scheme_result.get("success", False) else None
            }]
            
            # Compose enhanced final response
            memory_context = getattr(state, 'memory_context', []) if state else []
            
            # Convert messages to format expected by enhanced composer
            chat_history = [{"role": msg.role, "content": msg.content} for msg in state.messages] if state else []
            
            composed = compose_enhanced_answer(
                original_query=user_text,
                chat_history=chat_history,
                agent_responses=tools_used,
                intent="govt_scheme",
                context=context,
                memory_context=memory_context
            )
            final_response = composed.get("text", "")
            
            # Store conversation in memory if relevant
            if memory_service.is_available():
                memory_service.add_conversation_memory(session_id, user_text, final_response, "govt_scheme")
            
            yield {
                "type": "final",
                "text": final_response,
                "intents": intents,
                "citations": composed.get("citations", [])
            }
            return

        # Agronomist intent path using GPT-4o
        if "agronomist" in intents:
            yield {
                "type": "intents",
                "text": f"Detected intents: {', '.join(intents)}",
                "intents": intents
            }
            
            # Extract context for agronomic advice
            location_context = None
            if context.get("state"):
                location_context = f"State: {context.get('state')}"
                if context.get("district"):
                    location_context += f", District: {context.get('district')}"
            
            season = context.get("season")
            farmer_type = context.get("farmer_type")
            farm_size = context.get("farm_size")
            
            # Get agronomic advice
            agronomic_result = agronomist_agent.get_agronomic_advice(
                query=user_text,
                location_context=location_context,
                season=season,
                farmer_type=farmer_type,
                farm_size=farm_size,
                additional_context=context.get("additional_context")
            )
            
            tools_used = [{
                "name": "get_agronomic_advice",
                "input": {
                    "query": user_text,
                    "location_context": location_context,
                    "season": season,
                    "farmer_type": farmer_type,
                    "farm_size": farm_size
                },
                "output": agronomic_result,
                "ok": agronomic_result.get("success", False),
                "error": agronomic_result.get("error") if not agronomic_result.get("success", False) else None
            }]
            
            # Compose enhanced final response
            memory_context = getattr(state, 'memory_context', []) if state else []
            
            # Convert messages to format expected by enhanced composer
            chat_history = [{"role": msg.role, "content": msg.content} for msg in state.messages] if state else []
            
            composed = compose_enhanced_answer(
                original_query=user_text,
                chat_history=chat_history,
                agent_responses=tools_used,
                intent="agronomist",
                context=context,
                memory_context=memory_context
            )
            final_response = composed.get("text", "")
            
            # Store conversation in memory if relevant
            if memory_service.is_available():
                memory_service.add_conversation_memory(session_id, user_text, final_response, "agronomist")
            
            yield {
                "type": "final",
                "text": final_response,
                "intents": intents,
                "citations": composed.get("citations", [])
            }
            return

        # Handle general/unclear queries with helpful guidance
        if "general" in intents:
            # Use enhanced composer for consistent handling
            memory_context = getattr(state, 'memory_context', []) if state else []
            chat_history = [{"role": msg.role, "content": msg.content} for msg in state.messages] if state else []
            
            # Create empty agent responses for general case
            tools_used = [{
                "name": "general_guidance",
                "input": {"query": user_text},
                "output": {
                    "success": True,
                    "message": "Providing general agricultural assistance guidance",
                    "available_services": [
                        "Weather Information (current, forecast, historical, alerts)",
                        "Government Schemes (subsidies, regulations)",
                        "Market Data (crop prices)",
                        "Agricultural Advice (crop selection, farming techniques)",
                        "IoT Information (smart farming technology)"
                    ]
                },
                "ok": True,
                "error": None
            }]
            
            composed = compose_enhanced_answer(
                original_query=user_text,
                chat_history=chat_history,
                agent_responses=tools_used,
                intent="general",
                context=context,
                memory_context=memory_context
            )
            
            # Note: We don't store general guidance in memory as it's not user-specific
            
            yield {
                "type": "final",
                "text": composed.get("text", "I can help you with various farming-related questions. Please provide more specific details about what you need."),
                "intents": intents,
                "citations": composed.get("citations", [])
            }
            return

        # Fallback to original intent echo behavior for other unhandled intents
        intents_text = ", ".join(intents)
        response_text = f"I can help with {intents_text} related queries. Please provide more specific details about what you need."
        yield {"type": "final", "text": response_text, "intents": intents}


def _chunk_text(s: str, n: int) -> List[str]:
    return [s[i : i + n] for i in range(0, len(s), n)] if s else []


_app_graph: AppGraph | None = None


def get_app_graph() -> AppGraph:
    global _app_graph
    if _app_graph is None:
        _app_graph = AppGraph()
    return _app_graph
