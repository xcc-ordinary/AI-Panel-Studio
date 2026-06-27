/** SSE hook: 连接讨论事件流，解析 6 种命名事件，暴露 isConnected + lastEventId。
 *
 * 重连协议（Last-Event-ID）：
 * - publish() 写入 id: {Event.seq} 行 → 浏览器自动记录 lastEventId
 * - 断线后浏览器 EventSource 自动重连，请求头携带 Last-Event-ID
 * - 后端 get_events_after_seq() 只补发 seq > Last-Event-ID 的事件
 * - heartbeat / snapshot 不带 id: 字段，不污染浏览器 lastEventId
 * - 前端 useDiscussion 按 seq 去重，防止重连/快照重复推送
 */
import { useEffect, useRef, useState, useCallback } from "react";

export interface SSERawEvent {
  id: string;
  event: string;
  data: string;
}

interface UseSSEOptions {
  discussionId: string | null;
  onEvent: (evt: SSERawEvent) => void;
}

export function useSSE({ discussionId, onEvent }: UseSSEOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEventId, setLastEventId] = useState<string | null>(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!discussionId) return;

    const base = import.meta.env.VITE_API_BASE || 'http://localhost:8010';
    const url = `${base}/api/discussions/${discussionId}/events`;
    const es = new EventSource(url, { withCredentials: false });

    es.onopen = () => setIsConnected(true);

    const emit = (event: string, data: string, id: string) => {
      if (id && event !== 'heartbeat' && event !== 'snapshot') {
        setLastEventId(id);
      }
      onEventRef.current({ id, event, data });
    };

    // message 事件（无具名类型的兜底）
    es.onmessage = (msg: MessageEvent) => {
      emit('message', msg.data, msg.lastEventId ?? '');
    };

    // 6 种具名事件 + heartbeat + snapshot
    const types = [
      'utterance', 'panelist_status', 'consensus_update',
      'divergence_update', 'discussion_end', 'heartbeat', 'snapshot',
    ];
    const cleanups: (() => void)[] = [];
    for (const t of types) {
      const handler = (e: MessageEvent) => {
        emit(t, e.data, (e as MessageEvent & { lastEventId?: string }).lastEventId ?? '');
      };
      es.addEventListener(t, handler as EventListener);
      cleanups.push(() => es.removeEventListener(t, handler as EventListener));
    }

    es.onerror = () => {
      setIsConnected(false);
      onEventRef.current({ id: '', event: 'error', data: 'SSE connection error' });
    };

    return () => {
      es.close();
      cleanups.forEach(fn => fn());
      setIsConnected(false);
    };
  }, [discussionId]);

  return { isConnected, lastEventId };
}
