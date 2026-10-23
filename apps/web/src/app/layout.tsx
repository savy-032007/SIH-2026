import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'APAAR Platform',
  description:
    'AICTE student data management and verification platform. Development build — all data is synthetic.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // Phase 4 replaces this with the next-intl provider and a lang attribute driven
  // by the locale cookie (SPEC section 11).
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
