'use client';

import { useAuth } from '@/providers/auth-provider';

interface HeaderProps {
  onMenuToggle: () => void;
}

export default function Header({ onMenuToggle }: HeaderProps) {
  const { user } = useAuth();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-gray-200 bg-white px-4 md:px-6">
      <button
        type="button"
        onClick={onMenuToggle}
        className="md:hidden rounded-lg p-2 text-gray-500 hover:bg-gray-100"
        aria-label="Open menu"
      >
        <svg
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <div className="flex-1" />
      {user && (
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-sm font-semibold text-indigo-700">
            {(user.display_name ?? user.email)[0].toUpperCase()}
          </div>
          <span className="hidden sm:block text-sm font-medium text-gray-700">
            {user.display_name ?? user.email}
          </span>
        </div>
      )}
    </header>
  );
}
