import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useLanguage } from '../../context/LanguageContext';
import { 
  Brain, 
  Sparkles, 
  Leaf, 
  Beaker, 
  Sprout, 
  Lightbulb,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Loader2,
  RefreshCw,
  Zap,
  Cloud
} from 'lucide-react';
import { SensorData } from '../../types';
import { watsonxApi } from '../../services/watsonxApi';
import { sarvamApi } from '../../services/sarvamApi';

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
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  const [isConfigured, setIsConfigured] = useState(false);
  const [translating, setTranslating] = useState(false);
  const [configStatus, setConfigStatus] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<'watsonx' | 'fallback' | null>(null);

  useEffect(() => {
    // Check WatsonX configuration on component mount
    const configured = watsonxApi.isConfigured();
    const status = watsonxApi.getConfigStatus();
    
    setIsConfigured(configured);
    setConfigStatus(status);
    
    console.log('🤖 AIRecommendations: WatsonX configuration:', status);
  }, []);

  const fetchRecommendations = async (isManualRefresh = false) => {
    if (!sensorData) {
      setLoading(false);
      return;
    }
    
    try {
      setError(null);
      
      if (isManualRefresh) {
        setRefreshing(true);
      }
      
      // Always use the edge function approach (which handles both WatsonX and fallback)
      const recs = await watsonxApi.getRecommendations(sensorData);
      
      // 🌍 DEMO: Translate AI responses using Sarvam API
      if (currentLanguage !== 'en') {
        console.log(`🌍 AIRecommendations: Translating ${recs.length} recommendations to ${currentLanguage}`);
        setTranslating(true);
        
        try {
          // Transform recommendations to match Sarvam API format
          const recsForTranslation = recs.map(rec => ({
            id: rec.type + Math.random().toString(36).substr(2, 9),
            text: rec.description,
            confidence: rec.confidence,
            reasoning: rec.reasoning,
            priority: rec.priority,
          }));
          
          // Translate using Sarvam API
          const translatedRecs = await sarvamApi.translateRecommendations(
            recsForTranslation, 
            currentLanguage
          );
          
          // Transform back to original format
          const finalRecs = recs.map((rec, index) => ({
            ...rec,
            description: translatedRecs[index]?.text || rec.description,
            reasoning: translatedRecs[index]?.reasoning || rec.reasoning,
          }));
          
          console.log('✅ AIRecommendations: Translation completed via Sarvam API');
          setRecommendations(finalRecs);
          
        } catch (translationError) {
          console.warn('⚠️ AIRecommendations: Translation failed, using original text:', translationError);
          setRecommendations(recs); // Fallback to original if translation fails
        } finally {
          setTranslating(false);
        }
      } else {
        setRecommendations(recs);
      }
      
      // Determine source based on configuration and results
      if (isConfigured && recs.length > 0) {
        setSource('watsonx');
      } else {
        setSource('fallback');
      }
      
      setHasLoadedOnce(true);
    } catch (error) {
      console.error('❌ AIRecommendations: Error fetching recommendations:', error);
      setError('Failed to generate AI recommendations');
      setSource('fallback');
      
      // Set empty recommendations on error
      setRecommendations([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    // Only fetch recommendations on first load (first login)
    if (sensorData && !hasLoadedOnce) {
      setLoading(true);
      fetchRecommendations();
    } else if (sensorData && hasLoadedOnce) {
      setLoading(false);
    }
  }, [sensorData, hasLoadedOnce]);

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
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6">
        <div className="flex items-center mb-4 sm:mb-6">
          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-2 rounded-lg mr-3">
            <Brain className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
          </div>
          <h2 className="text-base sm:text-lg font-semibold text-gray-900">WatsonX AI Recommendations</h2>
        </div>
        
        <div className="flex items-center justify-center py-8 sm:py-12">
          <div className="text-center">
            <div className="relative">
              <Loader2 className="h-10 w-10 sm:h-12 sm:w-12 animate-spin text-indigo-600 mx-auto mb-4" />
              <div className="absolute inset-0 h-10 w-10 sm:h-12 sm:w-12 border-4 border-indigo-200 rounded-full mx-auto animate-pulse"></div>
            </div>
            <p className="text-gray-600 font-medium text-sm sm:text-base">Analyzing sensor data...</p>
            <p className="text-gray-500 text-xs sm:text-sm mt-1">
              {isConfigured ? 'Generating AI-powered insights with WatsonX' : 'Generating insights with fallback system'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 sm:mb-6 space-y-3 sm:space-y-0">
        <div className="flex items-center">
          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-2 rounded-lg mr-3">
            <Brain className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-semibold text-gray-900">{t('ai.recommendations')}</h2>
            <div className="flex items-center space-x-2 mt-1">
              {translating && (
                <>
                  <Loader2 className="h-3 w-3 text-blue-500 animate-spin" />
                  <span className="text-xs text-blue-600 font-medium">🌍 Translating via Sarvam AI...</span>
                </>
              )}
              {!translating && source === 'watsonx' ? (
                <>
                  <Zap className="h-3 w-3 text-indigo-500" />
                  <span className="text-xs text-indigo-600 font-medium">WatsonX AI Powered</span>
                  {currentLanguage !== 'en' && (
                    <span className="text-xs text-green-600 font-medium">• Translated via Sarvam AI</span>
                  )}
                </>
              ) : !translating && source === 'fallback' ? (
                <>
                  <Cloud className="h-3 w-3 text-yellow-500" />
                  <span className="text-xs text-yellow-600 font-medium">{t('ai.fallbackMode')}</span>
                  {currentLanguage !== 'en' && (
                    <span className="text-xs text-green-600 font-medium">• Translated via Sarvam AI</span>
                  )}
                </>
              ) : (
                <>
                  <AlertCircle className="h-3 w-3 text-gray-500" />
                  <span className="text-xs text-gray-600 font-medium">Ready</span>
                </>
              )}
            </div>
          </div>
        </div>
        
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center justify-center px-3 sm:px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 transition-all duration-200 text-sm"
        >
          <RefreshCw className={`h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Analyzing...' : 'Refresh'}
        </button>
      </div>

      {/* Configuration Warning */}
      {!isConfigured && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center mb-2">
            <AlertCircle className="h-4 w-4 text-yellow-600 mr-2" />
            <span className="text-sm font-medium text-yellow-800">Supabase Configuration Required</span>
          </div>
          <div className="text-xs text-yellow-700">
            Configure Supabase URL and API key to enable WatsonX AI recommendations via edge function.
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {recommendations.length === 0 ? (
        <div className="text-center py-6 sm:py-8">
          <Sparkles className="h-8 w-8 sm:h-10 sm:w-10 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600 font-medium text-sm sm:text-base">All conditions optimal!</p>
          <p className="text-gray-500 text-xs sm:text-sm">No immediate recommendations at this time.</p>
        </div>
      ) : (
        <div className="space-y-3 sm:space-y-4">
          {recommendations.map((rec, index) => {
            const TypeIcon = getTypeIcon(rec.type);
            return (
              <div
                key={`${rec.type}-${index}`}
                className={`border-2 rounded-lg sm:rounded-xl p-3 sm:p-4 transition-all duration-200 hover:shadow-md ${getPriorityColor(rec.priority)}`}
              >
                <div className="flex items-start space-x-3 sm:space-x-4">
                  <div className={`${getTypeColor(rec.type)} p-2 rounded-lg flex-shrink-0`}>
                    <TypeIcon className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2 space-y-1 sm:space-y-0">
                      <h3 className="font-semibold text-gray-900 text-sm sm:text-base">{rec.title}</h3>
                      <div className="flex items-center space-x-2 flex-shrink-0">
                        <span className={`text-xs font-medium px-2 py-1 rounded-full ${getPriorityTextColor(rec.priority)} bg-white/50`}>
                          {rec.priority.toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-600 bg-white/50 px-2 py-1 rounded-full">
                          {rec.confidence}% confidence
                        </span>
                      </div>
                    </div>
                    
                    <p className="text-gray-700 text-xs sm:text-sm mb-2 leading-relaxed">{rec.description}</p>
                    
                    <div className="bg-white/70 rounded-lg p-2 sm:p-3 mb-3">
                      <p className="text-xs text-gray-600">
                        <strong>AI Reasoning:</strong> {rec.reasoning}
                      </p>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-500 capitalize">{rec.type} recommendation</span>
                        {rec.actionable && (
                          <div className="flex items-center space-x-1">
                            <CheckCircle className="h-3 w-3 text-green-500" />
                            <span className="text-xs text-green-600 font-medium">Actionable</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        {source === 'watsonx' ? (
                          <>
                            <Zap className="h-3 w-3 text-indigo-500" />
                            <span className="text-xs text-indigo-600 font-medium">WatsonX AI</span>
                          </>
                        ) : (
                          <>
                            <TrendingUp className="h-3 w-3 text-yellow-500" />
                            <span className="text-xs text-yellow-600 font-medium">Fallback AI</span>
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

      <div className="mt-4 sm:mt-6 pt-3 sm:pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${source === 'watsonx' ? 'bg-indigo-400 animate-pulse' : 'bg-yellow-400'}`}></div>
            <span>
              {source === 'watsonx' ? 'Powered by IBM WatsonX AI' : 'Fallback recommendation system'}
            </span>
          </div>
          <span>
            {hasLoadedOnce ? 'Click refresh for new insights' : 'Auto-generated on first load'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default AIRecommendations;