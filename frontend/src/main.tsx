import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navbar } from "./components/Navbar";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";
import { JobListingsPage } from "./pages/JobListingsPage";
import { JobDetailPage } from "./pages/JobDetailPage";
import { ChatbotPage } from "./pages/ChatbotPage";
import { ATSRankingPage } from "./pages/ATSRankingPage";
import { LandingPage } from "./pages/LandingPage";
import { ApplicationsPage } from "./pages/ApplicationsPage";
import { JobCreatePage } from "./pages/JobCreatePage";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider } from "./hooks/useAuth";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <div className="min-h-screen">
            <Navbar />
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignupPage />} />

              <Route element={<ProtectedRoute allowedRoles={["applicant"]} />}>
                <Route path="/jobs" element={<JobListingsPage />} />
                <Route path="/jobs/:jobId" element={<JobDetailPage />} />
                <Route path="/applications" element={<ApplicationsPage />} />
              </Route>

              <Route element={<ProtectedRoute allowedRoles={["recruiter"]} />}>
                <Route path="/chatbot" element={<ChatbotPage />} />
                <Route path="/ranking" element={<ATSRankingPage />} />
                <Route path="/jobs/create" element={<JobCreatePage />} />
              </Route>
            </Routes>
          </div>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
