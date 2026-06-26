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
      {/* 临时导航 —— TODO Phase4 替换为正式路由 */}
      <nav
        className="flex items-center gap-4 px-4 py-2 text-xs border-b"
        style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
      >
        <button
          onClick={goHome}
          className="cursor-pointer transition-colors duration-[var(--duration-fast)] hover:opacity-80"
          style={{ color: page.name === 'home' ? 'var(--text-primary)' : 'var(--text-muted)' }}
        >
          首页
        </button>
        <button
          onClick={goCreate}
          className="cursor-pointer transition-colors duration-[var(--duration-fast)] hover:opacity-80"
          style={{ color: page.name === 'create' || page.name === 'roster' ? 'var(--text-primary)' : 'var(--text-muted)' }}
        >
          发起讨论
        </button>
        <button
          onClick={goDebug}
          className="cursor-pointer transition-colors duration-[var(--duration-fast)] hover:opacity-80 ml-auto"
          style={{ color: page.name === 'debug' ? 'var(--text-primary)' : 'var(--text-muted)' }}
        >
          SSE 调试
        </button>
      </nav>

      {/* 页面内容 */}
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
