import { Link, NavLink, useNavigate } from "react-router-dom";
import { useState, useEffect, useMemo } from "react";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "./ui/Button";
import { cn } from "@/utils/helpers";

export const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 16);
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navItems = useMemo(() => {
    if (!user) return [];
    if (user.role === "recruiter") {
      return [
        { label: "AI Assistant", to: "/chatbot" },
        { label: "ATS Ranking", to: "/ranking" },
        { label: "Create Role", to: "/jobs/create" },
      ];
    }

    return [
      { label: "Job Listings", to: "/jobs" },
      { label: "My Applications", to: "/applications" },
    ];
  }, [user]);

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <header
      className={cn(
        "sticky top-0 z-50 transition-all duration-500",
        isScrolled
          ? "backdrop-blur-xl bg-[#06071a]/85 border-b border-white/10 shadow-[0_10px_40px_rgba(6,7,26,0.35)]"
          : "bg-transparent border-b border-transparent"
      )}
    >
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
        <Link to="/" className="flex flex-col gap-[2px] text-white">
          <span className="text-lg font-semibold tracking-tight">
            RecruitAI Studio
          </span>
          <span className="text-[11px] uppercase tracking-[0.45em] text-white/50">
            orchestrate talent
          </span>
        </Link>

        {user ? (
          <nav className="hidden items-center gap-8 text-sm font-medium text-white/60 md:flex">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "transition-colors hover:text-white",
                    isActive ? "text-white" : "text-white/60"
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        ) : (
          <div className="hidden text-sm text-white/60 md:block">
            Log in or create an account to explore the platform.
          </div>
        )}

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <span className="hidden text-sm text-white/60 sm:inline-flex">
                {user.email}
              </span>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            </>
          ) : (
            <div className="flex items-center gap-3">
              <Link
                to="/login"
                className="hidden text-sm text-white/60 transition hover:text-white sm:inline-flex"
              >
                Sign in
              </Link>
              <Link to="/signup">
                <Button size="sm">Create account</Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
