import { api } from '@/lib/api';
import { ATSRankingResponse } from '@/types';

export const atsApi = {
  rankApplicants: async (jobId: string): Promise<ATSRankingResponse> => {
    const response = await api.post('/ats/rank', { job_id: jobId });
    return response.data;
  },
};
