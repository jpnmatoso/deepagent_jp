import { redirect } from "next/navigation";

const AUTH_URL = process.env.NEXT_PUBLIC_AUTH_URL || "http://localhost:8101";
const COOKIE_NAME = process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME || "deepagents_token";

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  expires_at: string;
}

function getCookies(): Record<string, string> {
  if (typeof document === "undefined") return {};
  return Object.fromEntries(
    document.cookie.split(";").map((c) => {
      const [key, ...val] = c.trim().split("=");
      return [key, val.join("=")];
    })
  );
}

function setCookie(name: string, value: string, days: number = 7): void {
  if (typeof document === "undefined") return;
  const expires = new Date(Date.now() + days * 24 * 60 * 60 * 1000).toUTCString();
  document.cookie = `${name}=${value};expires=${expires};path=/;SameSite=Strict`;
}

function removeCookie(name: string): void {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
}

export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  const response = await fetch(`${AUTH_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username: credentials.username,
      password: credentials.password,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Login failed");
  }

  return response.json();
}

export function setAuthToken(token: string, expiresAt?: string): void {
  const expires = expiresAt ? new Date(expiresAt) : undefined;
  const days = expires
    ? Math.ceil((expires.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    : 7;
  setCookie(COOKIE_NAME, token, days > 0 ? days : 7);
}

export function getAuthToken(): string | undefined {
  const cookies = getCookies();
  return cookies[COOKIE_NAME];
}

export function removeAuthToken(): void {
  removeCookie(COOKIE_NAME);
}

export function isAuthenticated(): boolean {
  const token = getAuthToken();
  return !!token;
}

export async function logout(): Promise<void> {
  removeAuthToken();
  redirect("/login");
}

export function getAuthHeader(): Record<string, string> {
  const token = getAuthToken();
  if (!token) {
    return {};
  }
  return {
    Authorization: `Bearer ${token}`,
  };
}