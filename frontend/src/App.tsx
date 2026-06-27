import { useState, useCallback } from 'react';
import type { CreateDiscussionResponse } from './types';
import DiscussionList from './components/home/DiscussionList';
import CreateDiscussion from './components/home/CreateDiscussion';
import PanelistRoster from './components/home/PanelistRoster';
import SseDebug from './components/debug/SseDebug'; // TODO Phase4 移除
import StudioView from './components/studio/StudioView';
import './App.css';

type Page =
  | { name: 'home' }
  | { name: 'create' }
  | { name: 'roster'; data: CreateDiscussionResponse }
  | { name: 'debug' }
  | { name: 'studio'; discussionId: string; topic?: string };

export default function App() {
  const [page, setPage] = useState<Page>({ name: 'home' });

  const goHome = useCallback(() => setPage({ name: 'home' }), []);
  const goCreate = useCallback(() => setPage({ name: 'create' }), []);
  const goDebug = useCallback(() => setPage({ name: 'debug' }), []);

  const handleCreated = useCallback((data: CreateDiscussionResponse) => {
    setPage({ name: 'roster', data });
  }, []);

  const handleConfirmed = useCallback((discussionId: string, topic: string) => {
    setPage({ name: 'studio', discussionId, topic });
  }, []);

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-canvas)' }}>
      {/* Apple Studio — 高强度磨砂玻璃导航 */}
      <nav className="glass-nav flex items-center gap-5 px-6 py-2.5 text-[13px] sticky top-0 z-10">
        <span className="text-heading text-[15px] mr-2 tracking-tight">
          AI Panel Studio
        </span>
        <button onClick={goHome} className="cursor-pointer transition-all duration-[var(--duration-fast)]"
          style={{
            color: page.name === 'home' ? 'var(--accent-brand)' : 'var(--text-secondary)',
            fontWeight: page.name === 'home' ? 500 : 400,
          }}>
          首页
        </button>
        <button onClick={goCreate} className="cursor-pointer transition-all duration-[var(--duration-fast)]"
          style={{
            color: page.name === 'create' || page.name === 'roster' ? 'var(--accent-brand)' : 'var(--text-secondary)',
            fontWeight: page.name === 'create' || page.name === 'roster' ? 500 : 400,
          }}>
          发起讨论
        </button>
        <button onClick={goDebug} className="cursor-pointer transition-all duration-[var(--duration-fast)] ml-auto text-xs"
          style={{ color: 'var(--text-muted)' }}
        >
          SSE 调试
        </button>
      </nav>

      {page.name === 'home' && (
        <DiscussionList
          onCreateNew={goCreate}
          onJoin={(id, topic) => setPage({ name: 'studio', discussionId: id, topic })}
        />
      )}
      {page.name === 'create' && (
        <CreateDiscussion onBack={goHome} onCreated={handleCreated} />
      )}
      {page.name === 'roster' && (
        <PanelistRoster data={page.data} onBackToCreate={goCreate} onConfirmed={handleConfirmed} />
      )}
      {page.name === 'debug' && <SseDebug />}
      {page.name === 'studio' && (
        <StudioView
          discussionId={page.discussionId}
          topic={page.topic}
          onBack={goHome}
        />
      )}
    </div>
  );
}
