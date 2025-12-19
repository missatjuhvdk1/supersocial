'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accountsAPI } from '@/lib/api';
import Card, { CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import Modal from '@/components/ui/Modal';
import Select from '@/components/ui/Select';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { Upload, MoreVertical, Trash2, RefreshCw } from 'lucide-react';
import { formatDate } from '@/lib/utils';

export default function AccountsPage() {
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const queryClient = useQueryClient();

  const { data: accounts, isLoading } = useQuery({
    queryKey: ['accounts', statusFilter],
    queryFn: async () => {
      // Placeholder data - replace with actual API call
      return [
        {
          id: '1',
          email: 'user1@tiktok.com',
          username: '@user1',
          status: 'active',
          proxy: '123.45.67.89:8080',
          lastUsed: '2024-01-15T10:30:00Z',
          postsCount: 45,
        },
        {
          id: '2',
          email: 'user2@tiktok.com',
          username: '@user2',
          status: 'active',
          proxy: '123.45.67.90:8080',
          lastUsed: '2024-01-15T09:15:00Z',
          postsCount: 32,
        },
        {
          id: '3',
          email: 'user3@tiktok.com',
          username: '@user3',
          status: 'banned',
          proxy: '123.45.67.91:8080',
          lastUsed: '2024-01-14T18:20:00Z',
          postsCount: 12,
        },
        {
          id: '4',
          email: 'user4@tiktok.com',
          username: '@user4',
          status: 'inactive',
          proxy: null,
          lastUsed: null,
          postsCount: 0,
        },
      ];
    },
  });

  const importMutation = useMutation({
    mutationFn: (file: File) => accountsAPI.import(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      setIsImportModalOpen(false);
      setSelectedFile(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => accountsAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });

  const handleImport = () => {
    if (selectedFile) {
      importMutation.mutate(selectedFile);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'error' | 'warning' | 'default'> = {
      active: 'success',
      banned: 'error',
      inactive: 'warning',
      pending: 'default',
    };
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>;
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">TikTok Accounts</h1>
          <p className="text-muted mt-2">Manage your TikTok accounts</p>
        </div>
        <Button onClick={() => setIsImportModalOpen(true)}>
          <Upload size={16} className="mr-2" />
          Import Accounts
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Accounts ({accounts?.length || 0})</CardTitle>
            <Select
              options={[
                { value: 'all', label: 'All Statuses' },
                { value: 'active', label: 'Active' },
                { value: 'inactive', label: 'Inactive' },
                { value: 'banned', label: 'Banned' },
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
                <TableHead>Email</TableHead>
                <TableHead>Username</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Proxy</TableHead>
                <TableHead>Posts</TableHead>
                <TableHead>Last Used</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {accounts?.map((account) => (
                <TableRow key={account.id}>
                  <TableCell className="font-medium">{account.email}</TableCell>
                  <TableCell>{account.username}</TableCell>
                  <TableCell>{getStatusBadge(account.status)}</TableCell>
                  <TableCell className="text-muted">
                    {account.proxy || 'Not assigned'}
                  </TableCell>
                  <TableCell>{account.postsCount}</TableCell>
                  <TableCell className="text-muted">
                    {account.lastUsed ? formatDate(account.lastUsed) : 'Never'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm">
                        <RefreshCw size={16} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteMutation.mutate(account.id)}
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

      <Modal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        title="Import Accounts"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsImportModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleImport}
              disabled={!selectedFile}
              isLoading={importMutation.isPending}
            >
              Import
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <p className="text-muted text-sm">
            Upload a CSV file with columns: email, password, username (optional)
          </p>
          <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <Upload size={48} className="mx-auto text-muted mb-4" />
              <p className="text-white font-medium mb-1">
                {selectedFile ? selectedFile.name : 'Click to upload CSV file'}
              </p>
              <p className="text-muted text-sm">or drag and drop</p>
            </label>
          </div>
        </div>
      </Modal>
    </div>
  );
}
