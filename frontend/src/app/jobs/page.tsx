'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsAPI } from '@/lib/api';
import Card, { CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import Select from '@/components/ui/Select';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { RefreshCw, XCircle, Eye } from 'lucide-react';
import { formatDate } from '@/lib/utils';
import { useState } from 'react';

export default function JobsPage() {
  const [statusFilter, setStatusFilter] = useState('all');
  const queryClient = useQueryClient();

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs', statusFilter],
    queryFn: async () => {
      // Placeholder data
      return [
        {
          id: '1',
          campaignName: 'Morning Posts',
          accountEmail: 'user1@tiktok.com',
          videoName: 'video1.mp4',
          status: 'completed',
          progress: 100,
          scheduledFor: '2024-01-15T09:00:00Z',
          startedAt: '2024-01-15T09:00:05Z',
          completedAt: '2024-01-15T09:02:30Z',
          error: null,
        },
        {
          id: '2',
          campaignName: 'Evening Content',
          accountEmail: 'user2@tiktok.com',
          videoName: 'video2.mp4',
          status: 'running',
          progress: 65,
          scheduledFor: '2024-01-15T18:00:00Z',
          startedAt: '2024-01-15T18:00:10Z',
          completedAt: null,
          error: null,
        },
        {
          id: '3',
          campaignName: 'Morning Posts',
          accountEmail: 'user3@tiktok.com',
          videoName: 'video3.mp4',
          status: 'pending',
          progress: 0,
          scheduledFor: '2024-01-15T10:30:00Z',
          startedAt: null,
          completedAt: null,
          error: null,
        },
        {
          id: '4',
          campaignName: 'Weekend Special',
          accountEmail: 'user4@tiktok.com',
          videoName: 'video4.mp4',
          status: 'failed',
          progress: 45,
          scheduledFor: '2024-01-15T12:00:00Z',
          startedAt: '2024-01-15T12:00:08Z',
          completedAt: null,
          error: 'Account rate limited',
        },
      ];
    },
  });

  const retryMutation = useMutation({
    mutationFn: (id: string) => jobsAPI.retry(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => jobsAPI.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'warning' | 'info' | 'error'> = {
      completed: 'success',
      running: 'info',
      pending: 'warning',
      failed: 'error',
      cancelled: 'default',
    };
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>;
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Jobs Queue</h1>
          <p className="text-muted mt-2">Monitor posting jobs and their status</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>All Jobs ({jobs?.length || 0})</CardTitle>
            <Select
              options={[
                { value: 'all', label: 'All Statuses' },
                { value: 'pending', label: 'Pending' },
                { value: 'running', label: 'Running' },
                { value: 'completed', label: 'Completed' },
                { value: 'failed', label: 'Failed' },
              ]}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-48"
            />
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Campaign</TableHead>
                <TableHead>Account</TableHead>
                <TableHead>Video</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Scheduled For</TableHead>
                <TableHead>Started At</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs?.map((job) => (
                <TableRow key={job.id}>
                  <TableCell className="font-medium">{job.campaignName}</TableCell>
                  <TableCell className="text-muted">{job.accountEmail}</TableCell>
                  <TableCell className="text-muted">{job.videoName}</TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      {getStatusBadge(job.status)}
                      {job.error && (
                        <span className="text-xs text-error">{job.error}</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-background rounded-full h-2 overflow-hidden w-20">
                        <div
                          className="bg-primary-500 h-full transition-all"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                      <span className="text-sm text-muted">{job.progress}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-muted">
                    {formatDate(job.scheduledFor)}
                  </TableCell>
                  <TableCell className="text-muted">
                    {job.startedAt ? formatDate(job.startedAt) : '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm">
                        <Eye size={16} />
                      </Button>
                      {job.status === 'failed' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => retryMutation.mutate(job.id)}
                        >
                          <RefreshCw size={16} />
                        </Button>
                      )}
                      {(job.status === 'pending' || job.status === 'running') && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => cancelMutation.mutate(job.id)}
                        >
                          <XCircle size={16} />
                        </Button>
                      )}
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
