import type { IngestionStatus } from '../../types';

const LABELS: Record<IngestionStatus, string> = {
  pending: 'Queued',
  processing: 'Processing',
  completed: 'Completed',
  completed_with_errors: 'Completed with errors',
  failed: 'Failed',
};

export function StatusBadge({ status }: { status: IngestionStatus }) {
  return <span className={`badge badge-${status}`}>{LABELS[status]}</span>;
}
