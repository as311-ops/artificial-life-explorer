'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const TABS = [
  { href: '/', label: 'Simulation', icon: '\u25C9' },
  { href: '/charts', label: 'Charts', icon: '\uD83D\uDCC8' },
  { href: '/settings', label: 'Settings', icon: '\u2699' },
] as const;

export function TabBar() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-[#0d0d0d] border-t border-[#1a1a1a] pb-[env(safe-area-inset-bottom)]">
      <div className="flex justify-around h-[49px]">
        {TABS.map(tab => {
          const isActive = tab.href === '/' ? pathname === '/' : pathname.startsWith(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`flex flex-col items-center justify-center flex-1 text-xs gap-0.5 ${
                isActive ? 'text-[#06D6A0]' : 'text-[#666]'
              }`}
            >
              <span className="text-lg">{tab.icon}</span>
              <span>{tab.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
