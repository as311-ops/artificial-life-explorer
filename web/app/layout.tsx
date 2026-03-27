import type { Metadata, Viewport } from 'next';
import { Geist_Mono } from 'next/font/google';
import { TabBar } from '@/components/TabBar';
import { SimulationProvider } from '@/components/SimulationProvider';
import './globals.css';

const geistMono = Geist_Mono({ subsets: ['latin'], variable: '--font-mono' });

export const metadata: Metadata = {
  title: 'ALife Simulator',
  description: 'BFF Universe Visualization',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'ALife',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  themeColor: '#06D6A0',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" className={`${geistMono.variable} dark`}>
      <body className="bg-[#0d0d0d] text-[#e8e8e8] min-h-screen antialiased">
        <SimulationProvider>
          <main className="pb-[calc(49px+env(safe-area-inset-bottom))] pt-[env(safe-area-inset-top)]">
            {children}
          </main>
          <TabBar />
        </SimulationProvider>
      </body>
    </html>
  );
}
