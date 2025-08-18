from __future__ import annotations
from typing import Any, Dict, List
import json
import os

from ..infra.settings import settings
from .prompts.response_composition import (
    SHETKARI_COMPOSER_SYSTEM_PROMPT,
    GEMINI_COMPOSER_PROMPT_TEMPLATE,
    ENHANCED_COMPOSER_SYSTEM_PROMPT,
    ENHANCED_COMPOSER_PROMPT_TEMPLATE,
    FALLBACK_RESPONSES
)

# Groq LLM (using same as delegation agent)
try:
    from groq import Groq
    _GROQ_AVAILABLE = True
except Exception:  # pragma: no cover
    _GROQ_AVAILABLE = False


def _groq_client():
    if not settings.groq_api_key or not _GROQ_AVAILABLE:
        return None
    try:
        return Groq(api_key=settings.groq_api_key)
    except Exception as e:
        print(f"Failed to create Groq client: {e}")
        return None


def _handle_govt_scheme_response(agent_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Handle government scheme responses by returning raw data without additional formatting"""
    citations: List[Dict[str, Any]] = []
    
    # Find the government scheme response
    scheme_response = None
    for resp in agent_responses:
        if resp.get("name") == "search_schemes" and resp.get("ok", False):
            scheme_response = resp.get("output", {})
            break
    
    if not scheme_response:
        return {
            "text": "No government scheme information available at the moment.",
            "citations": citations
        }
    
    # Extract the raw schemes information
    data = scheme_response.get("data", {})
    schemes_info = data.get("schemes_info", "")
    structured = data.get("schemes_structured", [])
    
    # Return structured JSON if available, otherwise return the raw text
    if structured:
        import json as _json
        text = "Here are the most relevant government schemes (max 5):\n\n```json\n"
        text += _json.dumps(structured[:5], ensure_ascii=False, indent=2)
        text += "\n```"
    elif schemes_info:
        text = schemes_info
    else:
        text = "Government scheme information is not available in the expected format."
    
    return {"text": text, "citations": citations}


def compose_enhanced_answer(
    original_query: str,
    chat_history: List[Dict[str, Any]],
    agent_responses: List[Dict[str, Any]],
    intent: str,
    context: Dict[str, Any],
    memory_context: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Enhanced composer that considers original query, chat history, and all agent responses.
    Uses Groq LLM (llama-3.1-8b-instant) for comprehensive context-aware responses.
    """
    citations: List[Dict[str, Any]] = []
    
    # Get Groq client
    client = _groq_client()
    if not client:
        # Fallback to basic composition if no LLM available
        return _fallback_enhanced_response(original_query, agent_responses, intent, context, memory_context)
    
    try:
        # Format chat history
        chat_history_text = ""
        if chat_history:
            for msg in chat_history[-5:]:  # Last 5 messages for context
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role and content:
                    chat_history_text += f"{role.capitalize()}: {content}\n"
        else:
            chat_history_text = "No previous conversation"
        
        # Format agent responses
        agent_responses_text = ""
        if agent_responses:
            for resp in agent_responses:
                name = resp.get("name", "unknown")
                output = resp.get("output", {})
                success = resp.get("ok", False)
                
                if success and output:
                    agent_responses_text += f"\n**{name.upper()} RESPONSE:**\n"
                    agent_responses_text += json.dumps(output, indent=2) + "\n"
                else:
                    error = resp.get("error", "Unknown error")
                    agent_responses_text += f"\n**{name.upper()} ERROR:** {error}\n"
        else:
            agent_responses_text = "No agent responses available"
        
        # Format memory context
        memory_context_text = ""
        if memory_context:
            relevant_memories = [mem.get("memory", "") for mem in memory_context[:3]]
            if relevant_memories:
                memory_context_text = "\n".join(f"- {mem}" for mem in relevant_memories)
        if not memory_context_text:
            memory_context_text = "No relevant previous conversations"
        
        # Format location info
        location_info = "Location not specified"
        if context.get("lat") and context.get("lon"):
            location_info = f"Latitude: {context.get('lat')}, Longitude: {context.get('lon')}"
            if context.get("state"):
                location_info += f", State: {context.get('state')}"
        
        # Special handling for government schemes - return raw response
        if intent == "govt_scheme":
            return _handle_govt_scheme_response(agent_responses)
        
        # Create the simplified prompt for other intents
        prompt = ENHANCED_COMPOSER_PROMPT_TEMPLATE.format(
            original_query=original_query,
            intent=intent,
            agent_responses=agent_responses_text
        )
        
        # Make Groq API call
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Same as delegation agent
            messages=[
                {"role": "system", "content": ENHANCED_COMPOSER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Lower temperature for more concise responses
            max_tokens=500,   # Reduced tokens to encourage concise responses
            timeout=30
        )
        
        text = response.choices[0].message.content.strip()
        
        if not text or len(text) < 20:
            return _fallback_enhanced_response(original_query, agent_responses, intent, context, memory_context)
        
        return {"text": text, "citations": citations}
        
    except Exception as e:
        print(f"Enhanced composer error: {e}")
        return _fallback_enhanced_response(original_query, agent_responses, intent, context, memory_context)


def compose_answer(tools_used: List[Dict[str, Any]], intent: str, locale: str | None = None, memory_context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Compose final answer with memory context. Falls back to deterministic template if no LLM key.

    Returns dict with {text, citations}
    """
    # Remove citations processing as requested by user
    citations: List[Dict[str, Any]] = []

    # If Groq is available, use it to craft natural text constrained to tools
    client = _groq_client()
    if client:
        tool_summaries = json.dumps({t["name"]: t.get("output", {}) for t in tools_used})
        
        # Add memory context to the prompt if available
        memory_context_text = ""
        if memory_context:
            relevant_memories = [mem.get("memory", "") for mem in memory_context[:3]]  # Top 3 memories
            if relevant_memories:
                memory_context_text = f"\n\nRelevant context from previous conversations:\n{chr(10).join(f'- {mem}' for mem in relevant_memories)}"
        
        prompt = GEMINI_COMPOSER_PROMPT_TEMPLATE.format(
            system_prompt=SHETKARI_COMPOSER_SYSTEM_PROMPT,
            intent=intent,
            locale=locale or 'en-IN',
            tool_summaries=tool_summaries
        ) + memory_context_text
        
        try:
            # Use Groq chat completion instead of Gemini
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Same as delegation agent
                messages=[
                    {"role": "system", "content": SHETKARI_COMPOSER_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
                timeout=30
            )
            text = resp.choices[0].message.content.strip() or ""
        except Exception as e:  # fallback
            text = _fallback_text(tools_used, intent, memory_context)
    else:
        text = _fallback_text(tools_used, intent, memory_context)

    return {"text": text, "citations": citations}


def _fallback_enhanced_response(
    original_query: str,
    agent_responses: List[Dict[str, Any]],
    intent: str,
    context: Dict[str, Any],
    memory_context: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Fallback response when LLM is not available for enhanced composer"""
    citations: List[Dict[str, Any]] = []
    
    # Try to provide a helpful response based on available agent responses
    if not agent_responses:
        return {
            "text": "I apologize, but I couldn't process your request at the moment. Please try rephrasing your question or contact support if the issue persists.",
            "citations": citations
        }
    
    # Check if any agent provided useful information
    useful_responses = [resp for resp in agent_responses if resp.get("ok", False)]
    
    if not useful_responses:
        # All agents failed
        return {
            "text": "I encountered some issues while gathering information for your query. Please check your location settings and try again with a more specific question.",
            "citations": citations
        }
    
    # Try to provide a basic response based on intent and successful agent responses
    if intent == "weather":
        return {
            "text": "Weather information retrieved. Check conditions for your farming activities.",
            "citations": citations
        }
    elif intent == "govt_scheme":
        # For govt schemes, try to extract raw data
        return _handle_govt_scheme_response(agent_responses)
    elif intent == "agronomist":
        return {
            "text": "Agricultural advice available. Consider local conditions for best results.",
            "citations": citations
        }
    elif intent == "market":
        return {
            "text": "Market information found. Verify current prices with local markets.",
            "citations": citations
        }
    else:
        return {
            "text": "Information processed. Please ask specific questions for detailed guidance.",
            "citations": citations
        }


def _fallback_text(tools_used: List[Dict[str, Any]], intent: str, memory_context: List[Dict[str, Any]] = None) -> str:
    # User-friendly deterministic text without exposing internal details
    if intent == "general":
        return "I can help with weather, market prices, government schemes, and farming advice. Please ask specific questions."

    if intent == "weather":
        # Handle new weather tool format with 4 specialized tools
        weather_tool = next((t for t in tools_used if t.get("name", "").startswith("get_")), {})
        tool_name = weather_tool.get("name", "")
        weather_output = weather_tool.get("output", {})
        
        if not weather_output.get("success", False):
            return f"Weather data unavailable: {weather_output.get('error', 'Unknown error')}"
        
        lines: List[str] = []
        data = weather_output.get("data", {})
        
        # Handle current weather tool
        if tool_name == "get_current_weather":
            temp = data.get("temperature_celsius")
            precip = data.get("precipitation_mm", 0)
            
            if temp is not None:
                lines.append(f"Current: {temp:.1f}°C")
            if precip > 0:
                lines.append(f"Rain: {precip:.1f}mm")
        
        # Handle future weather tool  
        elif tool_name == "get_future_weather":
            forecast = data.get("daily_forecast", [])
            if forecast and len(forecast) > 0:
                day = forecast[0]  # Tomorrow's forecast
                tmax = day.get("max_temp_celsius")
                tmin = day.get("min_temp_celsius")
                rain = day.get("precipitation_mm", 0)
                
                if tmax is not None and tmin is not None:
                    lines.append(f"Tomorrow: {tmin:.0f}-{tmax:.0f}°C")
                if rain > 0:
                    lines.append(f"Rain expected: {rain:.1f}mm")
        
        # Handle historical weather tool
        elif tool_name == "get_historical_weather":
            summary = data.get("summary", {})
            if summary:
                temp_summary = summary.get("temperature", {})
                if temp_summary:
                    avg_temp = temp_summary.get("avg_max_celsius")
                    if avg_temp is not None:
                        lines.append(f"Historical average: {avg_temp:.1f}°C")
        
        # Handle weather alerts tool
        elif tool_name == "get_weather_alerts":
            alert_count = data.get("alert_count", 0)
            
            if alert_count == 0:
                lines.append("No weather alerts.")
            else:
                alerts = data.get("alerts", [])
                if alerts:
                    event = alerts[0].get("event", "Weather Alert")
                    lines.append(f"⚠️ Alert: {event}")
        
        # Default fallback
        if not lines:
            lines.append("Weather data available.")
        
        return "\n".join(lines)

    if intent == "govt_scheme":
        # Handle government policy agent responses - return raw data
        policy_tool = next((t for t in tools_used if t.get("name") == "search_schemes"), {})
        policy_output = policy_tool.get("output", {})
        
        if not policy_output.get("success", False):
            return "Government scheme information unavailable."
        
        data = policy_output.get("data", {})
        schemes_info = data.get("schemes_info", "")
        structured = data.get("schemes_structured", [])
        
        # Return raw schemes data without additional formatting
        if structured:
            import json as _json
            return "Here are the most relevant government schemes (max 5):\n\n```json\n" + _json.dumps(structured[:5], ensure_ascii=False, indent=2) + "\n```"
        elif schemes_info:
            return schemes_info
        else:
            return "No government schemes found."

    if intent == "market":
        market = next((t.get("output", {}) for t in tools_used if t.get("name") == "market"), {})
        price = market.get("price") or market.get("modal_price") or market.get("average")
        loc = market.get("market") or market.get("district") or market.get("state")
        
        if price is not None:
            if loc:
                return f"Price near {loc}: {price}"
            else:
                return f"Latest price: {price}"
        else:
            return "Market information available."

    # Safe default
    return "Information available. Please ask specific questions for detailed guidance."
