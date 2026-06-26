/** 演播厅数据加载: GET 快照 → SSE 增量 */
import { useEffect, useState, useCallback, useRef } from 'react';
import type { Discussion, Panelist, Utterance, ConsensusPoint, DivergencePoint } from '../types';
import { getDiscussion, getTranscript, getConsensusState } from '../services/api';
import { useSSE, type SSERawEvent } from './useSSE';

interface DiscussionState {
  discussion: Discussion | null;
  panelists: Panelist[];
  utterances: Utterance[];
  consensus: ConsensusPoint[];
  divergences: DivergencePoint[];
  loading: boolean;
  error: string | null;
  isConnected: boolean;
  discussionEnded: boolean;
  hostSummary: string | null;
}

export function useDiscussion(discussionId: string | null): DiscussionState {
  const [discussion, setDiscussion] = useState<Discussion | null>(null);
  const [panelists, setPanelists] = useState<Panelist[]>([]);
  const [utterances, setUtterances] = useState<Utterance[]>([]);
  const [consensus, setConsensus] = useState<ConsensusPoint[]>([]);
  const [divergences, setDivergences] = useState<DivergencePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [discussionEnded, setDiscussionEnded] = useState(false);
  const [hostSummary, setHostSummary] = useState<string | null>(null);

  const panelistsRef = useRef(panelists);
  panelistsRef.current = panelists;

  // ── 快照加载 ──────────────────────────────────
  useEffect(() => {
    if (!discussionId) return;
    let cancelled = false;
    async function load() {
      setLoading(true); setError(null);
      try {
        const [disc, trans, cons] = await Promise.all([
          getDiscussion(discussionId),
          getTranscript(discussionId),
          getConsensusState(discussionId),
        ]);
        if (cancelled) return;
        setDiscussion(disc);
        setPanelists(disc.panelists || []);
        setUtterances(trans.utterances);
        setConsensus(cons.consensus_points);
        setDivergences(cons.divergence_points);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [discussionId]);

  // ── SSE 增量 ─────────────────────────────────
  const handleSSE = useCallback((evt: SSERawEvent) => {
    if (evt.event === 'error') return;

    try {
      const payload = JSON.parse(evt.data);

      switch (evt.event) {
        case 'utterance':
          setUtterances(prev => [...prev, payload as Utterance]);
          break;

        case 'panelist_status':
          setPanelists(prev => prev.map(p =>
            p.id === payload.panelist_id
              ? { ...p, status: payload.status, public_focus: payload.public_focus ?? p.public_focus }
              : p
          ));
          break;

        case 'consensus_update':
          setConsensus(prev => {
            const idx = prev.findIndex(c => c.id === payload.id);
            if (idx >= 0) return prev.map((c, i) => i === idx ? payload : c);
            return [...prev, payload];
          });
          break;

        case 'divergence_update':
          setDivergences(prev => {
            const idx = prev.findIndex(d => d.id === payload.id);
            if (idx >= 0) return prev.map((d, i) => i === idx ? payload : d);
            return [...prev, payload];
          });
          break;

        case 'discussion_end':
          setDiscussionEnded(true);
          setHostSummary(payload.summary || null);
          break;

        case 'snapshot':
          // snapshot 不带 id——不更新 lastEventId，仅用于快速恢复状态
          setUtterances(payload.recent_utterances || []);
          setConsensus(payload.consensus_points || []);
          setDivergences(payload.divergence_points || []);
          break;
      }
    } catch { /* ignore malformed JSON */ }
  }, []);

  const { isConnected } = useSSE({ discussionId, onEvent: handleSSE });

  return {
    discussion, panelists, utterances, consensus, divergences,
    loading, error, isConnected, discussionEnded, hostSummary,
  };
}
