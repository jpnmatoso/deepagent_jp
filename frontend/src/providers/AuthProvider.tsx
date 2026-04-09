"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useCallback,
} from "react";
import { useRouter } from "next/navigation";
import { getAuthToken, removeAuthToken, isAuthenticated } from "@/lib/auth";

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, expiresAt?: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [isAuth, setIsAuth] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsAuth(isAuthenticated());
    setIsLoading(false);
  }, []);

  const login = useCallback((token: string, expiresAt?: string) => {
    const expires = expiresAt ? new Date(expiresAt) : undefined;
    const days = expires
      ? Math.ceil((expires.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
      : 7;
    
    const cookieName = process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME || "deepagents_token";
    const expiresDate = new Date(Date.now() + days * 24 * 60 * 60 * 1000).toUTCString();
    document.cookie = `${cookieName}=${token};expires=${expiresDate};path=/;SameSite=Strict`;
    
    setIsAuth(true);
    router.push("/");
  }, [router]);

  const logout = useCallback(async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch (error) {
      console.error("Logout API error:", error);
    }
    removeAuthToken();
    setIsAuth(false);
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: isAuth,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}