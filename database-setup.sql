-- Supabase Database Setup
-- Run these SQL commands in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('applicant', 'recruiter')),
  full_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  requirements TEXT NOT NULL,
  salary TEXT,
  created_by UUID REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Applications table
CREATE TABLE IF NOT EXISTS applications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  applicant_id UUID REFERENCES users(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  recruiter_id UUID REFERENCES users(id) ON DELETE SET NULL,
  applicant_name TEXT,
  motivation TEXT,
  proud_project TEXT,
  cv_url TEXT NOT NULL,
  cv_path TEXT,
  cover_letter TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(applicant_id, job_id)
);

-- Ensure new applicant detail columns exist when upgrading an existing database
ALTER TABLE applications ADD COLUMN IF NOT EXISTS applicant_name TEXT;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS motivation TEXT;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS proud_project TEXT;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS cv_path TEXT;

-- AI search logs table
CREATE TABLE IF NOT EXISTS ai_search_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  query TEXT NOT NULL,
  sql_generated TEXT,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_jobs_created_by ON jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_applications_applicant ON applications(applicant_id);
CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_recruiter ON applications(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_ai_logs_user ON ai_search_logs(user_id);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_search_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view their own data"
  ON users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own data"
  ON users FOR UPDATE
  USING (auth.uid() = id);

-- RLS Policies for jobs table
CREATE POLICY "Anyone can view jobs"
  ON jobs FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Recruiters can create jobs"
  ON jobs FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM users
      WHERE id = auth.uid() AND role = 'recruiter'
    )
  );

CREATE POLICY "Recruiters can update their own jobs"
  ON jobs FOR UPDATE
  USING (
    created_by = auth.uid() AND
    EXISTS (
      SELECT 1 FROM users
      WHERE id = auth.uid() AND role = 'recruiter'
    )
  );

CREATE POLICY "Recruiters can delete their own jobs"
  ON jobs FOR DELETE
  USING (
    created_by = auth.uid() AND
    EXISTS (
      SELECT 1 FROM users
      WHERE id = auth.uid() AND role = 'recruiter'
    )
  );

-- RLS Policies for applications table
CREATE POLICY "Applicants can view their own applications"
  ON applications FOR SELECT
  USING (applicant_id = auth.uid());

CREATE POLICY "Recruiters can view their applications"
  ON applications FOR SELECT
  USING (
    recruiter_id = auth.uid() AND
    EXISTS (
      SELECT 1 FROM users
      WHERE id = auth.uid() AND role = 'recruiter'
    )
  );

CREATE POLICY "Applicants can create applications"
  ON applications FOR INSERT
  WITH CHECK (
    applicant_id = auth.uid() AND
    EXISTS (
      SELECT 1 FROM users
      WHERE id = auth.uid() AND role = 'applicant'
    ) AND
    recruiter_id = (
      SELECT created_by FROM jobs WHERE id = job_id
    )
  );

CREATE POLICY "Applicants can delete their own applications"
  ON applications FOR DELETE
  USING (applicant_id = auth.uid());

-- RLS Policies for ai_search_logs table
CREATE POLICY "Users can view their own logs"
  ON ai_search_logs FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own logs"
  ON ai_search_logs FOR INSERT
  WITH CHECK (user_id = auth.uid());

-- Storage buckets (Run in Supabase Storage settings or via SQL)
-- Create two storage buckets:
-- 1. cv-uploads (for CV files)
-- 2. applicant-documents (for additional documents)

-- Note: You need to create these buckets in Supabase Dashboard > Storage
-- and set appropriate policies for file access

-- Storage policies example (adjust bucket names as needed):
-- CREATE POLICY "Applicants can upload CVs"
--   ON storage.objects FOR INSERT
--   WITH CHECK (
--     bucket_id = 'cv-uploads' AND
--     auth.uid()::text = (storage.foldername(name))[1]
--   );

-- CREATE POLICY "Recruiters can view all CVs"
--   ON storage.objects FOR SELECT
--   USING (
--     bucket_id = 'cv-uploads' AND
--     EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'recruiter')
--   );
