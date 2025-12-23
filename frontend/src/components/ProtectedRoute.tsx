import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Spinner } from "./ui/Spinner";

interface ProtectedRouteProps {
  allowedRoles?: Array<"applicant" | "recruiter">;
  redirectPath?: string;
}

export const ProtectedRoute = ({
  allowedRoles,
  redirectPath = "/login",
}: ProtectedRouteProps) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to={redirectPath} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    const fallback = user.role === "recruiter" ? "/chatbot" : "/jobs";
    return <Navigate to={fallback} replace />;
  }

  return <Outlet />;
};
