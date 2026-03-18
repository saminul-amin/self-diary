'use client';

import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { setTokens, clearTokens, getRefreshToken } from '@/lib/auth';
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

  // On mount, try to fetch current user (token may still be in memory)
  useEffect(() => {
    apiClient
      .get('/auth/me')
      .then((res) => setUser(res.data))
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await apiClient.post('/auth/login', { email, password });
      const { user: userData, tokens } = res.data;
      setTokens(tokens.access_token, tokens.refresh_token);
      setUser(userData);
      router.push('/entries');
    },
    [router],
  );

  const register = useCallback(
    async (email: string, password: string, displayName?: string) => {
      const res = await apiClient.post('/auth/register', {
        email,
        password,
        display_name: displayName || null,
      });
      const { user: userData, tokens } = res.data;
      setTokens(tokens.access_token, tokens.refresh_token);
      setUser(userData);
      router.push('/entries');
    },
    [router],
  );

  const logout = useCallback(async () => {
    const refresh = getRefreshToken();
    try {
      if (refresh) {
        await apiClient.post('/auth/logout', { refresh_token: refresh });
      }
    } finally {
      clearTokens();
      setUser(null);
      router.push('/login');
    }
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
