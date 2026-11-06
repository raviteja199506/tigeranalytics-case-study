import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { pricingApi, pricingKeys } from '../../api/pricing';
import { toSearchParams } from '../../lib/query';
import type { PricingFilters, PricingQuery, SortField, SortOrder } from '../../types';

export const EMPTY_FILTERS: PricingFilters = {
  store_id: '',
  sku: '',
  product_name: '',
  min_price: '',
  max_price: '',
  date_from: '',
  date_to: '',
};

const DEFAULT_SORT: SortOrder = '-price_date';
const PAGE_SIZE = 25;
const FILTER_KEYS = Object.keys(EMPTY_FILTERS) as (keyof PricingFilters)[];
const SORT_FIELDS: readonly SortField[] = [
  'store_id',
  'sku',
  'product_name',
  'price',
  'price_date',
  'updated_at',
];

function isSortOrder(value: string): value is SortOrder {
  return SORT_FIELDS.includes(value.replace(/^-/, '') as SortField);
}

function pickFilters(source: { [K in keyof PricingFilters]?: string | null }): PricingFilters {
  return Object.fromEntries(FILTER_KEYS.map((key) => [key, source[key] ?? ''])) as PricingFilters;
}

function readQueryFromUrl(): PricingQuery {
  const params = new URLSearchParams(window.location.search);
  const sort = params.get('sort') ?? '';
  return {
    ...pickFilters(Object.fromEntries(params)),
    sort: isSortOrder(sort) ? sort : DEFAULT_SORT,
    page: Math.max(1, Number(params.get('page')) || 1),
    page_size: PAGE_SIZE,
  };
}

function writeQueryToUrl(query: PricingQuery): void {
  const params = toSearchParams({
    ...query,
    sort: query.sort === DEFAULT_SORT ? undefined : query.sort,
    page: query.page > 1 ? query.page : undefined,
    page_size: undefined,
  });
  const search = params.toString();
  window.history.replaceState(null, '', search ? `?${search}` : window.location.pathname);
}

export function usePricingSearch() {
  const [query, setQuery] = useState<PricingQuery>(readQueryFromUrl);

  useEffect(() => writeQueryToUrl(query), [query]);

  const result = useQuery({
    queryKey: pricingKeys.search(query),
    queryFn: ({ signal }) => pricingApi.search(query, signal),
    placeholderData: keepPreviousData,
  });

  const applyFilters = useCallback(
    (filters: PricingFilters) => setQuery((current) => ({ ...current, ...filters, page: 1 })),
    [],
  );

  const toggleSort = useCallback(
    (field: SortField) =>
      setQuery((current) => ({
        ...current,
        sort: current.sort === field ? `-${field}` : field,
        page: 1,
      })),
    [],
  );

  const goToPage = useCallback(
    (page: number) => setQuery((current) => ({ ...current, page })),
    [],
  );

  const filters = useMemo(() => pickFilters(query), [query]);

  return { query, filters, result, applyFilters, toggleSort, goToPage };
}
