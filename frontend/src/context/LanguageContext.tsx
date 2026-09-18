import React, { createContext, useContext, useState, useEffect } from 'react';
import { Language } from '../types';
import { translations } from '../i18n/translations';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, fallback?: string) => string;
  isLanguageModalOpen: boolean;
  setIsLanguageModalOpen: (open: boolean) => void;
  translateDynamic: (text: string) => Promise<string>;
  isTranslating: boolean;
  isSimpleMode: boolean;
  setIsSimpleMode: (simple: boolean) => void;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('weathergpt_preferred_lang');
    if (saved === 'pa' || saved === 'hi' || saved === 'en') {
      return saved;
    }
    return 'en'; // Default to English for new users
  });

  const [isSimpleMode, setIsSimpleModeState] = useState<boolean>(() => {
    const saved = localStorage.getItem('weathergpt_simple_mode');
    return saved !== null ? saved === 'true' : true; // Default to true for uneducated / low-literacy clarity
  });

  const setIsSimpleMode = (val: boolean) => {
    setIsSimpleModeState(val);
    localStorage.setItem('weathergpt_simple_mode', String(val));
  };

  const [isLanguageModalOpen, setIsLanguageModalOpen] = useState<boolean>(false);

  const [isTranslating, setIsTranslating] = useState<boolean>(false);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('weathergpt_preferred_lang', lang);
  };

  const t = (key: string, fallback?: string): string => {
    const langDict = translations[language];
    if (langDict && langDict[key]) {
      return langDict[key];
    }
    const enDict = translations['en'];
    if (enDict && enDict[key]) {
      return enDict[key];
    }
    return fallback || key;
  };

  const translateDynamic = async (text: string): Promise<string> => {
    if (!text || language === 'en') return text;
    try {
      setIsTranslating(true);
      const res = await fetch('/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, targetLanguage: language }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.translatedText) {
          return data.translatedText;
        }
      }
    } catch (err) {
      console.warn('Translation API fallback:', err);
    } finally {
      setIsTranslating(false);
    }
    return text;
  };

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        t,
        isLanguageModalOpen,
        setIsLanguageModalOpen,
        translateDynamic,
        isTranslating,
        isSimpleMode,
        setIsSimpleMode,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
