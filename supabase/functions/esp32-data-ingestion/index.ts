/*
  # ESP32 Data Ingestion Edge Function
  
  This function receives sensor data from ESP32 devices and stores it in the database.
  It validates the device API key and ensures data integrity.
*/

import { createClient } from 'npm:@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-api-key',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

interface SensorDataPayload {
  device_id: string;
  api_key: string;
  atmo_temp?: number;
  humidity?: number;
  light?: number;
  soil_temp?: number;
  moisture?: number;
  ec?: number;
  ph?: number;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
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
    // Initialize Supabase client with service role key
    // Accept alternate names since the Supabase UI reserves the SUPABASE_ prefix
    const SUPABASE_URL = Deno.env.get('PROJECT_URL') ?? Deno.env.get('SUPABASE_URL') ?? '';
    const SERVICE_KEY = Deno.env.get('SERVICE_ROLE_KEY') ?? Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';

    if (!SUPABASE_URL || !SERVICE_KEY) {
      console.error('Missing required env vars for Edge Function', {
        hasUrl: !!SUPABASE_URL,
        hasServiceKey: !!SERVICE_KEY,
      });
      return new Response(
        JSON.stringify({
          error: 'Server misconfiguration',
          details: 'Set PROJECT_URL and SERVICE_ROLE_KEY (or SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY) for this function',
        }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const supabase = createClient(SUPABASE_URL, SERVICE_KEY);

    // Parse request body
    const payload: SensorDataPayload = await req.json();

    // Validate required fields
    if (!payload.device_id || !payload.api_key) {
      return new Response(
        JSON.stringify({ error: 'device_id and api_key are required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Verify device and API key
    const { data: device, error: deviceError } = await supabase
      .from('devices')
      .select('id, user_id, device_name, is_active')
      .eq('device_id', payload.device_id)
      .eq('api_key', payload.api_key)
      .single();

    if (deviceError || !device) {
      return new Response(
        JSON.stringify({ error: 'Invalid device_id or api_key' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    if (!device.is_active) {
      return new Response(
        JSON.stringify({ error: 'Device is inactive' }),
        { status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Prepare sensor data for insertion with sanitization
    const coerceNum = (v: unknown) => {
      const n = typeof v === 'string' ? Number(v) : (v as number);
      return Number.isFinite(n) ? n : null;
    };

    const sensorDataRaw: Record<string, unknown> = {
      device_id: payload.device_id,
      user_id: device.user_id,
      atmo_temp: coerceNum(payload.atmo_temp),
      humidity: coerceNum(payload.humidity),
      // light must be integer per schema
      light: (() => {
        const n = coerceNum(payload.light);
        return n === null ? null : Math.round(n as number);
      })(),
      soil_temp: coerceNum(payload.soil_temp),
      moisture: coerceNum(payload.moisture),
      ec: coerceNum(payload.ec),
      ph: coerceNum(payload.ph),
      nitrogen: coerceNum(payload.nitrogen),
      phosphorus: coerceNum(payload.phosphorus),
      potassium: coerceNum(payload.potassium),
    };

    // Drop undefined keys (keep nulls to explicitly clear if needed)
    const sensorData = Object.fromEntries(
      Object.entries(sensorDataRaw).filter(([, v]) => v !== undefined)
    );

    // Insert sensor data
    const { data: insertedData, error: insertError } = await supabase
      .from('sensor_data')
      .insert(sensorData)
      .select()
      .single();

    if (insertError) {
      console.error('Error inserting sensor data:', insertError);
      const errObj = insertError as unknown as Record<string, unknown>;
      return new Response(
        JSON.stringify({
          error: 'Failed to store sensor data',
          details: insertError.message,
          code: typeof errObj.code === 'string' ? errObj.code : undefined,
          hint: typeof errObj.hint === 'string' ? errObj.hint : undefined,
        }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Update device last_seen timestamp
    await supabase
      .from('devices')
      .update({ last_seen: new Date().toISOString() })
      .eq('device_id', payload.device_id);

    const inserted = insertedData as { id?: string } | null;
    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Sensor data stored successfully',
        data_id: inserted?.id 
      }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Unexpected error:', error);
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});