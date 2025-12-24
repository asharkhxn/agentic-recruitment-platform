export interface User {
  id: string;
  email: string;
  role: "applicant" | "recruiter";
  full_name?: string;
}

export interface Job {
  id: string;
  title: string;
  description: string;
  requirements: string;
  salary?: string;
  created_by: string;
  created_at: string;
}

export interface JobCreate {
  title: string;
  description: string;
  requirements: string;
  salary?: string;
  location: string;
}

export interface Application {
  id: string;
  applicant_id: string;
  job_id: string;
  cv_url: string;
  cover_letter?: string;
  recruiter_id?: string;
  applicant_name?: string;
  motivation?: string;
  proud_project?: string;
  created_at: string;
}

export interface ApplicationCreate {
  job_id: string;
  cover_letter?: string;
  cv_file: File;
  motivation: string;
  proud_project: string;
}

export interface ChatMessage {
  message: string;
  user_id: string;
  conversation_id?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  sql_generated?: string;
}

export interface RankedApplicant {
  applicant_id: string;
  application_id: string;
  name: string;
  email: string;
  score: number;
  summary: string;
  cv_url: string;
  skills: string[];
}

export interface ATSRankingResponse {
  job_id: string;
  job_title: string;
  applicants: RankedApplicant[];
}

export interface AuthResponse {
  access_token: string;
  user: User;
}
