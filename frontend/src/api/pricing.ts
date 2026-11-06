import { toSearchParams } from '../lib/query';
import type { Page, PricingAudit, PricingQuery, PricingRecord, PricingUpdate } from '../types';
import { jsonBody, request } from './http';

export const pricingKeys = {
  all: ['pricing-records'] as const,
  search: (query: PricingQuery) => [...pricingKeys.all, 'search', query] as const,
  history: (id: number) => [...pricingKeys.all, 'history', id] as const,
};

export const pricingApi = {
  search: (query: PricingQuery, signal?: AbortSignal) =>
    request<Page<PricingRecord>>(`/pricing-records?${toSearchParams(query)}`, { signal }),

  get: (id: number) => request<PricingRecord>(`/pricing-records/${id}`),

  update: (id: number, payload: PricingUpdate) =>
    request<PricingRecord>(`/pricing-records/${id}`, { method: 'PATCH', ...jsonBody(payload) }),

  history: (id: number) => request<PricingAudit[]>(`/pricing-records/${id}/history`),
};
