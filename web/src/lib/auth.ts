/**
 * In-memory token storage and refresh logic.
 *
 * Tokens are NEVER stored in localStorage to prevent XSS leakage.
 * They live in module-scoped variables and are lost on page refresh
 * (the user re-authenticates or a refresh token cookie could be used
 * in a future enhancement).
 */
import axios from 'axios';

let accessToken: string | null = null;
let refreshToken: string | null = null;

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000') + '/v1';

export function getAccessToken(): string | null {
  return accessToken;
}

export function getRefreshToken(): string | null {
  return refreshToken;
}

export function setTokens(access: string, refresh: string): void {
  accessToken = access;
  refreshToken = refresh;
}

export function clearTokens(): void {
  accessToken = null;
  refreshToken = null;
}

/**
 * Attempt to get a new access token using the stored refresh token.
 * Returns the new access token, or null if refresh fails.
 */
export async function refreshAccessToken(): Promise<string | null> {
  if (!refreshToken) return null;

  try {
    const response = await axios.post(`${API_BASE}/auth/refresh`, {
      refresh_token: refreshToken,
    });
    const { access_token, refresh_token: newRefresh } = response.data;
    setTokens(access_token, newRefresh);
    return access_token;
  } catch {
    clearTokens();
    return null;
  }
}
