import React from 'react';
import { Slot } from 'expo-router';
import QueryProvider from '@/providers/query-provider';
import AuthProvider from '@/providers/auth-provider';
import SyncProvider from '@/providers/sync-provider';
import ConflictResolutionModal from '@/components/ConflictResolutionModal';

export default function RootLayout() {
  return (
    <QueryProvider>
      <AuthProvider>
        <SyncProvider>
          <Slot />
          <ConflictResolutionModal />
        </SyncProvider>
      </AuthProvider>
    </QueryProvider>
  );
}
