/*
  # AI Recommendations Edge Function
  
  This function handles AI API calls server-side to avoid CORS issues.
  It generates IAM tokens and calls the AI API to get farming recommendations.
*/

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

interface SensorData {
  timestamp: string;
  atmoTemp: number;
  humidity: number;
  light: number;
  ec: number;
  soilTemp: number;
  moisture: number;
  n: number;
  p: number;
  k: number;
  ph: number;
}

interface AIToken {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  expiration: number;
  scope: string;
}

interface AIRecommendation {
  type: 'practice' | 'fertilizer' | 'crop' | 'insight';
  title: string;
  description: string;
  confidence: number;
  priority: 'high' | 'medium' | 'low';
  actionable: boolean;
  reasoning: string;
}

// AI configuration (hardcoded per request)
const AI_API_KEY = 'ZJj1YCackRhQ6B-kAd2g2jiCY50ZT9EjRP9nnkWYR_aP';
const AI_PROJECT_ID = '376d3ee9-d461-4ec8-9fc2-eaac7675b030';
const IAM_URL = 'https://iam.cloud.ibm.com/identity/token';
const AI_URL = 'https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2023-05-29';

// OpenAI configuration (primary AI service)
const OPENAI_API_KEY = Deno.env.get('OPENAI_API_KEY') || '';
const OPENAI_URL = 'https://api.openai.com/v1/chat/completions';

// Generate IAM token for AI authentication
async function generateToken(): Promise<string> {
  try {
    console.log('🔑 AI Edge Function: Generating IAM token...');
    
    const formData = new URLSearchParams();
    formData.append('grant_type', 'urn:ibm:params:oauth:grant-type:apikey');
    formData.append('apikey', AI_API_KEY);

    const response = await fetch(IAM_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
      },
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`IAM token generation failed: ${response.status} - ${errorText}`);
    }

    const tokenData: AIToken = await response.json();
    console.log('✅ AI Edge Function: IAM token generated successfully');
    
    return tokenData.access_token;
  } catch (error) {
    console.error('❌ AI Edge Function: Error generating IAM token:', error);
    throw error;
  }
}

// Get OpenAI GPT-4o recommendations (primary AI service)
async function getOpenAIRecommendations(sensorData: SensorData, userLocation?: string, userLanguage?: string): Promise<{ recommendations: AIRecommendation[]; source: 'ai' | 'fallback' }> {
  try {
    console.log('🤖 AI Edge Function: Trying OpenAI GPT-4o as primary AI service...');
    
    if (!OPENAI_API_KEY) {
      throw new Error('OpenAI API key not configured');
    }
    
    const systemPrompt = generateSystemPrompt(sensorData, userLocation, userLanguage);
    
    console.log('📝 AI Edge Function: Generated system prompt preview:', {
      promptLength: systemPrompt.length,
      hasLocationContext: systemPrompt.includes('User Location:'),
      hasLanguageContext: systemPrompt.includes('CRITICAL LANGUAGE REQUIREMENT:'),
      userLanguage,
      userLocation,
      isNonEnglish: userLanguage && userLanguage !== 'english',
      languageInstructions: userLanguage && userLanguage !== 'english' ? `Should respond in ${userLanguage}` : 'Should respond in English'
    });
    
    // Log a sample of the actual prompt to verify language instructions are included
    if (userLanguage && userLanguage !== 'english') {
      console.log('🔍 AI Edge Function: Language context in prompt:', 
        systemPrompt.substring(systemPrompt.indexOf('CRITICAL LANGUAGE REQUIREMENT:'), 
        systemPrompt.indexOf('CRITICAL LANGUAGE REQUIREMENT:') + 300));
      
      // Add a simple test prompt to make sure OpenAI understands
      console.log('🧪 AI Edge Function: Testing language instruction with direct example');
    }
    
    const payload = {
      model: 'gpt-4o',
      messages: [
        {
          role: 'system',
          content: systemPrompt
        }
      ],
      temperature: 0,
      max_tokens: 2000
    };

    console.log('🚀 AI Edge Function: Sending request to OpenAI API...');
    
    const response = await fetch(OPENAI_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`OpenAI API request failed: ${response.status} - ${errorText}`);
    }

    const responseData = await response.json();
    console.log('✅ AI Edge Function: OpenAI response received');

    // Extract the AI response content
    const aiResponse = responseData.choices?.[0]?.message?.content;
    
    if (!aiResponse) {
      throw new Error('No content in OpenAI response');
    }

    console.log('🔍 AI Edge Function: Parsing OpenAI response...');
    
    // Parse the JSON response from the AI
    let recommendations: AIRecommendation[];
    try {
      // Clean the response in case there's extra text around the JSON
      const jsonMatch = aiResponse.match(/\[[\s\S]*\]/);
      const jsonString = jsonMatch ? jsonMatch[0] : aiResponse;
      recommendations = JSON.parse(jsonString);
    } catch (parseError) {
      console.error('❌ AI Edge Function: Failed to parse OpenAI response as JSON:', parseError);
      console.log('Raw OpenAI response:', aiResponse);
      
      // Return fallback recommendations if parsing fails
      return { recommendations: getFallbackRecommendations(sensorData), source: 'fallback' };
    }

    // Validate the recommendations structure
    const validRecommendations = recommendations.filter(rec => 
      rec.type && rec.title && rec.description && 
      typeof rec.confidence === 'number' && rec.priority && 
      typeof rec.actionable === 'boolean' && rec.reasoning
    );

    console.log(`✅ AI Edge Function: Generated ${validRecommendations.length} valid recommendations from OpenAI`);
    
    // Log a sample recommendation to verify language
    if (validRecommendations.length > 0 && userLanguage && userLanguage !== 'english') {
      console.log('🔍 AI Edge Function: Sample recommendation language check:', {
        userLanguage,
        sampleTitle: validRecommendations[0].title,
        sampleDescription: validRecommendations[0].description.substring(0, 100),
        appearsToBeInRequestedLanguage: !validRecommendations[0].title.match(/^[a-zA-Z\s]+$/) || validRecommendations[0].title.includes('।') || validRecommendations[0].title.includes('़') // Basic check for non-Latin characters
      });
    }
    
    return { recommendations: validRecommendations, source: 'ai' };

  } catch (error) {
    console.error('❌ AI Edge Function: Error getting OpenAI recommendations:', error);
    
    // Return fallback recommendations on error
    return { recommendations: getFallbackRecommendations(sensorData), source: 'fallback' };
  }
}

// Generate system prompt with current sensor data, location, and language context
function generateSystemPrompt(sensorData: SensorData, userLocation?: string, userLanguage?: string): string {
  const locationContext = userLocation ? `\n\nUser Location: ${userLocation}\nPlease consider local climate, soil conditions, and regional farming practices specific to this location when providing recommendations.` : '';
  const languageContext = userLanguage && userLanguage !== 'english' ? `\n\n🚨 CRITICAL LANGUAGE REQUIREMENT 🚨: 
  
  ALL RECOMMENDATIONS MUST BE PROVIDED IN ${userLanguage.toUpperCase()} LANGUAGE ONLY.
  
  - Translate the "title" field completely into ${userLanguage}
  - Translate the "description" field completely into ${userLanguage}  
  - Translate the "reasoning" field completely into ${userLanguage}
  - DO NOT USE ANY ENGLISH WORDS in the response
  - The user speaks ${userLanguage} as their primary language
  - They require agricultural advice in ${userLanguage} for proper understanding
  - Example: If the language is "hindi", respond with "सिंचाई बढ़ाएं" not "Increase Irrigation"
  - If language is "${userLanguage}", ALL content must be in ${userLanguage} script/characters
  
  REMEMBER: The entire JSON response content must be in ${userLanguage} language.` : '';
  
  return `You are an agricultural AI assistant. Based on the provided sensor data, historical trends, and farm profile, generate a list of actionable farming recommendations and insights.

Your response MUST be a JSON array of objects. Each object in the array MUST adhere to the following structure:

[
  {
    "type": "string", // Must be one of: "practice", "fertilizer", "crop", "insight"
    "title": "string", // A concise title for the recommendation
    "description": "string", // A detailed explanation of the recommendation
    "confidence": "number", // AI's confidence in the recommendation (0-100)
    "priority": "string", // Must be one of: "high", "medium", "low"
    "actionable": "boolean", // True if the recommendation is something the farmer can directly act upon
    "reasoning": "string" // The AI's reasoning for this recommendation, based on the input data
  }
]

Here is the current sensor data:
${JSON.stringify({
  timestamp: sensorData.timestamp,
  atmoTemp: sensorData.atmoTemp,
  humidity: sensorData.humidity,
  light: sensorData.light,
  ec: sensorData.ec,
  soilTemp: sensorData.soilTemp,
  moisture: sensorData.moisture,
  n: sensorData.n,
  p: sensorData.p,
  k: sensorData.k,
  ph: sensorData.ph
}, null, 2)}${locationContext}${languageContext}

${userLanguage && userLanguage !== 'english' ? `
🚨 FINAL REMINDER 🚨: 
- RESPOND ENTIRELY IN ${userLanguage.toUpperCase()} LANGUAGE
- ALL JSON CONTENT (title, description, reasoning) MUST BE IN ${userLanguage.toUpperCase()}
- NO ENGLISH WORDS ALLOWED IN THE RESPONSE
- TRANSLATE EVERYTHING TO ${userLanguage.toUpperCase()}` : ''}

Generate the recommendations now based on the user's location and provide them in their preferred language.`;
}

// Fallback recommendations when AI is unavailable
function getFallbackRecommendations(sensorData: SensorData): AIRecommendation[] {
  console.log('🔄 AI Edge Function: Using fallback recommendations');
  
  const recommendations: AIRecommendation[] = [];

  // Soil moisture check
  if (sensorData.moisture < 40) {
    recommendations.push({
      type: 'practice',
      title: 'Increase Irrigation',
      description: 'Soil moisture is below optimal levels. Consider increasing irrigation frequency or duration.',
      confidence: 85,
      priority: 'high',
      actionable: true,
      reasoning: `Current soil moisture at ${sensorData.moisture}% is below the optimal range of 40-60%.`
    });
  }

  // pH check
  if (sensorData.ph < 6.0 || sensorData.ph > 7.5) {
    recommendations.push({
      type: 'practice',
      title: 'Soil pH Adjustment',
      description: sensorData.ph < 6.0 ? 'Apply lime to increase soil pH' : 'Apply sulfur to decrease soil pH',
      confidence: 80,
      priority: 'medium',
      actionable: true,
      reasoning: `Current pH of ${sensorData.ph} is outside the optimal range of 6.0-7.5.`
    });
  }

  // Nutrient check
  if (sensorData.n < 30) {
    recommendations.push({
      type: 'fertilizer',
      title: 'Nitrogen Fertilizer Application',
      description: 'Apply nitrogen-rich fertilizer to boost plant growth and leaf development.',
      confidence: 75,
      priority: 'medium',
      actionable: true,
      reasoning: `Nitrogen levels at ${sensorData.n}ppm are below optimal range.`
    });
  }

  // Temperature check
  if (sensorData.atmoTemp > 35) {
    recommendations.push({
      type: 'practice',
      title: 'Heat Stress Management',
      description: 'High temperatures detected. Consider shade cloth or increased ventilation.',
      confidence: 78,
      priority: 'high',
      actionable: true,
      reasoning: `Atmospheric temperature at ${sensorData.atmoTemp}°C is above optimal range.`
    });
  }

  // Light check
  if (sensorData.light < 300) {
    recommendations.push({
      type: 'insight',
      title: 'Light Supplementation',
      description: 'Low light levels may affect photosynthesis. Consider LED grow lights.',
      confidence: 70,
      priority: 'medium',
      actionable: true,
      reasoning: `Light intensity at ${sensorData.light} lux is below optimal 400-800 lux range.`
    });
  }

  return recommendations;
}

// Get AI recommendations (tries OpenAI GPT-4o first, then rule-based fallback)
async function getRecommendations(sensorData: SensorData, userLocation?: string, userLanguage?: string): Promise<{ recommendations: AIRecommendation[]; source: 'ai' | 'fallback'; model?: string }> {
  // Try OpenAI GPT-4o first
  try {
    const openaiResult = await getOpenAIRecommendations(sensorData, userLocation, userLanguage);
    if (openaiResult.source === 'ai') {
      return { ...openaiResult, model: 'gpt-4o' };
    }
    // If OpenAI failed, fall through to rule-based fallback
  } catch (openaiError) {
    console.error('❌ AI Edge Function: OpenAI failed:', openaiError);
  }
  
  // OpenAI failed, use rule-based fallback
  console.log('🔄 AI Edge Function: AI system failed, using rule-based fallback');
  return { recommendations: getFallbackRecommendations(sensorData), source: 'fallback' };

  /* 
  // IBM WatsonX code (kept for future use but not currently active)
  // First try IBM WatsonX
  try {
    console.log('🤖 AI Edge Function: Trying IBM WatsonX first...');
    
    // Get access token
    const accessToken = await generateToken();
    
    // Prepare the request payload
    const payload = {
      messages: [
        {
          role: 'system',
          content: generateSystemPrompt(sensorData, userLocation, userLanguage)
        }
      ],
      project_id: AI_PROJECT_ID,
      model_id: 'ibm/granite-3-8b-instruct',
      frequency_penalty: 0,
      max_tokens: 2000,
      presence_penalty: 0,
      temperature: 0,
      top_p: 1,
      seed: null,
      stop: []
    };

    console.log('🚀 AI Edge Function: Sending request to IBM WatsonX API...');
    
    const response = await fetch(AI_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`IBM WatsonX API request failed: ${response.status} - ${errorText}`);
    }

    const responseData = await response.json();
    console.log('✅ AI Edge Function: IBM WatsonX response received');

    // Extract the AI response content
    const aiResponse = responseData.choices?.[0]?.message?.content;
    
    if (!aiResponse) {
      throw new Error('No content in IBM WatsonX response');
    }

    console.log('🔍 AI Edge Function: Parsing IBM WatsonX response...');
    
    // Parse the JSON response from the AI
    let recommendations: AIRecommendation[];
    try {
      // Clean the response in case there's extra text around the JSON
      const jsonMatch = aiResponse.match(/\[[\s\S]*\]/);
      const jsonString = jsonMatch ? jsonMatch[0] : aiResponse;
      recommendations = JSON.parse(jsonString);
    } catch (parseError) {
      console.error('❌ AI Edge Function: Failed to parse IBM WatsonX response as JSON:', parseError);
      console.log('Raw IBM WatsonX response:', aiResponse);
      throw new Error('Failed to parse IBM WatsonX response');
    }

    // Validate the recommendations structure
    const validRecommendations = recommendations.filter(rec => 
      rec.type && rec.title && rec.description && 
      typeof rec.confidence === 'number' && rec.priority && 
      typeof rec.actionable === 'boolean' && rec.reasoning
    );

    console.log(`✅ AI Edge Function: Generated ${validRecommendations.length} valid recommendations from IBM WatsonX`);
    return { recommendations: validRecommendations, source: 'ai', model: 'ibm-granite-3-8b' };

  } catch (ibmError) {
    console.error('❌ AI Edge Function: IBM WatsonX failed:', ibmError);
    // Continue to OpenAI fallback...
  }
  */
}

Deno.serve(async (req: Request) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  if (req.method !== 'POST') {
    return new Response(
      JSON.stringify({ error: 'Method not allowed' }),
      { status: 405, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  try {
    console.log('🤖 AI Edge Function: Request received');
    
    // Parse the sensor data and optional user context from request body
    const { sensorData, userLocation, userLanguage }: { 
      sensorData: SensorData; 
      userLocation?: string; 
      userLanguage?: string; 
    } = await req.json();
    
    if (!sensorData) {
      return new Response(
        JSON.stringify({ error: 'Sensor data is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log('📊 AI Edge Function: Processing request with context:', {
      timestamp: sensorData.timestamp,
      atmoTemp: sensorData.atmoTemp,
      moisture: sensorData.moisture,
      ph: sensorData.ph,
      userLocation: userLocation || 'Not specified',
      userLanguage: userLanguage || 'english',
      hasOpenAIKey: !!OPENAI_API_KEY,
      openAIKeyLength: OPENAI_API_KEY ? OPENAI_API_KEY.length : 0
    });

    // Get recommendations with user context
    const { recommendations, source, model } = await getRecommendations(sensorData, userLocation, userLanguage);
    
    console.log(`📋 AI Edge Function: Returning ${recommendations.length} recommendations (source: ${source}${model ? `, model: ${model}` : ''})`);

    return new Response(
      JSON.stringify({
        success: true,
        recommendations,
        timestamp: new Date().toISOString(),
        source,
        model
      }),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );

  } catch (error) {
    console.error('❌ AI Edge Function: Error:', error);
    
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error'
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
  }
});