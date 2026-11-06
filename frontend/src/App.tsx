import { useEffect, useState } from 'react';
import { IngestionView } from './features/ingestion/IngestionView';
import { PricingView } from './features/pricing/PricingView';

type Tab = 'records' | 'uploads';

const TABS: { id: Tab; label: string }[] = [
  { id: 'records', label: 'Pricing records' },
  { id: 'uploads', label: 'Feed uploads' },
];

function readTab(): Tab {
  return window.location.hash === '#uploads' ? 'uploads' : 'records';
}

export function App() {
  const [tab, setTab] = useState<Tab>(readTab);

  useEffect(() => {
    const onHashChange = () => setTab(readTab());
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const selectTab = (next: Tab) => {
    window.location.hash = next === 'records' ? '' : next;
    setTab(next);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-inner">
          <h1 className="brand">Pricing Feed Manager</h1>
          <nav role="tablist" aria-label="Sections" className="tabs">
            {TABS.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                role="tab"
                id={`tab-${id}`}
                aria-selected={tab === id}
                aria-controls={`tabpanel-${id}`}
                className="tab"
                onClick={() => selectTab(id)}
              >
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main
        className="app-main"
        role="tabpanel"
        id={`tabpanel-${tab}`}
        aria-labelledby={`tab-${tab}`}
      >
        {tab === 'records' ? <PricingView /> : <IngestionView />}
      </main>
    </div>
  );
}
