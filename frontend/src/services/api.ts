import type {
  DiscussionListResponse,
  Discussion,
  CreateDiscussionPayload,
  CreateDiscussionResponse,
  TranscriptResponse,
  ConsensusState,
} from '../types';

const BASE = `${import.meta.env.VITE_API_BASE || 'http://localhost:8010'}/api`;

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

/** US2: 获取讨论列表 */
export function listDiscussions(): Promise<DiscussionListResponse> {
  return request('/discussions');
}

/** US2: 获取单场讨论详情 */
export function getDiscussion(id: string): Promise<Discussion> {
  return request(`/discussions/${id}`);
}

/** US2: 删除讨论 */
export function deleteDiscussion(id: string): Promise<{ deleted: boolean }> {
  return request(`/discussions/${id}`, { method: 'DELETE' });
}

/** US1: 创建讨论（触发嘉宾生成）—— 后端 DeepSeek 真实生成。 */
export function createDiscussion(
  payload: CreateDiscussionPayload,
): Promise<CreateDiscussionResponse> {
  return request('/discussions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/** US1: 确认嘉宾阵容 */
export function confirmPanelists(discussionId: string): Promise<{ discussion_id: string; status: string }> {
  return request(`/discussions/${discussionId}/panelists/confirm`, { method: 'PATCH' });
}

/** US1: 重新生成嘉宾 */
export function regeneratePanelists(discussionId: string): Promise<{ panelists: CreateDiscussionResponse['panelists'] }> {
  return request(`/discussions/${discussionId}/panelists/regenerate`, { method: 'POST' });
}

/** US3: 获取 transcript */
export function getTranscript(
  discussionId: string,
  beforeRound?: number,
): Promise<TranscriptResponse> {
  const params = new URLSearchParams();
  if (beforeRound) params.set('before_round', String(beforeRound));
  params.set('limit', '50');
  return request(`/discussions/${discussionId}/transcript?${params}`);
}

/** US3: 获取当前共识状态 */
export function getConsensusState(discussionId: string): Promise<ConsensusState> {
  return request(`/discussions/${discussionId}/consensus/current`);
}

