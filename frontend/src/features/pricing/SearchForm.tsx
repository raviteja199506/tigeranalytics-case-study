import { useState, type ChangeEvent, type FormEvent } from 'react';
import { Field } from '../../components/Field';
import type { PricingFilters } from '../../types';
import { EMPTY_FILTERS } from './usePricingSearch';

type SearchFormProps = {
  initialFilters: PricingFilters;
  onSearch: (filters: PricingFilters) => void;
  busy: boolean;
};

export function SearchForm({ initialFilters, onSearch, busy }: SearchFormProps) {
  const [draft, setDraft] = useState<PricingFilters>(initialFilters);

  const bind = (key: keyof PricingFilters) => ({
    name: key,
    value: draft[key],
    onChange: (event: ChangeEvent<HTMLInputElement>) =>
      setDraft((current) => ({ ...current, [key]: event.target.value })),
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSearch(draft);
  };

  const clear = () => {
    setDraft(EMPTY_FILTERS);
    onSearch(EMPTY_FILTERS);
  };

  return (
    <form className="search-form" onSubmit={submit} aria-label="Search pricing records">
      <div className="search-grid">
        <Field label="Store ID">
          <input {...bind('store_id')} maxLength={32} placeholder="e.g. ST00012" />
        </Field>
        <Field label="SKU">
          <input {...bind('sku')} maxLength={64} placeholder="Exact SKU" />
        </Field>
        <Field label="Product name">
          <input {...bind('product_name')} maxLength={255} placeholder="Contains…" />
        </Field>
        <Field label="Min price">
          <input {...bind('min_price')} type="number" min="0" step="0.01" inputMode="decimal" />
        </Field>
        <Field label="Max price">
          <input {...bind('max_price')} type="number" min="0" step="0.01" inputMode="decimal" />
        </Field>
        <Field label="From date">
          <input {...bind('date_from')} type="date" />
        </Field>
        <Field label="To date">
          <input {...bind('date_to')} type="date" min={draft.date_from || undefined} />
        </Field>
      </div>
      <div className="form-actions">
        <button type="button" className="btn btn-ghost" onClick={clear}>
          Clear
        </button>
        <button type="submit" className="btn btn-primary" disabled={busy}>
          Search
        </button>
      </div>
    </form>
  );
}
