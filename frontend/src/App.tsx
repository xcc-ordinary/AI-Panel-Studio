import { useState, useCallback } from 'react';
import type { CreateDiscussionResponse } from './types';
import DiscussionList from './components/home/DiscussionList';
import CreateDiscussion from './components/home/CreateDiscussion';
import PanelistRoster from './components/home/PanelistRoster';
import SseDebug from './components/debug/SseDebug'; // TODO Phase4 移除
import './App.css';

type Page =
  | { name: 'home' }
  | { name: 'create' }
  | { name: 'roster'; data: CreateDiscussionResponse }
  | { name: 'debug' }
  | { name: 'studio'; discussionId: string };

export default function App() {
  const [page, setPage] = useState<Page>({ name: 'home' });

  const goHome = useCallback(() => setPage({ name: 'home' }), []);
  const goCreate = useCallback(() => setPage({ name: 'create' }), []);
  const goDebug = useCallback(() => setPage({ name: 'debug' }), []);

  const handleCreated = useCallback((data: CreateDiscussionResponse) => {
    setPage({ name: 'roster', data });
  }, []);

  const handleConfirmed = useCallback((discussionId: string) => {
    setPage({ name: 'studio', discussionId });
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
        <DiscussionList onCreateNew={goCreate} onJoin={id => setPage({ name: 'studio', discussionId: id })} />
      )}
      {page.name === 'create' && (
        <CreateDiscussion onBack={goHome} onCreated={handleCreated} />
      )}
      {page.name === 'roster' && (
        <PanelistRoster data={page.data} onBackToCreate={goCreate} onConfirmed={handleConfirmed} />
      )}
      {page.name === 'debug' && <SseDebug />}
      {page.name === 'studio' && (
        <div className="max-w-4xl mx-auto px-4 py-20 text-center">
          <p className="text-lg mb-2" style={{ color: 'var(--text-secondary)' }}>
            演播厅 — Phase 4 实现
          </p>
          <p className="text-sm mb-6" style={{ color: 'var(--text-muted)' }}>
            discussion_id: {page.discussionId}
          </p>
          <button
            onClick={goHome}
            className="px-5 py-2.5 rounded-lg text-sm font-medium cursor-pointer"
            style={{ background: 'var(--bg-raised)', color: 'var(--text-primary)' }}
          >
            返回首页
          </button>
        </div>
      )}
    </div>
  );
}
