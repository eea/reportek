import Vue from 'vue';
import VueI18n from 'vue-i18n';
import { getTranslationForLanguage, setApiLang } from '../api/i18n_api'

Vue.use(VueI18n);

export const i18n = new VueI18n({
  locale: window.navigator.language || 'en', // set locale
  fallbackLocale: 'en',
});

const loadedLanguages = ['en']; // our default language that is prelaoded

// IIFE (Immediately Invoked Function Expression) to get english
(function () {
  getTranslationForLanguage('en')
    .then(msgs => {
      i18n.setLocaleMessage('en', msgs);
      loadedLanguages.push('en');
      setI18nLanguage('en');
    })
})();

/**
 * will set the language for axios and locale in i18n object
 * @param {string} lang 
 */
function setI18nLanguage(lang) {
  i18n.locale = lang;
  setApiLang(lang);

  return lang;
}

/**
 * will load from server the messages from server if they haved been already loaded
 * @param {string} lang 
 */
export function loadLanguageAsync(lang) {
  if(!lang) {
    return Promise.resolve(lang);
  }

  lang = lang.toLowerCase();

  if (i18n.locale !== lang) {
    if (!loadedLanguages.includes(lang)) {
      return getTranslationForLanguage(lang)
        .then(msgs => {
          i18n.setLocaleMessage(lang, msgs);
          loadedLanguages.push(lang);
          return setI18nLanguage(lang);
        });
    }
    return Promise.resolve(setI18nLanguage(lang));
  }
  return Promise.resolve(lang);
}