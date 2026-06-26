/** 最小 SSE hook：连接讨论事件流，每收到事件回调 onEvent。 */
import { useEffect, useRef } from "react";

export interface SSERawEvent {
  id: string;
  event: string;
  data: string;
}

export function useSSE(
  discussionId: string | null,
  onEvent: (evt: SSERawEvent) => void,
  lastEventId?: string,
) {
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!discussionId) return;

    const url = `http://localhost:8000/api/discussions/${discussionId}/events`;
    const es = new EventSource(url, { withCredentials: false });

    es.onmessage = (msg) => {
      onEventRef.current({
        id: msg.lastEventId ?? "",
        event: msg.type === "message" ? "message" : msg.type,
        data: msg.data,
      });
    };

    // 为具名事件类型注册监听
    const types = ["utterance", "panelist_status", "consensus_update", "divergence_update", "discussion_end", "heartbeat", "snapshot"];
    const cleanups: (() => void)[] = [];
    for (const t of types) {
      const handler = (msg: MessageEvent) => {
        onEventRef.current({ id: msg.lastEventId ?? "", event: t, data: msg.data });
      };
      es.addEventListener(t, handler);
      cleanups.push(() => es.removeEventListener(t, handler));
    }

    es.onerror = () => {
      onEventRef.current({ id: "", event: "error", data: "SSE connection error" });
    };

    return () => {
      es.close();
      cleanups.forEach((fn) => fn());
    };
  }, [discussionId]);
}
