erDiagram
    DISCUSSION ||--o{ PANELIST : has
    DISCUSSION ||--o{ UTTERANCE : contains
    DISCUSSION ||--o{ CONSENSUS_POINT : derives
    DISCUSSION ||--o{ DIVERGENCE_POINT : derives
    DISCUSSION ||--o{ EVENT : logs
    PANELIST ||--o{ UTTERANCE : speaks

    DISCUSSION {
        string id PK "UUID"
        string topic "1-200字,经内容审核"
        string status "pending_panelists|in_progress|ended"
        int expert_count "2-8"
        int max_rounds "默认30,兜底上限"
        int current_round "当前轮次"
        string created_at "ISO8601"
        string ended_at "可空"
    }
    PANELIST {
        string id PK "UUID"
        string discussion_id FK "所属讨论,INDEX"
        string role "host|expert"
        string name "生成姓名"
        string title "职业/Title"
        string stance "立场"
        string color "专属颜色#hex"
        string status "idle|preparing|speaking|silent"
        string public_focus "JSON数组,公开关注点"
        int sort_order "host=0,expert 1..N"
    }
    UTTERANCE {
        string id PK "UUID"
        string discussion_id FK "INDEX"
        string panelist_id FK "发言人"
        int round_no "发言顺序(原seq,改名避免与SSE冲突)"
        string type "opening|statement|rebuttal|supplement|question|bridge|summary"
        string content "1-500字"
        string created_at "ISO8601"
    }
    CONSENSUS_POINT {
        string id PK "UUID"
        string discussion_id FK "INDEX"
        string content "共识描述(自然语言)"
        string involved_panelist_ids "JSON数组,认同者"
        string created_at "ISO8601"
        string updated_at "ISO8601,支撑实时更新"
    }
    DIVERGENCE_POINT {
        string id PK "UUID"
        string discussion_id FK "INDEX"
        string description "分歧描述"
        string camps "JSON: [{position,panelist_ids}]阵营分组"
        string created_at "ISO8601"
        string updated_at "ISO8601"
    }
    EVENT {
        int id PK "全局AUTOINCREMENT"
        string discussion_id FK "INDEX"
        int seq "per-discussion单调序列,SSE id唯一来源"
        string event_type "SSE事件类型"
        string payload_json "完整事件载荷"
        string created_at "ISO8601"
    }