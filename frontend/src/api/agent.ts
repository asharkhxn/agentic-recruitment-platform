import { api } from '@/lib/api';
import { ChatMessage, ChatResponse } from '@/types';

export const agentApi = {
  chat: async (message: ChatMessage): Promise<ChatResponse> => {
    const response = await api.post('/agent/chat', message);
    return response.data;
  },
};
