'use client';

import Button from '@/components/ui/button';
import { useAuth } from '@/providers/auth-provider';
import { formatDate } from '@/lib/utils';

export default function SettingsPage() {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      <div className="rounded-xl bg-white border border-gray-200 shadow-sm p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Profile</h2>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-sm text-gray-500">Display name</dt>
              <dd className="text-sm font-medium text-gray-900">{user.display_name || '—'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-500">Email</dt>
              <dd className="text-sm font-medium text-gray-900">{user.email}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-500">Member since</dt>
              <dd className="text-sm font-medium text-gray-900">{formatDate(user.created_at)}</dd>
            </div>
          </dl>
        </div>

        <hr className="border-gray-200" />

        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Account</h2>
          <p className="text-sm text-gray-500 mb-4">
            Signing out will clear your session on this device.
          </p>
          <Button variant="danger" onClick={logout}>
            Sign Out
          </Button>
        </div>
      </div>
    </div>
  );
}
