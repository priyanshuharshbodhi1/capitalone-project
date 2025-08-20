import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
// Language-specific translation removed
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { 
  Brain, 
  Sparkles, 
  Leaf, 
  Beaker, 
  Sprout, 
  Lightbulb,
  AlertCircle,
  CheckCircle,
  Loader2,
  RefreshCw,
  Zap,
  
} from 'lucide-react';
import { SensorData } from '../../types';
import { aiApi } from '../../services/aiApi';

interface AIRecommendation {
  type: 'practice' | 'fertilizer' | 'crop' | 'insight';
  title: string;
  description: string;
  confidence: number;
  priority: 'high' | 'medium' | 'low';
  actionable: boolean;
  reasoning: string;
}

interface AIRecommendationsProps {
  sensorData: SensorData | null;
}

const AIRecommendations: React.FC<AIRecommendationsProps> = ({ sensorData }) => {
  const { t } = useTranslation();
  const { currentLanguage } = useLanguage();
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  const [isConfigured, setIsConfigured] = useState(false);
  // Translation removed
  const [error, setError] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);

  useEffect(() => {
    // Check AI configuration on component mount
    const configured = aiApi.isConfigured();
    const status = aiApi.getConfigStatus();
    
    setIsConfigured(configured);
    // status available for debugging if needed
    
    console.log('🤖 AIRecommendations: AI configuration:', status);
  }, []);

  const fetchRecommendations = useCallback(async (isManualRefresh = false) => {
    if (!sensorData) {
      setLoading(false);
      return;
    }
    
    try {
      setError(null);
      
      if (isManualRefresh) {
        setRefreshing(true);
      }
      
      // Always use the edge function approach (handles both AI and fallback)
      // Get user location from user profile, fallback to localStorage, then default
      const userLocation = user?.location || localStorage.getItem('userLocation') || 'India';
      
      // Get language directly from localStorage (most reliable source)
      const userLanguage = localStorage.getItem('userLanguage') || 'english';
      
      console.log('🌍 AIRecommendations: User context for AI:', {
        contextLanguage: currentLanguage,
        userLanguageFromProfile: user?.language,
        localStorageLanguage: userLanguage,
        location: userLocation,
        userId: user?.id,
        userFromProfile: user?.location,
        usingLanguageForAI: userLanguage
      });
      
      // Let's verify which language value we're actually sending
      console.log('📝 AIRecommendations: Language verification:', {
        sendingToAI: userLanguage,
        isNonEnglish: userLanguage !== 'english',
        shouldGetTranslatedResponse: userLanguage !== 'english',
        contextVsLocalStorage: {
          context: currentLanguage,
          localStorage: userLanguage,
          match: currentLanguage === userLanguage
        }
      });
      
      const { recommendations: recs, model } = await aiApi.getRecommendations(sensorData, userLanguage, userLocation);
      setRecommendations(recs);
      setModel(model ?? null);
      
      setHasLoadedOnce(true);

      // Skip alert processing for demo purposes to avoid database operations
      // if (sensorData) {
      //   const user = {
      //     id: '00000000-0000-0000-0000-000000000001',
      //     name: 'Demo User',
      //     email: 'demo@example.com',
      //     phone: '+1234567890',
      //     location: 'Demo Farm'
      //   };
      //   await alertService.checkAndSendAlerts(sensorData, user, recs);
      // }
    } catch (error) {
      console.error('❌ AIRecommendations: Error fetching recommendations:', error);
      setError('Failed to generate AI recommendations');
      setModel(null);
      
      // Set empty recommendations on error
      setRecommendations([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [sensorData]); // Removed currentLanguage dependency since we get language directly from localStorage

  useEffect(() => {
    // Only fetch recommendations on first load (first login)
    if (sensorData && !hasLoadedOnce) {
      setLoading(true);
      fetchRecommendations();
    } else if (sensorData && hasLoadedOnce) {
      setLoading(false);
    }
  }, [sensorData, hasLoadedOnce, fetchRecommendations]);

  // Watch for language changes and refresh recommendations
  useEffect(() => {
    const handleLanguageChange = () => {
      console.log('🔄 AIRecommendations: Language changed, refreshing recommendations...');
      if (sensorData && hasLoadedOnce) {
        fetchRecommendations(true); // Force refresh when language changes
      }
    };

    // Listen for changes to currentLanguage context
    // This will trigger when user changes language in settings
    if (hasLoadedOnce) {
      handleLanguageChange();
    }
  }, [currentLanguage, sensorData, hasLoadedOnce, fetchRecommendations]);

  const handleRefresh = () => {
    console.log('🔄 AIRecommendations: Manual refresh triggered');
    setRefreshing(true);
    fetchRecommendations(true);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'practice': return Leaf;
      case 'fertilizer': return Beaker;
      case 'crop': return Sprout;
      case 'insight': return Lightbulb;
      default: return Brain;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'practice': return 'bg-emerald-500';
      case 'fertilizer': return 'bg-blue-500';
      case 'crop': return 'bg-green-500';
      case 'insight': return 'bg-purple-500';
      default: return 'bg-gray-500';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'border-red-200 bg-red-50';
      case 'medium': return 'border-yellow-200 bg-yellow-50';
      case 'low': return 'border-green-200 bg-green-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  const getPriorityTextColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-700';
      case 'medium': return 'text-yellow-700';
      case 'low': return 'text-green-700';
      default: return 'text-gray-700';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg sm:rounded-xl shadow-sm border border-gray-100 p-3 sm:p-4 lg:p-6">
        <div className="flex items-center mb-3 sm:mb-4 lg:mb-6">
          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-1.5 sm:p-2 rounded-lg mr-2 sm:mr-3">
            <Brain className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
          </div>
          <h2 className="text-sm sm:text-base lg:text-lg font-semibold text-gray-900">{t('ai.recommendations')}</h2>
        </div>
        
        <div className="flex items-center justify-center py-6 sm:py-8 lg:py-12">
          <div className="text-center">
            <div className="relative">
              <Loader2 className="h-8 w-8 sm:h-10 sm:w-10 lg:h-12 lg:w-12 animate-spin text-indigo-600 mx-auto mb-3 sm:mb-4" />
              <div className="absolute inset-0 h-8 w-8 sm:h-10 sm:w-10 lg:h-12 lg:w-12 border-4 border-indigo-200 rounded-full mx-auto animate-pulse"></div>
            </div>
            <p className="text-gray-600 font-medium text-xs sm:text-sm lg:text-base">Analyzing sensor data...</p>
            <p className="text-gray-500 text-xs sm:text-sm mt-1">
              {isConfigured ? 'Generating AI-powered insights' : 'Generating insights with fallback system'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg sm:rounded-xl shadow-sm border border-gray-100 p-3 sm:p-4 lg:p-6">
      <div className="flex flex-col space-y-3 sm:space-y-0 sm:flex-row sm:items-center sm:justify-between mb-3 sm:mb-4 lg:mb-6">
        <div className="flex items-center">
          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-1.5 sm:p-2 rounded-lg mr-2 sm:mr-3">
            <Brain className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
          </div>
          <div>
            <h2 className="text-sm sm:text-base lg:text-lg font-semibold text-gray-900">{t('ai.recommendations')}</h2>
            <div className="flex items-center space-x-1 sm:space-x-2 mt-1">
              {(model === 'gpt-4o' || model === 'ibm-granite-3-8b') && (
                <>
                  <Zap className="h-3 w-3 text-indigo-500" />
                  <span className="text-xs text-indigo-600 font-medium">
                    {model === 'gpt-4o' ? 'GPT-4o' : model === 'ibm-granite-3-8b' ? 'IBM Granite' : 'AI Powered'}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
        
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center justify-center w-full sm:w-auto px-3 sm:px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 transition-all duration-200 text-xs sm:text-sm min-h-[44px]"
        >
          <RefreshCw className={`h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          <span className="font-medium">{refreshing ? 'Analyzing...' : 'Refresh'}</span>
        </button>
      </div>

      {/* Configuration Warning */}
      {!isConfigured && (
        <div className="mb-3 sm:mb-4 p-2 sm:p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center mb-1 sm:mb-2">
            <AlertCircle className="h-3 w-3 sm:h-4 sm:w-4 text-yellow-600 mr-1 sm:mr-2 flex-shrink-0" />
            <span className="text-xs sm:text-sm font-medium text-yellow-800">Supabase Configuration Required</span>
          </div>
          <div className="text-xs text-yellow-700 leading-relaxed">
            Configure Supabase URL and API key to enable AI recommendations via edge function.
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-3 sm:mb-4 p-2 sm:p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600 text-xs sm:text-sm">{error}</p>
        </div>
      )}

      {recommendations.length === 0 ? (
        <div className="text-center py-4 sm:py-6 lg:py-8">
          <Sparkles className="h-6 w-6 sm:h-8 sm:w-8 lg:h-10 lg:w-10 text-gray-400 mx-auto mb-2 sm:mb-3" />
          <p className="text-gray-600 font-medium text-xs sm:text-sm lg:text-base">All conditions optimal!</p>
          <p className="text-gray-500 text-xs sm:text-sm">No immediate recommendations at this time.</p>
        </div>
      ) : (
        <div className="space-y-2 sm:space-y-3 lg:space-y-4">
          {recommendations.map((rec, index) => {
            const TypeIcon = getTypeIcon(rec.type);
            return (
              <div
                key={`${rec.type}-${index}`}
                className={`border-2 rounded-lg sm:rounded-xl p-2 sm:p-3 lg:p-4 transition-all duration-200 hover:shadow-md ${getPriorityColor(rec.priority)}`}
              >
                <div className="flex items-start space-x-2 sm:space-x-3 lg:space-x-4">
                  <div className={`${getTypeColor(rec.type)} p-1.5 sm:p-2 rounded-lg flex-shrink-0`}>
                    <TypeIcon className="h-3 w-3 sm:h-4 sm:w-4 lg:h-5 lg:w-5 text-white" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-col space-y-2 sm:space-y-1 sm:flex-row sm:items-start sm:justify-between mb-2">
                      <h3 className="font-semibold text-gray-900 text-xs sm:text-sm lg:text-base pr-2">{rec.title}</h3>
                      <div className="flex flex-wrap items-center gap-1 sm:gap-2 flex-shrink-0">
                        <span className={`text-xs font-medium px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full ${getPriorityTextColor(rec.priority)} bg-white/50`}>
                          {rec.priority.toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-600 bg-white/50 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full">
                          {rec.confidence}%
                        </span>
                      </div>
                    </div>
                    
                    <p className="text-gray-700 text-xs sm:text-sm mb-2 leading-relaxed">{rec.description}</p>
                    
                    <div className="bg-white/70 rounded-lg p-2 sm:p-3 mb-2 sm:mb-3">
                      <p className="text-xs text-gray-600 leading-relaxed">
                        <strong>AI Reasoning:</strong> {rec.reasoning}
                      </p>
                    </div>
                    
                    <div className="flex flex-col space-y-2 sm:space-y-0 sm:flex-row sm:items-center sm:justify-between">
                      <div className="flex items-center space-x-1 sm:space-x-2">
                        <span className="text-xs text-gray-500 capitalize">{rec.type} recommendation</span>
                        {rec.actionable && (
                          <div className="flex items-center space-x-1">
                            <CheckCircle className="h-3 w-3 text-green-500" />
                            <span className="text-xs text-green-600 font-medium">Actionable</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        {(model === 'gpt-4o' || model === 'ibm-granite-3-8b') && (
                          <>
                            <Zap className="h-3 w-3 text-indigo-500" />
                            <span className="text-xs text-indigo-600 font-medium">
                              {model === 'gpt-4o' ? 'GPT-4o' : model === 'ibm-granite-3-8b' ? 'IBM Granite' : 'AI Powered'}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-3 sm:mt-4 lg:mt-6 pt-2 sm:pt-3 lg:pt-4 border-t border-gray-200">
        <div className="flex flex-col space-y-1 sm:space-y-0 sm:flex-row sm:items-center sm:justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-1 sm:space-x-2">
            {(model === 'gpt-4o' || model === 'ibm-granite-3-8b') && (
              <>
                <div className="w-2 h-2 rounded-full flex-shrink-0 bg-indigo-400 animate-pulse"></div>
                <span className="text-xs">
                  {model === 'gpt-4o' ? 'GPT-4o recommendation engine' : 
                   model === 'ibm-granite-3-8b' ? 'IBM Granite recommendation engine' : 
                   'AI recommendation engine'}
                </span>
              </>
            )}
          </div>
          <span className="text-xs text-right sm:text-left">
            {hasLoadedOnce ? 'Click refresh for new insights' : 'Auto-generated on first load'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default AIRecommendations;