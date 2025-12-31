import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Authentication - TikTok Auto Poster',
  description: 'Login or register to access TikTok Auto Poster',
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        {/* Branding */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            TikTok Auto Poster
          </h1>
          <p className="text-gray-400">
            Automate your TikTok content posting
          </p>
        </div>

        {children}
      </div>
    </div>
  );
}
