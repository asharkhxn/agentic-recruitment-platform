import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useJobs } from '@/hooks/useJobs';
import * as jobsApi from '@/api/jobs';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('useJobs', () => {
  it('fetches jobs successfully', async () => {
    const mockJobs = [
      { id: '1', title: 'Developer', description: 'Great job', requirements: 'Skills', created_by: 'user1', created_at: '2024-01-01' },
    ];

    jest.spyOn(jobsApi.jobsApi, 'getAll').mockResolvedValue(mockJobs);

    const { result } = renderHook(() => useJobs(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockJobs);
  });
});
