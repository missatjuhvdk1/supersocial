'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { proxiesAPI } from '@/lib/api';
import Card, { CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import Modal from '@/components/ui/Modal';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { Upload, Activity, Trash2, RefreshCw } from 'lucide-react';

interface Proxy {
  id: string;
  host: string;
  port: number;
  type: string;
  username: string | null;
  status: string;
  latency: number | null;
  lastChecked: string | null;
}

export default function ProxiesPage() {
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const queryClient = useQueryClient();

  const { data: proxies, isLoading } = useQuery<Proxy[]>({
    queryKey: ['proxies'],
    queryFn: async (): Promise<Proxy[]> => {
      const response = await proxiesAPI.getAll();
      // Map backend response to frontend format
      return response.data.map((proxy: any): Proxy => ({
        id: String(proxy.id),
        host: proxy.host,
        port: proxy.port,
        type: proxy.type,
        username: proxy.username,
        status: proxy.status === 'active' ? 'working' : proxy.status === 'error' ? 'failed' : proxy.status,
        latency: proxy.latency_ms,
        lastChecked: proxy.last_checked,
      }));
    },
  });

  const [importError, setImportError] = useState<string | null>(null);
  const [importSuccess, setImportSuccess] = useState<string | null>(null);

  const importMutation = useMutation({
    mutationFn: (file: File) => proxiesAPI.import(file),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['proxies'] });
      const count = response.data?.length || 0;
      setImportSuccess(`Successfully imported ${count} proxies!`);
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

  const healthCheckMutation = useMutation({
    mutationFn: (id: string) => proxiesAPI.healthCheck(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proxies'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => proxiesAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proxies'] });
    },
  });

  const handleImport = () => {
    if (selectedFile) {
      importMutation.mutate(selectedFile);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'error' | 'warning'> = {
      working: 'success',
      failed: 'error',
      checking: 'warning',
    };
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>;
  };

  const getLatencyBadge = (latency: number | null) => {
    if (latency === null) return <span className="text-muted">N/A</span>;
    if (latency < 100) return <Badge variant="success">{latency}ms</Badge>;
    if (latency < 200) return <Badge variant="warning">{latency}ms</Badge>;
    return <Badge variant="error">{latency}ms</Badge>;
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Proxies</h1>
          <p className="text-muted mt-2">Manage your proxy pool</p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary">
            <Activity size={16} className="mr-2" />
            Check All
          </Button>
          <Button onClick={() => setIsImportModalOpen(true)}>
            <Upload size={16} className="mr-2" />
            Import Proxies
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Proxies ({proxies?.length || 0})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Host:Port</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Username</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Latency</TableHead>
                <TableHead>Last Checked</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {proxies?.map((proxy) => (
                <TableRow key={proxy.id}>
                  <TableCell className="font-medium font-mono">
                    {proxy.host}:{proxy.port}
                  </TableCell>
                  <TableCell>
                    <Badge variant="default">{proxy.type}</Badge>
                  </TableCell>
                  <TableCell className="text-muted">
                    {proxy.username || 'No auth'}
                  </TableCell>
                  <TableCell>{getStatusBadge(proxy.status)}</TableCell>
                  <TableCell>{getLatencyBadge(proxy.latency)}</TableCell>
                  <TableCell className="text-muted">
                    {proxy.lastChecked ? new Date(proxy.lastChecked).toLocaleString() : 'Never'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => healthCheckMutation.mutate(proxy.id)}
                        isLoading={healthCheckMutation.isPending}
                      >
                        <RefreshCw size={16} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteMutation.mutate(proxy.id)}
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
        onClose={() => {
          setIsImportModalOpen(false);
          setImportError(null);
          setImportSuccess(null);
          setSelectedFile(null);
        }}
        title="Import Proxies"
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
            <p>Upload a text file with proxies (one per line). Supported formats:</p>
            <div className="bg-gray-800 rounded p-3 font-mono text-xs space-y-1">
              <p className="text-green-400"># Without authentication:</p>
              <p>123.45.67.89:8080</p>
              <p className="text-green-400 mt-2"># With authentication:</p>
              <p>123.45.67.89:8080:username:password</p>
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
              accept=".txt,.csv"
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
                {selectedFile ? selectedFile.name : 'Click to upload file'}
              </p>
              <p className="text-muted text-sm">Accepts .txt files</p>
            </label>
          </div>
        </div>
      </Modal>
    </div>
  );
}
