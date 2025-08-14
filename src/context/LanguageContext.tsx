import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { supabaseApi } from '../services/supabaseApi';
import { useAuth } from './AuthContext';

type Language = 'en' | 'mr' | 'hi';

interface LanguageContextType {
  currentLanguage: Language;
  changeLanguage: (language: Language) => Promise<void>;
  languages: { code: Language; name: string; nativeName: string }[];
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

interface LanguageProviderProps {
  children: ReactNode;
}

// Define languages outside component to prevent re-creation
const LANGUAGES = [
  { code: 'en' as Language, name: 'English', nativeName: 'English' },
  { code: 'mr' as Language, name: 'Marathi', nativeName: 'मराठी' },
  { code: 'hi' as Language, name: 'Hindi', nativeName: 'हिन्दी' },
];

export const LanguageProvider: React.FC<LanguageProviderProps> = ({ children }) => {
  const { i18n } = useTranslation();
  const { user } = useAuth();
  
  // Initialize with saved language immediately
  const [currentLanguage, setCurrentLanguage] = useState<Language>(() => {
    const saved = localStorage.getItem('userLanguage') as Language;
    return (saved && LANGUAGES.some(lang => lang.code === saved)) ? saved : 'en';
  });

  // Set initial language immediately
  useEffect(() => {
    const savedLanguage = localStorage.getItem('userLanguage') as Language;
    if (savedLanguage && LANGUAGES.some(lang => lang.code === savedLanguage)) {
      i18n.changeLanguage(savedLanguage);
    }
  }, []); // Run once on mount

  // Load user's language preference on mount
  useEffect(() => {
    const loadUserLanguage = async () => {
      // First, always check localStorage for immediate loading
      const savedLanguage = localStorage.getItem('userLanguage') as Language;
      
      if (savedLanguage && LANGUAGES.some(lang => lang.code === savedLanguage)) {
        setCurrentLanguage(savedLanguage);
        await i18n.changeLanguage(savedLanguage);
        
        // If we have a saved language, that's our priority
        if (user) {
          try {
            const userData = await supabaseApi.getCurrentUser();
            if (userData?.language && userData.language !== savedLanguage) {
              // Only update if Supabase has a more recent change
              // For now, prioritize localStorage unless there's a specific reason to override
            }
          } catch (error) {
            console.warn('Could not load user language preference from Supabase:', error);
          }
        }
        return; // Exit early - we have a valid saved language
      }

      // If no saved language, try to get from Supabase (user logged in)
      if (user) {
        try {
          const userData = await supabaseApi.getCurrentUser();
          if (userData?.language) {
            const userLanguage = userData.language as Language;
            if (LANGUAGES.some(lang => lang.code === userLanguage)) {
              setCurrentLanguage(userLanguage);
              await i18n.changeLanguage(userLanguage);
              localStorage.setItem('userLanguage', userLanguage);
              return;
            }
          }
        } catch (error) {
          console.warn('Could not load user language preference from Supabase:', error);
        }
      }

      // Final fallback - only if no saved language anywhere
      const browserLanguage = navigator.language.split('-')[0] as Language;
      const languageToUse = 
        (LANGUAGES.some(lang => lang.code === browserLanguage)) ? browserLanguage : 'en';
      
      setCurrentLanguage(languageToUse);
      await i18n.changeLanguage(languageToUse);
      localStorage.setItem('userLanguage', languageToUse);
    };

    loadUserLanguage();
  }, [user]); // Removed i18n from dependencies to prevent infinite loops

  const changeLanguage = async (language: Language) => {
    try {
      // Update local state and i18n immediately
      setCurrentLanguage(language);
      await i18n.changeLanguage(language);
      
      // Save to localStorage as backup
      localStorage.setItem('userLanguage', language);

      // Save to Supabase if user is logged in
      if (user) {
        try {
          await supabaseApi.updateProfile({ language });
          console.log('Language preference saved to Supabase');
        } catch (error) {
          console.warn('Could not save language preference to Supabase:', error);
          // Continue anyway since local storage backup exists
        }
      }
    } catch (error) {
      console.error('Error changing language:', error);
    }
  };

  const value: LanguageContextType = {
    currentLanguage,
    changeLanguage,
    languages: LANGUAGES,
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};
