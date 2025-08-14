import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files
import english from './locales/english.json';
import hindi from './locales/hindi.json';
import marathi from './locales/marathi.json';
import assamese from './locales/assamese.json';
import bengali from './locales/bengali.json';
import bodo from './locales/bodo.json';
import dogri from './locales/dogri.json';
import gujarati from './locales/gujarati.json';
import kannada from './locales/kannada.json';
import kashmiri from './locales/kashmiri.json';
import konkani from './locales/konkani.json';
import maithili from './locales/maithili.json';
import malayalam from './locales/malayalam.json';
import manipuri from './locales/manipuri.json';
import nepali from './locales/nepali.json';
import odia from './locales/odia.json';
import punjabi from './locales/punjabi.json';
import sanskrit from './locales/sanskrit.json';
import santali from './locales/santali.json';
import sindhi from './locales/sindhi.json';
import tamil from './locales/tamil.json';
import telugu from './locales/telugu.json';
import urdu from './locales/urdu.json';

const resources = {
  english: {
    translation: english,
  },
  hindi: {
    translation: hindi,
  },
  marathi: {
    translation: marathi,
  },
  assamese: {
    translation: assamese,
  },
  bengali: {
    translation: bengali,
  },
  bodo: {
    translation: bodo,
  },
  dogri: {
    translation: dogri,
  },
  gujarati: {
    translation: gujarati,
  },
  kannada: {
    translation: kannada,
  },
  kashmiri: {
    translation: kashmiri,
  },
  konkani: {
    translation: konkani,
  },
  maithili: {
    translation: maithili,
  },
  malayalam: {
    translation: malayalam,
  },
  manipuri: {
    translation: manipuri,
  },
  nepali: {
    translation: nepali,
  },
  odia: {
    translation: odia,
  },
  punjabi: {
    translation: punjabi,
  },
  sanskrit: {
    translation: sanskrit,
  },
  santali: {
    translation: santali,
  },
  sindhi: {
    translation: sindhi,
  },
  tamil: {
    translation: tamil,
  },
  telugu: {
    translation: telugu,
  },
  urdu: {
    translation: urdu,
  },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'english',
    debug: process.env.NODE_ENV === 'development',
    
    interpolation: {
      escapeValue: false, // React already escapes values
    },
    
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
    },
  });

export default i18n;
