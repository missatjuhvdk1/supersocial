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

interface Job {
  id: string;
  campaignId: number;
  accountId: number;
  videoPath: string;
  caption: string;
  status: string;
  errorMessage: string | null;
  retryCount: number;
  maxRetries: number;
  createdAt: string;
  startedAt: string | null;
  completedAt: string | null;
}

export default function JobsPage() {
  const [statusFilter, setStatusFilter] = useState('all');
  const queryClient = useQueryClient();

  const { data: jobs, isLoading } = useQuery<Job[]>({
    queryKey: ['jobs', statusFilter],
    queryFn: async (): Promise<Job[]> => {
      const response = await jobsAPI.getAll({ status: statusFilter });
      // Map backend response to frontend format
      return response.data.map((job: any): Job => ({
        id: String(job.id),
        campaignId: job.campaign_id,
        accountId: job.account_id,
        videoPath: job.video_path,
        caption: job.caption,
        status: job.status,
        errorMessage: job.error_message,
        retryCount: job.retry_count,
        maxRetries: job.max_retries,
        createdAt: job.created_at,
        startedAt: job.started_at,
        completedAt: job.completed_at,
      }));
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
    const variants: Record<string, 'success' | 'warning' | 'info' | 'error' | 'default'> = {
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
                { value: 'cancelled', label: 'Cancelled' },
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
                <TableHead>Campaign ID</TableHead>
                <TableHead>Account ID</TableHead>
                <TableHead>Video/Caption</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Retries</TableHead>
                <TableHead>Created At</TableHead>
                <TableHead>Started At</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs?.map((job) => (
                <TableRow key={job.id}>
                  <TableCell className="font-medium">#{job.campaignId}</TableCell>
                  <TableCell className="text-muted">#{job.accountId}</TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      <span className="text-muted text-sm font-mono truncate max-w-xs" title={job.videoPath}>
                        {job.videoPath.split('/').pop() || job.videoPath}
                      </span>
                      {job.caption && (
                        <span className="text-xs text-muted truncate max-w-xs" title={job.caption}>
                          {job.caption}
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      {getStatusBadge(job.status)}
                      {job.errorMessage && (
                        <span className="text-xs text-error">{job.errorMessage}</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-muted">
                    {job.retryCount}/{job.maxRetries}
                  </TableCell>
                  <TableCell className="text-muted">
                    {formatDate(job.createdAt)}
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
