# Agentic Recruitment Platform

A simple full-stack recruitment app for hiring managers. Features authentication, job management, applicant submissions, and an AI assistant for recruitment tasks.

## Tech Stack

- React
- FastAPI
- Supabase
- Tailwind CSS
- Groq LLM

## Usage

1. Clone the repo
2. Install dependencies in `frontend` and `backend`
3. Start backend and frontend servers
4. Access the app in your browser

## Features

- User authentication (applicant & recruiter roles)
- Job posting and management
- Applicant submissions (CV upload, cover letter)
- AI-powered ATS ranking and job search
- Chatbot assistant for recruiters
- Secure file preview and download

## Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/asharkhxn/agentic-recruitment-platform.git
   cd agentic-recruitment-platform
   ```
2. Install dependencies:
   - Frontend:
     ```bash
     cd frontend
     npm install
     ```
   - Backend:
     ```bash
     cd ../backend
     pip install -r requirements.txt
     ```
3. Configure environment variables:
   - Copy `.env.example` to `.env` and fill in Supabase, Groq, and other secrets.
4. Start servers:
   - Backend:
     ```bash
     uvicorn main:app --reload
     ```
   - Frontend:
     ```bash
     npm run dev
     ```
5. Open your browser at `http://localhost:3000` (frontend) and `http://localhost:8000/docs` (backend API docs).

## Demo Video

A short walkthrough video demonstrating the recruiter and applicant flows,
including job creation, application submission, agentic ATS ranking and the agentic AI assistant:

- Demo: https://drive.google.com/file/d/1qvRXG2Oz8CgfezZ5L8PYjKbwNp5wRMkm/view?usp=sharing
