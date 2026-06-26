"""种子数据：插入 ≥5 条预设讨论，供首页展示与 E2E 测试复用。

用法: python -m scripts.seed          # 从 backend/ 目录运行
      python -m backend.scripts.seed  # 从项目根目录运行

幂等：检查已有数据，若已存在则跳过。
"""
import asyncio
import json
import uuid
from datetime import datetime, timezone

from app.database import get_db, init_db, close_db


def _now():
    return datetime.now(timezone.utc).isoformat()


# ── 5 条预设讨论数据 ──────────────────────────────────────────────

SEED_DISCUSSIONS = [
    {
        "id": "seed-001-ai-open-source",
        "topic": "AI是否应该开源？",
        "status": "in_progress",
        "expert_count": 4,
        "max_rounds": 30,
        "current_round": 8,
        "created_at": "2026-06-25T10:00:00Z",
        "panelists": [
            {"id": "seed-001-host", "role": "host", "name": "张明远", "title": "科技媒体主编",
             "stance": "中立——关注技术发展与社会影响的平衡", "color": "#2563EB", "status": "speaking",
             "public_focus": json.dumps(["引导讨论节奏", "确保各方观点得到表达"]), "sort_order": 0},
            {"id": "seed-001-p1", "role": "expert", "name": "李开放", "title": "开源社区领袖",
             "stance": "强烈支持——开源是技术创新的核心驱动力", "color": "#DC2626", "status": "idle",
             "public_focus": json.dumps(["关注开源生态的可持续性"]), "sort_order": 1},
            {"id": "seed-001-p2", "role": "expert", "name": "陈安全", "title": "网络安全专家",
             "stance": "谨慎支持——开源促进安全审计，但需建立标准", "color": "#059669", "status": "idle",
             "public_focus": json.dumps(["开源模型的安全审计机制"]), "sort_order": 2},
            {"id": "seed-001-p3", "role": "expert", "name": "王商业", "title": "AI企业CEO",
             "stance": "务实立场——核心模型保留，工具链开源", "color": "#D97706", "status": "silent",
             "public_focus": json.dumps([]), "sort_order": 3},
            {"id": "seed-001-p4", "role": "expert", "name": "赵伦理", "title": "科技伦理学者",
             "stance": "需建立全球治理框架——开源不等于无监管", "color": "#7C3AED", "status": "idle",
             "public_focus": json.dumps(["AI治理的国际协调机制"]), "sort_order": 4},
        ],
        "utterances": [
            {"id": "seed-001-u1", "panelist_id": "seed-001-host", "round_no": 1, "type": "opening",
             "content": "欢迎各位来到今天的圆桌讨论。今天的话题是：AI是否应该开源？我们有四位来自不同领域的专家。李开放先生，您先来谈谈？",
             "created_at": "2026-06-25T10:00:10Z"},
            {"id": "seed-001-u2", "panelist_id": "seed-001-p1", "round_no": 2, "type": "statement",
             "content": "开源是AI创新的生命线。如果每家公司都把模型锁在保险柜里，我们永远无法建立一个健康的AI生态。",
             "created_at": "2026-06-25T10:00:20Z"},
            {"id": "seed-001-u3", "panelist_id": "seed-001-p2", "round_no": 3, "type": "supplement",
             "content": "我补充一点：开源确实有助于安全审计。我们最近发现的一个关键漏洞，正是因为模型的代码是公开的，才被及时发现并修复。",
             "created_at": "2026-06-25T10:00:30Z"},
            {"id": "seed-001-u4", "panelist_id": "seed-001-p3", "round_no": 4, "type": "rebuttal",
             "content": "但公司的研发投入需要回报。完全开源意味着任何人都可以复制我们的成果，这会打击企业创新的积极性。",
             "created_at": "2026-06-25T10:00:40Z"},
            {"id": "seed-001-u5", "panelist_id": "seed-001-p4", "round_no": 5, "type": "statement",
             "content": "我们需要跳出二元思维。问题不是该不该开源，而是如何建立一套全球性的AI治理框架，让开源的益处最大化、风险最小化。",
             "created_at": "2026-06-25T10:00:50Z"},
            {"id": "seed-001-u6", "panelist_id": "seed-001-host", "round_no": 6, "type": "question",
             "content": "赵伦理学者提到了治理框架，这个观点很有意思。李开放，您觉得开源社区能接受某种形式的监管吗？",
             "created_at": "2026-06-25T10:01:00Z"},
            {"id": "seed-001-u7", "panelist_id": "seed-001-p1", "round_no": 7, "type": "statement",
             "content": "监管不等于封杀。如果监管框架是由社区共同制定的，我想开源社区是愿意参与的。关键在于透明和参与。",
             "created_at": "2026-06-25T10:01:10Z"},
            {"id": "seed-001-u8", "panelist_id": "seed-001-p2", "round_no": 8, "type": "supplement",
             "content": "同意。我们可以在开源社区内部先建立安全标准，再向监管机构证明自我规制的可行性，而不是等外部强加规则。",
             "created_at": "2026-06-25T10:01:20Z"},
        ],
        "consensus": [
            {"id": "seed-001-c1", "content": "与会专家一致认为需要建立AI开源的安全标准与治理框架",
             "involved_panelist_ids": json.dumps(["seed-001-p1", "seed-001-p2", "seed-001-p4"]),
             "updated_at": "2026-06-25T10:01:30Z"},
        ],
        "divergence": [
            {"id": "seed-001-d1", "description": "关于开源程度的根本分歧：一方主张完全开源，另一方认为核心模型应保留商业壁垒",
             "camps": json.dumps([
                 {"position": "完全开源", "panelist_ids": ["seed-001-p1"]},
                 {"position": "有限开源", "panelist_ids": ["seed-001-p3"]},
                 {"position": "有治理的开源", "panelist_ids": ["seed-001-p2", "seed-001-p4"]},
             ]),
             "updated_at": "2026-06-25T10:01:30Z"},
        ],
    },
    {
        "id": "seed-002-remote-work",
        "topic": "远程办公是未来趋势还是昙花一现？",
        "status": "in_progress",
        "expert_count": 3,
        "max_rounds": 30,
        "current_round": 5,
        "created_at": "2026-06-25T12:00:00Z",
        "panelists": [
            {"id": "seed-002-host", "role": "host", "name": "刘思辨", "title": "商业评论主持人",
             "stance": "中立——关注效率与人文的平衡", "color": "#2563EB", "status": "idle",
             "public_focus": json.dumps(["确保讨论兼顾企业视角与员工视角"]), "sort_order": 0},
            {"id": "seed-002-p1", "role": "expert", "name": "孙远程", "title": "远程办公平台创始人",
             "stance": "远程办公是生产力革命——打破地理限制", "color": "#DC2626", "status": "idle",
             "public_focus": json.dumps(["远程协作工具的演进方向"]), "sort_order": 1},
            {"id": "seed-002-p2", "role": "expert", "name": "周管理", "title": "组织行为学教授",
             "stance": "混合制是归宿——远程与线下各有不可替代的价值", "color": "#059669", "status": "silent",
             "public_focus": json.dumps([]), "sort_order": 2},
            {"id": "seed-002-p3", "role": "expert", "name": "吴效率", "title": "大型企业HR总监",
             "stance": "审慎乐观——远程适合特定岗位，但不是万能药", "color": "#D97706", "status": "idle",
             "public_focus": json.dumps(["员工远程绩效的公平评估"]), "sort_order": 3},
        ],
        "utterances": [
            {"id": "seed-002-u1", "panelist_id": "seed-002-host", "round_no": 1, "type": "opening",
             "content": "各位好，今天讨论远程办公的未来。疫情后许多公司开始回归办公室，那么远程办公到底是一次性实验还是长期趋势？孙远程，作为这个领域的创业者，你先说说。",
             "created_at": "2026-06-25T12:00:10Z"},
            {"id": "seed-002-u2", "panelist_id": "seed-002-p1", "round_no": 2, "type": "statement",
             "content": "远程办公不是趋势，而是已经发生的现实。我们平台上已经有200万开发者完全远程工作，生产力的提升是实实在在的数据。",
             "created_at": "2026-06-25T12:00:20Z"},
            {"id": "seed-002-u3", "panelist_id": "seed-002-p3", "round_no": 3, "type": "rebuttal",
             "content": "数据是一方面，但我们在HR实践中看到，远程环境下的团队凝聚力和新人培养确实面临挑战。不是所有岗位都适合远程。",
             "created_at": "2026-06-25T12:00:30Z"},
            {"id": "seed-002-u4", "panelist_id": "seed-002-p2", "round_no": 4, "type": "statement",
             "content": "我的研究表明，混合办公模式——每周2-3天远程——在员工满意度和团队协作上取得了最佳平衡点。",
             "created_at": "2026-06-25T12:00:40Z"},
            {"id": "seed-002-u5", "panelist_id": "seed-002-host", "round_no": 5, "type": "bridge",
             "content": "周教授提出了一个中间路线。吴总监，从HR的角度，混合模式在管理上可行吗？",
             "created_at": "2026-06-25T12:00:50Z"},
        ],
        "consensus": [
            {"id": "seed-002-c1", "content": "与会专家同意混合办公模式是当前阶段的最优解",
             "involved_panelist_ids": json.dumps(["seed-002-p1", "seed-002-p2", "seed-002-p3"]),
             "updated_at": "2026-06-25T12:01:00Z"},
        ],
        "divergence": [
            {"id": "seed-002-d1", "description": "关于「远程是否适合所有岗位」存在分歧：创业者认为可全面推广，HR认为需按岗位区别对待",
             "camps": json.dumps([
                 {"position": "全面推广", "panelist_ids": ["seed-002-p1"]},
                 {"position": "按岗位区分", "panelist_ids": ["seed-002-p3"]},
             ]),
             "updated_at": "2026-06-25T12:01:00Z"},
        ],
    },
    {
        "id": "seed-003-cars",
        "topic": "城市该不该限制私家车数量？",
        "status": "in_progress",
        "expert_count": 3,
        "max_rounds": 30,
        "current_round": 4,
        "created_at": "2026-06-25T14:00:00Z",
        "panelists": [
            {"id": "seed-003-host", "role": "host", "name": "林对话", "title": "公共政策主持人",
             "stance": "中立——从城市治理角度审视各方论据", "color": "#2563EB", "status": "idle",
             "public_focus": json.dumps(["推动讨论聚焦于可操作的政策方案"]), "sort_order": 0},
            {"id": "seed-003-p1", "role": "expert", "name": "马交通", "title": "交通规划师",
             "stance": "支持合理限制——拥堵与污染已超出城市承载能力", "color": "#DC2626", "status": "idle",
             "public_focus": json.dumps(["拥堵收费的经济学模型"]), "sort_order": 1},
            {"id": "seed-003-p2", "role": "expert", "name": "郑自由", "title": "消费者权益律师",
             "stance": "反对强制限制——购车是个人自由，应改善公共交通而非限制私家车", "color": "#059669", "status": "idle",
             "public_focus": json.dumps(["行政限制的合法性边界"]), "sort_order": 2},
            {"id": "seed-003-p3", "role": "expert", "name": "黄绿能", "title": "新能源汽车产业分析师",
             "stance": "建议差异化政策——新能源车应鼓励，燃油车逐步限制", "color": "#D97706", "status": "silent",
             "public_focus": json.dumps([]), "sort_order": 3},
        ],
        "utterances": [
            {"id": "seed-003-u1", "panelist_id": "seed-003-host", "round_no": 1, "type": "opening",
             "content": "今天的讨论涉及每个人的日常出行。城市该不该限制私家车？马交通师，您怎么看？",
             "created_at": "2026-06-25T14:00:10Z"},
            {"id": "seed-003-u2", "panelist_id": "seed-003-p1", "round_no": 2, "type": "statement",
             "content": "北京平均通勤时间已经超过47分钟。不限制私家车增长，我们的道路系统将在五年内基本瘫痪。这是数学问题，不是意识形态问题。",
             "created_at": "2026-06-25T14:00:20Z"},
            {"id": "seed-003-u3", "panelist_id": "seed-003-p2", "round_no": 3, "type": "rebuttal",
             "content": "限制个人出行自由是治标不治本。真正的问题是公共交通不够好——如果地铁覆盖更广、班次更密，人们自然会减少开车。",
             "created_at": "2026-06-25T14:00:30Z"},
            {"id": "seed-003-u4", "panelist_id": "seed-003-p3", "round_no": 4, "type": "statement",
             "content": "我们可以有第三条路：对燃油车征收拥堵费，同时给新能源车提供充电优惠。用市场信号引导而非行政命令一刀切。",
             "created_at": "2026-06-25T14:00:40Z"},
        ],
        "consensus": [
            {"id": "seed-003-c1", "content": "各方同意应优先改善公共交通基础设施，将其作为解决城市交通问题的基础",
             "involved_panelist_ids": json.dumps(["seed-003-p1", "seed-003-p2", "seed-003-p3"]),
             "updated_at": "2026-06-25T14:01:00Z"},
        ],
        "divergence": [
            {"id": "seed-003-d1", "description": "对限制手段产生分歧：交通规划师支持行政限制，律师强调改善公交，产业分析师建议市场化手段",
             "camps": json.dumps([
                 {"position": "行政限制", "panelist_ids": ["seed-003-p1"]},
                 {"position": "改善公交", "panelist_ids": ["seed-003-p2"]},
                 {"position": "市场引导", "panelist_ids": ["seed-003-p3"]},
             ]),
             "updated_at": "2026-06-25T14:01:00Z"},
        ],
    },
    {
        "id": "seed-004-prepared-food",
        "topic": "预制菜该不该进校园？",
        "status": "in_progress",
        "expert_count": 3,
        "max_rounds": 30,
        "current_round": 3,
        "created_at": "2026-06-25T16:00:00Z",
        "panelists": [
            {"id": "seed-004-host", "role": "host", "name": "陈主持", "title": "教育话题主持人",
             "stance": "中立——关注食品安全与教育公平", "color": "#2563EB", "status": "idle",
             "public_focus": json.dumps(["厘清预制菜的定义和标准"]), "sort_order": 0},
            {"id": "seed-004-p1", "role": "expert", "name": "何食品", "title": "食品安全专家",
             "stance": "有条件支持——标准化预制菜比小作坊更安全可控", "color": "#DC2626", "status": "idle",
             "public_focus": json.dumps(["预制菜国标的落实情况"]), "sort_order": 1},
            {"id": "seed-004-p2", "role": "expert", "name": "吕家长", "title": "家长代表、营养学博士",
             "stance": "反对——新鲜食材对儿童发育不可替代，营养流失是核心问题", "color": "#059669", "status": "idle",
             "public_focus": json.dumps(["预制菜的维生素流失数据"]), "sort_order": 2},
            {"id": "seed-004-p3", "role": "expert", "name": "钱供应", "title": "团餐供应链管理者",
             "stance": "务实派——预制菜是解决大规模供餐效率问题的现实途径", "color": "#7C3AED", "status": "silent",
             "public_focus": json.dumps([]), "sort_order": 3},
        ],
        "utterances": [
            {"id": "seed-004-u1", "panelist_id": "seed-004-host", "round_no": 1, "type": "opening",
             "content": "预制菜进校园引发了广泛争议。家长们担心营养和安全，学校面临成本压力。何食品专家，从食品安全的角度看，预制菜到底安不安全？",
             "created_at": "2026-06-25T16:00:10Z"},
            {"id": "seed-004-u2", "panelist_id": "seed-004-p1", "round_no": 2, "type": "statement",
             "content": "这是一个误区。规范生产的预制菜在微生物指标上往往优于现场制作，因为工业化的冷链和灭菌流程更加可控。问题出在监管执行，不是产品本身。",
             "created_at": "2026-06-25T16:00:20Z"},
            {"id": "seed-004-u3", "panelist_id": "seed-004-p2", "round_no": 3, "type": "rebuttal",
             "content": "安全不等于营养。我们的检测数据显示，预制菜经过高温灭菌后，维生素C损失高达60%。对于正在发育的孩子，这不是小问题。",
             "created_at": "2026-06-25T16:00:30Z"},
        ],
        "consensus": [
            {"id": "seed-004-c1", "content": "与会专家一致认为预制菜进校园的前提是建立严格的营养与安全标准体系",
             "involved_panelist_ids": json.dumps(["seed-004-p1", "seed-004-p2", "seed-004-p3"]),
             "updated_at": "2026-06-25T16:01:00Z"},
        ],
        "divergence": [
            {"id": "seed-004-d1", "description": "在「校园是否应该完全禁止预制菜」上产生根本分歧：食品安全专家认为应看标准，家长代表认为应全面使用新鲜食材",
             "camps": json.dumps([
                 {"position": "建立标准后准入", "panelist_ids": ["seed-004-p1", "seed-004-p3"]},
                 {"position": "校园应全面使用新鲜食材", "panelist_ids": ["seed-004-p2"]},
             ]),
             "updated_at": "2026-06-25T16:01:00Z"},
        ],
    },
    {
        "id": "seed-005-ai-teacher",
        "topic": "AI能否取代人类教师？",
        "status": "in_progress",
        "expert_count": 4,
        "max_rounds": 30,
        "current_round": 3,
        "created_at": "2026-06-25T18:00:00Z",
        "panelists": [
            {"id": "seed-005-host", "role": "host", "name": "沈思", "title": "教育科技主持人",
             "stance": "中立——关注技术可行性与教育本质", "color": "#2563EB", "status": "idle",
             "public_focus": json.dumps(["区分AI辅助教学与AI替代教学"]), "sort_order": 0},
            {"id": "seed-005-p1", "role": "expert", "name": "丁智能", "title": "AI教育产品创始人",
             "stance": "AI将变革但不会取代教师——个性化辅导是AI强项", "color": "#DC2626", "status": "idle",
             "public_focus": json.dumps(["自适应学习系统的效果数据"]), "sort_order": 1},
            {"id": "seed-005-p2", "role": "expert", "name": "教书育", "title": "资深中学教师",
             "stance": "教育的本质是人与人的连接——AI可辅助但无法替代", "color": "#059669", "status": "idle",
             "public_focus": json.dumps(["师生关系对学生心理健康的影响"]), "sort_order": 2},
            {"id": "seed-005-p3", "role": "expert", "name": "纪未来", "title": "教育政策研究员",
             "stance": "谨慎推进——需先解决数字鸿沟和教师AI培训问题", "color": "#D97706", "status": "idle",
             "public_focus": json.dumps(["偏远地区AI教育资源的可及性"]), "sort_order": 3},
            {"id": "seed-005-p4", "role": "expert", "name": "韩创新", "title": "神经科学教授",
             "stance": "人脑社交学习机制不可复制——但AI可以重塑教育形式", "color": "#7C3AED", "status": "silent",
             "public_focus": json.dumps([]), "sort_order": 4},
        ],
        "utterances": [
            {"id": "seed-005-u1", "panelist_id": "seed-005-host", "round_no": 1, "type": "opening",
             "content": "随着GPT和各类AI教育工具的出现，一个根本性的问题浮出水面：AI最终能否取代人类教师？今天我们有四位来自不同领域的专家。丁智能，你们已经在这个方向上创业了，你怎么看？",
             "created_at": "2026-06-25T18:00:10Z"},
            {"id": "seed-005-u2", "panelist_id": "seed-005-p1", "round_no": 2, "type": "statement",
             "content": "我们的产品已经在200所学校试点，数据显示AI辅导能让学生数学成绩平均提升15%。但我必须诚实地说——最好的效果是AI+教师配合，而不是替代。",
             "created_at": "2026-06-25T18:00:20Z"},
            {"id": "seed-005-u3", "panelist_id": "seed-005-p2", "round_no": 3, "type": "statement",
             "content": "成绩不是教育的全部。我班上的孩子来学校不只为了学数学——他们需要被看见、被理解、被鼓励。一个AI给不出真正有温度的目光。",
             "created_at": "2026-06-25T18:00:30Z"},
        ],
        "consensus": [
            {"id": "seed-005-c1", "content": "与会专家一致认为AI+教师协同模式是当前最优教育方案",
             "involved_panelist_ids": json.dumps(["seed-005-p1", "seed-005-p2", "seed-005-p3"]),
             "updated_at": "2026-06-25T18:01:00Z"},
        ],
        "divergence": [
            {"id": "seed-005-d1", "description": "对「AI在教育中的角色边界」存在认知分歧：创业者强调个性化辅导的潜力，教师强调情感连接不可替代，神经科学家认为大脑的社交学习机制尚未被AI模拟",
             "camps": json.dumps([
                 {"position": "AI主导个性化", "panelist_ids": ["seed-005-p1"]},
                 {"position": "教师主导育人", "panelist_ids": ["seed-005-p2"]},
                 {"position": "协同互补", "panelist_ids": ["seed-005-p3", "seed-005-p4"]},
             ]),
             "updated_at": "2026-06-25T18:01:00Z"},
        ],
    },
    {
        "id": "seed-006-ended-sample",
        "topic": "人类应该在月球建立永久基地吗？",
        "status": "ended",
        "expert_count": 3,
        "max_rounds": 30,
        "current_round": 12,
        "created_at": "2026-06-24T10:00:00Z",
        "ended_at": "2026-06-24T11:30:00Z",
        "panelists": [
            {"id": "seed-006-host", "role": "host", "name": "方天文", "title": "科学节目主持人",
             "stance": "中立——平衡科学探索与务实考量", "color": "#2563EB", "status": "idle",
             "public_focus": json.dumps([]), "sort_order": 0},
            {"id": "seed-006-p1", "role": "expert", "name": "钱航天", "title": "航天工程师",
             "stance": "强烈支持——月球基地是火星探索的必要跳板", "color": "#DC2626", "status": "idle",
             "public_focus": json.dumps([]), "sort_order": 1},
            {"id": "seed-006-p2", "role": "expert", "name": "李地球", "title": "气候科学家",
             "stance": "反对——应优先投资地球生态修复而非太空殖民", "color": "#059669", "status": "idle",
             "public_focus": json.dumps([]), "sort_order": 2},
            {"id": "seed-006-p3", "role": "expert", "name": "诸葛法", "title": "国际法学者",
             "stance": "需要先确立月球资源开发的国际法律框架", "color": "#D97706", "status": "idle",
             "public_focus": json.dumps([]), "sort_order": 3},
        ],
        "utterances": [
            {"id": "seed-006-u1", "panelist_id": "seed-006-host", "round_no": 1, "type": "opening",
             "content": "今天讨论一个宏大的话题：人类应该在月球建立永久基地吗？这不仅是科学问题，更涉及经济、法律和人类文明的未来。",
             "created_at": "2026-06-24T10:00:10Z"},
        ],
        "consensus": [
            {"id": "seed-006-c1", "content": "各方认同月球探索具有科学价值，但对其优先性和资源配置方式存在不同看法",
             "involved_panelist_ids": json.dumps(["seed-006-p1", "seed-006-p2", "seed-006-p3"]),
             "updated_at": "2026-06-24T11:20:00Z"},
        ],
        "divergence": [
            {"id": "seed-006-d1", "description": "对「何时启动月球基地建设」存在时间表上的根本分歧",
             "camps": json.dumps([
                 {"position": "10年内启动", "panelist_ids": ["seed-006-p1"]},
                 {"position": "先解决地球问题", "panelist_ids": ["seed-006-p2"]},
                 {"position": "法律框架先行", "panelist_ids": ["seed-006-p3"]},
             ]),
             "updated_at": "2026-06-24T11:20:00Z"},
        ],
    },
]


async def seed():
    await init_db()
    db = await get_db()

    inserted = 0
    for disc in SEED_DISCUSSIONS:
        # 幂等检查
        row = await db.execute("SELECT 1 FROM discussion WHERE id = ?", (disc["id"],))
        if await row.fetchone():
            continue

        await db.execute(
            "INSERT INTO discussion (id, topic, status, expert_count, max_rounds, current_round, created_at, ended_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (disc["id"], disc["topic"], disc["status"], disc["expert_count"],
             disc["max_rounds"], disc["current_round"], disc["created_at"], disc.get("ended_at")),
        )

        for p in disc["panelists"]:
            await db.execute(
                "INSERT INTO panelist (id, discussion_id, role, name, title, stance, color, status, public_focus, sort_order) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (p["id"], disc["id"], p["role"], p["name"], p["title"], p["stance"],
                 p["color"], p["status"], p["public_focus"], p["sort_order"]),
            )

        for u in disc["utterances"]:
            await db.execute(
                "INSERT INTO utterance (id, discussion_id, panelist_id, round_no, type, content, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (u["id"], disc["id"], u["panelist_id"], u["round_no"], u["type"], u["content"], u["created_at"]),
            )

        for c in disc["consensus"]:
            now = c.get("updated_at", _now())
            await db.execute(
                "INSERT INTO consensus_point (id, discussion_id, content, involved_panelist_ids, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (c["id"], disc["id"], c["content"], c["involved_panelist_ids"], c.get("created_at", now), c["updated_at"]),
            )

        for d in disc["divergence"]:
            now = d.get("updated_at", _now())
            await db.execute(
                "INSERT INTO divergence_point (id, discussion_id, description, camps, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (d["id"], disc["id"], d["description"], d["camps"], d.get("created_at", now), d["updated_at"]),
            )

        inserted += 1

    await db.commit()

    if inserted > 0:
        print(f"[seed] 插入 {inserted} 条新讨论")
    else:
        print("[seed] 所有种子数据已存在，跳过")

    await close_db()


if __name__ == "__main__":
    asyncio.run(seed())
