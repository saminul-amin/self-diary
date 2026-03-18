import RegisterForm from '@/components/auth/register-form';
import Link from 'next/link';

export const metadata = { title: 'Create account — SelfDiary' };

export default function RegisterPage() {
  return (
    <>
      <h2 className="mb-6 text-xl font-semibold text-gray-900">Create your account</h2>
      <RegisterForm />
      <p className="mt-4 text-center text-sm text-gray-500">
        Already have an account?{' '}
        <Link href="/login" className="font-medium text-indigo-600 hover:text-indigo-500">
          Sign in
        </Link>
      </p>
    </>
  );
}
