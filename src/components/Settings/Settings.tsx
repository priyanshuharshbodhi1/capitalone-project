import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { useTranslation } from 'react-i18next';
import { 
  User, 
  Mail, 
  Phone, 
  Save, 
  Loader2, 
  Sliders,
  AlertTriangle,
  CheckCircle,
  Smartphone,
  RefreshCw,
  Plus,
  MapPin,
  Calendar,
  Wifi,
  WifiOff,
  Edit3,
  Trash2,
  Key,
  Lock,
  Bell,
  BellOff,
  MessageSquare,
  MailIcon,
  Globe
} from 'lucide-react';
import { api } from '../../services/api';
import { supabaseApi } from '../../services/supabaseApi';

interface Threshold {
  id: string;
  device_id: string;
  parameter: string;
  min_value: number | null;
  max_value: number | null;
  alert_email: boolean;
  alert_sms: boolean;
  is_active: boolean;
}

interface Device {
  id: string;
  device_id: string;
  device_name: string;
  location: string | null;
  is_active: boolean;
  last_seen: string | null;
  api_key: string;
  created_at: string;
}

const Settings: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const { currentLanguage, changeLanguage, languages } = useLanguage();
  const [activeTab, setActiveTab] = useState<'profile' | 'devices' | 'thresholds' | 'language'>('profile');
  
  // Profile state
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: user?.phone || '',
  });
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState(false);
  
  // Device state
  const [devices, setDevices] = useState<Device[]>([]);
  const [devicesLoading, setDevicesLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingDevice, setEditingDevice] = useState<Device | null>(null);
  const [deviceFormData, setDeviceFormData] = useState({
    device_id: '',
    device_name: '',
    location: '',
  });
  const [deviceSubmitting, setDeviceSubmitting] = useState(false);
  
  // Thresholds state
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [thresholds, setThresholds] = useState<Threshold[]>([]);
  const [thresholdsLoading, setThresholdsLoading] = useState(false);
  const [thresholdsSaving, setThresholdsSaving] = useState<string>(''); // Track which threshold is being saved
  const [thresholdsSuccess, setThresholdsSuccess] = useState('');
  const [error, setError] = useState('');

  // Threshold parameter definitions
  const thresholdParameters = [
    { key: 'atmo_temp', label: t('settings.thresholdParameters.atmo_temp'), unit: '°C', defaultMin: 15, defaultMax: 35 },
    { key: 'humidity', label: t('settings.thresholdParameters.humidity'), unit: '%', defaultMin: 40, defaultMax: 80 },
    { key: 'light', label: t('settings.thresholdParameters.light'), unit: 'lux', defaultMin: 300, defaultMax: 800 },
    { key: 'soil_temp', label: t('settings.thresholdParameters.soil_temp'), unit: '°C', defaultMin: 18, defaultMax: 30 },
    { key: 'moisture', label: t('settings.thresholdParameters.moisture'), unit: '%', defaultMin: 30, defaultMax: 70 },
    { key: 'ec', label: t('settings.thresholdParameters.ec'), unit: 'dS/m', defaultMin: 0.5, defaultMax: 2.0 },
    { key: 'ph', label: t('settings.thresholdParameters.ph'), unit: '', defaultMin: 6.0, defaultMax: 7.5 },
    { key: 'nitrogen', label: t('settings.thresholdParameters.nitrogen'), unit: 'ppm', defaultMin: 20, defaultMax: 50 },
    { key: 'phosphorus', label: t('settings.thresholdParameters.phosphorus'), unit: 'ppm', defaultMin: 15, defaultMax: 25 },
    { key: 'potassium', label: t('settings.thresholdParameters.potassium'), unit: 'ppm', defaultMin: 15, defaultMax: 40 },
  ];

  // Default threshold values for sensor parameters
  const defaultThresholds = [
    { parameter: 'atmo_temp', min_value: 15.0, max_value: 35.0 },
    { parameter: 'humidity', min_value: 40.0, max_value: 80.0 },
    { parameter: 'moisture', min_value: 30.0, max_value: 70.0 },
    { parameter: 'ph', min_value: 6.0, max_value: 7.5 },
    { parameter: 'ec', min_value: 0.5, max_value: 2.0 },
    { parameter: 'soil_temp', min_value: 18.0, max_value: 30.0 },
    { parameter: 'nitrogen', min_value: 20.0, max_value: 50.0 },
    { parameter: 'phosphorus', min_value: 15.0, max_value: 25.0 },
    { parameter: 'potassium', min_value: 15.0, max_value: 40.0 },
    { parameter: 'light', min_value: 300.0, max_value: 800.0 },
  ];

  useEffect(() => {
    fetchDevices();
  }, []);

  useEffect(() => {
    if (selectedDevice) {
      fetchThresholds();
    }
  }, [selectedDevice]);

  const fetchDevices = async () => {
    try {
      console.log('🔍 Settings: Fetching devices...');
      setDevicesLoading(true);
      const deviceData = await supabaseApi.getUserDevices();
      console.log('✅ Settings: Devices fetched:', deviceData.length);
      setDevices(deviceData);
      if (deviceData.length > 0 && !selectedDevice) {
        setSelectedDevice(deviceData[0].device_id);
      }
    } catch (error) {
      console.error('❌ Settings: Error fetching devices:', error);
      setError('Failed to load devices');
    } finally {
      setDevicesLoading(false);
    }
  };

  const fetchThresholds = async () => {
    if (!selectedDevice) return;
    
    console.log('🎯 Settings: Fetching thresholds for device:', selectedDevice);
    setThresholdsLoading(true);
    setError('');
    
    try {
      const thresholdData = await supabaseApi.getThresholds(selectedDevice);
      console.log('✅ Settings: Thresholds fetched:', thresholdData.length);
      setThresholds(thresholdData);
    } catch (error) {
      console.error('❌ Settings: Error fetching thresholds:', error);
      setError('Failed to load thresholds');
    } finally {
      setThresholdsLoading(false);
    }
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileLoading(true);
    setProfileSuccess(false);
    setError('');

    try {
      await api.updateSettings(formData);
      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 3000);
    } catch (error) {
      console.error('❌ Settings: Error updating profile:', error);
      setError('Failed to update profile');
    } finally {
      setProfileLoading(false);
    }
  };

  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  // Device management functions
  const createDefaultThresholds = async (deviceId: string) => {
    try {
      // Create default thresholds for all sensor parameters
      for (const threshold of defaultThresholds) {
        await supabaseApi.updateThreshold(
          deviceId,
          threshold.parameter,
          threshold.min_value,
          threshold.max_value
        );
      }
      console.log(`Created default thresholds for device: ${deviceId}`);
    } catch (error) {
      console.error('Error creating default thresholds:', error);
      // Don't throw error here as device creation was successful
      // Just log the error for debugging
    }
  };

  const handleDeviceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setDeviceSubmitting(true);
    setError('');

    try {
      if (editingDevice) {
        await supabaseApi.updateDevice(editingDevice.device_id, {
          device_name: deviceFormData.device_name,
          location: deviceFormData.location || undefined,
        });
        setThresholdsSuccess('Device updated successfully');
      } else {
        // Add new device
        const newDevice = await supabaseApi.addDevice(
          deviceFormData.device_id,
          deviceFormData.device_name,
          deviceFormData.location || undefined
        );
        
        // Create default thresholds for the new device
        await createDefaultThresholds(newDevice.device_id);
        
        setThresholdsSuccess('Device added successfully with default thresholds');
      }
      
      await fetchDevices();
      resetDeviceForm();
    } catch (error: any) {
      setError(error.message || 'Failed to save device');
    } finally {
      setDeviceSubmitting(false);
    }
  };

  const handleDeviceDelete = async (deviceId: string) => {
    if (!confirm('Are you sure you want to delete this device? All associated data will be removed.')) {
      return;
    }

    try {
      await supabaseApi.deleteDevice(deviceId);
      setThresholdsSuccess('Device deleted successfully');
      await fetchDevices();
      if (selectedDevice === deviceId) {
        setSelectedDevice('');
      }
    } catch (error: any) {
      setError(error.message || 'Failed to delete device');
    }
  };

  const resetDeviceForm = () => {
    setDeviceFormData({ device_id: '', device_name: '', location: '' });
    setShowAddForm(false);
    setEditingDevice(null);
  };

  const startDeviceEdit = (device: Device) => {
    setEditingDevice(device);
    setDeviceFormData({
      device_id: device.device_id,
      device_name: device.device_name,
      location: device.location || '',
    });
    setShowAddForm(true);
  };

  const copyApiKey = (apiKey: string) => {
    navigator.clipboard.writeText(apiKey);
    setThresholdsSuccess('API key copied to clipboard');
    setTimeout(() => setThresholdsSuccess(''), 3000);
  };

  const getDeviceStatus = (device: Device) => {
    if (!device.last_seen) return 'never';
    
    const lastSeen = new Date(device.last_seen);
    const now = new Date();
    const diffMinutes = (now.getTime() - lastSeen.getTime()) / (1000 * 60);
    
    if (diffMinutes < 5) return 'online';
    if (diffMinutes < 30) return 'recent';
    return 'offline';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-600 bg-green-100';
      case 'recent': return 'text-yellow-600 bg-yellow-100';
      case 'offline': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    return status === 'online' || status === 'recent' ? Wifi : WifiOff;
  };

  // Threshold management functions
  const getThreshold = (parameter: string): Threshold | null => {
    return thresholds.find(t => t.parameter === parameter) || null;
  };

  const getThresholdValue = (parameter: string, type: 'min' | 'max'): number => {
    const threshold = getThreshold(parameter);
    if (threshold) {
      return type === 'min' ? (threshold.min_value || 0) : (threshold.max_value || 0);
    }
    
    // Return default values if no threshold exists
    const paramDef = thresholdParameters.find(p => p.key === parameter);
    return type === 'min' ? (paramDef?.defaultMin || 0) : (paramDef?.defaultMax || 0);
  };

  const getThresholdProperty = (parameter: string, property: 'alert_email' | 'alert_sms' | 'is_active'): boolean => {
    const threshold = getThreshold(parameter);
    if (threshold) {
      return threshold[property];
    }
    
    // Return default values if no threshold exists
    switch (property) {
      case 'alert_email': return true;
      case 'alert_sms': return false;
      case 'is_active': return true;
      default: return true;
    }
  };

  const updateThreshold = async (parameter: string, minValue: number, maxValue: number) => {
    if (!selectedDevice) return;

    console.log('🎯 Settings: Updating threshold:', { parameter, minValue, maxValue });
    setThresholdsSaving(parameter);
    setError('');

    try {
      // Use the improved updateThreshold method that handles insert/update logic
      await supabaseApi.updateThreshold(selectedDevice, parameter, minValue, maxValue);
      
      setThresholdsSuccess(`Updated ${parameter} threshold successfully`);
      setTimeout(() => setThresholdsSuccess(''), 3000);
      
      // Refresh thresholds to get the latest data
      await fetchThresholds();
      
      console.log('✅ Settings: Threshold updated successfully');
    } catch (error) {
      console.error('❌ Settings: Error updating threshold:', error);
      setError(`Failed to update ${parameter} threshold: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setThresholdsSaving('');
    }
  };

  const handleThresholdChange = (parameter: string, type: 'min' | 'max', value: string) => {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return;

    const currentMin = getThresholdValue(parameter, 'min');
    const currentMax = getThresholdValue(parameter, 'max');

    const newMin = type === 'min' ? numValue : currentMin;
    const newMax = type === 'max' ? numValue : currentMax;

    // Validate that min <= max
    if (newMin <= newMax) {
      updateThreshold(parameter, newMin, newMax);
    } else {
      setError(`Minimum value cannot be greater than maximum value for ${parameter}`);
      setTimeout(() => setError(''), 3000);
    }
  };

  // Handle threshold property changes (alert preferences and active status)
  const handleThresholdPropertyChange = async (parameter: string, property: 'alert_email' | 'alert_sms' | 'is_active', value: boolean) => {
    if (!selectedDevice) return;

    console.log('🎯 Settings: Updating threshold property:', { parameter, property, value });
    setThresholdsSaving(parameter);
    setError('');

    try {
      await supabaseApi.updateThresholdProperties(selectedDevice, parameter, {
        [property]: value
      });
      
      setThresholdsSuccess(`Updated ${parameter} ${property.replace('_', ' ')} successfully`);
      setTimeout(() => setThresholdsSuccess(''), 3000);
      
      // Refresh thresholds to get the latest data
      await fetchThresholds();
      
      console.log('✅ Settings: Threshold property updated successfully');
    } catch (error) {
      console.error('❌ Settings: Error updating threshold property:', error);
      setError(`Failed to update ${parameter} ${property}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setThresholdsSaving('');
    }
  };

  // Bulk save all thresholds with default values
  const initializeDefaultThresholds = async () => {
    if (!selectedDevice) return;

    console.log('🎯 Settings: Initializing default thresholds...');
    setThresholdsLoading(true);
    setError('');

    try {
      const thresholdUpdates = thresholdParameters.map(param => ({
        parameter: param.key,
        minValue: param.defaultMin,
        maxValue: param.defaultMax,
      }));

      await supabaseApi.updateMultipleThresholds(selectedDevice, thresholdUpdates);
      
      setThresholdsSuccess('Default thresholds initialized successfully');
      setTimeout(() => setThresholdsSuccess(''), 3000);
      
      // Refresh thresholds
      await fetchThresholds();
      
      console.log('✅ Settings: Default thresholds initialized');
    } catch (error) {
      console.error('❌ Settings: Error initializing default thresholds:', error);
      setError(`Failed to initialize default thresholds: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setThresholdsLoading(false);
    }
  };

  // Allow adding multiple devices (no limit)
  const canAddDevice = true;

  // Supported languages for switching in Settings
  const supportedLanguageCodes = new Set([
    'english',
    'hindi',
    'bengali',
    'marathi',
    'gujarati',
    'punjabi',
    'odia',
    'assamese',
    'malayalam',
    'kannada',
    'tamil',
    'telugu',
    'urdu',
    'nepali',
  ] as const);

  const supportedLanguages = languages.filter(l => supportedLanguageCodes.has(l.code as any));
  const unsupportedLanguages = languages.filter(l => !supportedLanguageCodes.has(l.code as any));
  const orderedLanguages = [...supportedLanguages, ...unsupportedLanguages];

  return (
    <div className="min-h-screen bg-gray-50 py-4 sm:py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow-sm rounded-xl border border-gray-100">
          {/* Header */}
          <div className="px-4 sm:px-6 py-4 border-b border-gray-200">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">{t('settings.title')}</h1>
            <p className="text-gray-600 mt-1 text-sm sm:text-base">{t('settings.subtitle')}</p>
          </div>

          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-4 sm:space-x-8 px-4 sm:px-6 overflow-x-auto pb-2 sm:pb-0">
              <button
                onClick={() => setActiveTab('profile')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 flex-shrink-0 ${
                  activeTab === 'profile'
                    ? 'border-emerald-500 text-emerald-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4" />
                  <span>{t('settings.profile')}</span>
                </div>
              </button>
              
              <button
                onClick={() => setActiveTab('devices')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 flex-shrink-0 ${
                  activeTab === 'devices'
                    ? 'border-emerald-500 text-emerald-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Smartphone className="h-4 w-4" />
                  <span>{t('settings.devices')}</span>
                </div>
              </button>
              
              <button
                onClick={() => setActiveTab('thresholds')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 flex-shrink-0 ${
                  activeTab === 'thresholds'
                    ? 'border-emerald-500 text-emerald-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Sliders className="h-4 w-4" />
                  <span>{t('settings.thresholds')}</span>
                </div>
              </button>
              
              <button
                onClick={() => setActiveTab('language')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 flex-shrink-0 ${
                  activeTab === 'language'
                    ? 'border-emerald-500 text-emerald-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Globe className="h-4 w-4" />
                  <span>{t('settings.language')}</span>
                </div>
              </button>
            </nav>
          </div>

          {/* Messages */}
          {error && (
            <div className="mx-4 sm:mx-6 mt-4 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
              <AlertTriangle className="h-5 w-5 text-red-500 mr-2 flex-shrink-0" />
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {(profileSuccess || thresholdsSuccess) && (
            <div className="mx-4 sm:mx-6 mt-4 bg-green-50 border border-green-200 rounded-lg p-4 flex items-center">
              <CheckCircle className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" />
              <p className="text-green-600 text-sm">{profileSuccess ? 'Profile updated successfully!' : thresholdsSuccess}</p>
            </div>
          )}

          {/* Tab Content */}
          <div className="p-4 sm:p-6">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <form onSubmit={handleProfileSubmit} className="space-y-6">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                    {t('settings.fullName')}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <User className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                    </div>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleProfileChange}
                      className="block w-full pl-9 sm:pl-10 pr-3 py-2 sm:py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 text-sm sm:text-base"
                      placeholder={t('auth.enterFullName')}
                      required
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    {t('settings.emailAddress')}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Mail className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                    </div>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleProfileChange}
                      className="block w-full pl-9 sm:pl-10 pr-3 py-2 sm:py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 text-sm sm:text-base"
                      placeholder={t('auth.enterEmail')}
                      required
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                    {t('settings.phoneNumber')}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Phone className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                    </div>
                    <input
                      type="tel"
                      id="phone"
                      name="phone"
                      value={formData.phone}
                      onChange={handleProfileChange}
                      className="block w-full pl-9 sm:pl-10 pr-3 py-2 sm:py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 text-sm sm:text-base"
                      placeholder={t('settings.enterPhoneNumber')}
                      required
                    />
                  </div>
                </div>

                <div className="pt-4">
                  <button
                    type="submit"
                    disabled={profileLoading}
                    className="w-full flex justify-center py-2 sm:py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    {profileLoading ? (
                      <>
                        <Loader2 className="animate-spin -ml-1 mr-2 sm:mr-3 h-4 w-4 sm:h-5 sm:w-5" />
                        {t('common.saving')}
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
{t('settings.saveProfile')}
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}

            {/* Devices Tab */}
            {activeTab === 'devices' && (
              <div className="space-y-6">
                {/* Device Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">{t('common.deviceManagement')}</h3>
                    <p className="text-gray-600 text-sm">{t('common.manageIoTDevice')}</p>
                  </div>
                  <button
                    onClick={() => setShowAddForm(true)}
                    disabled={!canAddDevice}
                    className={`flex items-center px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 transition-all duration-200 ${
                      canAddDevice
                        ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    {canAddDevice ? (
                      <Plus className="h-4 w-4 mr-2" />
                    ) : (
                      <Lock className="h-4 w-4 mr-2" />
                    )}
                    {canAddDevice ? t('common.addDevice') : t('common.deviceLimitReached')}
                  </button>
                </div>

                {/* Device Limit Notice removed: multiple devices now supported */}

                {/* Add/Edit Device Form */}
                {showAddForm && (
                  <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                    <h4 className="text-lg font-medium text-gray-900 mb-4">
                      {editingDevice ? t('common.editDevice') : t('common.addNewDevice')}
                    </h4>
                    
                    <form onSubmit={handleDeviceSubmit} className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t('common.deviceId')}
                          </label>
                          <input
                            type="text"
                            value={deviceFormData.device_id}
                            onChange={(e) => setDeviceFormData({ ...deviceFormData, device_id: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                            placeholder={t('common.deviceIdPlaceholder')}
                            required
                            disabled={!!editingDevice}
                          />
                          {editingDevice && (
                            <p className="text-xs text-gray-500 mt-1">{t('common.deviceIdCannotChange')}</p>
                          )}
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t('common.deviceName')}
                          </label>
                          <input
                            type="text"
                            value={deviceFormData.device_name}
                            onChange={(e) => setDeviceFormData({ ...deviceFormData, device_name: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                            placeholder={t('common.deviceNamePlaceholder')}
                            required
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          {t('common.locationOptional')}
                        </label>
                        <input
                          type="text"
                          value={deviceFormData.location}
                          onChange={(e) => setDeviceFormData({ ...deviceFormData, location: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                          placeholder={t('common.locationPlaceholder')}
                        />
                      </div>

                      {!editingDevice && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <h5 className="text-sm font-medium text-blue-900 mb-2">{t('common.defaultThresholds')}</h5>
                          <p className="text-sm text-blue-700">
                            {t('common.defaultThresholdsMessage')}
                          </p>
                          <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-blue-600">
                            {defaultThresholds.map((threshold) => (
                              <div key={threshold.parameter}>
                                <strong>{threshold.parameter}:</strong> {threshold.min_value} - {threshold.max_value}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="flex space-x-3">
                        <button
                          type="submit"
                          disabled={deviceSubmitting}
                          className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-50 transition-all duration-200"
                        >
                          {deviceSubmitting ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : (
                            <CheckCircle className="h-4 w-4 mr-2" />
                          )}
                          {editingDevice ? t('common.updateDevice') : t('common.addDevice')}
                        </button>
                        
                        <button
                          type="button"
                          onClick={resetDeviceForm}
                          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-all duration-200"
                        >
                          {t('common.cancel')}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Devices List */}
                {devicesLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-emerald-600 mr-2" />
                    <span className="text-gray-600">{t('common.loadingDevices')}</span>
                  </div>
                ) : devices.length === 0 ? (
                  <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                    <Smartphone className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h4 className="text-lg font-medium text-gray-900 mb-2">{t('common.noDevicesFound')}</h4>
                    <p className="text-gray-600 mb-6">{t('common.addIoTDevice')}</p>
                    <button
                      onClick={() => setShowAddForm(true)}
                      disabled={!canAddDevice}
                      className={`inline-flex items-center px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 transition-all duration-200 ${
                        canAddDevice
                          ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      {canAddDevice ? (
                        <Plus className="h-4 w-4 mr-2" />
                      ) : (
                        <Lock className="h-4 w-4 mr-2" />
                      )}
                      {canAddDevice ? t('common.addYourDevice') : t('common.deviceLimitReached')}
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-4">
                    {devices.map((device) => {
                      const status = getDeviceStatus(device);
                      const StatusIcon = getStatusIcon(status);
                      
                      return (
                        <div key={device.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
                          {/* Device Header */}
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center space-x-3">
                              <div className="bg-emerald-100 p-2 rounded-lg">
                                <Smartphone className="h-5 w-5 text-emerald-600" />
                              </div>
                              <div>
                                <h4 className="font-semibold text-gray-900">{device.device_name}</h4>
                                <p className="text-sm text-gray-500">{device.device_id}</p>
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-1">
                              <button
                                onClick={() => startDeviceEdit(device)}
                                className="p-1 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                              >
                                <Edit3 className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => handleDeviceDelete(device.device_id)}
                                className="p-1 text-gray-400 hover:text-red-600 transition-colors duration-200"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </div>

                          {/* Status */}
                          <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mb-3 ${getStatusColor(status)}`}>
                            <StatusIcon className="h-3 w-3 mr-1" />
                            {status === 'online' ? t('common.online') : status === 'recent' ? t('common.recentlyActive') : status === 'offline' ? t('common.offline') : t('common.neverConnected')}
                          </div>

                          {/* Device Info */}
                          <div className="space-y-2 mb-4">
                            {device.location && (
                              <div className="flex items-center text-sm text-gray-600">
                                <MapPin className="h-4 w-4 mr-2" />
                                {device.location}
                              </div>
                            )}
                            
                            <div className="flex items-center text-sm text-gray-600">
                              <Calendar className="h-4 w-4 mr-2" />
                              {t('common.added')} {new Date(device.created_at).toLocaleDateString()}
                            </div>

                            {device.last_seen && (
                              <div className="flex items-center text-sm text-gray-600">
                                <Wifi className="h-4 w-4 mr-2" />
                                {t('common.lastSeen')} {new Date(device.last_seen).toLocaleString()}
                              </div>
                            )}
                          </div>

                          {/* API Key */}
                          <div className="border-t border-gray-100 pt-4">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-medium text-gray-700">{t('common.apiKey')}</span>
                              <button
                                onClick={() => copyApiKey(device.api_key)}
                                className="flex items-center text-xs text-emerald-600 hover:text-emerald-700 transition-colors duration-200"
                              >
                                <Key className="h-3 w-3 mr-1" />
                                {t('common.copy')}
                              </button>
                            </div>
                            <div className="mt-1 font-mono text-xs text-gray-500 bg-gray-50 p-2 rounded border truncate">
                              {device.api_key}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Thresholds Tab */}
            {activeTab === 'thresholds' && (
              <div className="space-y-6">
                {/* Device Selection */}
                {devices.length > 0 ? (
                  <>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          {t('common.selectDevice')}
                        </label>
                        <div className="relative max-w-md">
                          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Smartphone className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                          </div>
                          <select
                            value={selectedDevice}
                            onChange={(e) => setSelectedDevice(e.target.value)}
                            className="block w-full pl-9 sm:pl-10 pr-3 py-2 sm:py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 text-sm sm:text-base"
                          >
                            {devices.map((device) => (
                              <option key={device.id} value={device.device_id}>
                                {device.device_name} ({device.device_id})
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                      
                      <div className="flex space-x-3">
                        <button
                          onClick={fetchThresholds}
                          disabled={thresholdsLoading}
                          className="flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 transition-all duration-200 text-sm"
                        >
                          <RefreshCw className={`h-4 w-4 mr-2 ${thresholdsLoading ? 'animate-spin' : ''}`} />
                          {t('common.refresh')}
                        </button>
                        
                        <button
                          onClick={initializeDefaultThresholds}
                          disabled={thresholdsLoading}
                          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 transition-all duration-200 text-sm"
                        >
                          <Sliders className="h-4 w-4 mr-2" />
                          {t('common.setDefaults')}
                        </button>
                      </div>
                    </div>

                    {/* Thresholds Configuration */}
                    {selectedDevice && (
                      <div>
                        <h4 className="text-lg font-medium text-gray-900 mb-4">{t('settings.sensorThresholds')}</h4>
                        <p className="text-sm text-gray-600 mb-6">
                          {t('settings.configureAlerts')}
                        </p>

                        {thresholdsLoading ? (
                          <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin text-emerald-600 mr-2" />
                            <span className="text-gray-600">{t('settings.loadingThresholds')}</span>
                          </div>
                        ) : (
                          <div className="space-y-4">
                            {thresholdParameters.map((param) => {
                              const isActive = getThresholdProperty(param.key, 'is_active');
                              const alertEmail = getThresholdProperty(param.key, 'alert_email');
                              const alertSms = getThresholdProperty(param.key, 'alert_sms');
                              
                              return (
                                <div key={param.key} className={`rounded-lg p-4 border transition-all duration-200 ${
                                  isActive 
                                    ? 'bg-white border-gray-200 shadow-sm' 
                                    : 'bg-gray-50 border-gray-200 opacity-75'
                                }`}>
                                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
                                    <div className="flex-1">
                                      <div className="flex items-center space-x-3 mb-2">
                                        <h5 className="font-medium text-gray-900">{param.label}</h5>
                                        <div className="flex items-center space-x-2">
                                          {/* Active/Inactive Toggle */}
                                          <button
                                            onClick={() => handleThresholdPropertyChange(param.key, 'is_active', !isActive)}
                                            disabled={thresholdsSaving === param.key}
                                            className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium transition-all duration-200 ${
                                              isActive 
                                                ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                                                : 'bg-red-100 text-red-700 hover:bg-red-200'
                                            } ${thresholdsSaving === param.key ? 'opacity-50 cursor-not-allowed' : ''}`}
                                          >
                                            {isActive ? <Bell className="h-3 w-3" /> : <BellOff className="h-3 w-3" />}
                                            <span>{isActive ? t('settings.active') : t('settings.disabled')}</span>
                                          </button>
                                        </div>
                                      </div>
                                      <p className="text-sm text-gray-500">{t('settings.unit')}: {param.unit || 'N/A'}</p>
                                    </div>
                                    
                                    {thresholdsSaving === param.key && (
                                      <div className="flex items-center text-sm text-blue-600 mt-2 sm:mt-0">
                                        <Loader2 className="h-4 w-4 animate-spin mr-1" />
                                        {t('settings.saving')}
                                      </div>
                                    )}
                                  </div>
                                  
                                  {/* Threshold Values */}
                                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                                    <div>
                                      <label className="block text-xs font-medium text-gray-700 mb-1">
                                        {t('settings.minimumValue')}
                                      </label>
                                      <input
                                        type="number"
                                        step="0.1"
                                        value={getThresholdValue(param.key, 'min')}
                                        onChange={(e) => handleThresholdChange(param.key, 'min', e.target.value)}
                                        disabled={thresholdsSaving === param.key || !isActive}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                                        placeholder={`${t('settings.defaultValue')}: ${param.defaultMin}`}
                                      />
                                    </div>
                                    
                                    <div>
                                      <label className="block text-xs font-medium text-gray-700 mb-1">
                                        {t('settings.maximumValue')}
                                      </label>
                                      <input
                                        type="number"
                                        step="0.1"
                                        value={getThresholdValue(param.key, 'max')}
                                        onChange={(e) => handleThresholdChange(param.key, 'max', e.target.value)}
                                        disabled={thresholdsSaving === param.key || !isActive}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                                        placeholder={`${t('settings.defaultValue')}: ${param.defaultMax}`}
                                      />
                                    </div>
                                  </div>

                                  {/* Alert Preferences */}
                                  <div className="border-t border-gray-200 pt-4">
                                    <h6 className="text-sm font-medium text-gray-700 mb-3">{t('settings.alertPreferences')}</h6>
                                    <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-6">
                                      {/* Email Alert Toggle */}
                                      <div className="flex items-center space-x-3">
                                        <button
                                          onClick={() => handleThresholdPropertyChange(param.key, 'alert_email', !alertEmail)}
                                          disabled={thresholdsSaving === param.key || !isActive}
                                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 ${
                                            alertEmail && isActive ? 'bg-emerald-600' : 'bg-gray-300'
                                          } ${thresholdsSaving === param.key || !isActive ? 'opacity-50 cursor-not-allowed' : ''}`}
                                        >
                                          <span
                                            className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform duration-200 ${
                                              alertEmail && isActive ? 'translate-x-5' : 'translate-x-1'
                                            }`}
                                          />
                                        </button>
                                        <div className="flex items-center space-x-1">
                                          <MailIcon className="h-4 w-4 text-gray-500" />
                                          <span className="text-sm text-gray-700">{t('settings.emailAlerts')}</span>
                                        </div>
                                      </div>

                                      {/* SMS Alert Toggle */}
                                      <div className="flex items-center space-x-3">
                                        <button
                                          onClick={() => handleThresholdPropertyChange(param.key, 'alert_sms', !alertSms)}
                                          disabled={thresholdsSaving === param.key || !isActive}
                                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 ${
                                            alertSms && isActive ? 'bg-emerald-600' : 'bg-gray-300'
                                          } ${thresholdsSaving === param.key || !isActive ? 'opacity-50 cursor-not-allowed' : ''}`}
                                        >
                                          <span
                                            className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform duration-200 ${
                                              alertSms && isActive ? 'translate-x-5' : 'translate-x-1'
                                            }`}
                                          />
                                        </button>
                                        <div className="flex items-center space-x-1">
                                          <MessageSquare className="h-4 w-4 text-gray-500" />
                                          <span className="text-sm text-gray-700">{t('settings.smsAlerts')}</span>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                  
                                  <div className="mt-3 text-xs text-gray-500">
                                    {t('settings.defaultRange')}: {param.defaultMin} - {param.defaultMax} {param.unit}
                                    {!isActive && (
                                      <span className="ml-2 text-red-600 font-medium">• {t('settings.alertsDisabled')}</span>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-8">
                    <Smartphone className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h4 className="text-lg font-medium text-gray-900 mb-2">{t('common.noDevicesFound')}</h4>
                    <p className="text-gray-600 mb-4">
                      {t('settings.needDeviceForThresholds')}
                    </p>
                    <button
                      onClick={() => setActiveTab('devices')}
                      className="inline-flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 transition-all duration-200"
                    >
                      <Smartphone className="h-4 w-4 mr-2" />
                      {t('common.goToDeviceManagement')}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Language Tab Content */}
            {activeTab === 'language' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    {t('settings.selectLanguage')}
                  </h3>
                  
                  {/* Language Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
                    {orderedLanguages.map((language) => {
                      const isSupported = supportedLanguageCodes.has(language.code as any);
                      return (
                        <button
                          key={language.code}
                          onClick={() => {
                            if (isSupported) changeLanguage(language.code);
                          }}
                          disabled={!isSupported}
                          title={isSupported ? '' : 'not completely supported.'}
                          className={`flex items-center justify-between p-4 rounded-lg border-2 transition-all duration-200 text-left ${
                            isSupported
                              ? (currentLanguage === language.code
                                  ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50')
                              : 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                          }`}
                          aria-disabled={!isSupported}
                        >
                          <div className="flex items-center space-x-3 min-w-0 flex-1">
                            <Globe className="h-5 w-5 flex-shrink-0" />
                            <div className="min-w-0 flex-1">
                              <div className="font-medium truncate">{language.name}</div>
                              <div className={`text-sm truncate ${isSupported ? 'opacity-75' : 'opacity-60'}`}>{language.nativeName}</div>
                              {!isSupported && (
                                <div className="text-xs text-gray-500 mt-1">not completely supported.</div>
                              )}
                            </div>
                          </div>
                          {isSupported && currentLanguage === language.code && (
                            <CheckCircle className="h-5 w-5 text-emerald-600 flex-shrink-0 ml-2" />
                          )}
                        </button>
                      );
                    })}
                  </div>

                  {/* Language Preference Notice */}
                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-start space-x-2">
                      <AlertTriangle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                      <div className="text-sm text-blue-800">
                        <div className="font-medium mb-1">Language Preference</div>
                        <div>Your language preference will be saved to your profile and applied automatically when you sign in.</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;