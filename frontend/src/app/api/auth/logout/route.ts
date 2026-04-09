import { NextResponse } from "next/server";

const COOKIE_NAME = process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME || "deepagents_token";

export async function POST() {
  const response = NextResponse.json({ success: true });

  response.cookies.set(COOKIE_NAME, "", {
    expires: new Date(0),
    path: "/",
  });

  return response;
}