import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { useRouter, useSegments } from 'expo-router';
import apiClient from '@/lib/api-client';
import { setTokens, clearTokens, loadTokens, getRefreshToken } from '@/lib/auth';
import type { User } from '@/types/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const segments = useSegments();

  // On mount, load tokens from SecureStore and fetch user
  useEffect(() => {
    (async () => {
      const hasTokens = await loadTokens();
      if (hasTokens) {
        try {
          const res = await apiClient.get('/auth/me');
          setUser(res.data);
        } catch {
          setUser(null);
        }
      }
      setIsLoading(false);
    })();
  }, []);

  // Protect routes: redirect based on auth state
  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === '(auth)';

    if (!user && !inAuthGroup) {
      router.replace('/(auth)/login');
    } else if (user && inAuthGroup) {
      router.replace('/(tabs)');
    }
  }, [user, segments, isLoading, router]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await apiClient.post('/auth/login', { email, password });
    const { user: userData, tokens } = res.data;
    await setTokens(tokens.access_token, tokens.refresh_token);
    setUser(userData);
  }, []);

  const register = useCallback(async (email: string, password: string, displayName?: string) => {
    const res = await apiClient.post('/auth/register', {
      email,
      password,
      display_name: displayName || null,
    });
    const { user: userData, tokens } = res.data;
    await setTokens(tokens.access_token, tokens.refresh_token);
    setUser(userData);
  }, []);

  const logout = useCallback(async () => {
    const refresh = getRefreshToken();
    try {
      if (refresh) {
        await apiClient.post('/auth/logout', { refresh_token: refresh });
      }
    } finally {
      await clearTokens();
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
