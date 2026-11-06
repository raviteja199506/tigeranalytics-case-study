export type IngestionStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'completed_with_errors'
  | 'failed';

export type IngestionJob = {
  id: string;
  filename: string;
  status: IngestionStatus;
  size_bytes: number;
  total_rows: number;
  accepted_rows: number;
  rejected_rows: number;
  error_message: string | null;
  uploaded_by: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
};

export type IngestionRowError = {
  row_number: number;
  message: string;
  raw_line: string | null;
};

export type PricingRecord = {
  id: number;
  store_id: string;
  sku: string;
  product_name: string;
  price: string;
  price_date: string;
  version: number;
  source_job_id: string | null;
  created_at: string;
  updated_at: string;
  updated_by: string | null;
};

export type FieldChange = { old: string | null; new: string | null };

export type PricingAudit = {
  id: number;
  version: number;
  changes: Record<string, FieldChange>;
  changed_by: string;
  changed_at: string;
};

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type SortField = 'store_id' | 'sku' | 'product_name' | 'price' | 'price_date' | 'updated_at';
export type SortOrder = SortField | `-${SortField}`;

export type PricingFilters = {
  store_id: string;
  sku: string;
  product_name: string;
  min_price: string;
  max_price: string;
  date_from: string;
  date_to: string;
};

export type PricingQuery = PricingFilters & {
  sort: SortOrder;
  page: number;
  page_size: number;
};

export type PricingUpdate = {
  version: number;
  product_name?: string;
  price?: string;
};
