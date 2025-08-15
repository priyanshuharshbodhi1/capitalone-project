import React, { useEffect, useMemo, useState } from 'react';
import { supabaseApi } from '../../services/supabaseApi';
import toast from 'react-hot-toast';

type Device = {
  id: string;
  device_id: string;
  device_name: string;
  location?: string | null;
  api_key?: string;
};

const numberOrUndefined = (v: string) => (v === '' ? undefined : Number(v));
const intOrUndefined = (v: string) => (v === '' ? undefined : Math.round(Number(v)));

const MockSensor: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [apiKey, setApiKey] = useState('');

  const [deviceForm, setDeviceForm] = useState({ device_id: '', device_name: '', location: '' });
  const [creatingDevice, setCreatingDevice] = useState(false);

  const [fields, setFields] = useState({
    atmo_temp: '',
    humidity: '',
    light: '',
    soil_temp: '',
    moisture: '',
    ec: '',
    ph: '',
    nitrogen: '',
    phosphorus: '',
    potassium: '',
  });

  const [autoSend, setAutoSend] = useState(false);

  // Generate a random number informed by thresholds
  const generateValue = (
    param: string,
    thresholds: any[],
    opts?: { mostlyWithin?: boolean }
  ): number => {
    const t = thresholds.find((x) => x.parameter === param);
    const min = typeof t?.min_value === 'number' ? t.min_value : undefined;
    const max = typeof t?.max_value === 'number' ? t.max_value : undefined;

    // Fallback ranges per parameter
    const defaults: Record<string, [number, number]> = {
      atmo_temp: [10, 40],
      soil_temp: [5, 35],
      humidity: [20, 90],
      light: [100, 1500],
      moisture: [10, 80],
      ec: [0.1, 3.0],
      ph: [4.5, 8.5],
      nitrogen: [0, 100],
      phosphorus: [0, 100],
      potassium: [0, 100],
    };

    const [dmin, dmax] = defaults[param] || [0, 100];

    // Distribution: if mostlyWithin, ~99% within threshold, else 25/50/25 split
    const r = Math.random();
    if (!opts?.mostlyWithin && min !== undefined && r < 0.25) {
      const lowMin = Math.max(dmin - (dmax - dmin) * 0.5, dmin - 50);
      const lowMax = min * 0.98;
      const a = isFinite(lowMin) ? lowMin : dmin * 0.5;
      const b = isFinite(lowMax) ? lowMax : dmin;
      return Number((a + Math.random() * Math.max(0.001, b - a)).toFixed(2));
    }

    if (!opts?.mostlyWithin && max !== undefined && r > 0.75) {
      const highMin = max * 1.02;
      const highMax = dmax + (dmax - dmin) * 0.5;
      const a = isFinite(highMin) ? highMin : dmax;
      const b = isFinite(highMax) ? highMax : dmax * 1.5;
      return Number((a + Math.random() * Math.max(0.001, b - a)).toFixed(2));
    }

    // Within range (prefer threshold window if available)
    const inMin = min ?? dmin;
    const inMax = max ?? dmax;
    return Number((inMin + Math.random() * Math.max(0.001, inMax - inMin)).toFixed(2));
  };

  const generateRandomFields = async (sendAfter = false, mostlyWithin = false) => {
    try {
      if (!selectedDeviceId) return toast.error('Select a device');

      const thresholds = await supabaseApi.getThresholds(selectedDeviceId);
      const keys = Object.keys(fields) as Array<keyof typeof fields>;
      const next: any = {};
      for (const k of keys) {
        next[k] = String(generateValue(k as string, thresholds as any[], { mostlyWithin }));
      }
      setFields(next);

      toast.success(sendAfter ? 'Random data generated. Sending…' : 'Random data generated');

      if (sendAfter) {
        const payload = {
          device_id: selectedDeviceId,
          api_key: apiKey.trim(),
          atmo_temp: numberOrUndefined(next.atmo_temp),
          humidity: numberOrUndefined(next.humidity),
          light: intOrUndefined(next.light),
          soil_temp: numberOrUndefined(next.soil_temp),
          moisture: numberOrUndefined(next.moisture),
          ec: numberOrUndefined(next.ec),
          ph: numberOrUndefined(next.ph),
          nitrogen: numberOrUndefined(next.nitrogen),
          phosphorus: numberOrUndefined(next.phosphorus),
          potassium: numberOrUndefined(next.potassium),
        };
        await supabaseApi.sendSensorData(payload as any);
        toast.success('Random sensor data sent');
      }
    } catch (e: any) {
      toast.error(e.message || 'Failed to generate/send data');
    }
  };

  // Auto-send loop (15s intervals, mostly within thresholds)
  useEffect(() => {
    if (!autoSend) return;
    if (!selectedDeviceId || !apiKey) {
      toast.error('Select device and API key for auto-send');
      setAutoSend(false);
      return;
    }
    let cancelled = false;
    const tick = async () => {
      if (cancelled) return;
      try {
        await generateRandomFields(true, true);
      } catch (err) {
        console.debug('Auto-send failed', err);
      }
    };
    // immediate send, then every 15s
    tick();
    const id = setInterval(tick, 15000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [autoSend, selectedDeviceId, apiKey]);

  const selectedDevice = useMemo(
    () => devices.find(d => d.device_id === selectedDeviceId),
    [devices, selectedDeviceId]
  );

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const list = await supabaseApi.getUserDevices();
        setDevices(list as any);
        if (list && list.length > 0) {
          setSelectedDeviceId(list[0].device_id);
          setApiKey(list[0].api_key || '');
        }
      } catch (e: any) {
        toast.error(e.message || 'Failed to load devices');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  useEffect(() => {
    if (selectedDevice) {
      setApiKey(selectedDevice.api_key || '');
    }
  }, [selectedDevice]);

  const handleCreateDevice = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingDevice(true);
    try {
      const created = await supabaseApi.addDevice(
        deviceForm.device_id.trim(),
        deviceForm.device_name.trim(),
        deviceForm.location.trim() || undefined
      );
      toast.success('Device created');
      const list = await supabaseApi.getUserDevices();
      setDevices(list as any);
      setSelectedDeviceId(created.device_id);
      setApiKey(created.api_key || '');
      setDeviceForm({ device_id: '', device_name: '', location: '' });
    } catch (e: any) {
      toast.error(e.message || 'Failed to create device');
    } finally {
      setCreatingDevice(false);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDeviceId) return toast.error('Select a device');
    if (!apiKey) return toast.error('API key is required');

    const payload = {
      device_id: selectedDeviceId,
      api_key: apiKey.trim(),
      atmo_temp: numberOrUndefined(fields.atmo_temp),
      humidity: numberOrUndefined(fields.humidity),
      light: intOrUndefined(fields.light),
      soil_temp: numberOrUndefined(fields.soil_temp),
      moisture: numberOrUndefined(fields.moisture),
      ec: numberOrUndefined(fields.ec),
      ph: numberOrUndefined(fields.ph),
      nitrogen: numberOrUndefined(fields.nitrogen),
      phosphorus: numberOrUndefined(fields.phosphorus),
      potassium: numberOrUndefined(fields.potassium),
    };

    try {
      await supabaseApi.sendSensorData(payload as any);
      toast.success('Sensor data sent');
    } catch (e: any) {
      toast.error(e.message || 'Failed to send data');
    }
  };

  return (
    <div className="min-h-screen bg-red-50 py-6">
      <div className="max-w-5xl mx-auto px-4">
        <h1 className="text-2xl font-semibold text-red-900 mb-1">Mock Sensor</h1>
        <p className="text-red-700 mb-6">Create/select a device and send mock sensor readings.</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-sm border border-red-200 p-5">
            <h2 className="text-lg font-medium text-red-900 mb-4">Select Device</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-red-800 mb-1">Device</label>
                <select
                  value={selectedDeviceId}
                  onChange={e => setSelectedDeviceId(e.target.value)}
                  className="w-full border-red-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
                  disabled={loading || autoSend}
                >
                  <option value="">-- Select --</option>
                  {devices.map(d => (
                    <option key={d.id} value={d.device_id}>
                      {d.device_name} ({d.device_id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-red-800 mb-1">API Key</label>
                <input
                  type="text"
                  value={apiKey}
                  onChange={e => setApiKey(e.target.value)}
                  placeholder="auto-filled after selecting device"
                  className="w-full border-red-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
                  disabled={autoSend}
                />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-red-200 p-5">
            <h2 className="text-lg font-medium text-red-900 mb-4">Create Device</h2>
            <form className="space-y-4" onSubmit={handleCreateDevice}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-red-800 mb-1">Device ID</label>
                  <input
                    type="text"
                    value={deviceForm.device_id}
                    onChange={e => setDeviceForm({ ...deviceForm, device_id: e.target.value })}
                    placeholder="unique-id"
                    className="w-full border-red-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-red-800 mb-1">Name</label>
                  <input
                    type="text"
                    value={deviceForm.device_name}
                    onChange={e => setDeviceForm({ ...deviceForm, device_name: e.target.value })}
                    placeholder="My Sensor"
                    className="w-full border-red-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-red-800 mb-1">Location</label>
                <input
                  type="text"
                  value={deviceForm.location}
                  onChange={e => setDeviceForm({ ...deviceForm, location: e.target.value })}
                  placeholder="Farm A / Greenhouse"
                  className="w-full border-red-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
                />
              </div>
              <button
                type="submit"
                disabled={creatingDevice}
                className="inline-flex items-center px-4 py-2 rounded-md bg-red-600 text-white hover:bg-red-700 disabled:opacity-60"
              >
                {creatingDevice ? 'Creating…' : 'Create Device'}
              </button>
            </form>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-red-200 p-5 mt-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              {/* Auto-send toggle next to title */}
              <button
                type="button"
                onClick={() => setAutoSend(v => !v)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${autoSend ? 'bg-red-600' : 'bg-red-200'}`}
                aria-pressed={autoSend}
                aria-label="Toggle auto-send"
              >
                <span
                  className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${autoSend ? 'translate-x-5' : 'translate-x-1'}`}
                />
              </button>
              <h2 className="text-lg font-medium text-red-900">Send Sensor Data</h2>
            </div>
            {autoSend && (
              <span className="text-xs text-red-700">Auto-sending every 15s</span>
            )}
          </div>
          <form className="space-y-4" onSubmit={handleSend}>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.keys(fields).map((k) => (
                <div key={k}>
                  <label className="block text-sm font-medium text-red-800 mb-1">{k}</label>
                  <input
                    type="number"
                    step="any"
                    value={(fields as any)[k]}
                    onChange={e => setFields(prev => ({ ...prev, [k]: e.target.value }))}
                    placeholder=""
                    className="w-full border-red-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
                    disabled={autoSend}
                  />
                </div>
              ))}
            </div>
            <div className="flex gap-3 flex-wrap items-center">
              {/* Reordered: Generate random first */}
              <button
                type="button"
                className="inline-flex items-center px-4 py-2 rounded-md border border-red-300 text-red-700 hover:bg-red-50"
                onClick={() => generateRandomFields(false)}
                disabled={autoSend}
              >
                Generate random
              </button>
              <button
                type="submit"
                className="inline-flex items-center px-4 py-2 rounded-md bg-red-600 text-white hover:bg-red-700 disabled:opacity-60"
                disabled={autoSend}
              >
                Send
              </button>
              <button
                type="button"
                className="inline-flex items-center px-4 py-2 rounded-md border border-red-300 text-red-700 hover:bg-red-50"
                onClick={() => setFields({
                  atmo_temp: '', humidity: '', light: '', soil_temp: '', moisture: '', ec: '', ph: '', nitrogen: '', phosphorus: '', potassium: ''
                })}
                disabled={autoSend}
              >
                Clear
              </button>
            </div>
          </form>
          <p className="text-xs text-red-700 mt-4">Uses the existing Supabase Edge Function: esp32-data-ingestion.</p>
        </div>
      </div>
    </div>
  );
};

export default MockSensor;
