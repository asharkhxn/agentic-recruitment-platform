import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Card, CardContent } from "@/components/ui/Card";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

export const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login, user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "Login - RecruitAI";
  }, []);

  useEffect(() => {
    if (!loading && user) {
      navigate(user.role === "recruiter" ? "/chatbot" : "/jobs", {
        replace: true,
      });
    }
  }, [user, loading, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const response = await login(email, password);
      const next = response.user.role === "recruiter" ? "/chatbot" : "/jobs";
      navigate(next, { replace: true });
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative flex min-h-[calc(100vh-5rem)] items-center justify-center px-6 py-24">
      <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute left-[-120px] top-[-140px] h-96 w-96 rounded-full bg-gradient-to-br from-[#6d6bff]/35 via-[#ad7bff]/30 to-[#fbc0ff]/25 blur-[140px]" />
        <div className="absolute right-[-160px] bottom-[-160px] h-[420px] w-[420px] rounded-full bg-gradient-to-br from-[#5c6cff]/20 via-[#977bff]/20 to-[#f7b6ff]/20 blur-[160px]" />
      </div>

      <div className="w-full max-w-lg">
        <Card>
          <CardContent className="space-y-8">
            <div className="space-y-4 text-center">
              <span className="accent-pill">Welcome back</span>
              <h2 className="text-3xl font-semibold tracking-tight text-white">
                Sign in to continue
              </h2>
              <p className="text-sm text-white/60">
                Access orchestrated job intelligence, chat with the assistant,
                and manage every candidate flow.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {error && <ErrorMessage message={error} />}

              <div className="space-y-2">
                <Label htmlFor="email" className="text-white/70">
                  Email address
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-white/70">
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? "Signing in…" : "Sign in"}
              </Button>

              <div className="text-center text-sm text-white/60">
                Don&apos;t have an account?{" "}
                <Link to="/signup" className="text-white hover:text-[#f4d3ff]">
                  Create one
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
