import { formatDate, formatDateTime, formatPrice } from '../../lib/format';
import type { PricingRecord, SortField, SortOrder } from '../../types';

type Column = { field: SortField; label: string; numeric?: boolean };

const COLUMNS: Column[] = [
  { field: 'store_id', label: 'Store' },
  { field: 'sku', label: 'SKU' },
  { field: 'product_name', label: 'Product' },
  { field: 'price', label: 'Price', numeric: true },
  { field: 'price_date', label: 'Price date' },
  { field: 'updated_at', label: 'Last updated' },
];

type PricingTableProps = {
  records: PricingRecord[];
  sort: SortOrder;
  onSort: (field: SortField) => void;
  onEdit: (record: PricingRecord) => void;
};

function ariaSort(sort: SortOrder, field: SortField): 'ascending' | 'descending' | 'none' {
  if (sort === field) return 'ascending';
  if (sort === `-${field}`) return 'descending';
  return 'none';
}

export function PricingTable({ records, sort, onSort, onEdit }: PricingTableProps) {
  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            {COLUMNS.map(({ field, label, numeric }) => {
              const direction = ariaSort(sort, field);
              return (
                <th key={field} aria-sort={direction} className={numeric ? 'numeric' : undefined}>
                  <button type="button" className="sort-button" onClick={() => onSort(field)}>
                    {label}
                    <span className={`sort-indicator sort-${direction}`} aria-hidden="true" />
                  </button>
                </th>
              );
            })}
            <th className="actions-column">
              <span className="visually-hidden">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.id}>
              <td className="mono">{record.store_id}</td>
              <td className="mono">{record.sku}</td>
              <td>{record.product_name}</td>
              <td className="numeric">{formatPrice(record.price)}</td>
              <td className="nowrap">{formatDate(record.price_date)}</td>
              <td className="muted nowrap">
                {formatDateTime(record.updated_at)}
                {record.updated_by && <span className="cell-sub">{record.updated_by}</span>}
              </td>
              <td className="actions-column">
                <button
                  type="button"
                  className="btn btn-small"
                  onClick={() => onEdit(record)}
                  aria-label={`Edit ${record.sku} at store ${record.store_id}`}
                >
                  Edit
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
