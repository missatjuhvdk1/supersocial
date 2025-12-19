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

interface Campaign {
  id: string;
  name: string;
  status: string;
  videoPath: string;
  captionTemplate: string;
  accountSelection: {
    strategy: string;
    filters: any;
    maxAccounts: number;
  };
  schedule: {
    startTime: string;
    endTime: string;
    intervalMinutes: number;
  };
  createdAt: string;
  updatedAt: string;
  startedAt: string | null;
  completedAt: string | null;
}

export default function CampaignsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: campaigns, isLoading } = useQuery<Campaign[]>({
    queryKey: ['campaigns'],
    queryFn: async (): Promise<Campaign[]> => {
      const response = await campaignsAPI.getAll();
      // Map backend response to frontend format
      return response.data.map((campaign: any): Campaign => ({
        id: String(campaign.id),
        name: campaign.name,
        status: campaign.status,
        videoPath: campaign.video_path,
        captionTemplate: campaign.caption_template,
        accountSelection: {
          strategy: campaign.account_selection.strategy,
          filters: campaign.account_selection.filters,
          maxAccounts: campaign.account_selection.max_accounts,
        },
        schedule: {
          startTime: campaign.schedule.start_time,
          endTime: campaign.schedule.end_time,
          intervalMinutes: campaign.schedule.interval_minutes,
        },
        createdAt: campaign.created_at,
        updatedAt: campaign.updated_at,
        startedAt: campaign.started_at,
        completedAt: campaign.completed_at,
      }));
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
    const variants: Record<string, 'success' | 'warning' | 'default' | 'error'> = {
      draft: 'default',
      running: 'success',
      paused: 'warning',
      completed: 'default',
      cancelled: 'error',
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
                <TableHead>Max Accounts</TableHead>
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
                  <TableCell>{campaign.accountSelection.maxAccounts}</TableCell>
                  <TableCell className="text-muted">
                    {campaign.schedule.startTime} - {campaign.schedule.endTime}
                    <span className="text-xs ml-2">
                      (every {campaign.schedule.intervalMinutes}m)
                    </span>
                  </TableCell>
                  <TableCell className="text-muted">
                    {formatDate(campaign.createdAt)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {campaign.status === 'running' ? (
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
                          disabled={campaign.status === 'completed' || campaign.status === 'cancelled'}
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
