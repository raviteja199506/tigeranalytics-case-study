import { IngestionJobList } from './IngestionJobList';
import { UploadForm } from './UploadForm';

export function IngestionView() {
  return (
    <>
      <section className="panel" aria-labelledby="upload-title">
        <header className="panel-header">
          <div>
            <h2 id="upload-title">Upload pricing feed</h2>
            <p className="muted">
              Files are validated row by row. Existing records for the same store, SKU and date
              are updated.
            </p>
          </div>
        </header>
        <UploadForm />
      </section>

      <section className="panel" aria-labelledby="jobs-title">
        <header className="panel-header">
          <h2 id="jobs-title">Recent uploads</h2>
        </header>
        <IngestionJobList />
      </section>
    </>
  );
}
