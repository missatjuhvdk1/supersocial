'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import Card, { CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { Save } from 'lucide-react';

export default function SettingsPage() {
  const [generalSettings, setGeneralSettings] = useState({
    apiUrl: 'http://localhost:8000',
    maxConcurrentJobs: '3',
    jobTimeout: '300',
    retryAttempts: '3',
  });

  const [uploadSettings, setUploadSettings] = useState({
    uploadTimeout: '120',
    maxVideoSize: '100',
    allowedFormats: 'mp4,mov,avi',
    autoGenerateThumbnail: 'true',
  });

  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: 'true',
    notifyOnSuccess: 'false',
    notifyOnFailure: 'true',
    emailAddress: 'admin@example.com',
  });

  const saveMutation = useMutation({
    mutationFn: async (settings: any) => {
      // API call to save settings
      console.log('Saving settings:', settings);
      return Promise.resolve();
    },
    onSuccess: () => {
      alert('Settings saved successfully!');
    },
  });

  const handleSaveGeneral = () => {
    saveMutation.mutate({ type: 'general', data: generalSettings });
  };

  const handleSaveUpload = () => {
    saveMutation.mutate({ type: 'upload', data: uploadSettings });
  };

  const handleSaveNotifications = () => {
    saveMutation.mutate({ type: 'notifications', data: notificationSettings });
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="text-muted mt-2">Configure your TikTok auto-poster</p>
      </div>

      <Tabs defaultValue="general">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="upload">Upload</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle>General Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="API Base URL"
                value={generalSettings.apiUrl}
                onChange={(e) =>
                  setGeneralSettings({ ...generalSettings, apiUrl: e.target.value })
                }
                placeholder="http://localhost:8000"
              />
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Max Concurrent Jobs"
                  type="number"
                  min="1"
                  value={generalSettings.maxConcurrentJobs}
                  onChange={(e) =>
                    setGeneralSettings({
                      ...generalSettings,
                      maxConcurrentJobs: e.target.value,
                    })
                  }
                />
                <Input
                  label="Job Timeout (seconds)"
                  type="number"
                  min="60"
                  value={generalSettings.jobTimeout}
                  onChange={(e) =>
                    setGeneralSettings({ ...generalSettings, jobTimeout: e.target.value })
                  }
                />
              </div>
              <Input
                label="Retry Attempts on Failure"
                type="number"
                min="0"
                value={generalSettings.retryAttempts}
                onChange={(e) =>
                  setGeneralSettings({ ...generalSettings, retryAttempts: e.target.value })
                }
              />
              <div className="flex justify-end">
                <Button
                  onClick={handleSaveGeneral}
                  isLoading={saveMutation.isPending}
                >
                  <Save size={16} className="mr-2" />
                  Save Changes
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="upload">
          <Card>
            <CardHeader>
              <CardTitle>Upload Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Upload Timeout (seconds)"
                  type="number"
                  min="30"
                  value={uploadSettings.uploadTimeout}
                  onChange={(e) =>
                    setUploadSettings({ ...uploadSettings, uploadTimeout: e.target.value })
                  }
                />
                <Input
                  label="Max Video Size (MB)"
                  type="number"
                  min="1"
                  value={uploadSettings.maxVideoSize}
                  onChange={(e) =>
                    setUploadSettings({ ...uploadSettings, maxVideoSize: e.target.value })
                  }
                />
              </div>
              <Input
                label="Allowed Video Formats"
                value={uploadSettings.allowedFormats}
                onChange={(e) =>
                  setUploadSettings({ ...uploadSettings, allowedFormats: e.target.value })
                }
                placeholder="mp4,mov,avi"
              />
              <Select
                label="Auto-Generate Thumbnail"
                options={[
                  { value: 'true', label: 'Enabled' },
                  { value: 'false', label: 'Disabled' },
                ]}
                value={uploadSettings.autoGenerateThumbnail}
                onChange={(e) =>
                  setUploadSettings({
                    ...uploadSettings,
                    autoGenerateThumbnail: e.target.value,
                  })
                }
              />
              <div className="flex justify-end">
                <Button
                  onClick={handleSaveUpload}
                  isLoading={saveMutation.isPending}
                >
                  <Save size={16} className="mr-2" />
                  Save Changes
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle>Notification Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Select
                label="Email Notifications"
                options={[
                  { value: 'true', label: 'Enabled' },
                  { value: 'false', label: 'Disabled' },
                ]}
                value={notificationSettings.emailNotifications}
                onChange={(e) =>
                  setNotificationSettings({
                    ...notificationSettings,
                    emailNotifications: e.target.value,
                  })
                }
              />
              {notificationSettings.emailNotifications === 'true' && (
                <>
                  <Input
                    label="Email Address"
                    type="email"
                    value={notificationSettings.emailAddress}
                    onChange={(e) =>
                      setNotificationSettings({
                        ...notificationSettings,
                        emailAddress: e.target.value,
                      })
                    }
                  />
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notificationSettings.notifyOnSuccess === 'true'}
                        onChange={(e) =>
                          setNotificationSettings({
                            ...notificationSettings,
                            notifyOnSuccess: e.target.checked ? 'true' : 'false',
                          })
                        }
                        className="w-4 h-4 text-primary-600 bg-background border-border rounded focus:ring-primary-500"
                      />
                      <span className="text-white text-sm">Notify on successful posts</span>
                    </label>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notificationSettings.notifyOnFailure === 'true'}
                        onChange={(e) =>
                          setNotificationSettings({
                            ...notificationSettings,
                            notifyOnFailure: e.target.checked ? 'true' : 'false',
                          })
                        }
                        className="w-4 h-4 text-primary-600 bg-background border-border rounded focus:ring-primary-500"
                      />
                      <span className="text-white text-sm">Notify on failed posts</span>
                    </label>
                  </div>
                </>
              )}
              <div className="flex justify-end">
                <Button
                  onClick={handleSaveNotifications}
                  isLoading={saveMutation.isPending}
                >
                  <Save size={16} className="mr-2" />
                  Save Changes
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
