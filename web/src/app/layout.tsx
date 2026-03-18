import type { Metadata } from 'next';
import './globals.css';
import QueryProvider from '@/providers/query-provider';
import AuthProvider from '@/providers/auth-provider';

export const metadata: Metadata = {
  title: 'SelfDiary',
  description: 'Your private digital diary',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">
        <QueryProvider>
          <AuthProvider>{children}</AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
