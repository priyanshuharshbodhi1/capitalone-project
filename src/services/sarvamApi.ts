/**
 * Sarvam AI Translation API Service
 * 
 * This service handles translation of AI responses from English to Indian languages
 * using Sarvam AI's translation API for better accuracy in agricultural terminology.
 */

interface SarvamTranslateRequest {
  input: string;
  source_language_code: string;
  target_language_code: string;
  speaker_gender?: 'Male' | 'Female';
  mode?: 'formal' | 'informal';
  model?: 'mayura:v1' | 'mayura:v2';
}

interface SarvamTranslateResponse {
  translated_text: string;
  audio_url?: string;
}

class SarvamAPI {
  private apiKey: string | null = null;
  private baseUrl = 'https://api.sarvam.ai';

  constructor() {
    this.apiKey = import.meta.env.VITE_SARVAM_API_KEY || null;
  }

  private isConfigured(): boolean {
    return !!this.apiKey;
  }

  /**
   * Language mapping from our i18n codes to Sarvam language codes
   */
  private getLanguageMapping(langCode: string): string {
    const mapping: Record<string, string> = {
      'en': 'en-IN',      // English (India)
      'hi': 'hi-IN',      // Hindi
      'mr': 'mr-IN',      // Marathi
      'gu': 'gu-IN',      // Gujarati
      'ta': 'ta-IN',      // Tamil
      'te': 'te-IN',      // Telugu
      'kn': 'kn-IN',      // Kannada
      'bn': 'bn-IN',      // Bengali
      'pa': 'pa-IN',      // Punjabi
    };
    
    return mapping[langCode] || 'en-IN';
  }

  /**
   * Translate text from English to target language
   */
  async translateText(
    text: string, 
    targetLanguage: string, 
    options: Partial<SarvamTranslateRequest> = {}
  ): Promise<string> {
    if (!this.isConfigured()) {
      console.warn('⚠️ SarvamAPI: API key not configured, returning original text');
      return text;
    }

    if (targetLanguage === 'en') {
      // No translation needed for English
      return text;
    }

    try {
      const targetLangCode = this.getLanguageMapping(targetLanguage);
      
      const requestBody: SarvamTranslateRequest = {
        input: text,
        source_language_code: 'en-IN',
        target_language_code: targetLangCode,
        speaker_gender: 'Male',
        mode: 'formal',
        model: 'mayura:v1',
        ...options,
      };

      console.log('🌍 SarvamAPI: Translating text to', targetLangCode);
      
      const response = await fetch(`${this.baseUrl}/translate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`Translation API error: ${response.status}`);
      }

      const data: SarvamTranslateResponse = await response.json();
      
      console.log('✅ SarvamAPI: Translation completed');
      return data.translated_text;
      
    } catch (error) {
      console.error('❌ SarvamAPI: Translation failed:', error);
      // Fallback to original text if translation fails
      return text;
    }
  }

  /**
   * Translate AI recommendations array
   */
  async translateRecommendations(
    recommendations: Array<{ 
      id: string; 
      text: string; 
      confidence: number; 
      reasoning: string;
      priority: string;
    }>, 
    targetLanguage: string
  ): Promise<Array<{ 
    id: string; 
    text: string; 
    confidence: number; 
    reasoning: string;
    priority: string;
  }>> {
    if (targetLanguage === 'en') {
      return recommendations;
    }

    try {
      // Translate all recommendations in parallel
      const translatedRecommendations = await Promise.all(
        recommendations.map(async (rec) => ({
          ...rec,
          text: await this.translateText(rec.text, targetLanguage),
          reasoning: await this.translateText(rec.reasoning, targetLanguage),
        }))
      );

      console.log(`✅ SarvamAPI: Translated ${recommendations.length} recommendations to ${targetLanguage}`);
      return translatedRecommendations;

    } catch (error) {
      console.error('❌ SarvamAPI: Failed to translate recommendations:', error);
      return recommendations; // Return original if translation fails
    }
  }

  /**
   * Translate chat messages
   */
  async translateChatMessage(message: string, targetLanguage: string): Promise<string> {
    return this.translateText(message, targetLanguage, {
      mode: 'informal', // More conversational for chat
    });
  }

  /**
   * Get supported languages
   */
  getSupportedLanguages(): Array<{ code: string; name: string; nativeName: string }> {
    return [
      { code: 'en', name: 'English', nativeName: 'English' },
      { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी' },
      { code: 'mr', name: 'Marathi', nativeName: 'मराठी' },
      { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી' },
      { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்' },
      { code: 'te', name: 'Telugu', nativeName: 'తెలుగు' },
      { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ' },
      { code: 'bn', name: 'Bengali', nativeName: 'বাংলা' },
      { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ' },
    ];
  }

  /**
   * Check API configuration status
   */
  getConfigStatus() {
    return {
      configured: this.isConfigured(),
      hasApiKey: !!this.apiKey,
      supportedLanguages: this.getSupportedLanguages().length,
    };
  }
}

export const sarvamApi = new SarvamAPI();
export type { SarvamTranslateRequest, SarvamTranslateResponse };
