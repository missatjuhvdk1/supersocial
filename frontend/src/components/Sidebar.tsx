'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  Globe,
  Megaphone,
  ListTodo,
  Settings,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { href: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/accounts', icon: Users, label: 'Accounts' },
  { href: '/proxies', icon: Globe, label: 'Proxies' },
  { href: '/campaigns', icon: Megaphone, label: 'Campaigns' },
  { href: '/jobs', icon: ListTodo, label: 'Jobs' },
  { href: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="w-64 h-screen bg-surface border-r border-border fixed left-0 top-0">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-white">
          TikTok<span className="text-primary-500">Auto</span>
        </h1>
        <p className="text-sm text-muted mt-1">Auto Poster Dashboard</p>
      </div>

      <nav className="px-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-muted hover:text-white hover:bg-surface-hover'
              )}
            >
              <Icon size={20} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold">
            A
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-white">Admin</p>
            <p className="text-xs text-muted">admin@example.com</p>
          </div>
        </div>
      </div>
    </div>
  );
}
