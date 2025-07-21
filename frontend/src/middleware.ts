import { defineMiddleware } from 'astro:middleware';

export const onRequest = defineMiddleware((context, next) => {
  // For static sites, skip server-side language detection
  return next();
});
