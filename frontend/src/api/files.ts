import { api } from "@/lib/api";

export const filesApi = {
  getCvPreview: async (
    applicationId: string
  ): Promise<{ signed_url: string }> => {
    const response = await api.get(
      `/files/applications/${applicationId}/preview`
    );
    return response.data;
  },
};
