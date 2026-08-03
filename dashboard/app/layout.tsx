import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Bybit UID Admin Dashboard',
  description: 'Premium admin dashboard for Bybit UID verification and Binance payouts.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
