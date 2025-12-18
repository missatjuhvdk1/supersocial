'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { campaignsAPI } from '@/lib/api';
import Card, { CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { Plus, Play, Pause, Trash2 } from 'lucide-react';
import { formatDate } from '@/lib/utils';

export default function CampaignsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: campaigns, isLoading } = useQuery({
    queryKey: ['campaigns'],
    queryFn: async () => {
      // Placeholder data
      return [
        {
          id: '1',
          name: 'Morning Posts',
          status: 'active',
          videosCount: 10,
          accountsCount: 5,
          completedJobs: 45,
          totalJobs: 50,
          schedule: '08:00 - 12:00',
          createdAt: '2024-01-10T08:00:00Z',
        },
        {
          id: '2',
          name: 'Evening Content',
          status: 'paused',
          videosCount: 8,
          accountsCount: 3,
          completedJobs: 20,
          totalJobs: 24,
          schedule: '18:00 - 22:00',
          createdAt: '2024-01-12T18:00:00Z',
        },
        {
          id: '3',
          name: 'Weekend Special',
          status: 'completed',
          videosCount: 5,
          accountsCount: 10,
          completedJobs: 50,
          totalJobs: 50,
          schedule: 'All day',
          createdAt: '2024-01-08T00:00:00Z',
        },
      ];
    },
  });

  const startMutation = useMutation({
    mutationFn: (id: string) => campaignsAPI.start(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });

  const pauseMutation = useMutation({
    mutationFn: (id: string) => campaignsAPI.pause(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => campaignsAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'warning' | 'default'> = {
      active: 'success',
      paused: 'warning',
      completed: 'default',
    };
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>;
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Campaigns</h1>
          <p className="text-muted mt-2">Manage your posting campaigns</p>
        </div>
        <Button onClick={() => router.push('/campaigns/new')}>
          <Plus size={16} className="mr-2" />
          New Campaign
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Campaigns ({campaigns?.length || 0})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Videos</TableHead>
                <TableHead>Accounts</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Schedule</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {campaigns?.map((campaign) => (
                <TableRow key={campaign.id}>
                  <TableCell className="font-medium">{campaign.name}</TableCell>
                  <TableCell>{getStatusBadge(campaign.status)}</TableCell>
                  <TableCell>{campaign.videosCount}</TableCell>
                  <TableCell>{campaign.accountsCount}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-background rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-primary-500 h-full"
                          style={{
                            width: `${(campaign.completedJobs / campaign.totalJobs) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="text-sm text-muted">
                        {campaign.completedJobs}/{campaign.totalJobs}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-muted">{campaign.schedule}</TableCell>
                  <TableCell className="text-muted">
                    {formatDate(campaign.createdAt)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {campaign.status === 'active' ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => pauseMutation.mutate(campaign.id)}
                        >
                          <Pause size={16} />
                        </Button>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => startMutation.mutate(campaign.id)}
                        >
                          <Play size={16} />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteMutation.mutate(campaign.id)}
                      >
                        <Trash2 size={16} />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
