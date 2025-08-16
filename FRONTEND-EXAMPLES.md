# 🎨 Frontend Integration Examples

Przykłady integracji Portfolio Backend API z różnymi frameworkami frontend.

## 📋 Spis treści
- [JavaScript/TypeScript](#javascript-typescript)
- [React Examples](#react-examples)
- [Vue.js Examples](#vuejs-examples)
- [Astro Examples](#astro-examples)
- [API Client Setup](#api-client-setup)

## 🔧 JavaScript/TypeScript

### API Client Configuration

```typescript
// api/client.ts
interface ApiConfig {
  baseUrl: string;
  timeout?: number;
}

class ApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor(config: ApiConfig) {
    this.baseUrl = config.baseUrl;
    this.loadTokensFromStorage();
  }

  private loadTokensFromStorage() {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  private saveTokens(accessToken: string, refreshToken?: string) {
    this.accessToken = accessToken;
    localStorage.setItem('access_token', accessToken);
    
    if (refreshToken) {
      this.refreshToken = refreshToken;
      localStorage.setItem('refresh_token', refreshToken);
    }
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    // Dodaj token autoryzacji jeśli dostępny
    if (this.accessToken) {
      config.headers = {
        ...config.headers,
        'Authorization': `Bearer ${this.accessToken}`,
      };
    }

    const response = await fetch(url, config);

    // Obsługa wygasłego tokenu
    if (response.status === 401 && this.refreshToken) {
      const newToken = await this.refreshAccessToken();
      if (newToken) {
        // Ponów żądanie z nowym tokenem
        config.headers = {
          ...config.headers,
          'Authorization': `Bearer ${newToken}`,
        };
        return this.request(endpoint, config);
      }
    }

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  private async refreshAccessToken(): Promise<string | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: this.refreshToken,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        this.saveTokens(data.access_token, data.refresh_token);
        return data.access_token;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }

    // Wyloguj użytkownika jeśli refresh nie udał się
    this.logout();
    return null;
  }

  // Auth methods
  async register(userData: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
  }) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async verifyEmail(email: string, code: string) {
    return this.request('/api/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({
        email,
        verification_code: code,
      }),
    });
  }

  async login(email: string, password: string) {
    const formData = new FormData();
    formData.append('username', email); // OAuth2 standard
    formData.append('password', password);

    const response = await fetch(`${this.baseUrl}/api/auth/login`, {
      method: 'POST',
      body: formData,
    });

    if (response.ok) {
      const data = await response.json();
      this.saveTokens(data.access_token, data.refresh_token);
      return data;
    }

    throw new Error('Login failed');
  }

  async logout() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  async getProfile() {
    return this.request('/api/auth/me');
  }

  // Blog methods
  async getBlogPosts(params?: {
    page?: number;
    per_page?: number;
    category?: string;
    language?: string;
    search?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }

    return this.request(`/api/blog/?${searchParams.toString()}`);
  }

  async getBlogPost(slug: string) {
    return this.request(`/api/blog/${slug}`);
  }

  async createBlogPost(postData: {
    title: string;
    content: string;
    slug: string;
    excerpt?: string;
    category?: string;
    tags?: string[];
  }) {
    return this.request('/api/blog/', {
      method: 'POST',
      body: JSON.stringify(postData),
    });
  }

  // Utility methods
  isAuthenticated(): boolean {
    return !!this.accessToken;
  }
}

// Export singleton instance
export const apiClient = new ApiClient({
  baseUrl: process.env.NODE_ENV === 'production' 
    ? 'https://your-api-domain.com' 
    : 'http://localhost:8000'
});
```

## ⚛️ React Examples

### Authentication Hook

```typescript
// hooks/useAuth.ts
import { useState, useEffect, useContext, createContext } from 'react';
import { apiClient } from '../api/client';

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  email_verified: boolean;
  // New role-based system
  role: {
    id: number;
    name: string; // "user" | "admin" | "moderator"
    display_name: string;
    color: string;
    permissions: string[];
    level: number;
  } | null;
  rank: {
    id: number;
    name: string; // "newbie" | "regular" | "trusted" | "star" | "legend" | "vip"
    display_name: string;
    icon: string;
    color: string;
    level: number;
  } | null;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  verifyEmail: (email: string, code: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if user is already logged in
    if (apiClient.isAuthenticated()) {
      loadUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  const loadUser = async () => {
    try {
      const userData = await apiClient.getProfile();
      setUser(userData);
    } catch (error) {
      console.error('Failed to load user:', error);
      apiClient.logout();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const loginData = await apiClient.login(email, password);
      setUser(loginData.user);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Login failed');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterData) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await apiClient.register(userData);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Registration failed');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const verifyEmail = async (email: string, code: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await apiClient.verifyEmail(email, code);
      // Po weryfikacji możesz przekierować do logowania
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Verification failed');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    apiClient.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      login,
      register,
      logout,
      verifyEmail,
      isLoading,
      error,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### Login Component

```tsx
// components/LoginForm.tsx
import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await login(email, password);
      // Redirect after successful login
    } catch (error) {
      // Error is handled by the hook
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-sm font-medium">
          Email
        </label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="mt-1 block w-full rounded-md border-gray-300"
        />
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium">
          Password
        </label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="mt-1 block w-full rounded-md border-gray-300"
        />
      </div>

      {error && (
        <div className="text-red-600 text-sm">{error}</div>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="w-full py-2 px-4 bg-blue-600 text-white rounded-md disabled:opacity-50"
      >
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

### Blog Posts Hook

```typescript
// hooks/useBlog.ts
import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface BlogPost {
  id: number;
  title: string;
  content: string;
  excerpt?: string;
  slug: string;
  author: string;
  category: string;
  language: string;
  is_published: boolean;
  published_at?: string;
  created_at: string;
  updated_at: string;
  tags: string[];
  meta_title?: string;
  meta_description?: string;
}

interface BlogResponse {
  items: BlogPost[];
  total: number;
  page: number;
  pages: number;
  per_page: number;
}

export function useBlog(params?: {
  page?: number;
  per_page?: number;
  category?: string;
  language?: string;
  search?: string;
}) {
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    pages: 0,
    per_page: 10,
  });

  useEffect(() => {
    loadPosts();
  }, [params]);

  const loadPosts = async () => {
    setLoading(true);
    setError(null);

    try {
      const response: BlogResponse = await apiClient.getBlogPosts(params);
      setPosts(response.items);
      setPagination({
        total: response.total,
        page: response.page,
        pages: response.pages,
        per_page: response.per_page,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load posts');
    } finally {
      setLoading(false);
    }
  };

  return {
    posts,
    loading,
    error,
    pagination,
    refetch: loadPosts,
  };
}

export function useBlogPost(slug: string) {
  const [post, setPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (slug) {
      loadPost();
    }
  }, [slug]);

  const loadPost = async () => {
    setLoading(true);
    setError(null);

    try {
      const postData = await apiClient.getBlogPost(slug);
      setPost(postData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load post');
    } finally {
      setLoading(false);
    }
  };

  return { post, loading, error, refetch: loadPost };
}
```

## 🟢 Vue.js Examples

### Composable for Authentication

```typescript
// composables/useAuth.ts
import { ref, computed } from 'vue';
import { apiClient } from '../api/client';

const user = ref(null);
const isLoading = ref(false);
const error = ref(null);

export function useAuth() {
  const isAuthenticated = computed(() => !!user.value);

  const login = async (email: string, password: string) => {
    isLoading.value = true;
    error.value = null;

    try {
      const loginData = await apiClient.login(email, password);
      user.value = loginData.user;
      return loginData;
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  const logout = () => {
    apiClient.logout();
    user.value = null;
  };

  const loadUser = async () => {
    if (!apiClient.isAuthenticated()) return;

    try {
      const userData = await apiClient.getProfile();
      user.value = userData;
    } catch (err) {
      logout();
    }
  };

  return {
    user: readonly(user),
    isAuthenticated,
    isLoading: readonly(isLoading),
    error: readonly(error),
    login,
    logout,
    loadUser,
  };
}
```

### Vue Login Component

```vue
<!-- components/LoginForm.vue -->
<template>
  <form @submit.prevent="handleLogin" class="space-y-4">
    <div>
      <label for="email">Email</label>
      <input
        v-model="email"
        type="email"
        id="email"
        required
        class="w-full p-2 border rounded"
      />
    </div>

    <div>
      <label for="password">Password</label>
      <input
        v-model="password"
        type="password"
        id="password"
        required
        class="w-full p-2 border rounded"
      />
    </div>

    <div v-if="error" class="text-red-600">
      {{ error }}
    </div>

    <button
      type="submit"
      :disabled="isLoading"
      class="w-full py-2 bg-blue-600 text-white rounded disabled:opacity-50"
    >
      {{ isLoading ? 'Logging in...' : 'Login' }}
    </button>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useAuth } from '../composables/useAuth';
import { useRouter } from 'vue-router';

const email = ref('');
const password = ref('');
const router = useRouter();

const { login, isLoading, error } = useAuth();

const handleLogin = async () => {
  try {
    await login(email.value, password.value);
    router.push('/dashboard');
  } catch (err) {
    // Error is handled by the composable
  }
};
</script>
```

## 🚀 Astro Examples

### API Service for Astro

```typescript
// src/lib/api.ts
export class PortfolioAPI {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async getBlogPosts(params?: {
    page?: number;
    category?: string;
    language?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const response = await fetch(
      `${this.baseUrl}/api/blog/?${searchParams.toString()}`
    );
    
    if (!response.ok) {
      throw new Error(`Failed to fetch blog posts: ${response.statusText}`);
    }

    return response.json();
  }

  async getBlogPost(slug: string) {
    const response = await fetch(`${this.baseUrl}/api/blog/${slug}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch blog post: ${response.statusText}`);
    }

    return response.json();
  }
}

export const api = new PortfolioAPI(
  import.meta.env.PROD 
    ? 'https://your-api-domain.com'
    : 'http://localhost:8000'
);
```

### Astro Blog Page

```astro
---
// src/pages/blog/index.astro
import { api } from '../../lib/api';
import Layout from '../../layouts/Layout.astro';

const currentPage = Number(Astro.url.searchParams.get('page')) || 1;
const category = Astro.url.searchParams.get('category') || undefined;
const language = Astro.url.searchParams.get('language') || 'pl';

let blogData;
try {
  blogData = await api.getBlogPosts({
    page: currentPage,
    category,
    language,
    per_page: 10,
  });
} catch (error) {
  console.error('Failed to load blog posts:', error);
  blogData = { items: [], total: 0, page: 1, pages: 1 };
}

const { items: posts, pagination } = blogData;
---

<Layout title="Blog">
  <main class="container mx-auto px-4 py-8">
    <h1 class="text-4xl font-bold mb-8">Blog</h1>
    
    <!-- Category Filter -->
    <div class="mb-6">
      <select onchange="window.location.href = `?category=${this.value}&language=${language}`">
        <option value="">All Categories</option>
        <option value="programming" selected={category === 'programming'}>Programming</option>
        <option value="tutorial" selected={category === 'tutorial'}>Tutorial</option>
        <option value="personal" selected={category === 'personal'}>Personal</option>
      </select>
    </div>

    <!-- Blog Posts -->
    <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {posts.map((post) => (
        <article class="bg-white rounded-lg shadow-md overflow-hidden">
          <div class="p-6">
            <h2 class="text-xl font-semibold mb-2">
              <a href={`/blog/${post.slug}`} class="hover:text-blue-600">
                {post.title}
              </a>
            </h2>
            
            {post.excerpt && (
              <p class="text-gray-600 mb-4">{post.excerpt}</p>
            )}
            
            <div class="flex items-center justify-between text-sm text-gray-500">
              <span>{new Date(post.published_at).toLocaleDateString()}</span>
              <span class="bg-gray-100 px-2 py-1 rounded">{post.category}</span>
            </div>
            
            {post.tags && post.tags.length > 0 && (
              <div class="mt-3 flex flex-wrap gap-1">
                {post.tags.map((tag) => (
                  <span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </article>
      ))}
    </div>

    <!-- Pagination -->
    {pagination.pages > 1 && (
      <div class="mt-8 flex justify-center gap-2">
        {Array.from({ length: pagination.pages }, (_, i) => i + 1).map((page) => (
          <a
            href={`?page=${page}${category ? `&category=${category}` : ''}${language ? `&language=${language}` : ''}`}
            class={`px-3 py-2 rounded ${
              page === currentPage
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 hover:bg-gray-300'
            }`}
          >
            {page}
          </a>
        ))}
      </div>
    )}
  </main>
</Layout>
```

### Single Blog Post Page

```astro
---
// src/pages/blog/[slug].astro
import { api } from '../../lib/api';
import Layout from '../../layouts/Layout.astro';

const { slug } = Astro.params;

let post;
try {
  post = await api.getBlogPost(slug);
} catch (error) {
  console.error(`Failed to load blog post ${slug}:`, error);
  return Astro.redirect('/404');
}

if (!post) {
  return Astro.redirect('/404');
}
---

<Layout title={post.meta_title || post.title}>
  <article class="container mx-auto px-4 py-8 max-w-4xl">
    <header class="mb-8">
      <h1 class="text-4xl font-bold mb-4">{post.title}</h1>
      
      <div class="flex items-center gap-4 text-gray-600 mb-4">
        <span>By {post.author}</span>
        <span>•</span>
        <time datetime={post.published_at}>
          {new Date(post.published_at).toLocaleDateString('pl-PL')}
        </time>
        <span>•</span>
        <span class="bg-gray-100 px-2 py-1 rounded text-sm">
          {post.category}
        </span>
      </div>

      {post.tags && post.tags.length > 0 && (
        <div class="flex flex-wrap gap-2">
          {post.tags.map((tag) => (
            <span class="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
              #{tag}
            </span>
          ))}
        </div>
      )}
    </header>

    <div class="prose prose-lg max-w-none" set:html={post.content} />

    <footer class="mt-12 pt-8 border-t">
      <div class="flex justify-between items-center">
        <a
          href="/blog"
          class="text-blue-600 hover:text-blue-800 font-medium"
        >
          ← Back to Blog
        </a>
        
        <div class="text-sm text-gray-500">
          Last updated: {new Date(post.updated_at).toLocaleDateString('pl-PL')}
        </div>
      </div>
    </footer>
  </article>
</Layout>
```

## 🛠️ Utility Functions

### Permission Checking

```typescript
// utils/permissions.ts
interface User {
  role: {
    id: number;
    name: string; // "user" | "admin" | "moderator"
    display_name: string;
    color: string;
    permissions: string[];
    level: number;
  } | null;
  rank: {
    id: number;
    name: string;
    display_name: string;
    icon: string;
    color: string;
    level: number;
  } | null;
}

export const permissions = {
  // Sprawdź czy użytkownik ma konkretną rolę
  hasRole: (user: User | null, roleName: string): boolean => {
    return user?.role?.name === roleName;
  },

  // Sprawdź czy użytkownik jest administratorem
  isAdmin: (user: User | null): boolean => {
    return permissions.hasRole(user, 'admin');
  },

  // Sprawdź czy użytkownik jest moderatorem
  isModerator: (user: User | null): boolean => {
    return permissions.hasRole(user, 'moderator');
  },

  // Sprawdź czy użytkownik ma uprawnienia administratora lub moderatora
  isAdminOrModerator: (user: User | null): boolean => {
    return permissions.isAdmin(user) || permissions.isModerator(user);
  },

  // Sprawdź czy użytkownik ma konkretne uprawnienie
  hasPermission: (user: User | null, permission: string): boolean => {
    if (!user?.role?.permissions) return false;
    return user.role.permissions.includes(permission);
  },

  // Sprawdź czy użytkownik może edytować posty
  canEditPosts: (user: User | null): boolean => {
    return permissions.isAdmin(user) || 
           permissions.hasPermission(user, 'post.edit');
  },

  // Sprawdź czy użytkownik może usuwać posty
  canDeletePosts: (user: User | null): boolean => {
    return permissions.isAdmin(user) || 
           permissions.hasPermission(user, 'post.delete');
  },

  // Sprawdź czy użytkownik może moderować komentarze
  canModerateComments: (user: User | null): boolean => {
    return permissions.isAdminOrModerator(user) || 
           permissions.hasPermission(user, 'comment.moderate');
  },

  // Sprawdź czy użytkownik może zarządzać użytkownikami
  canManageUsers: (user: User | null): boolean => {
    return permissions.isAdmin(user) || 
           permissions.hasPermission(user, 'user.manage');
  },

  // Sprawdź czy użytkownik ma wystarczający poziom uprawnień
  hasMinimumLevel: (user: User | null, minLevel: number): boolean => {
    return (user?.role?.level ?? 0) >= minLevel;
  }
};

// Hook dla React
export function usePermissions(user: User | null) {
  return {
    isAdmin: permissions.isAdmin(user),
    isModerator: permissions.isModerator(user),
    isAdminOrModerator: permissions.isAdminOrModerator(user),
    canEditPosts: permissions.canEditPosts(user),
    canDeletePosts: permissions.canDeletePosts(user),
    canModerateComments: permissions.canModerateComments(user),
    canManageUsers: permissions.canManageUsers(user),
    hasPermission: (permission: string) => permissions.hasPermission(user, permission),
    hasRole: (roleName: string) => permissions.hasRole(user, roleName),
    hasMinimumLevel: (minLevel: number) => permissions.hasMinimumLevel(user, minLevel)
  };
}
```

### Authorization Error Handling

```typescript
// utils/authErrors.ts
export class AuthorizationError extends Error {
  constructor(
    message: string,
    public requiredRole?: string,
    public requiredPermission?: string
  ) {
    super(message);
    this.name = 'AuthorizationError';
  }
}

export function handleAuthorizationError(error: any, user: User | null): string {
  if (error.status === 403 || error.status === 401) {
    // Sprawdź szczegóły błędu autoryzacji
    if (error.message?.includes('admin')) {
      return 'Ta operacja wymaga uprawnień administratora. Skontaktuj się z administratorem systemu.';
    }
    
    if (error.message?.includes('moderator')) {
      return 'Ta operacja wymaga uprawnień moderatora lub administratora.';
    }

    if (error.message?.includes('permission')) {
      return 'Nie masz wymaganych uprawnień do wykonania tej operacji.';
    }

    // Domyślne komunikaty w zależności od statusu
    switch (error.status) {
      case 401:
        return 'Musisz się zalogować, aby wykonać tę operację.';
      case 403:
        return 'Nie masz uprawnień do wykonania tej operacji.';
      default:
        return 'Wystąpił błąd autoryzacji.';
    }
  }
  
  return error.message || 'Wystąpił nieoczekiwany błąd.';
}

// Komponenty React dla różnych poziomów uprawnień
export function AdminOnly({ 
  user, 
  children, 
  fallback 
}: { 
  user: User | null; 
  children: React.ReactNode; 
  fallback?: React.ReactNode;
}) {
  if (!permissions.isAdmin(user)) {
    return fallback || (
      <div className="text-gray-500 p-4 text-center">
        Ta funkcja jest dostępna tylko dla administratorów.
      </div>
    );
  }
  return <>{children}</>;
}

export function ModeratorOnly({ 
  user, 
  children, 
  fallback 
}: { 
  user: User | null; 
  children: React.ReactNode; 
  fallback?: React.ReactNode;
}) {
  if (!permissions.isAdminOrModerator(user)) {
    return fallback || (
      <div className="text-gray-500 p-4 text-center">
        Ta funkcja jest dostępna tylko dla moderatorów i administratorów.
      </div>
    );
  }
  return <>{children}</>;
}

export function RequirePermission({ 
  user, 
  permission,
  children, 
  fallback 
}: { 
  user: User | null; 
  permission: string;
  children: React.ReactNode; 
  fallback?: React.ReactNode;
}) {
  if (!permissions.hasPermission(user, permission)) {
    return fallback || (
      <div className="text-gray-500 p-4 text-center">
        Brak wymaganych uprawnień: {permission}
      </div>
    );
  }
  return <>{children}</>;
}
```

### Protected API Calls

```typescript
// utils/protectedApi.ts
import { apiClient } from '../api/client';
import { handleAuthorizationError } from './authErrors';

export class ProtectedApiClient {
  constructor(private user: User | null) {}

  // Wrapper dla wywołań API wymagających uprawnień administratora
  async adminApiCall<T>(
    apiCall: () => Promise<T>,
    errorMessage = 'Operacja wymaga uprawnień administratora'
  ): Promise<T> {
    if (!permissions.isAdmin(this.user)) {
      throw new AuthorizationError(errorMessage, 'admin');
    }

    try {
      return await apiCall();
    } catch (error) {
      const message = handleAuthorizationError(error, this.user);
      throw new Error(message);
    }
  }

  // Wrapper dla wywołań API wymagających uprawnień moderatora
  async moderatorApiCall<T>(
    apiCall: () => Promise<T>,
    errorMessage = 'Operacja wymaga uprawnień moderatora lub administratora'
  ): Promise<T> {
    if (!permissions.isAdminOrModerator(this.user)) {
      throw new AuthorizationError(errorMessage, 'moderator');
    }

    try {
      return await apiCall();
    } catch (error) {
      const message = handleAuthorizationError(error, this.user);
      throw new Error(message);
    }
  }

  // Wrapper dla wywołań API wymagających konkretnego uprawnienia
  async permissionApiCall<T>(
    permission: string,
    apiCall: () => Promise<T>,
    errorMessage = `Operacja wymaga uprawnienia: ${permission}`
  ): Promise<T> {
    if (!permissions.hasPermission(this.user, permission)) {
      throw new AuthorizationError(errorMessage, undefined, permission);
    }

    try {
      return await apiCall();
    } catch (error) {
      const message = handleAuthorizationError(error, this.user);
      throw new Error(message);
    }
  }

  // Metody dla konkretnych operacji
  async createBlogPost(postData: any) {
    return this.adminApiCall(
      () => apiClient.createBlogPost(postData),
      'Tylko administratorzy mogą tworzyć posty na blogu'
    );
  }

  async deleteBlogPost(postId: number) {
    return this.adminApiCall(
      () => apiClient.deleteBlogPost(postId),
      'Tylko administratorzy mogą usuwać posty'
    );
  }

  async moderateComment(commentId: number, action: string) {
    return this.moderatorApiCall(
      () => apiClient.moderateComment(commentId, action),
      'Tylko moderatorzy i administratorzy mogą moderować komentarze'
    );
  }

  async manageUser(userId: number, userData: any) {
    return this.permissionApiCall(
      'user.manage',
      () => apiClient.updateUser(userId, userData),
      'Nie masz uprawnień do zarządzania użytkownikami'
    );
  }
}

// Hook dla React
export function useProtectedApi(user: User | null) {
  return new ProtectedApiClient(user);
}
```

### Practical Usage Examples

```tsx
// components/AdminPanel.tsx
import { useAuth } from '../hooks/useAuth';
import { usePermissions, AdminOnly, ModeratorOnly } from '../utils/permissions';
import { useProtectedApi } from '../utils/protectedApi';

export function AdminPanel() {
  const { user } = useAuth();
  const permissions = usePermissions(user);
  const protectedApi = useProtectedApi(user);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleDeletePost = async (postId: number) => {
    setLoading(true);
    setError(null);

    try {
      await protectedApi.deleteBlogPost(postId);
      // Odśwież listę postów
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Błąd podczas usuwania posta');
    } finally {
      setLoading(false);
    }
  };

  const handleModerateComment = async (commentId: number, action: string) => {
    setLoading(true);
    setError(null);

    try {
      await protectedApi.moderateComment(commentId, action);
      // Odśwież komentarze
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Błąd podczas moderacji');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-panel">
      <h2>Panel Administracyjny</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Sekcja tylko dla administratorów */}
      <AdminOnly user={user}>
        <div className="mb-6">
          <h3>Zarządzanie Postami</h3>
          <button
            onClick={() => handleDeletePost(123)}
            disabled={loading}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 disabled:opacity-50"
          >
            {loading ? 'Usuwanie...' : 'Usuń Post'}
          </button>
        </div>
      </AdminOnly>

      {/* Sekcja dla moderatorów i administratorów */}
      <ModeratorOnly user={user}>
        <div className="mb-6">
          <h3>Moderacja Komentarzy</h3>
          <div className="space-x-2">
            <button
              onClick={() => handleModerateComment(456, 'approve')}
              disabled={loading}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
            >
              Zatwierdź
            </button>
            <button
              onClick={() => handleModerateComment(456, 'reject')}
              disabled={loading}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
            >
              Odrzuć
            </button>
          </div>
        </div>
      </ModeratorOnly>

      {/* Warunkowe wyświetlanie na podstawie uprawnień */}
      {permissions.canManageUsers && (
        <div className="mb-6">
          <h3>Zarządzanie Użytkownikami</h3>
          <p>Tu będzie lista użytkowników...</p>
        </div>
      )}

      {/* Informacja o brakujących uprawnieniach */}
      {!permissions.isAdminOrModerator && (
        <div className="text-gray-500 p-4 text-center">
          Nie masz uprawnień do wyświetlenia tej sekcji.
        </div>
      )}
    </div>
  );
}
```

```tsx
// components/BlogPostEditor.tsx
import { useAuth } from '../hooks/useAuth';
import { usePermissions } from '../utils/permissions';
import { useProtectedApi } from '../utils/protectedApi';

export function BlogPostEditor({ postId }: { postId?: number }) {
  const { user } = useAuth();
  const permissions = usePermissions(user);
  const protectedApi = useProtectedApi(user);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    excerpt: '',
    category: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Sprawdź uprawnienia przed renderowaniem
  if (!permissions.canEditPosts) {
    return (
      <div className="text-center p-8">
        <h2 className="text-xl font-semibold text-gray-600 mb-4">
          Brak uprawnień
        </h2>
        <p className="text-gray-500">
          Nie masz uprawnień do edycji postów na blogu.
        </p>
        <p className="text-sm text-gray-400 mt-2">
          Skontaktuj się z administratorem, jeśli uważasz, że to błąd.
        </p>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (postId) {
        await protectedApi.updateBlogPost(postId, formData);
      } else {
        await protectedApi.createBlogPost(formData);
      }
      // Przekieruj po sukcesie
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Błąd podczas zapisywania posta');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">
        {postId ? 'Edytuj Post' : 'Nowy Post'}
      </h2>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label htmlFor="title" className="block text-sm font-medium mb-1">
            Tytuł
          </label>
          <input
            type="text"
            id="title"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            className="w-full p-2 border rounded-md"
            required
          />
        </div>

        <div>
          <label htmlFor="excerpt" className="block text-sm font-medium mb-1">
            Skrót
          </label>
          <textarea
            id="excerpt"
            value={formData.excerpt}
            onChange={(e) => setFormData({ ...formData, excerpt: e.target.value })}
            className="w-full p-2 border rounded-md h-20"
          />
        </div>

        <div>
          <label htmlFor="content" className="block text-sm font-medium mb-1">
            Treść
          </label>
          <textarea
            id="content"
            value={formData.content}
            onChange={(e) => setFormData({ ...formData, content: e.target.value })}
            className="w-full p-2 border rounded-md h-64"
            required
          />
        </div>

        <div>
          <label htmlFor="category" className="block text-sm font-medium mb-1">
            Kategoria
          </label>
          <select
            id="category"
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            className="w-full p-2 border rounded-md"
          >
            <option value="">Wybierz kategorię</option>
            <option value="programming">Programowanie</option>
            <option value="tutorial">Tutorial</option>
            <option value="personal">Osobiste</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Zapisywanie...' : (postId ? 'Aktualizuj Post' : 'Utwórz Post')}
        </button>
      </div>
    </form>
  );
}
```

```tsx
// components/Navigation.tsx
import { useAuth } from '../hooks/useAuth';
import { usePermissions } from '../utils/permissions';

export function Navigation() {
  const { user, logout } = useAuth();
  const permissions = usePermissions(user);

  return (
    <nav className="bg-gray-800 text-white">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-4">
            <a href="/" className="text-xl font-bold">Portfolio</a>
            <a href="/blog" className="hover:text-gray-300">Blog</a>
            
            {/* Linki widoczne tylko dla zalogowanych */}
            {user && (
              <>
                <a href="/profile" className="hover:text-gray-300">Profil</a>
                
                {/* Linki dla moderatorów i administratorów */}
                {permissions.isAdminOrModerator && (
                  <a href="/moderation" className="hover:text-gray-300">Moderacja</a>
                )}
                
                {/* Linki tylko dla administratorów */}
                {permissions.isAdmin && (
                  <>
                    <a href="/admin" className="hover:text-gray-300">Admin</a>
                    <a href="/blog/new" className="hover:text-gray-300">Nowy Post</a>
                  </>
                )}
              </>
            )}
          </div>

          <div className="flex items-center space-x-4">
            {user ? (
              <div className="flex items-center space-x-2">
                <span className="text-sm">
                  Witaj, {user.username}
                  {user.role && (
                    <span 
                      className="ml-2 px-2 py-1 text-xs rounded"
                      style={{ backgroundColor: user.role.color, color: 'white' }}
                    >
                      {user.role.display_name}
                    </span>
                  )}
                </span>
                <button
                  onClick={logout}
                  className="text-sm hover:text-gray-300"
                >
                  Wyloguj
                </button>
              </div>
            ) : (
              <div className="space-x-2">
                <a href="/login" className="hover:text-gray-300">Logowanie</a>
                <a href="/register" className="hover:text-gray-300">Rejestracja</a>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
```

### Vue.js Permission Examples

```vue
<!-- components/AdminSection.vue -->
<template>
  <div v-if="permissions.isAdminOrModerator" class="admin-section">
    <h3>Panel Administracyjny</h3>
    
    <!-- Funkcje dla administratorów -->
    <div v-if="permissions.isAdmin" class="admin-only">
      <button 
        @click="deletePost"
        :disabled="loading"
        class="btn btn-danger"
      >
        {{ loading ? 'Usuwanie...' : 'Usuń Post' }}
      </button>
    </div>
    
    <!-- Funkcje dla moderatorów i administratorów -->
    <div v-if="permissions.canModerateComments" class="moderator-tools">
      <button @click="moderateComment('approve')" class="btn btn-success">
        Zatwierdź Komentarz
      </button>
      <button @click="moderateComment('reject')" class="btn btn-warning">
        Odrzuć Komentarz
      </button>
    </div>
    
    <!-- Komunikat o błędzie -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
  
  <!-- Brak uprawnień -->
  <div v-else class="no-permissions">
    <p>Nie masz uprawnień do wyświetlenia tej sekcji.</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useAuth } from '../composables/useAuth';
import { permissions } from '../utils/permissions';

const { user } = useAuth();
const loading = ref(false);
const error = ref<string | null>(null);

const userPermissions = computed(() => ({
  isAdmin: permissions.isAdmin(user.value),
  isAdminOrModerator: permissions.isAdminOrModerator(user.value),
  canModerateComments: permissions.canModerateComments(user.value),
}));

const deletePost = async () => {
  if (!permissions.isAdmin(user.value)) {
    error.value = 'Nie masz uprawnień do usuwania postów.';
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    // Wywołanie API
    console.log('Usuwanie posta...');
  } catch (err) {
    error.value = 'Błąd podczas usuwania posta.';
  } finally {
    loading.value = false;
  }
};

const moderateComment = async (action: string) => {
  if (!permissions.canModerateComments(user.value)) {
    error.value = 'Nie masz uprawnień do moderacji komentarzy.';
    return;
  }

  try {
    // Wywołanie API
    console.log(`Moderacja komentarza: ${action}`);
  } catch (err) {
    error.value = 'Błąd podczas moderacji komentarza.';
  }
};
</script>
```

### Route Protection Middleware

```typescript
// middleware/authMiddleware.ts
import { NextRequest, NextResponse } from 'next/server';
import { permissions } from '../utils/permissions';

interface RouteConfig {
  path: string;
  requiredRole?: string;
  requiredPermission?: string;
  adminOnly?: boolean;
  moderatorOnly?: boolean;
}

const protectedRoutes: RouteConfig[] = [
  { path: '/admin', adminOnly: true },
  { path: '/blog/new', adminOnly: true },
  { path: '/blog/edit', adminOnly: true },
  { path: '/moderation', moderatorOnly: true },
  { path: '/users/manage', requiredPermission: 'user.manage' },
];

export function authMiddleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const user = getUserFromRequest(request); // Implementacja zależna od sposobu przechowywania sesji

  // Znajdź konfigurację dla aktualnej ścieżki
  const routeConfig = protectedRoutes.find(route => 
    pathname.startsWith(route.path)
  );

  if (!routeConfig) {
    return NextResponse.next(); // Ścieżka nie wymaga autoryzacji
  }

  // Sprawdź czy użytkownik jest zalogowany
  if (!user) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Sprawdź wymagania dotyczące uprawnień
  if (routeConfig.adminOnly && !permissions.isAdmin(user)) {
    return NextResponse.redirect(new URL('/unauthorized', request.url));
  }

  if (routeConfig.moderatorOnly && !permissions.isAdminOrModerator(user)) {
    return NextResponse.redirect(new URL('/unauthorized', request.url));
  }

  if (routeConfig.requiredRole && !permissions.hasRole(user, routeConfig.requiredRole)) {
    return NextResponse.redirect(new URL('/unauthorized', request.url));
  }

  if (routeConfig.requiredPermission && !permissions.hasPermission(user, routeConfig.requiredPermission)) {
    return NextResponse.redirect(new URL('/unauthorized', request.url));
  }

  return NextResponse.next();
}

function getUserFromRequest(request: NextRequest) {
  // Tu powinna być implementacja pobierania użytkownika z sesji/tokenu
  // Na przykład z JWT token w cookies lub headers
  return null; // Placeholder
}
```

```typescript
// hooks/useRouteProtection.ts (React Router)
import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from './useAuth';
import { permissions } from '../utils/permissions';

interface RouteProtectionConfig {
  adminOnly?: boolean;
  moderatorOnly?: boolean;
  requiredRole?: string;
  requiredPermission?: string;
  redirectTo?: string;
}

export function useRouteProtection(config: RouteProtectionConfig) {
  const { user, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (isLoading) return; // Czekaj na załadowanie danych użytkownika

    // Sprawdź czy użytkownik jest zalogowany
    if (!user) {
      navigate('/login', { 
        state: { from: location.pathname },
        replace: true 
      });
      return;
    }

    // Sprawdź wymagania dotyczące uprawnień
    let hasAccess = true;
    let errorMessage = '';

    if (config.adminOnly && !permissions.isAdmin(user)) {
      hasAccess = false;
      errorMessage = 'Ta strona jest dostępna tylko dla administratorów.';
    }

    if (config.moderatorOnly && !permissions.isAdminOrModerator(user)) {
      hasAccess = false;
      errorMessage = 'Ta strona jest dostępna tylko dla moderatorów i administratorów.';
    }

    if (config.requiredRole && !permissions.hasRole(user, config.requiredRole)) {
      hasAccess = false;
      errorMessage = `Ta strona wymaga roli: ${config.requiredRole}.`;
    }

    if (config.requiredPermission && !permissions.hasPermission(user, config.requiredPermission)) {
      hasAccess = false;
      errorMessage = `Ta strona wymaga uprawnienia: ${config.requiredPermission}.`;
    }

    if (!hasAccess) {
      navigate(config.redirectTo || '/unauthorized', {
        state: { errorMessage, from: location.pathname },
        replace: true
      });
    }
  }, [user, isLoading, navigate, location.pathname, config]);

  return {
    isAuthorized: !isLoading && user && (
      (!config.adminOnly || permissions.isAdmin(user)) &&
      (!config.moderatorOnly || permissions.isAdminOrModerator(user)) &&
      (!config.requiredRole || permissions.hasRole(user, config.requiredRole)) &&
      (!config.requiredPermission || permissions.hasPermission(user, config.requiredPermission))
    ),
    isLoading
  };
}
```

```tsx
// components/ProtectedRoute.tsx
import { ReactNode } from 'react';
import { useRouteProtection } from '../hooks/useRouteProtection';

interface ProtectedRouteProps {
  children: ReactNode;
  adminOnly?: boolean;
  moderatorOnly?: boolean;
  requiredRole?: string;
  requiredPermission?: string;
  fallback?: ReactNode;
}

export function ProtectedRoute({
  children,
  adminOnly,
  moderatorOnly,
  requiredRole,
  requiredPermission,
  fallback
}: ProtectedRouteProps) {
  const { isAuthorized, isLoading } = useRouteProtection({
    adminOnly,
    moderatorOnly,
    requiredRole,
    requiredPermission
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthorized) {
    return fallback || (
      <div className="text-center p-8">
        <h2 className="text-xl font-semibold text-gray-600 mb-4">
          Brak dostępu
        </h2>
        <p className="text-gray-500">
          Nie masz uprawnień do wyświetlenia tej strony.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}

// Przykład użycia w routingu
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/blog" element={<Blog />} />
      <Route path="/login" element={<Login />} />
      
      {/* Chronione trasy */}
      <Route 
        path="/admin/*" 
        element={
          <ProtectedRoute adminOnly>
            <AdminPanel />
          </ProtectedRoute>
        } 
      />
      
      <Route 
        path="/moderation" 
        element={
          <ProtectedRoute moderatorOnly>
            <ModerationPanel />
          </ProtectedRoute>
        } 
      />
      
      <Route 
        path="/blog/new" 
        element={
          <ProtectedRoute requiredPermission="post.create">
            <BlogEditor />
          </ProtectedRoute>
        } 
      />
      
      <Route path="/unauthorized" element={<UnauthorizedPage />} />
    </Routes>
  );
}
```

### API Response Error Handling

```typescript
// utils/apiErrorHandler.ts
export interface ApiErrorResponse {
  detail: string;
  status_code: number;
  error_type?: string;
  required_role?: string;
  required_permission?: string;
}

export function createApiErrorHandler(user: User | null) {
  return (error: any): string => {
    // Obsługa błędów autoryzacji z backendu
    if (error.status === 403) {
      if (error.detail?.includes('admin')) {
        return 'Ta operacja wymaga uprawnień administratora.';
      }
      
      if (error.detail?.includes('moderator')) {
        return 'Ta operacja wymaga uprawnień moderatora.';
      }

      if (error.detail?.includes('role')) {
        const requiredRole = extractRequiredRole(error.detail);
        return `Ta operacja wymaga roli: ${requiredRole}.`;
      }

      if (error.detail?.includes('permission')) {
        const requiredPermission = extractRequiredPermission(error.detail);
        return `Ta operacja wymaga uprawnienia: ${requiredPermission}.`;
      }

      return 'Nie masz uprawnień do wykonania tej operacji.';
    }

    if (error.status === 401) {
      return 'Musisz się zalogować, aby wykonać tę operację.';
    }

    // Inne błędy API
    return error.detail || error.message || 'Wystąpił nieoczekiwany błąd.';
  };
}

function extractRequiredRole(errorMessage: string): string {
  const match = errorMessage.match(/role[:\s]+([a-zA-Z_]+)/i);
  return match ? match[1] : 'unknown';
}

function extractRequiredPermission(errorMessage: string): string {
  const match = errorMessage.match(/permission[:\s]+([a-zA-Z_.]+)/i);
  return match ? match[1] : 'unknown';
}

// Hook dla React
export function useApiErrorHandler() {
  const { user } = useAuth();
  return createApiErrorHandler(user);
}
```

### Error Handling

```typescript
// utils/errorHandling.ts
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function handleApiError(error: any): string {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 401:
        return 'Authentication required. Please log in.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 422:
        return 'Invalid data provided. Please check your input.';
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
        return 'Server error. Please try again later.';
      default:
        return error.message || 'An unexpected error occurred.';
    }
  }
  
  return 'Network error. Please check your connection.';
}
```

### Form Validation

```typescript
// utils/validation.ts
export const validation = {
  email: (email: string): string | null => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) return 'Email is required';
    if (!emailRegex.test(email)) return 'Invalid email format';
    return null;
  },

  password: (password: string): string | null => {
    if (!password) return 'Password is required';
    if (password.length < 8) return 'Password must be at least 8 characters';
    if (!/[A-Z]/.test(password)) return 'Password must contain an uppercase letter';
    if (!/[a-z]/.test(password)) return 'Password must contain a lowercase letter';
    if (!/\d/.test(password)) return 'Password must contain a number';
    if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)) {
      return 'Password must contain a special character';
    }
    return null;
  },

  username: (username: string): string | null => {
    if (!username) return 'Username is required';
    if (username.length < 3) return 'Username must be at least 3 characters';
    if (username.length > 50) return 'Username must be less than 50 characters';
    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
      return 'Username can only contain letters, numbers, underscores, and hyphens';
    }
    return null;
  },

  verificationCode: (code: string): string | null => {
    if (!code) return 'Verification code is required';
    if (!/^\d{6}$/.test(code)) return 'Verification code must be 6 digits';
    return null;
  },
};
```

## 📱 Mobile Examples (React Native)

### Async Storage for Tokens

```typescript
// services/storage.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

export const storage = {
  async setTokens(accessToken: string, refreshToken?: string) {
    await AsyncStorage.setItem('access_token', accessToken);
    if (refreshToken) {
      await AsyncStorage.setItem('refresh_token', refreshToken);
    }
  },

  async getTokens() {
    const accessToken = await AsyncStorage.getItem('access_token');
    const refreshToken = await AsyncStorage.getItem('refresh_token');
    return { accessToken, refreshToken };
  },

  async clearTokens() {
    await AsyncStorage.multiRemove(['access_token', 'refresh_token']);
  },
};
```

---

**Made with ❤️ for developers by KGR33N**
