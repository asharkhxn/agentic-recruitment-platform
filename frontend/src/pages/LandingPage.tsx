import { Link } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";

export const LandingPage = () => {
  const { user, loading } = useAuth();
  const showAuthCtas = !loading && !user;

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-[10%] top-[-160px] h-[360px] w-[360px] rounded-full bg-gradient-to-br from-[#6d6bff]/35 via-[#ad7bff]/30 to-[#fbc0ff]/25 blur-[160px]" />
        <div className="absolute right-[-140px] bottom-[-140px] h-[420px] w-[420px] rounded-full bg-gradient-to-br from-[#5c6cff]/20 via-[#977bff]/20 to-[#f7b6ff]/24 blur-[180px]" />
      </div>

      <section className="mx-auto flex min-h-[calc(100vh-5rem)] w-full max-w-6xl flex-col justify-center gap-10 px-6 py-24 text-white">
        <span className="accent-pill w-max">
          Orchestrate hiring intelligence
        </span>
        <div className="max-w-3xl space-y-6">
          <h1 className="text-4xl font-semibold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
            RecruitAI Studio aligns recruiters and applicants around the same
            source of truth.
          </h1>
          <p className="text-base text-white/70 sm:text-lg">
            From discovering roles to ranking talent, RecruitAI Studio keeps
            every step transparent. Log in to pick up where you left off or
            create an account to start orchestrating talent flows in minutes.
          </p>
        </div>

        {showAuthCtas && (
          <div className="flex flex-col gap-4 sm:flex-row">
            <Link to="/login">
              <Button size="lg" className="w-full sm:w-auto">
                Sign in
              </Button>
            </Link>
            <Link to="/signup">
              <Button
                variant="outline"
                size="lg"
                className="w-full border-white/30 text-white hover:text-white sm:w-auto"
              >
                Create an account
              </Button>
            </Link>
          </div>
        )}
      </section>
    </div>
  );
};
