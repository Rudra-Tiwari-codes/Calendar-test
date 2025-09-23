-- Temporary script to disable RLS for testing
-- Run this in your Supabase SQL Editor to allow anonymous access

-- Disable RLS on users table (temporary for testing)
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- Alternative: Create a permissive policy for anonymous users
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Allow anonymous access for calendar bot" ON users FOR ALL USING (true);

-- To re-enable RLS later:
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- DROP POLICY IF EXISTS "Allow anonymous access for calendar bot" ON users;