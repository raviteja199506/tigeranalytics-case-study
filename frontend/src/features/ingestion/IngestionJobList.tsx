import { useQuery } from '@tanstack/react-query';
import { Fragment, useState } from 'react';
import { ingestionApi, ingestionKeys } from '../../api/ingestion';
import { Alert, errorMessage } from '../../components/Alert';
import { formatBytes, formatCount, formatDateTime } from '../../lib/format';
import type { IngestionJob } from '../../types';
import { JobErrors } from './JobErrors';
import { StatusBadge } from './StatusBadge';

const POLL_INTERVAL_MS = 2_000;

const isActive = (job: IngestionJob) => job.status === 'pending' || job.status === 'processing';

export function IngestionJobList() {
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);
  const { data, isPending, isError, error } = useQuery({
    queryKey: ingestionKeys.recent(),
    queryFn: () => ingestionApi.recent(),
    refetchInterval: (query) => (query.state.data?.some(isActive) ? POLL_INTERVAL_MS : false),
  });

  if (isPending) return <p className="muted placeholder">Loading recent uploads…</p>;
  if (isError) return <Alert tone="error">{errorMessage(error)}</Alert>;
  if (data.length === 0) return <p className="muted placeholder">No feeds uploaded yet.</p>;

  const toggle = (jobId: string) => setExpandedJobId((current) => (current === jobId ? null : jobId));

  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>File</th>
            <th>Status</th>
            <th className="numeric">Rows</th>
            <th className="numeric">Accepted</th>
            <th className="numeric">Rejected</th>
            <th>Uploaded</th>
            <th className="actions-column">
              <span className="visually-hidden">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((job) => {
            const expanded = expandedJobId === job.id;
            const hasDetails = job.rejected_rows > 0 || Boolean(job.error_message);
            return (
              <Fragment key={job.id}>
                <tr>
                  <td>
                    {job.filename}
                    <span className="cell-sub">{formatBytes(job.size_bytes)}</span>
                  </td>
                  <td>
                    <StatusBadge status={job.status} />
                  </td>
                  <td className="numeric">{formatCount(job.total_rows)}</td>
                  <td className="numeric">{formatCount(job.accepted_rows)}</td>
                  <td className="numeric">{formatCount(job.rejected_rows)}</td>
                  <td className="muted nowrap">
                    {formatDateTime(job.created_at)}
                    <span className="cell-sub">{job.uploaded_by}</span>
                  </td>
                  <td className="actions-column">
                    {hasDetails && (
                      <button
                        type="button"
                        className="btn btn-small"
                        aria-expanded={expanded}
                        aria-controls={`job-details-${job.id}`}
                        onClick={() => toggle(job.id)}
                      >
                        {expanded ? 'Hide' : 'Details'}
                      </button>
                    )}
                  </td>
                </tr>
                {expanded && (
                  <tr className="details-row" id={`job-details-${job.id}`}>
                    <td colSpan={7}>
                      {job.error_message && <Alert tone="error">{job.error_message}</Alert>}
                      {job.rejected_rows > 0 && <JobErrors jobId={job.id} />}
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
