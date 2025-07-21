// Client-side language detection for static sites
(function() {
  // Only run on initial page load
  if (document.documentElement.getAttribute('data-language-detected') === 'true') {
    return;
  }

  // Mark that language detection has been run
  document.documentElement.setAttribute('data-language-detected', 'true');

  // Check if user has manually clicked a language switcher recently
  const manualChoice = sessionStorage.getItem('manual-language-choice');
  if (manualChoice) {
    return; // Don't auto-detect if user made manual choice this session
  }

  // Check if user has a saved preference
  const savedLanguage = getCookie('preferred-language');
  if (savedLanguage && (savedLanguage === 'en' || savedLanguage === 'pl')) {
    return; // User has preference, don't auto-detect
  }

  // Get browser language
  const browserLanguage = navigator.language || navigator.languages?.[0];
  if (!browserLanguage) return;

  const primaryLang = browserLanguage.toLowerCase().split('-')[0];
  const currentPath = window.location.pathname;

  // Detect if we should redirect based on browser language
  let shouldRedirect = false;
  let targetPath = currentPath;

  if (primaryLang === 'pl' && !currentPath.startsWith('/pl')) {
    // User prefers Polish but is on English site
    shouldRedirect = true;
    targetPath = currentPath === '/' ? '/pl' : '/pl' + currentPath;
  } else if (primaryLang !== 'pl' && currentPath.startsWith('/pl')) {
    // User doesn't prefer Polish but is on Polish site
    shouldRedirect = true;
    targetPath = currentPath.replace('/pl', '') || '/';
  }

  // Redirect if needed
  if (shouldRedirect && targetPath !== currentPath) {
    // Set cookie to remember the detected preference
    setCookie('preferred-language', primaryLang === 'pl' ? 'pl' : 'en', 30);
    
    // Add a small delay to ensure the page is ready
    setTimeout(() => {
      window.location.href = targetPath;
    }, 100);
  }

  // Helper functions
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }

  function setCookie(name, value, days) {
    const expires = new Date(Date.now() + days * 24 * 60 * 60 * 1000).toUTCString();
    document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Lax`;
  }
})();
