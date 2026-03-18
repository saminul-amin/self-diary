export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-indigo-50 to-white px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-indigo-600">SelfDiary</h1>
          <p className="mt-2 text-sm text-gray-500">Your private digital journal</p>
        </div>
        <div className="rounded-xl bg-white p-6 shadow-lg">{children}</div>
      </div>
    </div>
  );
}
