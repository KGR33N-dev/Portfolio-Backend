import { commonTranslations } from './common';
import { homeTranslations } from './pages/home';
import { blogTranslations } from './pages/blog';
import { contactTranslations } from './pages/contact';
import { privacyTranslations } from './pages/privacy';
import { termsTranslations } from './pages/terms';
import { errorTranslations } from './pages/error';
import { notificationTranslations } from './pages/notifications';

export const languages = {
  en: 'English',
  pl: 'Polski',
};

export const showDefaultLang = true;

export const defaultLang = 'en';

// Łączenie wszystkich tłumaczeń
export const ui = {
  en: {
    ...commonTranslations.en,
    ...homeTranslations.en,
    ...blogTranslations.en,
    ...contactTranslations.en,
    ...privacyTranslations.en,
    ...termsTranslations.en,
    ...errorTranslations.en,
    ...notificationTranslations.en,
  },
  pl: {
    ...commonTranslations.pl,
    ...homeTranslations.pl,
    ...blogTranslations.pl,
    ...contactTranslations.pl,
    ...privacyTranslations.pl,
    ...termsTranslations.pl,
    ...errorTranslations.pl,
    ...notificationTranslations.pl,
  },
} as const;
