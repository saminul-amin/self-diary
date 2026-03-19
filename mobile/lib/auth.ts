/**
 * Token storage using expo-secure-store.
 *
 * Unlike the web client (in-memory only), mobile persists tokens
 * in the device keychain/keystore so the user stays authenticated
 * across app restarts.
 */
import * as SecureStore from 'expo-secure-store';
import axios from 'axios';

const ACCESS_KEY = 'selfdiary_access_token';
const REFRESH_KEY = 'selfdiary_refresh_token';

const API_BASE = (process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000') + '/v1';

// In-memory cache to avoid async SecureStore reads on every request
let accessToken: string | null = null;
let refreshToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function getRefreshToken(): string | null {
  return refreshToken;
}

export async function setTokens(access: string, refresh: string): Promise<void> {
  accessToken = access;
  refreshToken = refresh;
  await SecureStore.setItemAsync(ACCESS_KEY, access);
  await SecureStore.setItemAsync(REFRESH_KEY, refresh);
}

export async function clearTokens(): Promise<void> {
  accessToken = null;
  refreshToken = null;
  await SecureStore.deleteItemAsync(ACCESS_KEY);
  await SecureStore.deleteItemAsync(REFRESH_KEY);
}

/** Load tokens from SecureStore into memory (called on app startup). */
export async function loadTokens(): Promise<boolean> {
  const access = await SecureStore.getItemAsync(ACCESS_KEY);
  const refresh = await SecureStore.getItemAsync(REFRESH_KEY);
  if (access && refresh) {
    accessToken = access;
    refreshToken = refresh;
    return true;
  }
  return false;
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
    await setTokens(access_token, newRefresh);
    return access_token;
  } catch {
    await clearTokens();
    return null;
  }
}
