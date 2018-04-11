/* eslint-disable */
import { fetch } from './config_api';
import axios from 'axios';


const langMessages = {
  'en-US': {
    'reporting_for': 'Reporting for',
    'country_question': 'Which country are you reporting for?',
    'envelope_status': 'Envelope Status',
  },
  'en': {
    'reporting_for': 'Reporting for',
    'country_question': 'Which country are you reporting for?',
    'envelope_status': 'Envelope Status',
  },
  'fr': {
    'reporting_for': 'Rapport pour',
    'country_question': 'Pour quel pays déclarez-vous?',
    'envelope_status': "Statut de l'enveloppe",
  }
}
const languages = {
  en : {
    lang: 'en-US',
    text: 'En'
  }, 
  ja: { 
    lang: 'fr',
    text: 'Fr'
  }};

export function getTranslationForLanguage(id) {
  return new Promise((resolve, reject) => {
    resolve(langMessages[id] || langMessages['en']);
  });
}

export function setApiLang(lang) {
  axios.defaults.headers.common['Accept-Language'] = lang;
}

export function getSupportedLanguages() {
  return Promise.resolve(languages);
}
