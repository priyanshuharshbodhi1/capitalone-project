from __future__ import annotations
import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Tuple

from .state import AgentState, TurnMessage
from .delegating_agent import route_intent
from .composer_agent import compose_answer
from .agents.weather_agent import weather_agent
from .agents.market_agent import fetch_market
from .agents.govt_policy_agent import govt_policy_agent
from .memory.checkpointer import RedisCheckpointer
from ..infra.settings import settings

# Gemini tool calling setup
try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

_checkpointer = RedisCheckpointer()

# Weather tool definitions moved inline to _get_gemini_client()

def _get_gemini_client():
    """Get configured Gemini client with tools"""
    if not settings.gemini_api_key or not _GEMINI_AVAILABLE:
        print("⚠️ Gemini client unavailable: missing API key or import failed")
        return None
    
    try:
        genai.configure(api_key=settings.gemini_api_key)
        
        # Create tools in correct Gemini format - using function declarations
        tools = [
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name="get_current_weather",
                        description="Get real-time weather conditions including soil parameters for immediate farm decisions like irrigation and pesticide application",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "lat": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Latitude coordinate"),
                                "lon": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Longitude coordinate")
                            },
                            required=["lat", "lon"]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_future_weather",
                        description="Get weather forecast for crop planning, planting timing, and harvest scheduling",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "lat": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Latitude coordinate"),
                                "lon": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Longitude coordinate"),
                                "days": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Number of forecast days (1-16)")
                            },
                            required=["lat", "lon"]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_historical_weather",
                        description="Get historical weather patterns for crop selection and seasonal analysis",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "lat": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Latitude coordinate"),
                                "lon": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Longitude coordinate"),
                                "start_date": genai.protos.Schema(type=genai.protos.Type.STRING, description="Start date in YYYY-MM-DD format"),
                                "end_date": genai.protos.Schema(type=genai.protos.Type.STRING, description="End date in YYYY-MM-DD format")
                            },
                            required=["lat", "lon", "start_date", "end_date"]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_weather_alerts",
                        description="Get weather alerts and warnings for crop protection and emergency planning",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "lat": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Latitude coordinate"),
                                "lon": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Longitude coordinate")
                            },
                            required=["lat", "lon"]
                        )
                    )
                ]
            )
        ]
        
        print("✅ Gemini client initialized successfully with tools")
        return genai.GenerativeModel("gemini-1.5-flash", tools=tools)
        
    except Exception as e:
        print(f"❌ Failed to initialize Gemini client: {e}")
        return None

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


def _langgraph_style_tool_execution(user_text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """LangGraph-style tool calling: LLM decides which tools to call with parameters"""
    print(f"🤖 Starting tool execution for query: {user_text[:100]}...")
    print(f"📍 Context: {context}")
    
    client = _get_gemini_client()
    if not client:
        print("❌ No Gemini client available, skipping tool execution")
        return []
    
    lat = context.get("lat")
    lon = context.get("lon")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        print(f"❌ Invalid coordinates: lat={lat}, lon={lon}")
        return []
    
    print(f"✅ Valid coordinates: lat={lat}, lon={lon}")
    
    # LangGraph-style prompt: Let LLM decide which tools and parameters to use
    prompt = f"""You are an agricultural AI assistant helping Indian farmers. 
    
    Farmer's location: {lat}, {lon}
    Farmer's question: "{user_text}"
    
    Based on their question, determine which weather tools would be most helpful.
    You can call multiple tools in parallel if needed.
    
    Available tools:
    1. get_current_weather(lat, lon) - for immediate decisions like irrigation, spraying
    2. get_future_weather(lat, lon, days) - for planning activities, harvest timing  
    3. get_historical_weather(lat, lon, start_date, end_date) - for comparing patterns
    4. get_weather_alerts(lat, lon) - for emergency planning, crop protection
    
    Call the appropriate tools to provide comprehensive agricultural guidance."""
    
    try:
        response = client.generate_content(prompt)
        tools_executed = []
        
        # Execute tools in parallel (LangGraph ToolNode style)
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call'):
                            func_call = part.function_call
                            tool_name = func_call.name
                            parameters = dict(func_call.args)
                            
                            # Inject location automatically
                            parameters.setdefault('lat', lat)
                            parameters.setdefault('lon', lon)
                            
                            # Execute tool (parallel execution in real LangGraph)
                            result = _execute_tool_call(tool_name, parameters)
                            
                            tools_executed.append({
                                "name": tool_name,
                                "input": parameters,
                                "output": result,
                                "ok": result.get("success", False),
                                "error": result.get("error") if not result.get("success", False) else None,
                                "execution_type": "parallel"
                            })
        
        return tools_executed
        
    except Exception as e:
        print(f"LangGraph-style tool execution error: {e}")
        return []

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
            
            # Use LangGraph-style tool calling: LLM decides which tools to execute
            tools_used = _langgraph_style_tool_execution(user_text, context)
            
            if not tools_used:
                yield {
                    "type": "final",
                    "text": "I couldn't determine the appropriate weather tool for your query. Please try rephrasing your question.",
                    "intents": intents,
                    "citations": []
                }
                return
            
            # Second message: Composed answer after tool execution
            composed = compose_answer(tools_used, intent="weather", locale=context.get("locale"))
            yield {
                "type": "final",
                "text": composed.get("text", ""),
                "intents": intents,
                "citations": composed.get("citations", []),
            }
            return

        # Government Policy intent path using Perplexity Sonar
        if "govt_policy" in intents:
            yield {
                "type": "intents",
                "text": f"Detected intents: {', '.join(intents)}",
                "intents": intents
            }
            
            # Extract context for policy search
            state = context.get("state")
            farmer_type = context.get("farmer_type")
            
            # Search government schemes using Perplexity Sonar
            policy_result = govt_policy_agent.search_schemes(user_text, state, farmer_type)
            
            tools_used = [{
                "name": "search_schemes",
                "input": {"query": user_text, "state": state, "farmer_type": farmer_type},
                "output": policy_result,
                "ok": policy_result.get("success", False),
                "error": policy_result.get("error") if not policy_result.get("success", False) else None
            }]
            
            # Compose final response
            composed = compose_answer(tools_used, intent="govt_policy", locale=context.get("locale"))
            yield {
                "type": "final",
                "text": composed.get("text", ""),
                "intents": intents,
                "citations": composed.get("citations", [])
            }
            return

        # Fallback to original intent echo behavior: echo detected intents
        intents_text = ", ".join(intents)
        response_text = f"Detected intents: {intents_text}"
        yield {"type": "final", "text": response_text, "intents": intents}


def _chunk_text(s: str, n: int) -> List[str]:
    return [s[i : i + n] for i in range(0, len(s), n)] if s else []


_app_graph: AppGraph | None = None


def get_app_graph() -> AppGraph:
    global _app_graph
    if _app_graph is None:
        _app_graph = AppGraph()
    return _app_graph
