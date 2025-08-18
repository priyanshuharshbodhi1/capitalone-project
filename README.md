# Shetkari – Agricultural IoT Monitoring System

Every year, farmers face unpredictable crop losses due to poor visibility into real-time farm conditions.
From erratic weather and poor irrigation to delayed responses to soil imbalances, traditional farming lacks intelligent 24/7 monitoring systems that can provide timely alerts or guidance.

Introducing Shetkari, India's everything app for farmers. It's a smart agricultural IoT platform designed for precision farming and sustainable agriculture. It's a helpfull AI powered asistant with multiple agents. It's a plant docter for getting quick and actionable advice. and much more...

- Frontend: React + TypeScript
- Backend: FastAPI + Python + LangGraph 
- Memory Layer: mem0
- Translations: 
- Data: Supabase (Postgres + RLS, auth, edge functions)
- AI: OpenAI, groq(llama-8.1)
- Integrations: OpenWeatherMap, Bolt IoT, Webhooks/Zapier

## Overview

Shetkari monitors key farm parameters, analyzes trends, and provides actionable, localized recommendations. It supports both real devices (ESP32) and a mock-sensor page for demos/testing.

## Key Features

- Real-time sensor monitoring (10+ parameters)
- Historical analytics and charts
- AI-powered, localized recommendations based on recorded data
- Contextual conversation memory using mem0 for personalized farming advice
- AI-powered plant doctor for instant disease identification and treatment
- Robust fallback recommendations when AI is unavailable
- Advanced alerting via webhooks(SMS, Whatsapp, Emails)
- Device management and API key auth for sensors
- Mobile-first UI, touch-friendly interactions
- Multi-language support (English, Marathi, Hindi, etc. - 13 to be accurate currently)

### 🤖 **AI-Powered Recommendations**
- **Cloud AI via Edge Function**: Serverless function generates intelligent farming insights
- **Smart Analysis**: Automated recommendations based on sensor data patterns
- **Actionable Insights**: Specific guidance for irrigation, fertilization, and crop management
- **Fallback System**: Local AI recommendations when cloud services are unavailable

### 🎛️ **Device Management**
- **ESP32 Integration**: Native support for ESP32 microcontrollers
- **Device Status Monitoring**: Last seen timestamps and connectivity status
- **Bulk Configuration**: Manage multiple devices from a single dashboard

### 🔌 **IoT Appliance Control**
- **Bolt IoT Integration**: Control irrigation pumps, lights, fans, and heaters
- **Real-time Control**: Instant on/off switching with status feedback
- **Safety Features**: Device status validation and error handling
- **Remote Management**: Control farm equipment from anywhere

### 🚨 **Advanced Alert System**
- **Threshold-based Monitoring**: Customizable min/max thresholds for each parameter
- **Multi-channel Notifications**: Email and SMS alerts via Salesforce integration
- **Webhook Automation**: Automatic HTTP notifications to external systems
- **Alert History**: Complete audit trail of all triggered alerts

### 🧠 **Intelligent Memory System**
- **Contextual Conversations**: Remembers user's farm details, crop types, and farming preferences. Only stores valuable agricultural information, filters out generic conversations
- **Personalized Recommendations**: Uses conversation history to provide tailored farming advice. Remembers location, farm size, soil type, and previous queries
- **Session-based Memory**: Individual memory context for each user session
- **Limitations**: New session (refresh page): Memory resets (starts fresh) -- Can be fixed.

### 🤝 **Multi-Agent Assistant System(Assistant)**
- **Orchestrated Intelligence**: Multiple specialized AI agents work together seamlessly
- **Intent Classification**: Automatically routes queries to the most appropriate agent
- **Agent Collaboration**: Agents can share context and collaborate on complex farming scenarios
- **Unified Interface**: Single chat interface powered by multiple domain experts
- **LangGraph Framework**: Advanced agent orchestration with memory and state management

#### **🎯 Agent Specializations:**

**🌤️ Weather Agent:**
- Real-time weather conditions and soil parameters
- Weather forecasts for crop planning and harvest timing  
- Historical weather analysis for seasonal planning
- Weather alerts and warnings for crop protection
- Integration with OpenWeatherMap API for accurate data

**🏛️ Government Schemes Agent:**
- Agricultural subsidies and government schemes search
- Policy information and eligibility criteria
- Application guidance for farming benefits
- State-specific scheme recommendations
- Integration with government databases and APIs

**🌾 Agronomist Agent:**
- General farming advice and best practices
- Crop selection and rotation recommendations
- Soil management and fertilization guidance
- Pest and disease prevention strategies
- Irrigation and water management advice

**📈 Market Agent(Not Implemented):**
- Current crop prices and market trends
- Price forecasting and market analysis
- Best selling locations and market intelligence
- Commodity trading insights
- Integration with agricultural market data sources

**Finance Agent(Not Implemented)**
- Based on user data, memories and conversation histor provide best finantial advice like Loan, insurance etc

**🔄 Agent Orchestration Flow:**
1. **Query Reception**: User message received by the orchestrator
2. **Memory Retrieval**: Previous context and farm details loaded from mem0
3. **Intent Classification**: AI determines which agent(s) should handle the query
4. **Agent Selection**: Appropriate specialist agent(s) activated
5. **Tool Execution**: Agents use external APIs and data sources
6. **Response Composition**: Results combined into coherent, actionable advice
7. **Memory Storage**: Important agricultural information saved for future context

**🏗️ Technical Architecture:**
- **LangGraph Framework**: State machine for complex agent workflows
- **Groq LLM**: Fast intent classification and tool selection
- **OpenAI Integration**: Memory operations and response composition
- **FastAPI Backend**: RESTful API with streaming responses
- **Modular Design**: Each agent is independently deployable and testable

### 🌱 **Plant Disease Diagnosis (PlantDoc)**
- **Image-based Diagnosis**: Upload plant photos for instant disease identification
- **AI-Powered Analysis**: Advanced computer vision models for accurate plant health assessment
- **Treatment Recommendations**: Specific treatment plans and preventive measures
- **Multi-crop Support**: Supports diagnosis for various crop types and plant species
- **Localized Solutions**: Treatment suggestions adapted to Indian agricultural practices
- **Assistant Integration**: Diagnosed diseases can be discussed with agricultural agents for comprehensive treatment plans

## Architecture

- Frontend app: `src/` (Vite)
- FastAPI: `server`
- Edge Functions: `supabase/functions/ai-recommendations/`
- DB & migrations: `supabase/`, `supabase/migrations/`
- Infrastructure helpers: `server/infra/`

## Monitored Parameters(IoT)

- Atmospheric temperature (°C)
- Atmospheric humidity (%)
- Light intensity (lux)
- Soil temperature (°C)
- Soil moisture (%)
- Electrical Conductivity (dS/m)
- Soil pH
- Nitrogen (ppm)
- Phosphorus (ppm)
- Potassium (ppm)


## Local Setup

Prerequisites:
- Node.js 18+
- Python 3.11+
- Supabase CLI (for Edge Functions) optional but recommended
- OpenAI-compatible API key if testing AI
- Git, make, curl recommended

Setup:(Linux Environment prefered and tested)

1. Clone and install frontend
```bash
npm install
```

2. Configure env
```bash
cp .env.example .env
# fill values for VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, etc.
```
For quick evaluation for judges, I have have provided .env file in the repo itself.

3. Start frontend
```bash
npm run dev
```

Backend (FastAPI):

1. Create venv and install
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r server/requirements.txt
```

2. Run API
```bash
uvicorn server.api.main:app --reload --port 8000
```

Supabase Edge Function (AI Recommendations):

- Directory: `supabase/functions/ai-recommendations/`
- Local serve (CLI):
```bash
supabase functions serve ai-recommendations
```
- Ensure environment variables for the function are supplied (AI_API_KEY, AI_CHAT_URL, AI_MODEL).
- Deploy to Supabase:
```bash
supabase functions deploy ai-recommendations
```

Database:

- Run migrations with Supabase CLI:
```bash
supabase db push
```
- Ensure RLS policies are applied; see `supabase/migrations/` and `database-migrations/`.

OS-specific notes:

- macOS:
  - Use Homebrew for node/python
  - Gatekeeper may block binaries; allow in System Settings
- Linux:
  - Use system package manager for python3.11 and node
  - Ensure libssl and build-essential are installed
- Windows:
  - Use WSL2 (recommended) or native Python and Node
  - Activate venv with `.venv\Scripts\activate`

## **Key Screens**

### 1. **Dashboard**: Real-time sensor data, weather, and AI recommendations
- Live sensor readings with visual indicators
- Weather integration and forecasts
- AI-generated farming recommendations
- Device status and connectivity monitoring

### 2. **Assistant**: Multi-agent AI system for comprehensive agricultural support
- **Sub-Agents**: Agronomist, Weather, Market, and Government Policy agents
- **Memory-Enabled**: Remembers your farm context and previous conversations
- **Contextual Responses**: Provides personalized advice based on your farming history
- **Natural Language**: Ask questions in plain language about farming, weather, schemes, etc.
- **Real-time API Integration**: Live data from weather services, government databases, and market sources
- **Streaming Responses**: Real-time token streaming for responsive user experience
- **Tool-calling LLMs**: Advanced function calling for precise data retrieval and analysis

### 3. **PlantDoc**: AI-powered plant disease diagnosis
- Upload plant photos for instant disease identification
- Detailed treatment recommendations and preventive measures
- Crop-specific diagnosis for major Indian agricultural crops
- Integrated with assistant for follow-up farming advice

### 4. **Analytics**: Historical data visualization with statistical analysis
- Trend analysis and pattern recognition
- Comparative charts and growth metrics
- Export capabilities for record keeping

### 5. **Settings**: Device management, thresholds, language selection and user preferences
- Device configuration and API key management
- Customizable alert thresholds
- Multi-language interface settings
- User profile and farming preferences

## 🔧 ESP32 Integration

### **Hardware Setup**
Connect your sensors to the ESP32 according to your specific sensor requirements. The system supports:
- DHT22 for temperature and humidity
- LDR or photodiode for light intensity
- Soil NPK sensor

### **Data Ingestion Endpoint**
**Endpoint**: `POST /functions/v1/esp32-data-ingestion`

**Headers**:
```
Content-Type: application/json
Authorization: Bearer YOUR_SUPABASE_ANON_KEY
```

**Payload Example**:
```json
{
  "device_id": "ESP32_001",
  "api_key": "device-specific-api-key",
  "atmo_temp": 25.5,
  "humidity": 65.2,
  "light": 450,
  "soil_temp": 22.1,
  "moisture": 45.8,
  "ec": 1.2,
  "ph": 6.8,
  "nitrogen": 35.0,
  "phosphorus": 18.5,
  "potassium": 28.3
}
```

### **Arduino Code Example**


## Testing the Application

### Mock Sensor Page (http://localhost:5173/mock-sensor) 

Purpose: Simulate IoT sensor payloads for demos and testing without hardware.

Usage:
- Open the app at `http://localhost:5173/mock-sensor`.
- Create a device
- Click "Generate Random" button and then "Send Button" OR Toggle  Auto-Send Mode to send random data every 15 seconds OR Enter parameters (temperature, humidity, soil metrics, etc.) in fields directly.
- Submit to publish synthetic readings to the app state/flows.
- Use Dashboard and Analytics to verify ingestion, banners, and AI recommendations.

### Testing Memory Features in Assistant

The memory system is **session-based** and **user-specific**. Here's how to test it:

#### **Prerequisites for Memory Testing:**
```bash
# 1. Install mem0 dependency
pip install mem0ai

# 2. Set OpenAI API key (required for mem0)
export OPENAI_API_KEY="your_openai_api_key"

# 3. Test memory integration
python test_memory.py
```

#### **Manual Testing Steps:**

1. **Navigate to Assistant Page** (`http://localhost:5173/assistant`)

2. **Start a Conversation with Farm Context:**
   ```
   User: "I have a 5-acre wheat farm in Punjab"
   Bot: [Responds with farming advice]
   ```

3. **Ask Related Questions to Test Memory:**
   ```
   User: "What's the current weather for my farm?"
   Bot: [Should remember your location and farm details]
   
   User: "Should I irrigate my wheat today?"
   Bot: [Should provide context-aware advice for wheat in Punjab]
   ```

4. **Test Memory Persistence:**
   - Refresh the page (new session)
   - Previous session's memory won't carry over (session-based)
   - Start new conversation to build new memory context

#### **What Gets Remembered:**
✅ **Stored in Memory:**
- Farm location and coordinates
- Crop types and farm size
- Soil conditions and farming preferences
- Successful weather/farming queries
- Government scheme inquiries
- Agricultural advice exchanges

❌ **Not Stored:**
- Generic greetings ("hello", "thanks")
- Error responses or failed queries
- Non-agricultural conversations
- Short, low-value messages

#### **Memory Features to Test:**
- **Contextual Responses**: Ask follow-up questions without repeating context
- **Personalized Advice**: Notice how responses become more tailored to your farm
- **Cross-Intent Memory**: Weather advice considering your crop type
- **Farming Context**: Location-based recommendations

### Testing Multi-Agent System

#### **Agent Collaboration Examples:**

**🌾 Weather + Agronomist Collaboration:**
```
User: "Should I plant tomatoes next week?"
→ Weather Agent: Checks forecast conditions
→ Agronomist Agent: Considers soil temperature and planting season
→ Combined Response: Weather-aware planting recommendation
```

**🏛️ Schemes + Market Integration:**
```
User: "I want to start organic farming"
→ Govt Schemes Agent: Finds organic farming subsidies
→ Market Agent: Provides organic crop price premiums
→ Combined Response: Financial viability analysis with subsidy options
```

**🌡️ Weather + Memory Context:**
```
Session Context: "5-acre wheat farm in Punjab"
User: "Will it rain tomorrow?"
→ Memory: Retrieves Punjab location + wheat crop context
→ Weather Agent: Punjab-specific forecast
→ Response: "For your wheat farm in Punjab, expect..."
```

#### **Testing Different Agent Types:**

**🌤️ Weather Agent Examples:**
- "What's the current weather for my farm?"
- "Should I irrigate my wheat today?"
- "7-day weather forecast for crop planning"
- "Historical rainfall patterns for this season"
- "Are there any weather alerts for my area?"

**🏛️ Government Schemes Examples:**
- "Subsidies available for drip irrigation"
- "PM-KISAN scheme eligibility and benefits"
- "Organic farming certification support"
- "Crop insurance schemes in Maharashtra"
- "Solar pump subsidy application process"

**📈 Market Agent Examples:**
- "Current wheat prices in Punjab markets"
- "Best time to sell my tomato crop"
- "Price trends for organic vegetables"
- "Market demand for millets this season"
- "Transportation costs to nearest mandi"

**🌾 Agronomist Agent Examples:**
- "How to improve soil fertility naturally?"
- "Pest control for cotton bollworm"
- "Crop rotation for sustainable farming"
- "Water management during drought"
- "Organic fertilizer recommendations"

**🔄 Cross-Agent Collaborative Queries:**
- "Weather-based fertilizer application timing"
- "Market trends for monsoon-dependent crops"
- "Government schemes for climate-resilient farming"
- "Drought management with available subsidies"
- "Organic farming: weather, market, and policy guide"

#### **Advanced Assistant Features:**

**🎯 Smart Intent Detection:**
```
Query: "My tomato plants are wilting, it's been dry"
→ Detects: Weather + Agronomist intent
→ Weather Agent: Checks rainfall and humidity
→ Agronomist: Analyzes wilting causes and solutions
→ Response: Weather-informed irrigation recommendations
```

**💾 Context Persistence:**
```
Session History:
1. "I have 2 acres of rice in Bihar"
2. "What's the weather forecast?"
→ Agent remembers: crop=rice, location=Bihar, area=2-acres
→ Provides: Bihar-specific weather for rice farming
```

**🔧 Tool Integration:**
- **Weather APIs**: OpenWeatherMap for real-time conditions
- **Government APIs**: Direct integration with scheme databases  
- **Market APIs**: Live pricing from agricultural commodity exchanges
- **Knowledge Bases**: Comprehensive agricultural best practices database

#### **Agent Implementation Architecture:**

**📁 Code Structure:**
```
server/agent/
├── orchestrator_agent.py       # Main agent coordinator
├── delegating_agent.py         # Intent classification
├── composer_agent.py           # Response composition
├── agents/
│   ├── weather_agent.py        # Weather specialist
│   ├── govt_scheme_agent.py    # Government schemes
│   ├── market_agent.py         # Market information
│   └── plant_doc_agent.py      # Plant diagnosis
├── memory/
│   ├── memory_agent.py         # mem0 integration
│   └── checkpointer.py         # Session management
└── prompts/
    ├── intent_classification.py
    └── response_composition.py
```

**⚡ Performance Features:**
- **Streaming Responses**: Real-time token delivery for better UX
- **Parallel Tool Execution**: Multiple API calls processed simultaneously
- **Smart Caching**: Memory layer reduces redundant API calls
- **Fallback Systems**: Graceful degradation when external services fail
- **Error Recovery**: Automatic retry logic with exponential backoff

**🔄 Request/Response Flow:**
```
POST /agent/complete
{
  "messages": [...],
  "context": {
    "session_id": "unique_id",
    "lat": 28.6139,
    "lon": 77.2090,
    "locale": "en-IN"
  }
}

Response:
{
  "text": "Based on your wheat farm in Punjab...",
  "intent": "weather",
  "citations": []
}
```


## Mobile UX Guidelines

- Responsive layout and touch-friendly controls
- Clear cards with primary actions visible
- Accessible colors/contrast; large tap targets


## Contributing

- Conventional commits, TypeScript best practices
- Keep components modular and under ~300 lines where feasible
- Avoid introducing new patterns before iterating on existing ones
- Update docs and tests for changes

## License

MIT
