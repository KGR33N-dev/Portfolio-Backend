# 📝 Blog Management - Copy-Paste Examples

Gotowe do kopiowania funkcje i komponenty dla zarządzania blogiem.

## 🔧 Utility Functions

### Walidacja posta

```typescript
interface BlogPostData {
  title: string;
  content: string;
  slug: string;
  excerpt?: string;
  category?: string;
  language?: 'pl' | 'en';
  tags?: string[];
  meta_title?: string;
  meta_description?: string;
}

function validateBlogPost(data: BlogPostData): string[] {
  const errors: string[] = [];
  
  if (!data.title || data.title.trim().length === 0) {
    errors.push('Tytuł jest wymagany');
  }
  if (data.title && data.title.length > 200) {
    errors.push('Tytuł nie może być dłuższy niż 200 znaków');
  }
  
  if (!data.content || data.content.trim().length === 0) {
    errors.push('Treść jest wymagana');
  }
  
  if (!data.slug || data.slug.trim().length === 0) {
    errors.push('Slug jest wymagany');
  }
  if (data.slug && data.slug.length > 200) {
    errors.push('Slug nie może być dłuższy niż 200 znaków');
  }
  if (data.slug && !/^[a-z0-9-]+$/.test(data.slug)) {
    errors.push('Slug może zawierać tylko małe litery, cyfry i myślniki');
  }
  
  if (data.language && !['pl', 'en'].includes(data.language)) {
    errors.push('Język musi być "pl" lub "en"');
  }
  
  return errors;
}
```

### Generowanie slug

```typescript
function generateSlug(title: string): string {
  const polishChars = {
    'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
    'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'
  };
  
  return title
    .toLowerCase()
    .trim()
    // Zamień polskie znaki
    .replace(/[ąćęłńóśźż]/g, (char) => polishChars[char] || char)
    // Usuń znaki specjalne oprócz spacji i myślników
    .replace(/[^a-z0-9\s-]/g, '')
    // Spacje na myślniki
    .replace(/\s+/g, '-')
    // Wielokrotne myślniki na jeden
    .replace(/-+/g, '-')
    // Usuń myślniki z początku i końca
    .replace(/^-|-$/g, '');
}

// Testowanie
console.log(generateSlug("Nowy post o JavaScript!")); // "nowy-post-o-javascript"
console.log(generateSlug("Łąka żółte kwiaty")); // "laka-zolte-kwiaty"
```

### Walidacja tagów

```typescript
function validateTags(tags: string[]): string[] {
  return tags
    .filter(tag => tag.trim().length > 0)
    .map(tag => tag.trim().toLowerCase())
    .filter(tag => tag.length <= 50)
    .slice(0, 10); // Maksymalnie 10 tagów
}

function parseTagsFromString(tagsString: string): string[] {
  return validateTags(
    tagsString.split(',').map(tag => tag.trim())
  );
}
```

## 📱 React Hooks

### useBlogPost Hook

```typescript
import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface UseBlogPostResult {
  post: BlogPost | null;
  loading: boolean;
  error: string | null;
  updatePost: (updates: Partial<BlogPostData>) => Promise<void>;
  publishPost: () => Promise<void>;
  unpublishPost: () => Promise<void>;
  deletePost: () => Promise<boolean>;
  refetch: () => Promise<void>;
}

export function useBlogPost(id: number): UseBlogPostResult {
  const [post, setPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPost = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const postData = await apiClient.getBlogPostById(id);
      setPost(postData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Błąd pobierania posta');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchPost();
    }
  }, [id]);

  const updatePost = async (updates: Partial<BlogPostData>) => {
    try {
      const updatedPost = await apiClient.updateBlogPost(id, updates);
      setPost(updatedPost);
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Błąd aktualizacji');
    }
  };

  const publishPost = async () => {
    try {
      await apiClient.publishPost(id);
      setPost(prev => prev ? { ...prev, is_published: true } : null);
    } catch (err) {
      throw new Error('Błąd publikacji posta');
    }
  };

  const unpublishPost = async () => {
    try {
      await apiClient.unpublishPost(id);
      setPost(prev => prev ? { ...prev, is_published: false } : null);
    } catch (err) {
      throw new Error('Błąd ukrywania posta');
    }
  };

  const deletePost = async (): Promise<boolean> => {
    const confirmed = window.confirm(
      'Czy na pewno chcesz usunąć ten post? Ta operacja jest nieodwracalna.'
    );
    
    if (confirmed) {
      try {
        await apiClient.deleteBlogPost(id);
        return true;
      } catch (err) {
        throw new Error('Błąd usuwania posta');
      }
    }
    
    return false;
  };

  return {
    post,
    loading,
    error,
    updatePost,
    publishPost,
    unpublishPost,
    deletePost,
    refetch: fetchPost,
  };
}
```

### useAutoSave Hook

```typescript
import { useEffect, useRef } from 'react';

export function useAutoSave<T>(
  data: T,
  onSave: (data: T) => void,
  delay: number = 30000
) {
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      onSave(data);
    }, delay);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [data, onSave, delay]);
}

// Użycie
function BlogEditor() {
  const [formData, setFormData] = useState<BlogPostData>(initialData);
  
  useAutoSave(formData, (data) => {
    localStorage.setItem('blog-draft', JSON.stringify(data));
    console.log('Draft saved');
  });
  
  // ...
}
```

## 🎨 React Components

### BlogPostForm Component

```tsx
import React, { useState, useEffect } from 'react';

interface BlogPostFormProps {
  initialData?: Partial<BlogPostData>;
  onSubmit: (data: BlogPostData) => Promise<void>;
  onCancel?: () => void;
  isEditing?: boolean;
  isSubmitting?: boolean;
}

export function BlogPostForm({
  initialData,
  onSubmit,
  onCancel,
  isEditing = false,
  isSubmitting = false
}: BlogPostFormProps) {
  const [formData, setFormData] = useState<BlogPostData>({
    title: '',
    content: '',
    slug: '',
    excerpt: '',
    category: 'programming',
    language: 'pl',
    tags: [],
    meta_title: '',
    meta_description: '',
    ...initialData
  });

  const [errors, setErrors] = useState<string[]>([]);
  const [isDirty, setIsDirty] = useState(false);

  // Auto-save draft
  useAutoSave(formData, (data) => {
    if (isDirty && (data.title || data.content)) {
      localStorage.setItem('blog-draft', JSON.stringify(data));
    }
  });

  // Load draft on mount
  useEffect(() => {
    if (!isEditing) {
      const draft = localStorage.getItem('blog-draft');
      if (draft) {
        try {
          const parsed = JSON.parse(draft);
          setFormData(prev => ({ ...prev, ...parsed }));
        } catch (e) {
          console.error('Failed to parse draft:', e);
        }
      }
    }
  }, [isEditing]);

  const updateField = (field: keyof BlogPostData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setIsDirty(true);
    
    // Auto-generate slug from title
    if (field === 'title' && !isEditing && !formData.slug) {
      setFormData(prev => ({ ...prev, slug: generateSlug(value) }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationErrors = validateBlogPost(formData);
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }
    
    setErrors([]);
    
    try {
      await onSubmit(formData);
      
      // Clear draft after successful submission
      if (!isEditing) {
        localStorage.removeItem('blog-draft');
      }
      
    } catch (error) {
      setErrors([error.message || 'Wystąpił błąd podczas zapisywania']);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">
            {isEditing ? 'Edytuj post' : 'Nowy post'}
          </h1>
          
          {isDirty && (
            <span className="text-sm text-orange-600 bg-orange-100 px-2 py-1 rounded">
              Niezapisane zmiany
            </span>
          )}
        </div>

        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tytuł *
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => updateField('title', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Wprowadź tytuł posta"
            required
          />
        </div>

        {/* Slug */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Slug URL *
          </label>
          <div className="flex">
            <span className="inline-flex items-center px-3 text-sm text-gray-500 bg-gray-50 border border-r-0 border-gray-300 rounded-l-md">
              /blog/
            </span>
            <input
              type="text"
              value={formData.slug}
              onChange={(e) => updateField('slug', e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-r-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              placeholder="url-friendly-slug"
              pattern="^[a-z0-9-]+$"
              required
            />
          </div>
          <p className="mt-1 text-xs text-gray-500">
            Tylko małe litery, cyfry i myślniki
          </p>
        </div>

        {/* Category and Language */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Kategoria
            </label>
            <select
              value={formData.category}
              onChange={(e) => updateField('category', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="programming">Programming</option>
              <option value="tutorial">Tutorial</option>
              <option value="personal">Personal</option>
              <option value="news">News</option>
              <option value="review">Review</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Język
            </label>
            <select
              value={formData.language}
              onChange={(e) => updateField('language', e.target.value as 'pl' | 'en')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="pl">Polski</option>
              <option value="en">English</option>
            </select>
          </div>
        </div>

        {/* Content */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Treść *
          </label>
          <textarea
            value={formData.content}
            onChange={(e) => updateField('content', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-96 font-mono text-sm"
            placeholder="Napisz treść posta... (obsługuje HTML i Markdown)"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Obsługuje HTML i Markdown
          </p>
        </div>

        {/* Excerpt */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Krótki opis
          </label>
          <textarea
            value={formData.excerpt}
            onChange={(e) => updateField('excerpt', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-24"
            placeholder="Krótki opis posta dla listy i SEO"
          />
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tagi
          </label>
          <input
            type="text"
            value={formData.tags?.join(', ') || ''}
            onChange={(e) => updateField('tags', parseTagsFromString(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="javascript, tutorial, react (oddziel przecinkami)"
          />
          <p className="mt-1 text-xs text-gray-500">
            Maksymalnie 10 tagów, każdy do 50 znaków
          </p>
          
          {formData.tags && formData.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {formData.tags.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* SEO Section */}
        <details className="bg-gray-50 rounded-lg">
          <summary className="px-4 py-3 font-medium cursor-pointer hover:bg-gray-100 rounded-lg">
            Ustawienia SEO (opcjonalne)
          </summary>
          <div className="px-4 pb-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Meta Title
              </label>
              <input
                type="text"
                value={formData.meta_title}
                onChange={(e) => updateField('meta_title', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Tytuł dla wyszukiwarek (jeśli inny niż główny)"
                maxLength={60}
              />
              <p className="mt-1 text-xs text-gray-500">
                Zalecane: 50-60 znaków
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Meta Description
              </label>
              <textarea
                value={formData.meta_description}
                onChange={(e) => updateField('meta_description', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-20"
                placeholder="Opis dla wyszukiwarek"
                maxLength={160}
              />
              <p className="mt-1 text-xs text-gray-500">
                Zalecane: 150-160 znaków ({formData.meta_description?.length || 0}/160)
              </p>
            </div>
          </div>
        </details>

        {/* Errors */}
        {errors.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h4 className="text-red-800 font-medium mb-2">Błędy:</h4>
            <ul className="text-red-700 text-sm space-y-1">
              {errors.map((error, index) => (
                <li key={index} className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>{error}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 pt-6 border-t">
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Zapisywanie...
              </span>
            ) : (
              isEditing ? 'Zaktualizuj post' : 'Utwórz post'
            )}
          </button>
          
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={isSubmitting}
              className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50 transition-colors"
            >
              Anuluj
            </button>
          )}
          
          {isDirty && (
            <button
              type="button"
              onClick={() => {
                const draft = JSON.stringify(formData);
                localStorage.setItem('blog-draft', draft);
                alert('Szkic zapisany!');
              }}
              className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
            >
              Zapisz szkic
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
```

### BlogPostList Component

```tsx
import React from 'react';
import { formatDate } from '../utils/date';

interface BlogPostListProps {
  posts: BlogPost[];
  onEdit?: (post: BlogPost) => void;
  onDelete?: (post: BlogPost) => void;
  onTogglePublish?: (post: BlogPost) => void;
  isAdmin?: boolean;
}

export function BlogPostList({
  posts,
  onEdit,
  onDelete,
  onTogglePublish,
  isAdmin = false
}: BlogPostListProps) {
  
  const handleDelete = (post: BlogPost) => {
    if (window.confirm(`Czy na pewno chcesz usunąć post "${post.title}"?`)) {
      onDelete?.(post);
    }
  };

  return (
    <div className="space-y-4">
      {posts.map((post) => (
        <div
          key={post.id}
          className={`bg-white rounded-lg shadow-sm border-l-4 p-6 ${
            post.is_published ? 'border-green-400' : 'border-yellow-400'
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-xl font-semibold text-gray-900">
                  {post.title}
                </h3>
                
                <span className={`px-2 py-1 text-xs rounded-full ${
                  post.is_published 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {post.is_published ? 'Opublikowany' : 'Szkic'}
                </span>
                
                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                  {post.category}
                </span>
                
                <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded uppercase">
                  {post.language}
                </span>
              </div>
              
              {post.excerpt && (
                <p className="text-gray-600 mb-3">{post.excerpt}</p>
              )}
              
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span>Autor: {post.author}</span>
                <span>•</span>
                <span>Utworzony: {formatDate(post.created_at)}</span>
                {post.updated_at !== post.created_at && (
                  <>
                    <span>•</span>
                    <span>Edytowany: {formatDate(post.updated_at)}</span>
                  </>
                )}
                {post.published_at && (
                  <>
                    <span>•</span>
                    <span>Opublikowany: {formatDate(post.published_at)}</span>
                  </>
                )}
              </div>
              
              {post.tags && post.tags.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {post.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
            
            {isAdmin && (
              <div className="flex items-center gap-2 ml-4">
                <a
                  href={`/blog/${post.slug}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                >
                  Podgląd
                </a>
                
                {onEdit && (
                  <button
                    onClick={() => onEdit(post)}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                  >
                    Edytuj
                  </button>
                )}
                
                {onTogglePublish && (
                  <button
                    onClick={() => onTogglePublish(post)}
                    className={`px-3 py-1 text-sm rounded transition-colors ${
                      post.is_published
                        ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    {post.is_published ? 'Ukryj' : 'Publikuj'}
                  </button>
                )}
                
                {onDelete && (
                  <button
                    onClick={() => handleDelete(post)}
                    className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                  >
                    Usuń
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
      
      {posts.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <div className="text-4xl mb-4">📝</div>
          <h3 className="text-lg font-medium mb-2">Brak postów</h3>
          <p>Nie znaleziono żadnych postów spełniających kryteria.</p>
        </div>
      )}
    </div>
  );
}
```

## 🛠️ Utility Functions

### Date formatting

```typescript
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('pl-PL', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
  
  if (diffInHours < 1) return 'mniej niż godzinę temu';
  if (diffInHours < 24) return `${diffInHours} godzin temu`;
  
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) return `${diffInDays} dni temu`;
  
  return formatDate(dateString);
}
```

### Error handling

```typescript
export function handleBlogError(error: any): string {
  if (error.status === 403) {
    return 'Brak uprawnień administratora';
  }
  if (error.status === 404) {
    return 'Post nie został znaleziony';
  }
  if (error.status === 409) {
    return 'Post o tym adresie URL już istnieje';
  }
  if (error.status === 422) {
    return 'Dane wejściowe są nieprawidłowe';
  }
  
  return error.message || 'Wystąpił nieoczekiwany błąd';
}
```

## 📱 Complete Example Page

```tsx
// pages/admin/blog/new.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BlogPostForm } from '../../../components/BlogPostForm';
import { apiClient } from '../../../api/client';
import { handleBlogError } from '../../../utils/errors';

export function NewBlogPostPage() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (postData: BlogPostData) => {
    setIsSubmitting(true);
    
    try {
      const newPost = await apiClient.createBlogPost(postData);
      
      // Clear draft
      localStorage.removeItem('blog-draft');
      
      // Show success message
      alert('Post został utworzony pomyślnie!');
      
      // Redirect to edit page or post list
      navigate(`/admin/blog/${newPost.id}/edit`);
      
    } catch (error) {
      alert(handleBlogError(error));
      throw error; // Re-throw to keep form in error state
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    if (window.confirm('Czy na pewno chcesz anulować? Niezapisane zmiany zostaną utracone.')) {
      navigate('/admin/blog');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto py-8">
        <BlogPostForm
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          isSubmitting={isSubmitting}
        />
      </div>
    </div>
  );
}
```

---

**💡 Wskazówka:** Skopiuj potrzebne funkcje i dostosuj je do swoich potrzeb. Wszystkie komponenty są napisane w TypeScript i używają Tailwind CSS do stylowania.
