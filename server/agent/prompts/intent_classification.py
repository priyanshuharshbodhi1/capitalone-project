"""
Intent Classification Prompts for Agricultural AI Assistant

This module contains all prompts related to intent detection and classification
for farming-related queries.
"""

GEMINI_INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for a farming assistant.
Allowed intents: {intents}.
Given the user text, output ONLY a compact JSON object with exactly one key 'intents' whose value is an array of relevant intents.
Multiple intents are allowed if the query spans multiple domains.
No extra text.
Examples:
USER: Will it rain tomorrow?
OUTPUT: {{"intents": ["weather"]}}
USER: Tomato prices near Nashik
OUTPUT: {{"intents": ["market"]}}
USER: What seed variety suits this unpredictable weather?
OUTPUT: {{"intents": ["weather", "agronomist"]}}
USER: Government subsidies for drip irrigation?
OUTPUT: {{"intents": ["govt_policy", "IoT_info"]}}
USER: {user_text}
OUTPUT:"""

# Intent categories and keywords for heuristic fallback
INTENT_KEYWORDS = {
    "weather": ["weather", "rain", "temperature", "forecast", "wind", "humid", "humidity", "sun", "monsoon"],
    "market": ["price", "market", "mandi", "sell", "rate", "wholesale", "buyer", "auction"],
    "govt_policy": ["policy", "government", "scheme", "subsidy", "loan", "credit", "regulation", "law"],
    "agronomist": ["crop", "suitable", "variety", "sowing", "planting", "yield", "irrigation", "fertilizer", "pest", "disease", "seed", "soil", "nutrition", "expert", "advice"],
    "IoT_info": ["sensor", "iot", "device", "monitor", "data", "smart", "automation", "technology", "equipment"]
}

SUPPORTED_INTENTS = ["market", "weather", "govt_policy", "agronomist", "IoT_info"]
