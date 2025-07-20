export const supportedLanguages = ['en', 'pl'] as const;
export type SupportedLanguage = typeof supportedLanguages[number];

export function detectLanguage(acceptLanguageHeader?: string): SupportedLanguage {
  if (!acceptLanguageHeader) return 'en';

  // Parse Accept-Language header
  const languages = acceptLanguageHeader
    .split(',')
    .map(lang => {
      const [code, q = '1'] = lang.trim().split(';q=');
      return {
        code: code.trim().toLowerCase().split('-')[0], // Get primary language code
        quality: parseFloat(q)
      };
    })
    .sort((a, b) => b.quality - a.quality); // Sort by preference

  // Find the first supported language
  for (const lang of languages) {
    if (supportedLanguages.includes(lang.code as SupportedLanguage)) {
      return lang.code as SupportedLanguage;
    }
  }

  return 'en'; // Default fallback
}

export function shouldRedirect(currentPath: string, detectedLang: SupportedLanguage): boolean {
  // Don't redirect if already on correct language path
  if (currentPath === '/' && detectedLang === 'en') return false;
  if (currentPath.startsWith('/pl') && detectedLang === 'pl') return false;
  if (currentPath.startsWith('/en') && detectedLang === 'en') return false;
  
  // Don't redirect if user has visited before (check for cookie)
  return true;
}

export function getRedirectPath(currentPath: string, targetLang: SupportedLanguage): string {
if (targetLang === 'en') {
    // Remove /pl prefix if present
    return currentPath.replace(/^\/pl(\/|$)/, '/') || '/';
} else {
    // Add /pl prefix if not present
    if (currentPath === '/' || currentPath === '') return '/pl';
    if (currentPath.startsWith('/pl')) return currentPath;
    return `/pl${currentPath}`;
}
}
