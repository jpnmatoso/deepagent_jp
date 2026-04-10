import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_DEPLOYMENT_URL || "http://localhost:8101";
const COOKIE_NAME = process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME || "deepagents_token";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    console.log("[Auth] Attempting login to:", BACKEND_URL);

    const response = await fetch(`${BACKEND_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: body.username,
        password: body.password,
      }),
    });

    console.log("[Auth] Response status:", response.status);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      console.log("[Auth] Error response:", error);
      return NextResponse.json(
        { detail: error.detail || "Login failed" },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log("[Auth] Login successful!");

    const expiresAt = data.expires_at
      ? new Date(data.expires_at)
      : new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

    const response_ = NextResponse.json(data);

    response_.cookies.set(COOKIE_NAME, data.token, {
      expires: expiresAt,
      httpOnly: false,
      sameSite: "strict",
      path: "/",
    });

    return response_;
  } catch (error) {
    console.error("Login error:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}