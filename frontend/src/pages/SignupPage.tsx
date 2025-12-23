import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Card, CardContent } from "@/components/ui/Card";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

export const SignupPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [role, setRole] = useState<"applicant" | "recruiter">("applicant");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { signup, user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "Sign Up - RecruitAI";
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
      const response = await signup(email, password, firstName, lastName, role);
      const next = response.user.role === "recruiter" ? "/chatbot" : "/jobs";
      navigate(next, { replace: true });
    } catch (err: any) {
      setError(err.message || "Signup failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative flex min-h-[calc(100vh-5rem)] items-center justify-center px-6 py-24">
      <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute left-[-180px] top-[-180px] h-[460px] w-[460px] rounded-full bg-gradient-to-br from-[#ffb8f5]/25 via-[#8c6dff]/25 to-[#5c6bff]/20 blur-[160px]" />
        <div className="absolute right-[-140px] bottom-[-160px] h-[360px] w-[360px] rounded-full bg-gradient-to-br from-[#6f6cff]/25 via-[#b27bff]/20 to-[#ffd9ff]/25 blur-[150px]" />
      </div>

      <div className="w-full max-w-3xl">
        <Card>
          <CardContent className="space-y-10">
            <div className="space-y-4 text-center">
              <span className="accent-pill">Create your profile</span>
              <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                Build your seat in the recruiting constellation.
              </h2>
              <p className="mx-auto max-w-2xl text-sm text-white/65 sm:text-base">
                Whether you&apos;re hiring or landing your next role, a
                RecruitAI account unlocks orchestrated workflows, AI copilots,
                and instant applicant intelligence.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {error && <ErrorMessage message={error} />}

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="firstName" className="text-white/70">
                    First name
                  </Label>
                  <Input
                    id="firstName"
                    type="text"
                    placeholder="Avery"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lastName" className="text-white/70">
                    Last name
                  </Label>
                  <Input
                    id="lastName"
                    type="text"
                    placeholder="Stone"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required
                  />
                </div>
              </div>

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
                  placeholder="Minimum 6 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                />
              </div>

              <div className="space-y-3">
                <Label className="text-white/70">I&apos;m here as</Label>
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-3 rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm text-white/80">
                    <input
                      type="radio"
                      value="applicant"
                      checked={role === "applicant"}
                      onChange={() => setRole("applicant")}
                      className="h-4 w-4 accent-[#8d6cff]"
                    />
                    <span>Applicant</span>
                  </label>
                  <label className="flex items-center gap-3 rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm text-white/80">
                    <input
                      type="radio"
                      value="recruiter"
                      checked={role === "recruiter"}
                      onChange={() => setRole("recruiter")}
                      className="h-4 w-4 accent-[#8d6cff]"
                    />
                    <span>Recruiter</span>
                  </label>
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? "Creating account…" : "Create account"}
              </Button>

              <div className="text-center text-sm text-white/60">
                Already have an account?{" "}
                <Link to="/login" className="text-white hover:text-[#f4d3ff]">
                  Sign in
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
