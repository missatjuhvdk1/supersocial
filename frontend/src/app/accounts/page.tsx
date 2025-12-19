'use client';

import { useState, useMemo } from 'react';
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

interface Account {
  id: string;
  email: string;
  status: string;
  proxy: string | null;
  lastUsed: string | null;
  createdAt: string;
}

export default function AccountsPage() {
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const queryClient = useQueryClient();

  const { data: accountsData, isLoading } = useQuery<Account[]>({
    queryKey: ['accounts'],
    queryFn: async (): Promise<Account[]> => {
      const response = await accountsAPI.getAll();
      // Map backend response to frontend format
      return response.data.map((account: any): Account => ({
        id: String(account.id),
        email: account.email,
        status: account.status,
        proxy: account.proxy_id ? `Proxy #${account.proxy_id}` : null,
        lastUsed: account.last_used,
        createdAt: account.created_at,
      }));
    },
  });

  // Client-side filtering by status
  const accounts = useMemo(() => {
    if (!accountsData) return [];
    if (statusFilter === 'all') return accountsData;
    return accountsData.filter(account => account.status === statusFilter);
  }, [accountsData, statusFilter]);

  const [importError, setImportError] = useState<string | null>(null);
  const [importSuccess, setImportSuccess] = useState<string | null>(null);

  const importMutation = useMutation({
    mutationFn: (file: File) => accountsAPI.import(file),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      const count = response.data?.length || 0;
      setImportSuccess(`Successfully imported ${count} accounts!`);
      setImportError(null);
      setSelectedFile(null);
      setTimeout(() => {
        setIsImportModalOpen(false);
        setImportSuccess(null);
      }, 2000);
    },
    onError: (error: any) => {
      setImportError(error.response?.data?.detail || error.message || 'Import failed');
      setImportSuccess(null);
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
                <TableHead>Status</TableHead>
                <TableHead>Proxy</TableHead>
                <TableHead>Last Used</TableHead>
                <TableHead>Created At</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted py-8">
                    Loading accounts...
                  </TableCell>
                </TableRow>
              ) : accounts?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted py-8">
                    No accounts found. Import some accounts to get started.
                  </TableCell>
                </TableRow>
              ) : (
                accounts?.map((account) => (
                  <TableRow key={account.id}>
                    <TableCell className="font-medium">{account.email}</TableCell>
                    <TableCell>{getStatusBadge(account.status)}</TableCell>
                    <TableCell className="text-muted">
                      {account.proxy || 'Not assigned'}
                    </TableCell>
                    <TableCell className="text-muted">
                      {account.lastUsed ? formatDate(account.lastUsed) : 'Never'}
                    </TableCell>
                    <TableCell className="text-muted">
                      {formatDate(account.createdAt)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteMutation.mutate(account.id)}
                          isLoading={deleteMutation.isPending}
                        >
                          <Trash2 size={16} />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Modal
        isOpen={isImportModalOpen}
        onClose={() => {
          setIsImportModalOpen(false);
          setImportError(null);
          setImportSuccess(null);
          setSelectedFile(null);
        }}
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
          <div className="text-muted text-sm space-y-2">
            <p>Upload a CSV file with columns: email, password, status (optional), proxy_id (optional), profile_id (optional)</p>
            <div className="bg-gray-800 rounded p-3 font-mono text-xs space-y-1">
              <p className="text-green-400"># CSV Example:</p>
              <p>email,password,status,proxy_id,profile_id</p>
              <p>user1@example.com,password123,active,1,</p>
              <p>user2@example.com,password456,active,,</p>
            </div>
          </div>

          {importError && (
            <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm">
              {importError}
            </div>
          )}

          {importSuccess && (
            <div className="bg-green-500/10 border border-green-500/50 rounded-lg p-3 text-green-400 text-sm">
              {importSuccess}
            </div>
          )}

          <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => {
                setSelectedFile(e.target.files?.[0] || null);
                setImportError(null);
              }}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <Upload size={48} className="mx-auto text-muted mb-4" />
              <p className="text-white font-medium mb-1">
                {selectedFile ? selectedFile.name : 'Click to upload CSV file'}
              </p>
              <p className="text-muted text-sm">Accepts .csv files</p>
            </label>
          </div>
        </div>
      </Modal>
    </div>
  );
}
