import { api } from '@/lib/api';
import { Application } from '@/types';

export const applicationsApi = {
  getAll: async (jobId?: string): Promise<Application[]> => {
    const response = await api.get('/applications', {
      params: jobId ? { job_id: jobId } : {},
    });
    return response.data;
  },

  getById: async (id: string): Promise<Application> => {
    const response = await api.get(`/applications/${id}`);
    return response.data;
  },

  create: async (formData: FormData): Promise<Application> => {
    const response = await api.post('/applications', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/applications/${id}`);
  },
};
