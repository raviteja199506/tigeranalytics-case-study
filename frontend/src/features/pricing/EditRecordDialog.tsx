import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { ApiError } from '../../api/http';
import { pricingApi, pricingKeys } from '../../api/pricing';
import { Alert, errorMessage } from '../../components/Alert';
import { Field } from '../../components/Field';
import { formatDate, formatDateTime, toEditablePrice } from '../../lib/format';
import type { PricingRecord, PricingUpdate } from '../../types';

type EditRecordDialogProps = {
  record: PricingRecord;
  onClose: () => void;
};

const FIELD_LABELS: Record<string, string> = { price: 'Price', product_name: 'Product name' };

export function buildUpdate(
  base: PricingRecord,
  productName: string,
  price: string,
): PricingUpdate | null {
  const update: PricingUpdate = { version: base.version };
  const trimmedName = productName.trim();
  if (trimmedName !== base.product_name) update.product_name = trimmedName;
  if (Number(price) !== Number(base.price)) update.price = price.trim();
  return update.product_name === undefined && update.price === undefined ? null : update;
}

export function EditRecordDialog({ record, onClose }: EditRecordDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const queryClient = useQueryClient();
  const [base, setBase] = useState(record);
  const [productName, setProductName] = useState(record.product_name);
  const [price, setPrice] = useState(toEditablePrice(record.price));

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) dialog.showModal();
  }, []);

  const history = useQuery({
    queryKey: pricingKeys.history(record.id),
    queryFn: () => pricingApi.history(record.id),
  });

  const save = useMutation({
    mutationFn: (payload: PricingUpdate) => pricingApi.update(record.id, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: pricingKeys.all });
      onClose();
    },
  });

  const reload = useMutation({
    mutationFn: () => pricingApi.get(record.id),
    onSuccess: (latest) => {
      setBase(latest);
      setProductName(latest.product_name);
      setPrice(toEditablePrice(latest.price));
      save.reset();
      void queryClient.invalidateQueries({ queryKey: pricingKeys.all });
    },
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const update = buildUpdate(base, productName, price);
    if (update) save.mutate(update);
    else onClose();
  };

  const conflict = save.error instanceof ApiError && save.error.isConflict;

  return (
    <dialog ref={dialogRef} className="dialog" onClose={onClose} aria-labelledby="edit-title">
      <form onSubmit={submit} className="dialog-body">
        <header className="dialog-header">
          <h2 id="edit-title">Edit pricing record</h2>
          <p className="muted">
            Store <span className="mono">{base.store_id}</span> · SKU{' '}
            <span className="mono">{base.sku}</span> · {formatDate(base.price_date)} · v
            {base.version}
          </p>
        </header>

        <Field label="Product name">
          <input
            value={productName}
            onChange={(event) => setProductName(event.target.value)}
            required
            maxLength={255}
          />
        </Field>
        <Field label="Price" hint="Local store currency, up to 4 decimal places">
          <input
            value={price}
            onChange={(event) => setPrice(event.target.value)}
            type="number"
            min="0.0001"
            step="0.0001"
            inputMode="decimal"
            required
          />
        </Field>

        {save.isError && (
          <Alert tone="error">
            {errorMessage(save.error)}
            {conflict && (
              <button
                type="button"
                className="btn btn-small alert-action"
                onClick={() => reload.mutate()}
                disabled={reload.isPending}
              >
                Load latest version
              </button>
            )}
          </Alert>
        )}

        <section className="history" aria-labelledby="history-title">
          <h3 id="history-title">Change history</h3>
          {history.isPending && <p className="muted">Loading history…</p>}
          {history.isError && <Alert tone="error">{errorMessage(history.error)}</Alert>}
          {history.data?.length === 0 && <p className="muted">No manual edits yet.</p>}
          {history.data && history.data.length > 0 && (
            <ol className="history-list">
              {history.data.map((entry) => (
                <li key={entry.id}>
                  <div className="history-meta">
                    v{entry.version} · {entry.changed_by} · {formatDateTime(entry.changed_at)}
                  </div>
                  {Object.entries(entry.changes).map(([field, change]) => (
                    <div key={field}>
                      {FIELD_LABELS[field] ?? field}: <del>{change.old}</del> → <ins>{change.new}</ins>
                    </div>
                  ))}
                </li>
              ))}
            </ol>
          )}
        </section>

        <footer className="dialog-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={save.isPending}>
            {save.isPending ? 'Saving…' : 'Save changes'}
          </button>
        </footer>
      </form>
    </dialog>
  );
}
