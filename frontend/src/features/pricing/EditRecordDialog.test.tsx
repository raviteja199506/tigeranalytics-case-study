import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import type { PricingRecord } from '../../types';
import { buildUpdate, EditRecordDialog } from './EditRecordDialog';

const record: PricingRecord = {
  id: 7,
  store_id: 'ST001',
  sku: 'SKU-1',
  product_name: 'Whole Milk 1L',
  price: '1.9900',
  price_date: '2026-01-10',
  version: 3,
  source_job_id: null,
  created_at: '2026-01-10T08:00:00Z',
  updated_at: '2026-01-10T08:00:00Z',
  updated_by: null,
};

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function renderDialog(onClose = vi.fn()) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <EditRecordDialog record={record} onClose={onClose} />
    </QueryClientProvider>,
  );
  return onClose;
}

beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
    this.open = true;
  };
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('buildUpdate', () => {
  it('returns null when nothing changed', () => {
    expect(buildUpdate(record, ' Whole Milk 1L ', '1.99')).toBeNull();
  });

  it('includes only changed fields with the current version', () => {
    expect(buildUpdate(record, 'Whole Milk 1L', '2.15')).toEqual({ version: 3, price: '2.15' });
  });
});

describe('EditRecordDialog', () => {
  it('submits the changed price and closes on success', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation(async (_input, init) =>
        init?.method === 'PATCH'
          ? jsonResponse(200, { ...record, price: '2.1500', version: 4 })
          : jsonResponse(200, []),
      );
    const onClose = renderDialog();

    const price = screen.getByLabelText(/^Price/);
    await userEvent.clear(price);
    await userEvent.type(price, '2.15');
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const patch = fetchMock.mock.calls.find(([, init]) => init?.method === 'PATCH');
    expect(patch?.[0]).toBe('/api/v1/pricing-records/7');
    expect(JSON.parse(String(patch?.[1]?.body))).toEqual({ version: 3, price: '2.15' });
  });

  it('offers to reload when the record was changed by someone else', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (_input, init) =>
      init?.method === 'PATCH'
        ? jsonResponse(409, { detail: 'Pricing record 7 was modified by another user.' })
        : jsonResponse(200, []),
    );
    const onClose = renderDialog();

    await userEvent.clear(screen.getByLabelText(/^Price/));
    await userEvent.type(screen.getByLabelText(/^Price/), '3.00');
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('modified by another user');
    expect(screen.getByRole('button', { name: 'Load latest version' })).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
  });
});
