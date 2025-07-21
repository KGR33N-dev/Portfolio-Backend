import React, { useState, useEffect } from 'react';

interface BlogPost {
  id: number;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  author: string;
  meta_title: string;
  meta_description: string;
  language: string;
  category: string;
  created_at: string;
  updated_at: string;
  is_published: boolean;
  published_at: string;
  tags: string[];
}

interface BlogPostViewProps {
  slug: string;
  apiUrl?: string;
}

const BlogPostView: React.FC<BlogPostViewProps> = ({ 
  slug,
  apiUrl = 'http://localhost:8000/api/blog/' 
}) => {
  const [post, setPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPost();
  }, [slug]);

  const fetchPost = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl}${slug}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          setError('Post nie został znaleziony');
        } else {
          throw new Error('Błąd podczas pobierania posta');
        }
        return;
      }

      const data = await response.json();
      setPost(data);
      setError(null);

      // Dynamically update page title
      if (data.meta_title || data.title) {
        document.title = `${data.meta_title || data.title} - Portfolio KGR33N`;
      }

      // Update meta description
      if (data.meta_description || data.excerpt) {
        const metaDescription = document.querySelector('meta[name="description"]');
        if (metaDescription) {
          metaDescription.setAttribute('content', data.meta_description || data.excerpt);
        }
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Wystąpił błąd');
      setPost(null);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pl-PL', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // Convert basic markdown to HTML
  const renderContent = (content: string) => {
    return content
      .replace(/^# (.*$)/gm, '<h1 class="text-4xl font-bold mb-6 text-gray-900 dark:text-gray-100">$1</h1>')
      .replace(/^## (.*$)/gm, '<h2 class="text-3xl font-bold mb-4 mt-8 text-gray-900 dark:text-gray-100">$1</h2>')
      .replace(/^### (.*$)/gm, '<h3 class="text-2xl font-bold mb-3 mt-6 text-gray-900 dark:text-gray-100">$1</h3>')
      .replace(/^\* (.*$)/gm, '<li class="mb-1 text-gray-700 dark:text-gray-300">$1</li>')
      .replace(/^- (.*$)/gm, '<li class="mb-1 text-gray-700 dark:text-gray-300">$1</li>')
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900 dark:text-gray-100">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>')
      .replace(/\n\n/g, '</p><p class="mb-4 text-gray-700 dark:text-gray-300 leading-relaxed">')
      .replace(/\n/g, '<br>');
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-16">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-lg text-gray-600 dark:text-gray-300">
          Ładowanie posta...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-8 max-w-md mx-auto">
          <div className="text-red-600 dark:text-red-400 mb-4">
            <svg className="w-12 h-12 mx-auto mb-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-red-800 dark:text-red-200 mb-2">
            {error}
          </h2>
          <p className="text-red-600 dark:text-red-300 mb-4">
            Nie udało się załadować tego posta.
          </p>
          <div className="space-x-3">
            <button 
              onClick={fetchPost}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Spróbuj ponownie
            </button>
            <a 
              href="/blog"
              className="px-4 py-2 bg-gray-300 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-400 dark:hover:bg-gray-600 transition-colors"
            >
              Powrót do bloga
            </a>
          </div>
        </div>
      </div>
    );
  }

  if (!post) {
    return null;
  }

  const wrappedContent = `<p class="mb-4 text-gray-700 dark:text-gray-300 leading-relaxed">${renderContent(post.content)}</p>`;

  return (
    <article className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <header className="mb-8 text-center">
        <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-4 text-gray-900 dark:text-gray-100">
          {post.title}
        </h1>
        
        <div className="flex flex-wrap justify-center items-center gap-4 text-sm text-gray-500 dark:text-gray-400 mb-6">
          <time dateTime={post.published_at || post.created_at} className="flex items-center">
            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
            </svg>
            {formatDate(post.published_at || post.created_at)}
          </time>
          
          <span className="flex items-center">
            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
            {post.author}
          </span>
          
          {post.category && (
            <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-3 py-1 rounded-full text-xs">
              {post.category}
            </span>
          )}
          
          <span className="text-xs">
            Język: {post.language === 'pl' ? '🇵🇱 Polski' : '🇬🇧 English'}
          </span>
        </div>

        {post.excerpt && (
          <div className="text-xl text-gray-600 dark:text-gray-300 leading-relaxed mb-8 max-w-3xl mx-auto">
            {post.excerpt}
          </div>
        )}
      </header>

      {/* Content */}
      <div 
        className="prose prose-lg dark:prose-invert max-w-none"
        dangerouslySetInnerHTML={{ __html: wrappedContent }}
      />

      {/* Tags */}
      {post.tags && post.tags.length > 0 && (
        <footer className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex flex-wrap gap-2">
            <span className="text-sm text-gray-500 dark:text-gray-400 mr-2">Tagi:</span>
            {post.tags.map((tag) => (
              <span 
                key={tag}
                className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 px-2 py-1 rounded text-sm hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors cursor-pointer"
              >
                #{tag}
              </span>
            ))}
          </div>
        </footer>
      )}

      {/* Back to blog link */}
      <div className="mt-12 text-center">
        <a 
          href="/blog"
          className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
        >
          <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
          Powrót do bloga
        </a>
      </div>
    </article>
  );
};

export default BlogPostView;
