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

**🏛️ Government Schemes Agent:**
- Agricultural subsidies and government schemes search
- Policy information and eligibility criteria
- Integration with government databases and APIs

**🌾 Agronomist Agent:**
- General farming advice and best practices
- Pest and disease prevention strategies
- Irrigation and water management advice

**📈 Market Agent(Not Implemented):**
- Current crop prices and market trends
- Best selling locations and market intelligence
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
![IoT Artecture Diagram](assets/IoT_Arc.png)
![Assistant/Chatbot Agentic Artecture](assets/Agentic_Arc.png)

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
### 2. **Assistant**: Multi-agent AI system for comprehensive agricultural support
### 3. **PlantDoc**: AI-powered plant disease diagnosis
### 4. **Analytics**: Historical data visualization with statistical analysis
### 5. **Settings**: Device management, thresholds, language selection and user preferences

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
<!-- ![IoT Setup](assets/IoT_Setup.png)
![Ardino IDE](assets/ardino_ide.png) -->

<p float="left">
  <img src="assets/IoT_Setup.png" width="200" /> 
  <img src="assets/ardino_ide.png" width="200" />
</p>

## Testing the Application

### Mock Sensor Page (http://localhost:5173/mock-sensor) 

Purpose: Simulate IoT sensor payloads for demos and testing without hardware.

Usage:
- Open the app at `http://localhost:5173/mock-sensor`.
- Create a device
- Click "Generate Random" button and then "Send Button" OR Toggle  Auto-Send Mode to send random data every 15 seconds OR Enter parameters (temperature, humidity, soil metrics, etc.) in fields directly.
- Submit to publish synthetic readings to the app state/flows.
- Use Dashboard and Analytics to verify ingestion, banners, and AI recommendations.


### Testing Multi-Agent System

#### **Agent Collaboration Examples:**

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
- "Subsidies available for drip irrigation"
- "Current wheat prices in Punjab markets"
- "Pest control for cotton bollworm"


#### **Advanced Assistant Features:**

**🎯 Smart Intent Detection:**
```
Query: "My tomato plants are wilting, it's been dry"
→ Detects: Weather + Agronomist intent
→ Weather Agent: Checks rainfall and humidity
→ Agronomist: Analyzes wilting causes and solutions
→ Response: Weather-informed irrigation recommendations
```

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


## Mobile View
![Demo](assets/mobiel_view.mp4)


## License

MIT
