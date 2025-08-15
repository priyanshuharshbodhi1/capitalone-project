import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  RefreshCw, 
  Loader2,
  Calendar,
  Activity
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import SensorChart from '../Dashboard/SensorChart';
import { SensorData } from '../../types';
import { api } from '../../services/api';
import { supabaseApi } from '../../services/supabaseApi';
import { isSupabaseConfigured } from '../../lib/supabase';

const Analytics: React.FC = () => {
  const { t } = useTranslation();
  const [sensorData, setSensorData] = useState<SensorData | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h');

  const fetchSensorData = async () => {
    try {
      // Prefer real data if Supabase is configured; fall back to demo
      let data: SensorData | null = null;
      if (isSupabaseConfigured()) {
        data = await supabaseApi.getLatestSensorData();
      }
      if (data) {
        setIsDemo(false);
        setSensorData(data);
      } else {
        const demo = await api.getLatestSensorData();
        setIsDemo(true);
        setSensorData(demo);
      }
    } catch (error) {
      console.error('Error fetching sensor data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSensorData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchSensorData();
  };

  const sensorParameters = [
    { key: 'atmoTemp', title: t('sensors.atmosphericTemperature'), unit: '°C', color: '#EF4444' },
    { key: 'humidity', title: t('sensors.atmosphericHumidity'), unit: '%', color: '#3B82F6' },
    { key: 'light', title: t('sensors.lightIntensity'), unit: 'lux', color: '#F59E0B' },
    { key: 'ec', title: t('sensors.ec'), unit: 'dS/m', color: '#8B5CF6' },
    { key: 'soilTemp', title: t('sensors.soilTemperature'), unit: '°C', color: '#F97316' },
    { key: 'moisture', title: t('sensors.moisture'), unit: '%', color: '#06B6D4' },
    { key: 'n', title: t('sensors.n'), unit: 'ppm', color: '#10B981' },
    { key: 'p', title: t('sensors.p'), unit: 'ppm', color: '#14B8A6' },
    { key: 'k', title: t('sensors.k'), unit: 'ppm', color: '#059669' },
    { key: 'ph', title: t('sensors.ph'), unit: '', color: '#6366F1' },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center">
          <Loader2 className="h-10 w-10 sm:h-12 sm:w-12 animate-spin text-emerald-600 mx-auto mb-4" />
          <p className="text-gray-600 text-sm sm:text-base">{t('common.loadingAnalytics')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-4 sm:py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Demo data banner */}
        {isDemo && (
          <div className="mb-4">
            <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg overflow-hidden">
              <div className="px-3 py-2">
                <div className="animate-marquee text-xs sm:text-sm">
                  This is DEMO data. Add a mock sensor (from /mock-sensor) or a real device (from /settings) to send real readings.
                </div>
              </div>
            </div>
          </div>
        )}
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 sm:mb-8 space-y-4 sm:space-y-0">
          <div>
            <div className="flex items-center space-x-3">
              <div className="bg-blue-500 p-2 rounded-lg">
                <BarChart3 className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
                  {t('analytics.title')}
                  {isDemo && (
                    <span className="ml-3 text-xs sm:text-sm font-semibold text-red-700 bg-red-50 border border-red-200 rounded px-2 py-0.5">
                      DEMO DATA
                    </span>
                  )}
                </h1>
                <p className="text-gray-600 mt-1 text-sm sm:text-base">{t('analytics.subtitle')}</p>
              </div>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center space-y-3 sm:space-y-0 sm:space-x-3">
            <div className="flex space-x-2 overflow-x-auto pb-2 sm:pb-0">
              {(['24h', '7d', '30d'] as const).map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`flex items-center px-3 sm:px-4 py-2 text-sm rounded-lg font-medium transition-colors duration-200 whitespace-nowrap ${
                    timeRange === range
                      ? 'bg-blue-100 text-blue-700 border-2 border-blue-200'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  <Calendar className="h-3 w-3 sm:h-4 sm:w-4 mr-1" />
                  {t(`common.${range}`)}
                </button>
              ))}
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center justify-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-50 transition-all duration-200 text-sm sm:text-base"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? t('common.refreshing') : t('common.refresh')}
            </button>
          </div>
        </div>

        {/* Analytics Overview */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6 mb-6 sm:mb-8">
          <div className="flex items-center mb-4">
            <Activity className="h-4 w-4 sm:h-5 sm:w-5 text-emerald-500 mr-2" />
            <h2 className="text-base sm:text-lg font-semibold text-gray-900">{t('analytics.statisticalAnalysis')}</h2>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
            <div className="text-center p-3 sm:p-4 bg-emerald-50 rounded-lg">
              <div className="text-xl sm:text-2xl font-bold text-emerald-600">10</div>
              <div className="text-xs sm:text-sm text-emerald-700">{t('analytics.activeSensors')}</div>
            </div>
            <div className="text-center p-3 sm:p-4 bg-blue-50 rounded-lg">
              <div className="text-xl sm:text-2xl font-bold text-blue-600">{t(`common.${timeRange}`)}</div>
              <div className="text-xs sm:text-sm text-blue-700">{t('analytics.timeRange')}</div>
            </div>
            <div className="text-center p-3 sm:p-4 bg-purple-50 rounded-lg">
              <div className="text-xl sm:text-2xl font-bold text-purple-600">{t('analytics.realTimeUpdates')}</div>
              <div className="text-xs sm:text-sm text-purple-700">{t('analytics.dataUpdates')}</div>
            </div>
            <div className="text-center p-3 sm:p-4 bg-orange-50 rounded-lg">
              <div className="text-xl sm:text-2xl font-bold text-orange-600">{t('analytics.minMaxAvg')}</div>
              <div className="text-xs sm:text-sm text-orange-700">{t('analytics.statistics')}</div>
            </div>
          </div>
        </div>

        {/* Charts Grid - All 10 Parameters with Statistics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          {sensorParameters.map((param) => (
            <SensorChart
              key={param.key}
              parameter={param.key as keyof Omit<SensorData, 'timestamp'>}
              title={param.title}
              unit={param.unit}
              color={param.color}
              timeRange={timeRange}
              showStats={true}
            />
          ))}
        </div>

        {/* Data Summary */}
        {sensorData && (
          <div className="mt-6 sm:mt-8 bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-4">{t('analytics.currentReadings')}</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4 text-sm">
              {sensorParameters.map((param) => (
                <div key={param.key} className="text-center p-2 sm:p-3 bg-gray-50 rounded-lg">
                  <div className="font-semibold text-gray-900 text-sm sm:text-base">
                    {sensorData[param.key as keyof Omit<SensorData, 'timestamp'>]}
                    <span className="text-gray-500 ml-1 text-xs sm:text-sm">{param.unit}</span>
                  </div>
                  <div className="text-gray-600 text-xs mt-1 leading-tight">{param.title}</div>
                </div>
              ))}
            </div>
            <div className="mt-4 text-xs text-gray-500 text-center">
              {t('analytics.lastUpdated')}: {new Date(sensorData.timestamp).toLocaleString()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Analytics;