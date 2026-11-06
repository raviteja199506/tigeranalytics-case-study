import { useQuery } from '@tanstack/react-query';
import { ingestionApi, ingestionKeys } from '../../api/ingestion';
import { Alert, errorMessage } from '../../components/Alert';

export function JobErrors({ jobId }: { jobId: string }) {
  const { data, isPending, isError, error } = useQuery({
    queryKey: ingestionKeys.errors(jobId),
    queryFn: () => ingestionApi.errors(jobId),
  });

  if (isPending) return <p className="muted">Loading row errors…</p>;
  if (isError) return <Alert tone="error">{errorMessage(error)}</Alert>;
  if (data.length === 0) return <p className="muted">No row-level errors were recorded.</p>;

  return (
    <table className="data-table compact">
      <thead>
        <tr>
          <th className="numeric">Line</th>
          <th>Problem</th>
          <th>Raw content</th>
        </tr>
      </thead>
      <tbody>
        {data.map((rowError) => (
          <tr key={rowError.row_number}>
            <td className="numeric">{rowError.row_number}</td>
            <td>{rowError.message}</td>
            <td className="mono muted truncate" title={rowError.raw_line ?? undefined}>
              {rowError.raw_line}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
