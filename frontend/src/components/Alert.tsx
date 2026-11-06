import type { ReactNode } from 'react';

type AlertProps = {
  tone?: 'error' | 'success' | 'info';
  children: ReactNode;
};

export function Alert({ tone = 'info', children }: AlertProps) {
  return (
    <div className={`alert alert-${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      {children}
    </div>
  );
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.';
}
