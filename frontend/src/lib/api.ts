import axios from 'axios';

// Ensure /api/v1 is always the base path
const apiBase = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/+$/, '');
const api = axios.create({
  baseURL: `${apiBase}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for API calls
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for API calls
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// API Endpoints
export const accountsAPI = {
  getAll: () => api.get('/accounts'),
  getById: (id: string) => api.get(`/accounts/${id}`),
  create: (data: any) => api.post('/accounts', data),
  update: (id: string, data: any) => api.put(`/accounts/${id}`, data),
  delete: (id: string) => api.delete(`/accounts/${id}`),
  import: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/accounts/bulk-import-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const proxiesAPI = {
  getAll: () => api.get('/proxies'),
  create: (data: any) => api.post('/proxies', data),
  update: (id: string, data: any) => api.put(`/proxies/${id}`, data),
  delete: (id: string) => api.delete(`/proxies/${id}`),
  import: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/proxies/bulk-import-txt', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  healthCheck: (id: string) => api.post(`/proxies/${id}/health-check`),
};

export const campaignsAPI = {
  getAll: () => api.get('/campaigns'),
  getById: (id: string) => api.get(`/campaigns/${id}`),
  create: (data: any) => api.post('/campaigns', data),
  createWithVideo: (formData: FormData) =>
    api.post('/campaigns/create-with-video', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  update: (id: string, data: any) => api.put(`/campaigns/${id}`, data),
  delete: (id: string) => api.delete(`/campaigns/${id}`),
  start: (id: string) => api.post(`/campaigns/${id}/start`),
  pause: (id: string) => api.post(`/campaigns/${id}/pause`),
};

export const jobsAPI = {
  getAll: (params?: { status?: string }) => {
    const queryParams = params?.status && params.status !== 'all'
      ? { status: params.status }
      : undefined;
    return api.get('/jobs', { params: queryParams });
  },
  getById: (id: string) => api.get(`/jobs/${id}`),
  cancel: (id: string) => api.post(`/jobs/${id}/cancel`),
  retry: (id: string) => api.post(`/jobs/${id}/retry`),
};

export const statsAPI = {
  getDashboard: () => api.get('/stats/dashboard'),
};
