import { useState } from 'react';
import { Alert, errorMessage } from '../../components/Alert';
import type { PricingRecord } from '../../types';
import { EditRecordDialog } from './EditRecordDialog';
import { Pagination } from './Pagination';
import { PricingTable } from './PricingTable';
import { SearchForm } from './SearchForm';
import { usePricingSearch } from './usePricingSearch';

export function PricingView() {
  const { query, filters, result, applyFilters, toggleSort, goToPage } = usePricingSearch();
  const [editing, setEditing] = useState<PricingRecord | null>(null);
  const { data, isPending, isError, error, isFetching } = result;

  return (
    <section className="panel" aria-labelledby="pricing-title">
      <header className="panel-header">
        <div>
          <h2 id="pricing-title">Pricing records</h2>
          <p className="muted">Search by store, SKU, product, price or date and correct records.</p>
        </div>
        {isFetching && !isPending && <span className="spinner" aria-label="Refreshing" />}
      </header>

      <SearchForm initialFilters={filters} onSearch={applyFilters} busy={isFetching} />

      {isError && <Alert tone="error">{errorMessage(error)}</Alert>}
      {isPending && <p className="muted placeholder">Loading pricing records…</p>}

      {data && data.items.length === 0 && (
        <p className="muted placeholder">No pricing records match these criteria.</p>
      )}

      {data && data.items.length > 0 && (
        <>
          <PricingTable
            records={data.items}
            sort={query.sort}
            onSort={toggleSort}
            onEdit={setEditing}
          />
          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onPageChange={goToPage}
          />
        </>
      )}

      {editing && <EditRecordDialog record={editing} onClose={() => setEditing(null)} />}
    </section>
  );
}
