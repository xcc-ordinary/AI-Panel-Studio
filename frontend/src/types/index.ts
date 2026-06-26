/** 讨论状态 */
export type DiscussionStatus = 'pending_panelists' | 'in_progress' | 'ended';

/** 嘉宾角色 */
export type PanelistRole = 'host' | 'expert';

/** 嘉宾状态 */
export type PanelistStatus = 'idle' | 'preparing' | 'speaking' | 'silent';

/** 发言类型 */
export type UtteranceType =
  | 'opening' | 'statement' | 'rebuttal' | 'supplement'
  | 'question' | 'bridge' | 'summary';

export interface Panelist {
  id: string;
  discussion_id: string;
  role: PanelistRole;
  name: string;
  title: string;
  stance: string;
  color: string;
  status: PanelistStatus;
  public_focus: string;
  sort_order: number;
}

export interface Discussion {
  id: string;
  topic: string;
  status: DiscussionStatus;
  expert_count: number;
  max_rounds: number;
  current_round: number;
  panelist_count: number;
  created_at: string;
  ended_at?: string | null;
  panelists?: Panelist[];
}

export interface DiscussionListResponse {
  discussions: Discussion[];
  active_count: number;
  max_concurrent: number;
}

export interface Utterance {
  id: string;
  round_no: number;
  panelist_id: string;
  panelist_name: string;
  panelist_title: string;
  panelist_color: string;
  type: UtteranceType;
  content: string;
  created_at: string;
}

export interface TranscriptResponse {
  utterances: Utterance[];
  has_more: boolean;
}

export interface ConsensusPoint {
  id: string;
  content: string;
  involved_panelist_ids: string[];
  updated_at: string;
}

export interface DivergenceCamp {
  position: string;
  panelist_ids: string[];
}

export interface DivergencePoint {
  id: string;
  description: string;
  camps: DivergenceCamp[];
  updated_at: string;
}

export interface ConsensusState {
  consensus_points: ConsensusPoint[];
  divergence_points: DivergencePoint[];
  last_event_seq: number;
}

export interface CreateDiscussionPayload {
  topic: string;
  expert_count: number;
}

export interface CreateDiscussionResponse {
  discussion_id: string;
  topic: string;
  status: DiscussionStatus;
  panelists: Panelist[];
}

export interface SSERawEvent {
  id: string;
  event: string;
  data: string;
}
