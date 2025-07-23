-- Initialize database for Portfolio Backend
-- This script runs only if using local PostgreSQL

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create initial admin user (optional)
-- INSERT INTO users (username, email, hashed_password, is_active, is_admin) 
-- VALUES ('admin', 'admin@example.com', '$2b$12$...hashed_password_here...', true, true);

-- Initial blog post (optional)
-- INSERT INTO blog_posts (title, slug, content, excerpt, author, category, is_published, published_at, language)
-- VALUES (
--     'Witaj na moim blogu!',
--     'witaj-na-moim-blogu',
--     'To jest pierwszy post na moim blogu. Więcej treści wkrótce!',
--     'Pierwszy post na blogu portfolio.',
--     'KGR33N',
--     'general',
--     true,
--     NOW(),
--     'pl'
-- );
