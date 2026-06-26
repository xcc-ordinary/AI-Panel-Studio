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

/** US1: 创建讨论（触发嘉宾生成） */
export async function createDiscussion(
  payload: CreateDiscussionPayload,
): Promise<CreateDiscussionResponse> {
  // TODO Phase4: 接 DeepSeek 真实生成。当前用 mock 占位。
  const resp = await fetch(`${BASE}/discussions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (resp.status === 502) {
    // LLM 不可用时返回 mock 阵容
    return mockCreateDiscussion(payload);
  }
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
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

// ── Mock 占位 ─────────────────────────────────────────────

async function mockCreateDiscussion(payload: CreateDiscussionPayload): Promise<CreateDiscussionResponse> {
  const colors = ['#38BDF8','#F87171','#818CF8','#FBBF24','#A78BFA','#FB923C','#E879F9','#2DD4BF','#FCA5A5'];
  const count = payload.expert_count;
  const panelists = [
    {
      id: `mock-host`, discussion_id: 'mock-d', role: 'host' as const,
      name: '张明远', title: '科技媒体主编', stance: '中立——引导多元观点对话',
      color: colors[0], status: 'idle' as const, public_focus: '[]', sort_order: 0,
    },
  ];
  const mockNames = ['李开放','陈安全','王商业','赵伦理','孙远程','周管理','吴效率','何食品'];
  const mockTitles = ['开源社区领袖','网络安全专家','AI企业CEO','科技伦理学者','远程办公平台创始人','组织行为学教授','大型企业HR总监','食品安全专家'];
  const mockStances = [
    '强烈支持——技术创新需要开放生态',
    '谨慎支持——安全审计需要透明，但需建立标准',
    '务实立场——核心模型保留，工具链开源',
    '需建立全球治理框架——开源不等于无监管',
    '远程办公是生产力革命——打破地理限制',
    '混合制是归宿——远程与线下各有不可替代的价值',
    '审慎乐观——远程适合特定岗位，但不是万能药',
    '有条件支持——标准化预制菜比小作坊更安全可控',
  ];

  for (let i = 0; i < count; i++) {
    panelists.push({
      id: `mock-p${i}`, discussion_id: 'mock-d', role: 'expert' as const,
      name: mockNames[i] || `专家${i + 1}`, title: mockTitles[i] || '领域专家',
      stance: mockStances[i] || '独特视角——从专业领域出发审视话题',
      color: colors[(i + 1) % colors.length], status: 'idle' as const,
      public_focus: '[]', sort_order: i + 1,
    });
  }

  // 模拟 1-3 秒生成延迟
  await new Promise(r => setTimeout(r, 800 + Math.random() * 1500));

  return {
    discussion_id: 'mock-d',
    topic: payload.topic,
    status: 'pending_panelists',
    panelists,
  };
}
