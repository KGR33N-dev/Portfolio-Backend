import { useTranslations } from './i18n/utils';
import { languages } from './i18n';

type SupportedLanguage = keyof typeof languages;

// Function to get navigation data based on language
export const getHeaderData = (lang: SupportedLanguage) => {
  const t = useTranslations(lang);
  
  return {
    links: [
      {
        text: t('nav.portfolio'),
        href: `/${lang}`,
      },
      {
        text: t('nav.blog'),
        href: `/${lang}/blog`,
      },
      {
        text: t('nav.contact'),
        href: `/${lang}/contact`,
      },
    ],
  };
};

export const getFooterData = (lang: SupportedLanguage) => {
  const t = useTranslations(lang);
  
  return {
    links: [
    ],
    secondaryLinks: [
      { 
        text: t('footer.terms'), 
        href: `/${lang}/terms`
      },
      { 
        text: t('footer.privacy'), 
        href: `/${lang}/privacy`
      },
    ],
    socialLinks: [
      { ariaLabel: 'X', icon: 'tabler:brand-x', href: 'https://x.com/KGR33N_' },
    ],
  };
};
