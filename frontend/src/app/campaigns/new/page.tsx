'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';
import { campaignsAPI, accountsAPI } from '@/lib/api';
import Card, { CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import { Upload, X, Video } from 'lucide-react';

export default function NewCampaignPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: '',
    caption: '',
    accountSelection: 'all',
    randomCount: '5',
    selectedAccounts: [] as string[],
    scheduleStart: '08:00',
    scheduleEnd: '20:00',
    delayMin: '60',
    delayMax: '180',
  });
  const [videos, setVideos] = useState<File[]>([]);

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: async () => {
      // Placeholder - use actual API
      return Array.from({ length: 10 }, (_, i) => ({
        id: `${i + 1}`,
        email: `user${i + 1}@tiktok.com`,
        username: `@user${i + 1}`,
      }));
    },
  });

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'video/*': ['.mp4', '.mov', '.avi'] },
    onDrop: (acceptedFiles) => {
      setVideos([...videos, ...acceptedFiles]);
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => campaignsAPI.create(data),
    onSuccess: () => {
      router.push('/campaigns');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const campaignData = new FormData();
    campaignData.append('name', formData.name);
    campaignData.append('caption', formData.caption);
    campaignData.append('accountSelection', formData.accountSelection);
    campaignData.append('scheduleStart', formData.scheduleStart);
    campaignData.append('scheduleEnd', formData.scheduleEnd);
    campaignData.append('delayMin', formData.delayMin);
    campaignData.append('delayMax', formData.delayMax);

    if (formData.accountSelection === 'random') {
      campaignData.append('randomCount', formData.randomCount);
    } else if (formData.accountSelection === 'specific') {
      campaignData.append('selectedAccounts', JSON.stringify(formData.selectedAccounts));
    }

    videos.forEach((video) => {
      campaignData.append('videos', video);
    });

    createMutation.mutate(campaignData);
  };

  const removeVideo = (index: number) => {
    setVideos(videos.filter((_, i) => i !== index));
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Create New Campaign</h1>
        <p className="text-muted mt-2">Set up a new posting campaign</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Campaign Name"
              placeholder="e.g., Morning Posts"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Caption Template
              </label>
              <textarea
                className="w-full px-4 py-2 bg-background border border-border rounded-lg text-white placeholder-muted focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all min-h-[100px]"
                placeholder="Enter caption... Use {hashtags} for dynamic content"
                value={formData.caption}
                onChange={(e) => setFormData({ ...formData, caption: e.target.value })}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Videos</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive ? 'border-primary-500 bg-primary-500/10' : 'border-border'
              }`}
            >
              <input {...getInputProps()} />
              <Upload size={48} className="mx-auto text-muted mb-4" />
              <p className="text-white font-medium mb-1">
                {isDragActive ? 'Drop videos here' : 'Click or drag videos here'}
              </p>
              <p className="text-muted text-sm">Supports MP4, MOV, AVI</p>
            </div>

            {videos.length > 0 && (
              <div className="mt-4 space-y-2">
                {videos.map((video, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-background rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <Video size={20} className="text-primary-500" />
                      <span className="text-white text-sm">{video.name}</span>
                      <span className="text-muted text-xs">
                        {(video.size / 1024 / 1024).toFixed(2)} MB
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeVideo(index)}
                      className="text-muted hover:text-white transition-colors"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Account Selection</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select
              label="Selection Mode"
              options={[
                { value: 'all', label: 'All Active Accounts' },
                { value: 'random', label: 'Random X Accounts' },
                { value: 'specific', label: 'Specific Accounts' },
              ]}
              value={formData.accountSelection}
              onChange={(e) =>
                setFormData({ ...formData, accountSelection: e.target.value })
              }
            />

            {formData.accountSelection === 'random' && (
              <Input
                label="Number of Random Accounts"
                type="number"
                min="1"
                value={formData.randomCount}
                onChange={(e) => setFormData({ ...formData, randomCount: e.target.value })}
              />
            )}

            {formData.accountSelection === 'specific' && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Select Accounts
                </label>
                <div className="max-h-48 overflow-y-auto space-y-2 p-4 bg-background rounded-lg border border-border">
                  {accounts?.map((account) => (
                    <label key={account.id} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.selectedAccounts.includes(account.id)}
                        onChange={(e) => {
                          const selected = e.target.checked
                            ? [...formData.selectedAccounts, account.id]
                            : formData.selectedAccounts.filter((id) => id !== account.id);
                          setFormData({ ...formData, selectedAccounts: selected });
                        }}
                        className="w-4 h-4 text-primary-600 bg-background border-border rounded focus:ring-primary-500"
                      />
                      <span className="text-white text-sm">{account.email}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Schedule Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Start Time"
                type="time"
                value={formData.scheduleStart}
                onChange={(e) => setFormData({ ...formData, scheduleStart: e.target.value })}
              />
              <Input
                label="End Time"
                type="time"
                value={formData.scheduleEnd}
                onChange={(e) => setFormData({ ...formData, scheduleEnd: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Min Delay (seconds)"
                type="number"
                min="0"
                value={formData.delayMin}
                onChange={(e) => setFormData({ ...formData, delayMin: e.target.value })}
              />
              <Input
                label="Max Delay (seconds)"
                type="number"
                min="0"
                value={formData.delayMax}
                onChange={(e) => setFormData({ ...formData, delayMax: e.target.value })}
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={() => router.push('/campaigns')}
          >
            Cancel
          </Button>
          <Button type="submit" isLoading={createMutation.isPending}>
            Create Campaign
          </Button>
        </div>
      </form>
    </div>
  );
}
