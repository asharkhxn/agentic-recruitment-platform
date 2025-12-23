import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { authApi } from "@/api/auth";
import { supabase } from "@/lib/supabase";
import { User, AuthResponse } from "@/types";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<AuthResponse>;
  signup: (
    email: string,
    password: string,
    firstName: string,
    lastName: string,
    role: "applicant" | "recruiter"
  ) => Promise<AuthResponse>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const toUser = (sessionUser: any): User => ({
  id: sessionUser.id,
  email: sessionUser.email!,
  role: sessionUser.user_metadata?.role || "applicant",
  full_name:
    sessionUser.user_metadata?.full_name ||
    [
      sessionUser.user_metadata?.first_name,
      sessionUser.user_metadata?.last_name,
    ]
      .filter(Boolean)
      .join(" ") ||
    undefined,
});

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();

        if (session?.user) {
          const userData = toUser(session.user);
          setUser(userData);
          localStorage.setItem("user", JSON.stringify(userData));
          localStorage.setItem("access_token", session.access_token);
        } else {
          const currentUser = authApi.getCurrentUser();
          setUser(currentUser);
        }
      } catch (error) {
        console.error("Session check error:", error);
        const currentUser = authApi.getCurrentUser();
        setUser(currentUser);
      } finally {
        setLoading(false);
      }
    };

    checkSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        const userData = toUser(session.user);
        setUser(userData);
        localStorage.setItem("user", JSON.stringify(userData));
        localStorage.setItem("access_token", session.access_token);
      } else {
        setUser(null);
        localStorage.removeItem("user");
        localStorage.removeItem("access_token");
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const login = async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    localStorage.setItem("access_token", response.access_token);
    localStorage.setItem("user", JSON.stringify(response.user));
    setUser(response.user);
    return response;
  };

  const signup = async (
    email: string,
    password: string,
    firstName: string,
    lastName: string,
    role: "applicant" | "recruiter"
  ) => {
    const response = await authApi.signup(
      email,
      password,
      firstName,
      lastName,
      role
    );
    localStorage.setItem("access_token", response.access_token);
    localStorage.setItem("user", JSON.stringify(response.user));
    setUser(response.user);
    return response;
  };

  const logout = async () => {
    await authApi.logout();
    setUser(null);
  };

  const value = useMemo(
    () => ({ user, loading, login, signup, logout }),
    [user, loading]
  );

  return React.createElement(AuthContext.Provider, { value }, children);
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
