import { api } from "@/lib/api";
import { Job, JobCreate } from "@/types";

export const jobsApi = {
  getAll: async (): Promise<Job[]> => {
    const response = await api.get("/jobs");
    return response.data;
  },

  getJobsByRecruiter: async (recruiterId: string): Promise<Job[]> => {
    const response = await api.get(`/jobs/by-recruiter/${recruiterId}`);
    return response.data;
  },

  getById: async (id: string): Promise<Job> => {
    const response = await api.get(`/jobs/${id}`);
    return response.data;
  },

  create: async (job: JobCreate): Promise<Job> => {
    const response = await api.post("/jobs", job);
    return response.data;
  },

  update: async (id: string, job: JobCreate): Promise<Job> => {
    const response = await api.put(`/jobs/${id}`, job);
    return response.data;
  },

  close: async (id: string): Promise<any> => {
    const response = await api.post(`/jobs/close/${id}`);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/jobs/${id}`);
  },
};
