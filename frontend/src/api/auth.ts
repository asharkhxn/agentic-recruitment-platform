import { supabase } from "@/lib/supabase";
import { AuthResponse } from "@/types";

export const authApi = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) throw error;

    return {
      access_token: data.session!.access_token,
      user: {
        id: data.user!.id,
        email: data.user!.email!,
        role: data.user!.user_metadata?.role || "applicant",
        full_name: data.user!.user_metadata?.full_name || undefined,
      },
    };
  },

  signup: async (
    email: string,
    password: string,
    firstName: string,
    lastName: string,
    role: "applicant" | "recruiter"
  ): Promise<AuthResponse> => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          role,
          first_name: firstName,
          last_name: lastName,
          full_name: `${firstName} ${lastName}`,
        },
      },
    });

    if (error) throw error;
    if (!data.user) throw new Error("Signup failed");

    return {
      access_token: data.session!.access_token,
      user: {
        id: data.user.id,
        email: data.user.email!,
        role,
        full_name: `${firstName} ${lastName}`,
      },
    };
  },

  logout: async (): Promise<void> => {
    await supabase.auth.signOut();
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
  },

  getCurrentUser: () => {
    const userStr = localStorage.getItem("user");
    return userStr ? JSON.parse(userStr) : null;
  },
};
