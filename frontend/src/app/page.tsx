'use client';

import { useQuery } from '@tanstack/react-query';
import { statsAPI } from '@/lib/api';
import Card, { CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Users, Globe, Megaphone, CheckCircle, XCircle, Clock } from 'lucide-react';

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      // Placeholder data - replace with actual API call
      return {
        accounts: { total: 45, active: 38, inactive: 7 },
        proxies: { total: 30, working: 28, failed: 2 },
        campaigns: { total: 12, active: 5, completed: 7 },
        jobs: { pending: 23, running: 3, completed: 156, failed: 8 },
      };
    },
  });

  const statCards = [
    {
      title: 'Accounts',
      icon: Users,
      value: stats?.accounts.total || 0,
      active: stats?.accounts.active || 0,
      inactive: stats?.accounts.inactive || 0,
      color: 'text-primary-500',
    },
    {
      title: 'Proxies',
      icon: Globe,
      value: stats?.proxies.total || 0,
      active: stats?.proxies.working || 0,
      inactive: stats?.proxies.failed || 0,
      color: 'text-accent-500',
    },
    {
      title: 'Campaigns',
      icon: Megaphone,
      value: stats?.campaigns.total || 0,
      active: stats?.campaigns.active || 0,
      inactive: stats?.campaigns.completed || 0,
      color: 'text-purple-500',
    },
  ];

  const jobStats = [
    { label: 'Pending', value: stats?.jobs.pending || 0, icon: Clock, color: 'text-yellow-500' },
    { label: 'Running', value: stats?.jobs.running || 0, icon: CheckCircle, color: 'text-blue-500' },
    { label: 'Completed', value: stats?.jobs.completed || 0, icon: CheckCircle, color: 'text-green-500' },
    { label: 'Failed', value: stats?.jobs.failed || 0, icon: XCircle, color: 'text-red-500' },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-muted mt-2">Overview of your TikTok automation system</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-muted">{stat.title}</h3>
                  <Icon className={stat.color} size={24} />
                </div>
                <div className="text-3xl font-bold text-white mb-2">{stat.value}</div>
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-green-500">{stat.active} active</span>
                  <span className="text-red-500">{stat.inactive} inactive</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Job Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {jobStats.map((stat) => {
              const Icon = stat.icon;
              return (
                <div key={stat.label} className="flex items-center gap-4">
                  <Icon className={stat.color} size={32} />
                  <div>
                    <div className="text-2xl font-bold text-white">{stat.value}</div>
                    <div className="text-sm text-muted">{stat.label}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <div className="mt-8">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center gap-4 p-4 bg-background rounded-lg">
                  <div className="w-2 h-2 bg-primary-500 rounded-full" />
                  <div className="flex-1">
                    <p className="text-white text-sm">Posted video to @account_{i}</p>
                    <p className="text-muted text-xs mt-1">{i} minutes ago</p>
                  </div>
                  <span className="text-green-500 text-sm">Success</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
