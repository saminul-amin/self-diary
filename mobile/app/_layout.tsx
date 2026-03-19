import React from 'react';
import { Slot } from 'expo-router';
import QueryProvider from '@/providers/query-provider';
import AuthProvider from '@/providers/auth-provider';

export default function RootLayout() {
  return (
    <QueryProvider>
      <AuthProvider>
        <Slot />
      </AuthProvider>
    </QueryProvider>
  );
}
