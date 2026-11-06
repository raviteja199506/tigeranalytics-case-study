import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRef, useState, type ChangeEvent, type DragEvent, type FormEvent } from 'react';
import { ingestionApi, ingestionKeys } from '../../api/ingestion';
import { Alert, errorMessage } from '../../components/Alert';
import { formatBytes } from '../../lib/format';

const MAX_UPLOAD_BYTES = 512 * 1024 * 1024;

export function validateFeedFile(file: File): string | null {
  if (!file.name.toLowerCase().endsWith('.csv')) return 'Only .csv files are accepted.';
  if (file.size === 0) return 'The selected file is empty.';
  if (file.size > MAX_UPLOAD_BYTES) return `Files must be ${formatBytes(MAX_UPLOAD_BYTES)} or smaller.`;
  return null;
}

export function UploadForm() {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const upload = useMutation({
    mutationFn: ingestionApi.upload,
    onSuccess: () => {
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
      void queryClient.invalidateQueries({ queryKey: ingestionKeys.all });
    },
  });

  const select = (candidate: File | undefined) => {
    upload.reset();
    setFile(candidate ?? null);
    setValidationError(candidate ? validateFeedFile(candidate) : null);
  };

  const onDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setDragging(false);
    select(event.dataTransfer.files[0]);
  };

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (file && !validationError) upload.mutate(file);
  };

  return (
    <form className="upload-form" onSubmit={submit} aria-label="Upload pricing feed">
      <label
        className={`dropzone${dragging ? ' dropzone-active' : ''}`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="visually-hidden"
          onChange={(event: ChangeEvent<HTMLInputElement>) => select(event.target.files?.[0])}
        />
        <span className="dropzone-title">
          {file ? file.name : 'Drop a CSV file here or click to browse'}
        </span>
        <span className="muted">
          {file
            ? formatBytes(file.size)
            : 'Required columns: Store ID, SKU, Product Name, Price, Date (YYYY-MM-DD)'}
        </span>
      </label>

      {validationError && <Alert tone="error">{validationError}</Alert>}
      {upload.isError && <Alert tone="error">{errorMessage(upload.error)}</Alert>}
      {upload.isSuccess && (
        <Alert tone="success">
          {upload.data.filename} was accepted and is being processed.
        </Alert>
      )}

      <div className="form-actions">
        <button
          type="submit"
          className="btn btn-primary"
          disabled={!file || Boolean(validationError) || upload.isPending}
        >
          {upload.isPending ? 'Uploading…' : 'Upload feed'}
        </button>
      </div>
    </form>
  );
}
