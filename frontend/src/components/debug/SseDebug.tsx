/** 临时调试组件：验证 SSE 事件流。Phase 3 验证后移除。 */
import { useState, useRef, useCallback } from "react";
import { useSSE, type SSERawEvent } from "../../hooks/useSSE";

export default function SseDebug() {
  const [discussionId, setDiscussionId] = useState("seed-001-ai-open-source");
  const [inputValue, setInputValue] = useState(discussionId);
  const [events, setEvents] = useState<SSERawEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleEvent = useCallback((evt: SSERawEvent) => {
    if (evt.event === "error") {
      setConnected(false);
      return;
    }
    setConnected(true);
    setEvents((prev) => {
      const next = [...prev, evt];
      return next.length > 50 ? next.slice(-50) : next;
    });
    // 自动滚动
    setTimeout(() => {
      if (containerRef.current) {
        containerRef.current.scrollTop = containerRef.current.scrollHeight;
      }
    }, 0);
  }, []);

  const handleConnect = () => setDiscussionId(inputValue);

  useSSE(discussionId, handleEvent);

  return (
    <div style={{ padding: 16, fontFamily: "monospace", maxWidth: 900, margin: "0 auto" }}>
      <h2>SSE 调试面板（临时）</h2>

      <div style={{ marginBottom: 12, display: "flex", gap: 8 }}>
        <input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          style={{ flex: 1, padding: "4px 8px", fontSize: 14 }}
          placeholder="discussion_id"
        />
        <button onClick={handleConnect} style={{ padding: "4px 16px" }}>
          连接
        </button>
        <span style={{ padding: 4 }}>
          状态: {connected ? <span style={{ color: "green" }}>● 已连接</span> : <span style={{ color: "red" }}>● 断开</span>}
        </span>
        <span style={{ padding: 4 }}>事件数: {events.length}</span>
      </div>

      <div
        ref={containerRef}
        style={{
          height: 500,
          overflow: "auto",
          background: "#1e1e1e",
          color: "#d4d4d4",
          borderRadius: 8,
          padding: 12,
          fontSize: 13,
          lineHeight: 1.6,
        }}
      >
        {events.length === 0 && <div style={{ color: "#888" }}>等待事件...</div>}
        {events.map((e, i) => (
          <div key={i} style={{ borderBottom: "1px solid #333", padding: "4px 0" }}>
            <span style={{ color: "#569cd6" }}>[{e.id}]</span>{" "}
            <span style={{ color: e.event === "utterance" ? "#4ec9b0" : e.event === "heartbeat" ? "#888" : "#dcdcaa" }}>
              {e.event}
            </span>
            {" "}
            <span style={{ color: "#ce9178" }}>{e.data.substring(0, 120)}{e.data.length > 120 ? "…" : ""}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
