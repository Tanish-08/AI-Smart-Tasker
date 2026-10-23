import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Navbar from '@/components/Navbar';

const inter = Inter({ subsets: ['latin'], display: 'swap' });

export const metadata: Metadata = {
  title: 'AI Task Manager - Stay Accountable',
  description: 'Intelligent task management with AI-powered motivation and insights. Never miss a deadline again.',
  keywords: 'task manager, AI, productivity, deadline tracking, task analytics',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          <Navbar />
          <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
          <footer className="bg-white border-t border-gray-200 py-6 mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <p className="text-center text-sm text-gray-600">
                &copy; {new Date().getFullYear()} AI Task Manager. Built with Next.js and FastAPI.
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
