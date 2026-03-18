import LoginForm from '@/components/auth/login-form';
import Link from 'next/link';

export const metadata = { title: 'Sign in — SelfDiary' };

export default function LoginPage() {
  return (
    <>
      <h2 className="mb-6 text-xl font-semibold text-gray-900">Sign in to your account</h2>
      <LoginForm />
      <p className="mt-4 text-center text-sm text-gray-500">
        Don&apos;t have an account?{' '}
        <Link href="/register" className="font-medium text-indigo-600 hover:text-indigo-500">
          Create one
        </Link>
      </p>
    </>
  );
}
