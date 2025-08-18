from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
import json

try:
    from mem0 import Memory
    _MEM0_AVAILABLE = True
except ImportError:
    _MEM0_AVAILABLE = False
    logging.warning("mem0ai not available. Install with: pip install mem0ai")

from ...infra.settings import settings


class MemoryService:
    """Simple wrapper around mem0 for agricultural chatbot memory"""
    
    def __init__(self):
        self.memory: Optional[Memory] = None
        self._initialize_memory()
    
    def _initialize_memory(self):
        """Initialize mem0 with OpenAI backend if available"""
        if not _MEM0_AVAILABLE:
            logging.warning("mem0ai not available - memory features disabled")
            return
            
        if not settings.openai_api_key:
            logging.warning("OpenAI API key not found - memory features disabled")
            return
            
        try:
            # Configure mem0 with OpenAI
            config = {
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": "gpt-4o-mini",  # Cost-effective model for memory operations
                        "temperature": 0.1,
                        "api_key": settings.openai_api_key
                    }
                },
                "embedder": {
                    "provider": "openai", 
                    "config": {
                        "model": "text-embedding-3-small",  # Cost-effective embedding model
                        "api_key": settings.openai_api_key
                    }
                }
            }
            
            self.memory = Memory.from_config(config)
            logging.info("✅ Memory service initialized successfully with mem0")
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize memory service: {e}")
            self.memory = None
    
    def is_available(self) -> bool:
        """Check if memory service is available"""
        return self.memory is not None
    
    def add_memory(self, user_id: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a memory for the user
        
        Args:
            user_id: Unique identifier for the user (session_id)
            message: The message/information to store
            metadata: Additional context information
            
        Returns:
            bool: True if memory was added successfully
        """
        if not self.is_available():
            return False
            
        try:
            # Add memory with metadata
            memory_data = {
                "messages": [{"role": "user", "content": message}],
                "user_id": user_id
            }
            
            if metadata:
                memory_data["metadata"] = metadata
                
            result = self.memory.add(**memory_data)
            logging.info(f"✅ Added memory for user {user_id}: {message[:100]}...")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to add memory for user {user_id}: {e}")
            return False
    
    def get_relevant_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for a user query
        
        Args:
            user_id: Unique identifier for the user
            query: The current user query
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of relevant memory objects in standardized format
        """
        if not self.is_available():
            return []
            
        try:
            # Search for relevant memories
            memories = self.memory.search(
                query=query,
                user_id=user_id,
                limit=limit
            )
            
            # Debug: Print the raw memory format
            logging.info(f"🔍 Raw memories type: {type(memories)}, length: {len(memories) if hasattr(memories, '__len__') else 'N/A'}")
            if memories:
                logging.info(f"🔍 First memory type: {type(memories[0])}, content: {str(memories[0])[:100]}...")
            
            # Normalize memory format - mem0 can return different formats
            normalized_memories = []
            for i, memory in enumerate(memories):
                try:
                    if isinstance(memory, dict):
                        # If it's already a dict, standardize the format
                        normalized_memory = {
                            "memory": memory.get("memory", memory.get("text", memory.get("content", str(memory)))),
                            "metadata": memory.get("metadata", {}),
                            "score": memory.get("score", memory.get("relevance_score", 0.0))
                        }
                    elif isinstance(memory, str):
                        # If it's a string, wrap it in our format
                        normalized_memory = {
                            "memory": memory,
                            "metadata": {"type": "text_memory"},
                            "score": 1.0
                        }
                    else:
                        # Handle other formats by converting to string
                        logging.warning(f"🔍 Unknown memory format at index {i}: {type(memory)}")
                        normalized_memory = {
                            "memory": str(memory),
                            "metadata": {"type": "unknown_format"},
                            "score": 0.5
                        }
                    normalized_memories.append(normalized_memory)
                except Exception as mem_error:
                    logging.error(f"❌ Error processing memory {i}: {mem_error}")
                    continue
            
            logging.info(f"✅ Retrieved and normalized {len(normalized_memories)} relevant memories for user {user_id}")
            return normalized_memories
            
        except Exception as e:
            # Check if this is a specific error code from mem0
            if "0" in str(e):
                logging.warning(f"⚠️ Memory retrieval returned empty result for user {user_id} - likely no memories yet")
            else:
                logging.error(f"❌ Failed to retrieve memories for user {user_id}: {e}")
            return []
    
    def add_farming_context(self, user_id: str, context: Dict[str, Any]) -> bool:
        """
        Add farming-specific context to memory
        
        Args:
            user_id: User identifier
            context: Farming context (location, crops, farm size, etc.)
        """
        if not context:
            return False
            
        # Create a natural language description of the farming context
        context_parts = []
        
        if context.get("lat") and context.get("lon"):
            context_parts.append(f"Farmer is located at coordinates {context['lat']}, {context['lon']}")
            
        if context.get("state"):
            context_parts.append(f"Farmer is in {context['state']} state")
            
        if context.get("farmer_type"):
            context_parts.append(f"Farmer type: {context['farmer_type']}")
            
        if context.get("locale"):
            context_parts.append(f"Preferred language: {context['locale']}")
            
        if context_parts:
            context_message = ". ".join(context_parts) + "."
            return self.add_memory(user_id, context_message, {"type": "farming_context", **context})
            
        return False
    
    def should_store_conversation(self, user_message: str, intent: str, bot_response: str) -> bool:
        """
        Determine if a conversation should be stored in memory
        
        Args:
            user_message: User's message
            intent: Detected intent
            bot_response: Bot's response
            
        Returns:
            bool: True if conversation should be stored
        """
        # Don't store generic/low-value interactions
        low_value_patterns = [
            "hello", "hi", "thanks", "thank you", "bye", "goodbye",
            "what can you do", "help", "how are you"
        ]
        
        user_lower = user_message.lower().strip()
        
        # Skip generic greetings and thanks
        if any(pattern in user_lower for pattern in low_value_patterns):
            return False
            
        # Skip very short messages (likely not informative)
        if len(user_message.strip()) < 10:
            return False
            
        # Skip if bot couldn't provide useful response
        if "sorry" in bot_response.lower() or "error" in bot_response.lower():
            return False
            
        # Always store specific agricultural intents
        valuable_intents = ["weather", "govt_scheme", "market", "plant_doc"]
        if intent in valuable_intents:
            return True
            
        # Store if message contains agricultural information
        agricultural_keywords = [
            "crop", "farm", "soil", "irrigation", "fertilizer", "seed", "harvest",
            "pesticide", "weather", "rain", "drought", "yield", "acre", "hectare"
        ]
        
        if any(keyword in user_lower for keyword in agricultural_keywords):
            return True
            
        return False

    def add_conversation_memory(self, user_id: str, user_message: str, bot_response: str, intent: str) -> bool:
        """
        Add conversation exchange to memory (only if relevant)
        
        Args:
            user_id: User identifier
            user_message: What the user asked
            bot_response: How the bot responded
            intent: The detected intent
        """
        # Check if this conversation should be stored
        if not self.should_store_conversation(user_message, intent, bot_response):
            logging.info(f"Skipping memory storage for low-value conversation: {user_message[:50]}...")
            return False
            
        # Extract key information from the conversation
        memory_parts = []
        
        # Add user's question in a clean format
        memory_parts.append(f"User inquiry: {user_message}")
        
        # Add relevant facts from bot response (first 300 chars of meaningful content)
        response_preview = bot_response[:300].strip()
        if response_preview:
            memory_parts.append(f"Key information provided: {response_preview}")
            
        memory_text = ". ".join(memory_parts)
        
        metadata = {
            "type": "valuable_conversation",
            "intent": intent,
            "user_query": user_message,
            "timestamp": self._get_timestamp()
        }
        
        return self.add_memory(user_id, memory_text, metadata)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for metadata"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def extract_user_preferences(self, user_message: str) -> Dict[str, Any]:
        """
        Extract user preferences/facts from their message that should be remembered
        
        Args:
            user_message: The user's message
            
        Returns:
            Dictionary of extracted information
        """
        preferences = {}
        
        # Simple keyword-based extraction - can be enhanced with NLP
        message_lower = user_message.lower()
        
        # Extract crop types
        crops = ["wheat", "rice", "tomato", "potato", "onion", "cotton", "sugarcane", "maize", "barley"]
        mentioned_crops = [crop for crop in crops if crop in message_lower]
        if mentioned_crops:
            preferences["crops"] = mentioned_crops
            
        # Extract farm size indicators
        if any(word in message_lower for word in ["acre", "hectare", "bigha"]):
            # Extract size mentions
            words = message_lower.split()
            for i, word in enumerate(words):
                if word in ["acre", "acres", "hectare", "hectares", "bigha"]:
                    if i > 0 and words[i-1].isdigit():
                        preferences["farm_size"] = f"{words[i-1]} {word}"
                        break
        
        # Extract soil type
        soil_types = ["clay", "sandy", "loamy", "black", "red", "alluvial"]
        mentioned_soil = [soil for soil in soil_types if soil in message_lower]
        if mentioned_soil:
            preferences["soil_type"] = mentioned_soil[0]
        
        return preferences


# Global memory service instance
_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """Get the global memory service instance"""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
