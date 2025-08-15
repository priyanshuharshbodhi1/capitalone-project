import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  AlertTriangle, 
  Clock, 
  CheckCircle, 
  RefreshCw, 
  Loader2,
  Filter,
  Calendar,
  TrendingUp,
  TrendingDown,
  Minus,
  Mail,
  MessageSquare
} from 'lucide-react';
import { Alert } from '../../types';
import { supabaseApi } from '../../services/supabaseApi';
import { format } from 'date-fns';

const AlertHistory: React.FC = () => {
  const { t } = useTranslation();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<'all' | 'sent' | 'pending'>('all');
  const [error, setError] = useState<string | null>(null);
  const [clearing, setClearing] = useState(false);

  const fetchAlerts = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      }
      setError(null);
      
      console.log('📋 AlertHistory: Fetching alerts...');
      const alertsData = await supabaseApi.getAlerts(undefined, 50); // Get last 50 alerts
      console.log('✅ AlertHistory: Alerts fetched:', alertsData.length);
      
      setAlerts(alertsData);
    } catch (error) {
      console.error('❌ AlertHistory: Error fetching alerts:', error);
      setError('Failed to load alerts');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  // Subscribe to real-time alerts so UI updates without manual refresh
  useEffect(() => {
    const subscription: { unsubscribe?: () => void } = supabaseApi.subscribeToAlerts(() => {
      console.log('🔔 AlertHistory: New alert detected via realtime, refreshing list');
      fetchAlerts();
    });

    return () => {
      try {
        subscription?.unsubscribe?.();
      } catch (e) {
        console.warn('⚠️ AlertHistory: Error during unsubscribe', e);
      }
    };
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchAlerts(true);
  };

  const handleClearAll = async () => {
    try {
      setClearing(true);
      setError(null);
      
      console.log('🗑️ AlertHistory: Clearing all alerts...');
      await supabaseApi.clearAllAlerts();
      console.log('✅ AlertHistory: All alerts cleared');
      
      // Refresh the alerts list
      await fetchAlerts();
    } catch (error) {
      console.error('❌ AlertHistory: Error clearing alerts:', error);
      setError('Failed to clear alerts');
    } finally {
      setClearing(false);
    }
  };

  const getFilteredAlerts = () => {
    switch (filter) {
      case 'sent':
        return alerts.filter(alert => alert.is_sent);
      case 'pending':
        return alerts.filter(alert => !alert.is_sent);
      default:
        return alerts;
    }
  };

  const getSeverityIcon = (alert: Alert) => {
    if (alert.current_value < (alert.threshold_min || 0)) {
      return <TrendingDown className="h-4 w-4 text-red-500" />;
    } else if (alert.current_value > (alert.threshold_max || 0)) {
      return <TrendingUp className="h-4 w-4 text-orange-500" />;
    }
    return <Minus className="h-4 w-4 text-yellow-500" />;
  };

  const getSeverityColor = (alert: Alert) => {
    if (alert.current_value < (alert.threshold_min || 0)) {
      return 'border-red-200 bg-red-50';
    } else if (alert.current_value > (alert.threshold_max || 0)) {
      return 'border-orange-200 bg-orange-50';
    }
    return 'border-yellow-200 bg-yellow-50';
  };

  const getSeverityText = (alert: Alert) => {
    if (alert.current_value < (alert.threshold_min || 0)) {
      return 'LOW';
    } else if (alert.current_value > (alert.threshold_max || 0)) {
      return 'HIGH';
    }
    return 'NORMAL';
  };

  const getAlertTypeIcon = (alertType: string) => {
    switch (alertType.toLowerCase()) {
      case 'email':
        return <Mail className="h-3 w-3" />;
      case 'sms':
        return <MessageSquare className="h-3 w-3" />;
      case 'both':
        return (
          <div className="flex space-x-1">
            <Mail className="h-3 w-3" />
            <MessageSquare className="h-3 w-3" />
          </div>
        );
      default:
        return <AlertTriangle className="h-3 w-3" />;
    }
  };

  const filteredAlerts = getFilteredAlerts();
  const sentCount = alerts.filter(alert => alert.is_sent).length;
  const pendingCount = alerts.filter(alert => !alert.is_sent).length;

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6">
        <div className="flex items-center mb-4 sm:mb-6">
          <div className="bg-orange-500 p-2 rounded-lg mr-3">
            <AlertTriangle className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
          </div>
          <h2 className="text-base sm:text-lg font-semibold text-gray-900">{t('alerts.title')}</h2>
        </div>
        
        <div className="flex items-center justify-center py-8 sm:py-12">
          <div className="text-center">
            <Loader2 className="h-10 w-10 sm:h-12 sm:w-12 animate-spin text-orange-600 mx-auto mb-4" />
            <p className="text-gray-600 font-medium text-sm sm:text-base">Loading alerts...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 sm:mb-6 space-y-3 sm:space-y-0">
        <div className="flex items-center">
          <div className="bg-orange-500 p-2 rounded-lg mr-3">
            <AlertTriangle className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-semibold text-gray-900">{t('alerts.title')}</h2>
            <p className="text-gray-600 text-xs sm:text-sm mt-1">
              {t('alerts.subtitle')}
            </p>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={handleClearAll}
            disabled={alerts.length === 0 || refreshing || clearing}
            className="flex items-center justify-center px-3 sm:px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 transition-all duration-200 text-sm"
          >
            <AlertTriangle className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
            {clearing ? 'Clearing...' : 'Clear All'}
          </button>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center justify-center px-3 sm:px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 disabled:opacity-50 transition-all duration-200 text-sm"
          >
            <RefreshCw className={`h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-3 gap-3 sm:gap-4 mb-4 sm:mb-6">
        <div className="text-center p-3 sm:p-4 bg-gray-50 rounded-lg">
          <div className="text-xl sm:text-2xl font-bold text-gray-600">{alerts.length}</div>
          <div className="text-xs sm:text-sm text-gray-700">{t('alerts.totalAlerts')}</div>
        </div>
        <div className="text-center p-3 sm:p-4 bg-green-50 rounded-lg">
          <div className="text-xl sm:text-2xl font-bold text-green-600">{sentCount}</div>
          <div className="text-xs sm:text-sm text-green-700">{t('alerts.sent')}</div>
        </div>
        <div className="text-center p-3 sm:p-4 bg-yellow-50 rounded-lg">
          <div className="text-xl sm:text-2xl font-bold text-yellow-600">{pendingCount}</div>
          <div className="text-xs sm:text-sm text-yellow-700">{t('alerts.pending')}</div>
        </div>
      </div>

      {/* Filter Buttons */}
      <div className="flex space-x-2 mb-4 sm:mb-6 overflow-x-auto pb-2 sm:pb-0">
        {(['all', 'sent', 'pending'] as const).map((filterType) => (
          <button
            key={filterType}
            onClick={() => setFilter(filterType)}
            className={`flex items-center px-3 sm:px-4 py-2 text-sm rounded-lg font-medium transition-colors duration-200 whitespace-nowrap ${
              filter === filterType
                ? 'bg-orange-100 text-orange-700 border-2 border-orange-200'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Filter className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
{filterType === 'all' ? t('alerts.all') : t(`alerts.${filterType}`)}
            {filterType === 'all' && ` (${alerts.length})`}
            {filterType === 'sent' && ` (${sentCount})`}
            {filterType === 'pending' && ` (${pendingCount})`}
          </button>
        ))}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {/* Alerts List */}
      {filteredAlerts.length === 0 ? (
        <div className="text-center py-8 sm:py-12">
          <AlertTriangle className="h-12 w-12 sm:h-16 sm:w-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 font-medium text-sm sm:text-base">
            {filter === 'all' ? t('alerts.noAlerts') : t(`alerts.no${filter.charAt(0).toUpperCase() + filter.slice(1)}Alerts`)}
          </p>
          <p className="text-gray-500 text-xs sm:text-sm mt-1">
            {filter === 'all' 
              ? t('alerts.normalOperation')
              : t('alerts.tryChangingFilter')
            }
          </p>
        </div>
      ) : (
        <div className="space-y-3 sm:space-y-4 max-h-96 overflow-y-auto">
          {filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`border-2 rounded-lg sm:rounded-xl p-3 sm:p-4 transition-all duration-200 hover:shadow-md ${getSeverityColor(alert)}`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {getSeverityIcon(alert)}
                  <span className="font-semibold text-gray-900 text-sm sm:text-base">
                    {alert.parameter.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                    getSeverityText(alert) === 'HIGH' ? 'bg-red-100 text-red-700' :
                    getSeverityText(alert) === 'LOW' ? 'bg-red-100 text-red-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>
                    {getSeverityText(alert)}
                  </span>
                </div>
                
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-1 text-gray-500">
                    {getAlertTypeIcon(alert.alert_type)}
                    <span className="text-xs">{alert.alert_type.toUpperCase()}</span>
                  </div>
                  
                  {alert.is_sent ? (
                    <div className="flex items-center space-x-1 text-green-600">
                      <CheckCircle className="h-4 w-4" />
                      <span className="text-xs font-medium">Sent</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-1 text-yellow-600">
                      <Clock className="h-4 w-4" />
                      <span className="text-xs font-medium">Pending</span>
                    </div>
                  )}
                </div>
              </div>
              
              <p className="text-gray-700 text-xs sm:text-sm mb-3 leading-relaxed">
                {alert.message}
              </p>
              
              <div className="bg-white/70 rounded-lg p-2 sm:p-3 mb-3">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                  <div>
                    <span className="text-gray-500">Current:</span>
                    <span className="font-medium ml-1">{alert.current_value}</span>
                  </div>
                  {alert.threshold_min && (
                    <div>
                      <span className="text-gray-500">Min:</span>
                      <span className="font-medium ml-1">{alert.threshold_min}</span>
                    </div>
                  )}
                  {alert.threshold_max && (
                    <div>
                      <span className="text-gray-500">Max:</span>
                      <span className="font-medium ml-1">{alert.threshold_max}</span>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center space-x-1">
                  <Calendar className="h-3 w-3" />
                  <span>{format(new Date(alert.created_at), 'MMM dd, yyyy HH:mm')}</span>
                </div>
                
                {alert.sent_at && (
                  <div className="flex items-center space-x-1 text-green-600">
                    <CheckCircle className="h-3 w-3" />
                    <span>Sent {format(new Date(alert.sent_at), 'HH:mm')}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="mt-4 sm:mt-6 pt-3 sm:pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-orange-400 animate-pulse"></div>
            <span>{t('alerts.realTimeMonitoring')}</span>
          </div>
          <span>{t('alerts.lastUpdated')}: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
};

export default AlertHistory;