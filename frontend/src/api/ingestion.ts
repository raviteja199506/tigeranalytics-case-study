import type { IngestionJob, IngestionRowError } from '../types';
import { request } from './http';

export const ingestionKeys = {
  all: ['ingestions'] as const,
  recent: () => [...ingestionKeys.all, 'recent'] as const,
  errors: (jobId: string) => [...ingestionKeys.all, 'errors', jobId] as const,
};

export const ingestionApi = {
  upload: (file: File) => {
    const body = new FormData();
    body.append('file', file);
    return request<IngestionJob>('/ingestions', { method: 'POST', body });
  },

  recent: (limit = 20) => request<IngestionJob[]>(`/ingestions?limit=${limit}`),

  errors: (jobId: string) => request<IngestionRowError[]>(`/ingestions/${jobId}/errors`),
};
