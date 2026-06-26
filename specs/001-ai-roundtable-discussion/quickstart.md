# Quickstart: AI Panel Studio MVP 验证指南

**Date**: 2026-06-26

## Prerequisites

- Python 3.11+
- Node.js 22+
- DeepSeek API Key (set in `backend/.env`)

## Setup

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set DEEPSEEK_API_KEY=sk-...

# Frontend
cd frontend
npm install
```

## Environment Variables (`backend/.env`)

```
DEEPSEEK_API_KEY=sk-xxxxxxxx
DEEPSEEK_MODEL=deepseek-chat
DATABASE_PATH=./data/apanel.db
MAX_CONCURRENT_DISCUSSIONS=10
DEFAULT_MAX_ROUNDS=30
```

## Run

```bash
# Terminal 1: Backend (port 8000)
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --port 8000

# Terminal 2: Frontend (port 5173)
cd frontend
npm run dev
```

Open `http://localhost:5173` in browser.

## Validation Scenarios

### VS-1: Create Discussion & Generate Panelists

1. Open homepage → See empty state "还没有讨论，发起第一场吧"
2. Click "发起新讨论"
3. Enter topic "AI是否应该开源？", expert count 4
4. **Verify**: Within 10s, see 1 host + 4 experts with name, title, stance, unique color
5. Click "重新生成" → **Verify**: New panelist set, different personas
6. Click "确认阵容"

**Pass**: Navigated to studio view, discussion status "in_progress"

### VS-2: Live Discussion Flow

1. After VS-1, in studio view:
2. **Verify**: Host delivers opening within 5s — transcript shows opening utterance with host name + color
3. **Verify**: Within 10s, first expert speaks — transcript updates in real-time, no page refresh
4. **Verify**: Each utterance shows speaker name, title, and color badge — no "举手"/"准备发言" text
5. **Verify**: Panelist status windows show state changes (idle → preparing → speaking → idle)
6. Wait for ~5 utterances → **Verify**: Consensus panel shows at least one point

**Pass**: Real-time transcript scrolling, panelist states update, consensus appears

### VS-3: Multi-Discussion Isolation

1. Create Discussion A: topic "AI开源", 3 experts
2. Open new browser tab, create Discussion B: topic "远程办公", 3 experts
3. **Verify**: Tab A transcript does NOT contain Discussion B content
4. **Verify**: Tab B transcript does NOT contain Discussion A content
5. End Discussion A (wait or delete) → **Verify**: Discussion B unaffected

**Pass**: Complete data isolation between concurrent discussions

### VS-4: SSE Reconnection

1. During active discussion, open browser DevTools → Network
2. Find the SSE connection → Right click → "Block request URL"
3. Wait 5 seconds, then unblock
4. **Verify**: Within 3s, transcript and consensus panel recover to latest state
5. **Verify**: No missing utterances — all utterances during disconnection appear

**Pass**: Full state recovery after reconnection

### VS-5: Discussion End

1. Either: Wait for host to naturally conclude (may take many rounds) OR
   Create discussion with expert_count=2 and wait for max_rounds (currently 30)
   **Alternative**: Manually trigger end via API: `DELETE /api/discussions/{id}`
2. **Verify**: After end, host summary appears as natural language paragraph
3. **Verify**: No JSON or structured data visible in summary
4. **Verify**: Discussion marked "已结束" on homepage

**Pass**: Clean conclusion with natural language summary

### VS-6: Content Moderation

1. Try creating discussion with empty topic → **Verify**: Error "请输入讨论话题"
2. Try creating discussion with 1-char topic → **Verify**: Accepted or rejected per moderation rules
3. Try creating discussion with topic exceeding 200 chars → **Verify**: Rejected with clear message

**Pass**: Input validation and moderation behave correctly

### VS-7: Concurrency Limit

1. Create 10 discussions (or configure lower limit for testing)
2. Try creating the 11th → **Verify**: Friendly rejection with "当前讨论已满（10/10）"
3. **Verify**: Homepage shows "10/10" count display
4. Delete one discussion
5. Create new discussion → **Verify**: Now accepted

**Pass**: Limit enforced with user-friendly messaging

## Expected Issues (Known MVP Limitations)

- DeepSeek API may occasionally return malformed JSON for panelist generation — retry logic handles this
- Very long discussions (>20 rounds) may experience slower consensus extraction due to prompt size
- Mobile layout (<768px) is functional but may require horizontal scroll for some panels
- No authentication — anyone can observe or delete any discussion

## Quick Test Command

```bash
# Run backend tests
cd backend && python -m pytest tests/ -v

# Run frontend unit tests
cd frontend && npx vitest run

# Run E2E tests (requires backend + frontend running)
cd frontend && npx playwright test
```
