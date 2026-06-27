/** 演播厅数据加载: GET 快照 → SSE 增量
 *
 * 去重策略（防止重连/快照导致重复数据）：
 * - utterance: 按 Event.seq（SSE id 字段）去重，seenSeqs 集合
 * - panelist_status: 按 panelist_id 幂等覆盖
 * - consensus_update / divergence_update: 按业务 id upsert
 * - snapshot: 合并（按 id 去重追加 / upsert），绝不替换已有状态
 *
 * 重连协议：
 * - 浏览器 EventSource 自动发送 Last-Event-ID = 最后收到的 id: 字段值
 * - 后端只补发 seq > Last-Event-ID 的事件（get_events_after_seq WHERE seq > ?）
 * - snapshot 不带 id: 字段，不污染浏览器 lastEventId
 */
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

  // seq 去重：杜绝重连/快照/回放导致同一条事件被重复消费
  const seenSeqsRef = useRef<Set<number>>(new Set());

  // ── 快照加载 ──────────────────────────────────
  useEffect(() => {
    if (!discussionId) {
      seenSeqsRef.current.clear();
      return;
    }
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
        // REST 快照加载后清空 seq 去重集（新讨论新起点）
        seenSeqsRef.current.clear();
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

    // 解析 Event.seq（SSE id 字段 = 全局事件序号）
    const seq = evt.id ? parseInt(evt.id, 10) : 0;

    try {
      const payload = JSON.parse(evt.data);

      switch (evt.event) {
        case 'utterance': {
          // seq 去重：同一事件绝不重复 append
          if (seq && seenSeqsRef.current.has(seq)) break;
          if (seq) seenSeqsRef.current.add(seq);
          setUtterances(prev => [...prev, payload as Utterance]);
          break;
        }

        case 'panelist_status':
          // 幂等合并：按 panelist_id 覆盖
          setPanelists(prev => prev.map(p =>
            p.id === payload.panelist_id
              ? { ...p, status: payload.status, public_focus: payload.public_focus ?? p.public_focus }
              : p
          ));
          break;

        case 'consensus_update':
          // 幂等合并：按业务 id upsert
          setConsensus(prev => {
            const idx = prev.findIndex(c => c.id === payload.id);
            if (idx >= 0) return prev.map((c, i) => i === idx ? payload : c);
            return [...prev, payload];
          });
          break;

        case 'divergence_update':
          // 幂等合并：按业务 id upsert
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
          // 重连快照：合并而非替换——防止冲掉已有状态
          // snapshot 不带 id: 字段（不污染浏览器 lastEventId），所有数据按业务 id 去重合并
          if (payload.recent_utterances?.length) {
            setUtterances(prev => {
              const existing = new Set(prev.map(u => u.id));
              const newOnes = (payload.recent_utterances as Utterance[])
                .filter(u => !existing.has(u.id));
              return [...prev, ...newOnes];
            });
          }
          if (payload.consensus_points?.length) {
            setConsensus(prev => {
              const map = new Map(prev.map(c => [c.id, c]));
              for (const c of payload.consensus_points as ConsensusPoint[]) {
                map.set(c.id, c);
              }
              return [...map.values()];
            });
          }
          if (payload.divergence_points?.length) {
            setDivergences(prev => {
              const map = new Map(prev.map(d => [d.id, d]));
              for (const d of payload.divergence_points as DivergencePoint[]) {
                map.set(d.id, d);
              }
              return [...map.values()];
            });
          }
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
