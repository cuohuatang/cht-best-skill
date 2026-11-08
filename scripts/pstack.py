#!/usr/bin/env python3
"""pstack — 帝王团队编排引擎（cht-best-skill V0.0.5 · 组织层）

把"把 AI 当员工养"落成可执行的落盘状态机，而不是口号：
  manifest.json  = 机器可读的花名册/任务台账/技能库（唯一事实源）
  agents/<id>/{outbox,inbox} = 每个 AI 员工独立输出区（身份隔离，好排查）
  handoff = 真的把上游产物落到下游 inbox，杜绝人工传话
  capture = 把干成的方法沉淀成可复用技能
  verify  = 硬闸门（3-5 岗上限、职责契约完整、验收与证据、复述确认）

用法:
    python3 pstack.py init [--dir DIR] [--team NAME]
    python3 pstack.py hire --id ID --name NAME --class CLASS --duty DUTY \
                           --scenario SCENARIO [--schedule SCHED] [--dir DIR]
    python3 pstack.py onboard [--dir DIR]            # 生成"自报家门 + 怎么搭手"契约
    python3 pstack.py dispatch --to ID --task TASK --acceptance ACC [--dir DIR]
    python3 pstack.py handoff --from ID --to ID [--file PATH] [--dir DIR]
    python3 pstack.py capture --name NAME --from-task TASK --method METHOD [--dir DIR]
    python3 pstack.py reuse --name NAME --task TASK [--dir DIR]
    python3 pstack.py review [--dir DIR]             # 定期查岗迭代
    python3 pstack.py verify [--dir DIR]             # 硬闸门，退出码 1 阻断
    python3 pstack.py status [--dir DIR]

三才槽位（class）：天才/决策层 · 地才/执行层 · 人才/编排层
"""
import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_ROOT = "agent-team"
MIN_AGENTS, MAX_AGENTS = 3, 5          # 重质不重量：3-5 个调教透的
CLASSES = ("天才/决策层", "地才/执行层", "人才/编排层")
REQUIRED_AGENT_FIELDS = ("duty", "scenario", "schedule", "outputs", "acceptance")

# 三才默认班子（刘邦=人，只定方向搭班子，不在花名册里）
SEED_AGENTS = [
    {
        "id": "zhangliang", "name": "张良", "class": "天才/决策层",
        "duty": "理解任务、拆分成可派发的子任务、定验收标准、跟进进度；不写执行产物",
        "scenario": "多步/跨会话/需拆分的复杂任务开工前",
        "schedule": "on-demand", "reports_to": "boss", "may_hire": ["专项参谋"],
        "inputs": ["目标与约束", "task_plan.md 的野心升级三项"],
        "outputs": ["分派清单(含每项验收标准)", "风险与依赖说明"],
        "acceptance": ["每个子任务都有可执行动作与验收标准", "不臆造需求(心法02)"],
    },
    {
        "id": "hanxin", "name": "韩信", "class": "地才/执行层",
        "duty": "按分派清单具体干活、产出可点开的证据；可按需招募专项执行 AI",
        "scenario": "需要真正产出文件/代码/数据的执行阶段",
        "schedule": "on-demand", "reports_to": "zhangliang", "may_hire": ["专项工程师"],
        "inputs": ["分派清单", "上游 handoff 的原始材料"],
        "outputs": ["产物文件路径", "命令输出/前后对比"],
        "acceptance": ["交付必须带证据路径(心法05)", "缺数据先要，绝不编造(心法03)"],
    },
    {
        "id": "xiaohe", "name": "萧何", "class": "人才/编排层",
        "duty": "维护三文件记忆、技能库、验证护栏与后勤；调用预设技能完成标准化重复工作",
        "scenario": "全程；尤其是记忆落盘、技能沉淀、多层校验、查岗迭代",
        "schedule": "on-demand", "reports_to": "boss", "may_hire": ["账房/校验员"],
        "inputs": ["各角色 outbox 产物", "progress.md 日志"],
        "outputs": ["findings/progress 更新", "技能文件", "查岗考核表"],
        "acceptance": ["外部验证标准，禁止 AI 自评", "每步留痕可追溯"],
    },
]


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def slug(s):
    s = re.sub(r'[\\/:*?"<>|\s]+', "-", str(s).strip())
    return re.sub(r"-{2,}", "-", s).strip("-")[:50] or "item"


def root_of(args):
    # --dir 可放在子命令之前或之后（common parent + SUPPRESS 避免默认值覆盖）
    d = getattr(args, "dir", None)
    return Path(d).expanduser().resolve() if d else Path.cwd() / DEFAULT_ROOT


def load(root):
    mf = root / "manifest.json"
    if not mf.is_file():
        print(f"[x] 未找到团队：{mf}，请先跑 pstack.py init", file=sys.stderr)
        return None
    return json.loads(mf.read_text(encoding="utf-8"))


def save(root, data):
    data["updated"] = now()
    (root / "manifest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_init(args):
    root = root_of(args)
    root.mkdir(parents=True, exist_ok=True)
    mf = root / "manifest.json"
    if mf.is_file() and not args.force:
        print(f"[=] 团队已存在：{root}（--force 可重建）")
        return 0
    data = {
        "team": args.team, "version": "V0.0.5", "created": now(), "updated": now(),
        "boss": {
            "role": "刘邦/调度者(人)",
            "duty": "只定方向与搭班子，不亲自干活、不做传话筒、不做思考型军师",
            "keeps": ["提问权", "决断权", "最终结果审核权"],
        },
        "agents": [], "tasks": [], "skills": [], "handoffs": [], "reviews": [],
        "principles": {
            "capacity": f"常设岗 {MIN_AGENTS}-{MAX_AGENTS} 个，重质不重量；专项执行实例按需临时招募，不入常设花名册",
            "no_relay": "凡需人工把信息从 A 搬到 B，立即停工并反问 AI：这一步怎么自动化？",
            "no_persona": "角色=职责契约(输入/输出/验收)，不是人设形容词；禁止『你是某某专家』",
            "voice_restate": "交代任务后必须让 AI 用自己的话复述一遍，确认听懂才开工",
            "identity": "每个员工独立 outbox，输出与人分开，出问题好排查",
        },
    }
    for a in SEED_AGENTS:
        data["agents"].append(dict(a, status="active", version=1, created=now()))
    save(root, data)
    render_roster(root, data)
    for a in data["agents"]:
        d = root / "agents" / a["id"]
        (d / "outbox").mkdir(parents=True, exist_ok=True)
        (d / "inbox").mkdir(parents=True, exist_ok=True)
        render_profile(d, a)
    for sub in ("skills", "ledger", "reviews", "handoffs"):
        (root / sub).mkdir(exist_ok=True)
    (root / "ONBOARDING.md").write_text(ONBOARDING_TPL, encoding="utf-8")
    print(f"帝王团队已组建：{root}")
    print(f"  常设岗 {len(data['agents'])} 个（上限 {MAX_AGENTS}）：" +
          "、".join(f"{a['name']}({a['class']})" for a in data["agents"]))
    print("  刘邦=你：只定方向搭班子；张良拆分、韩信执行、萧何编排与后勤")
    print("\n下一步：")
    print("  ① 填 ONBOARDING.md（先自报家门，再问『咱俩怎么搭手』）")
    print(f"  ② python3 pstack.py onboard   # 生成协作契约提问清单")
    print(f"  ③ python3 pstack.py verify \"{root}\"   # 硬闸门校验")
    return 0


ONBOARDING_TPL = """# 入职契约：先自报家门，再谈怎么搭手

> 第 3 条心法：别一上来就甩指令。先告诉 AI 你是谁、干啥的、最烦啥活，再问「你觉得咱俩怎么搭手？」。
> 复述确认门（第 7 条）：讲完让 AI 用自己的话复述一遍，听懂没、缺啥一眼看明白。

## A. 我（刘邦）自报家门 —— 由人填

- 我是谁 / 我的角色：【待填】
- 我主要干什么业务：【待填】
- 我最烦、最耗时的活：【待填】
- 哪些活最好交给 AI：【待填】
- 我只要什么结果（方向/验收）：【待填】

## B. 反问 AI —— 让 AI 先给思路

> 你觉得咱俩怎么搭手？从哪开始？我上面说的哪里你还需要补材料？

- AI 的搭手建议：【待填】
- AI 说还缺的材料：【待填】

## C. 复述确认门 —— 未确认不得开工

> 用你自己的话，把目标、约束、交付物、验收标准复述一遍。

- AI 复述：【待填】
- 人确认（听懂了 / 缺什么）：【待填】

> 硬闸门：A/B/C 的【待填】未清空，`verify_team.py` 阻断派工。
"""


def render_profile(d: Path, a: dict):
    lines = [
        f"# {a['name']} · {a['id']}", "",
        f"- 三才槽位：{a['class']}",
        f"- 汇报对象：{a['reports_to']}",
        f"- 定时：{a['schedule']}",
        f"- 状态：{a.get('status','active')} / v{a.get('version',1)}",
        "", "## 职责（动词描述，禁止人设形容词）", f"{a['duty']}", "",
        "## 什么时候好用", f"{a['scenario']}", "",
        "## 输入", *[f"- {x}" for x in a["inputs"]], "",
        "## 输出", *[f"- {x}" for x in a["outputs"]], "",
        "## 验收标准", *[f"- {x}" for x in a["acceptance"]], "",
        "## 可自行招募（递归分工）", *[f"- {x}" for x in a.get("may_hire", [])], "",
        f"> 独立输出区：`agents/{a['id']}/outbox/`（与人分开，出问题好排查）",
    ]
    (d / "PROFILE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_roster(root: Path, data: dict):
    lines = [
        f"# {data['team']} · 花名册", "",
        f"- 建团：{data['created']} · 更新：{data['updated']}",
        f"- 常设岗：{len(data['agents'])}/{MAX_AGENTS}（重质不重量）", "",
        f"## 刘邦（人）= {data['boss']['role']}", "",
        f"{data['boss']['duty']}", "",
        "保留：" + "、".join(data["boss"]["keeps"]), "",
        "## 三才常设岗", "",
        "| 槽位 | 姓名 | ID | 职责 | 定时 | 汇报对象 | 状态 |",
        "|---|---|---|---|---|---|---|",
    ]
    for a in data["agents"]:
        lines.append(f"| {a['class']} | {a['name']} | `{a['id']}` | {a['duty']} | "
                     f"{a['schedule']} | {a['reports_to']} | {a.get('status','active')} |")
    lines += ["", "## 红线", ""]
    for k, v in data["principles"].items():
        lines.append(f"- **{k}**：{v}")
    lines += ["", "> 常设岗 3-5 个；专项执行实例按需临时招募，不入常设花名册（AI 不在多在精）。",
              "> 角色 = 职责契约（输入/输出/验收），不是人设形容词；禁止『你是某某专家』。"]
    (root / "ROSTER.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_hire(args):
    root = root_of(args)
    data = load(root)
    if data is None:
        return 1
    if any(a["id"] == args.id for a in data["agents"]):
        print(f"[x] 岗位 {args.id} 已存在", file=sys.stderr)
        return 1
    if len(data["agents"]) >= MAX_AGENTS:
        print(f"[x] 常设岗已满 {MAX_AGENTS} 个（AI 不在多在精）。"
              f"请先 review 考核调整，或把专项活作为临时执行实例外派，不要再加半吊子。",
              file=sys.stderr)
        return 1
    if args.class_ not in CLASSES:
        print(f"[x] class 必须是：{' / '.join(CLASSES)}", file=sys.stderr)
        return 1
    a = {
        "id": args.id, "name": args.name, "class": args.class_,
        "duty": args.duty, "scenario": args.scenario,
        "schedule": args.schedule, "reports_to": args.reports_to,
        "may_hire": [x.strip() for x in args.may_hire.split(",") if x.strip()],
        "inputs": [x.strip() for x in args.inputs.split(",") if x.strip()],
        "outputs": [x.strip() for x in args.outputs.split(",") if x.strip()],
        "acceptance": [x.strip() for x in args.acceptance.split(",") if x.strip()],
        "status": "active", "version": 1, "created": now(),
    }
    # AI 人事：职责契约五问，缺一即拒绝（防止捏出半吊子员工）
    missing = [f for f in REQUIRED_AGENT_FIELDS if not a.get(f)]
    if missing:
        print(f"[x] 职责契约缺字段：{missing} —— AI 人事必须先问清再捏人", file=sys.stderr)
        return 1
    data["agents"].append(a)
    save(root, data)
    render_roster(root, data)
    d = root / "agents" / a["id"]
    (d / "outbox").mkdir(parents=True, exist_ok=True)
    (d / "inbox").mkdir(parents=True, exist_ok=True)
    render_profile(d, a)
    print(f"+ 已聘用 {a['name']}({a['class']}) → {d}")
    print(f"  常设岗 {len(data['agents'])}/{MAX_AGENTS}")
    return 0


def cmd_onboard(args):
    root = root_of(args)
    data = load(root)
    if data is None:
        return 1
    print("=== AI 人事 · 造人五问（先问清场景，再捏职责清晰的员工）===")
    for i, q in enumerate([
        "你是干什么的？业务场景是什么？",
        "哪些活最好使、最该交给 AI？哪些必须人定？",
        "要不要定时干活？（on-demand / cron:<表达式> / event:<事件>）",
        "主要跟谁对接？上游给什么、下游要什么？",
        "做到什么算合格？外部验证标准是什么（禁止 AI 自评）？",
    ], 1):
        print(f"  {i}. {q}")
    print("\n=== 搭手之前，先自报家门 ===")
    print("  告诉 AI：我是谁 / 干啥的 / 最烦啥活 → 再问「你觉得咱俩怎么搭手？」")
    print("  讲完补一句「用你自己的话复述一遍」→ 听懂没、缺啥一眼看明白")
    print(f"\n契约文件：{root / 'ONBOARDING.md'}（未清空【待填】时 verify 阻断派工）")
    return 0


def cmd_dispatch(args):
    root = root_of(args)
    data = load(root)
    if data is None:
        return 1
    if not any(a["id"] == args.to for a in data["agents"]):
        print(f"[x] 花名册里没有 {args.to}", file=sys.stderr)
        return 1
    # 复述确认门：ONBOARDING.md 未填完，禁止派工
    ob = root / "ONBOARDING.md"
    if ob.is_file() and "【待填】" in ob.read_text(encoding="utf-8"):
        print("[x] 入职契约未确认（ONBOARDING.md 仍有【待填】）。"
              "先自报家门 + 让 AI 复述一遍，再派工。", file=sys.stderr)
        return 1
    tid = f"T{len(data['tasks'])+1:03d}"
    t = {
        "id": tid, "to": args.to, "task": args.task,
        "acceptance": args.acceptance, "evidence_path": "",
        "status": "dispatched", "created": now(),
    }
    data["tasks"].append(t)
    save(root, data)
    card = [
        f"# {tid} · 派工单", "", f"- 派给：{args.to}", f"- 时间：{t['created']}",
        f"- 状态：{t['status']}", "", "## 任务", args.task, "",
        "## 验收标准（可核验）", args.acceptance, "",
        "## 证据路径（交付必填，心法05）", "> 【待填】", "",
        "## AI 复述确认", "> 【待填】用你自己的话复述目标与验收标准", "",
        f"> 产物落在 `agents/{args.to}/outbox/`，交接用 pstack.py handoff，不要人工搬运。",
    ]
    (root / "ledger" / f"{tid}-{slug(args.task)}.md").write_text(
        "\n".join(card) + "\n", encoding="utf-8")
    print(f"+ 派工 {tid} → {args.to}：{args.task}")
    return 0


def cmd_handoff(args):
    """第 6 条的可执行化：真的把上游产物落到下游 inbox，杜绝人工传话。"""
    root = root_of(args)
    data = load(root)
    if data is None:
        return 1
    ids = {a["id"] for a in data["agents"]}
    if args.src not in ids or args.dst not in ids:
        print("[x] --from / --to 必须是花名册内的 ID", file=sys.stderr)
        return 1
    src = root / "agents" / args.src / "outbox"
    dst = root / "agents" / args.dst / "inbox"
    dst.mkdir(parents=True, exist_ok=True)
    files = ([Path(args.file)] if args.file
             else [p for p in src.rglob("*") if p.is_file()])
    moved = []
    for f in files:
        f = Path(f).expanduser()
        if not f.is_file():
            continue
        target = dst / f.name
        shutil.copy2(f, target)
        moved.append(str(target.relative_to(root)))
    rec = {"from": args.src, "to": args.dst, "files": moved, "at": now()}
    data["handoffs"].append(rec)
    save(root, data)
    (root / "handoffs" / f"{now().replace(' ','-').replace(':','')}-{args.src}-to-{args.dst}.md").write_text(
        f"# 自动流转：{args.src} → {args.dst}\n\n- 时间：{now()}\n" +
        "".join(f"- `{m}`\n" for m in moved) +
        "\n> 未经人手搬运。若发现自己在复制粘贴，立刻停，反问 AI 怎么自动化。\n",
        encoding="utf-8")
    print(f"⇄ 自动流转 {args.src} → {args.dst}：{len(moved)} 个文件")
    if not moved:
        print("  (!) 上游 outbox 为空，请先把产物落到 outbox/")
    return 0


def cmd_capture(args):
    """第 4 条：干成事儿立刻存成技能，以后『用这个技能干 XX』。"""
    root = root_of(args)
    data = load(root)
    if data is None:
        return 1
    name = slug(args.name)
    if any(s["name"] == name for s in data["skills"]) and not args.force:
        print(f"[x] 技能 {name} 已存在（--force 覆盖）", file=sys.stderr)
        return 1
    sk = {"name": name, "from_task": args.from_task, "method": args.method,
          "created": now(), "reuse_count": 0, "source": "pstack capture"}
    data["skills"] = [s for s in data["skills"] if s["name"] != name] + [sk]
    save(root, data)
    (root / "skills" / f"{name}.md").write_text(
        f"# 技能：{name}\n\n- 沉淀自：{args.from_task}\n- 时间：{now()}\n\n"
        f"## 方法（可复用步骤）\n\n{args.method}\n\n"
        f"## 调用方式\n\n> 用这个技能干【XX】\n\n"
        f"> 建议同步备份到 GitHub（攒公司资产），并纳入 verify 的复用检查。\n",
        encoding="utf-8")
    print(f"+ 技能已固化：{root / 'skills' / (name + '.md')}")
    print(f"  以后说「用这个技能干 XX」即可套用；当前技能库 {len(data['skills'])} 个")
    return 0


def cmd_reuse(args):
    root = root_of(args)
    data = load(root)
    if data is None:
        return 1
    sk = next((s for s in data["skills"] if s["name"] == slug(args.name)), None)
    if not sk:
        print(f"[x] 技能库里没有 {args.name}；先 capture 再复用", file=sys.stderr)
        return 1
    sk["reuse_count"] += 1
    save(root, data)
    print(f"复用技能「{sk['name']}」干：{args.task}")
    print(f"\n--- 方法 ---\n{sk['method']}\n--- 累计复用 {sk['reuse_count']} 次 ---")
    return 0


def cmd_review(args):
    """第 1 条：定期查岗考核，根据问题升级调整。"""
    root = root_of(args)
    data = load(root)
    if data is None:
        return 1
    counts = {}
    for t in data["tasks"]:
        counts[t["to"]] = counts.get(t["to"], 0) + 1
    lines = [
        f"# 查岗考核 · {now()}", "",
        f"- 常设岗：{len(data['agents'])}/{MAX_AGENTS}",
        f"- 任务：{len(data['tasks'])} · 技能：{len(data['skills'])} · 自动流转：{len(data['handoffs'])}",
        "", "| 岗位 | 三才 | 定时 | 承接任务 | 待验证 | 建议 |", "|---|---|---|---|---|---|",
    ]
    for a in data["agents"]:
        n = counts.get(a["id"], 0)
        todo = sum(1 for t in data["tasks"]
                   if t["to"] == a["id"] and not t.get("evidence_path"))
        advice = ("升级职责/调教" if todo else "保持；可考虑沉淀技能")
        if a["schedule"] not in ("on-demand",) and not a["schedule"].startswith(("cron:", "event:")):
            advice = "定时配置不合法，需修正"
        lines.append(f"| {a['name']} | {a['class']} | {a['schedule']} | {n} | {todo} | {advice} |")
    lines += ["", "## 本次迭代结论（人定，刘邦只定方向）", "> 【待填】", "",
              "## 要不要调整班子", "> 例如：某岗长期 0 任务 → 合并；某岗积压 → 招专项临时实例；职责过期 → 升 version", ""]
    p = root / "reviews" / f"{datetime.now().strftime('%Y%m%d-%H%M')}.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    data["reviews"].append({"at": now(), "path": str(p.relative_to(root))})
    save(root, data)
    print(f"查岗表：{p}")
    print("  " + "；".join(f"{a['name']} 承接 {counts.get(a['id'],0)} 项" for a in data["agents"]))
    return 0


def verify_team(root: Path):
    """硬闸门。返回 (ok, problems)。供 verify_team.py 与 pstack verify 共用。"""
    problems = []
    mf = root / "manifest.json"
    if not mf.is_file():
        return False, [f"未组建团队：缺 {mf}"]
    data = json.loads(mf.read_text(encoding="utf-8"))
    agents = data.get("agents", [])

    n = len(agents)
    if n < MIN_AGENTS:
        problems.append(f"常设岗不足：{n} < {MIN_AGENTS}（三才齐备才成班子）")
    if n > MAX_AGENTS:
        problems.append(f"常设岗超编：{n} > {MAX_AGENTS}（AI 不在多在精，别搞半吊子杂牌军）")

    present = {a.get("class") for a in agents}
    for c in CLASSES:
        if c not in present:
            problems.append(f"三才缺位：{c}")

    for a in agents:
        for f in REQUIRED_AGENT_FIELDS:
            if not a.get(f):
                problems.append(f"岗位 {a.get('id','?')} 职责契约缺字段 {f}")
        if not (root / "agents" / a.get("id", "") / "outbox").is_dir():
            problems.append(f"岗位 {a.get('id','?')} 缺独立 outbox（身份隔离）")
        sched = a.get("schedule", "")
        if not (sched == "on-demand" or sched.startswith(("cron:", "event:"))):
            problems.append(f"岗位 {a.get('id','?')} 定时配置不合法：{sched!r}")

    ob = root / "ONBOARDING.md"
    if not ob.is_file():
        problems.append("缺 ONBOARDING.md（先自报家门再谈搭手）")
    elif "【待填】" in ob.read_text(encoding="utf-8"):
        problems.append("入职契约未完成：ONBOARDING.md 仍有【待填】（未让 AI 复述确认）")

    for t in data.get("tasks", []):
        if not t.get("acceptance"):
            problems.append(f"任务 {t.get('id')} 缺验收标准")
        if t.get("status") == "done" and not t.get("evidence_path"):
            problems.append(f"任务 {t.get('id')} 标记完成但无证据路径（违反心法05）")

    return (len(problems) == 0), problems


def cmd_verify(args):
    root = root_of(args)
    ok, problems = verify_team(root)
    print(f"帝王团队硬闸门：{root}")
    if ok:
        print("  [OK] 常设岗 3-5、三才齐备、职责契约完整、身份隔离、定时合法")
        print("  [OK] 入职契约已确认、任务有验收标准")
        print("→ 通过：可派工 / 可交付。")
        return 0
    for p in problems:
        print(f"  [NG] {p}")
    print(f"→ 未通过（{len(problems)} 项）：先补齐再派工。")
    return 1


def cmd_status(args):
    root = root_of(args)
    data = load(root)
    if data is None:
        return 1
    print(f"{data['team']} · v{data['version']} · {root}")
    print(f"  刘邦：{data['boss']['role']}（只定方向搭班子）")
    print(f"  常设岗 {len(data['agents'])}/{MAX_AGENTS}：" +
          "、".join(f"{a['name']}[{a['class'].split('/')[0]}]" for a in data["agents"]))
    print(f"  任务 {len(data['tasks'])} · 技能 {len(data['skills'])} · "
          f"流转 {len(data['handoffs'])} · 查岗 {len(data['reviews'])}")
    ok, probs = verify_team(root)
    print(f"  硬闸门：{'通过' if ok else '未通过(' + str(len(probs)) + '项)'}")
    return 0


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dir", default=argparse.SUPPRESS,
                        help="团队根目录（默认 ./agent-team，可置于子命令前后）")
    ap = argparse.ArgumentParser(description="pstack · 帝王团队编排引擎",
                                 parents=[common])
    sub = ap.add_subparsers(dest="cmd", required=True, parser_class=argparse.ArgumentParser)

    p = sub.add_parser("init", help="组建班子", parents=[common])
    p.add_argument("--team", default="帝王团队")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("hire", help="AI 人事：捏职责清晰的员工（3-5 上限）", parents=[common])
    for f in ("id", "name", "duty", "scenario", "schedule", "inputs", "outputs", "acceptance"):
        p.add_argument(f"--{f}", required=True)
    p.add_argument("--class", dest="class_", required=True, help=" / ".join(CLASSES))
    p.add_argument("--reports-to", default="boss")
    p.add_argument("--may-hire", default="")
    p.set_defaults(func=cmd_hire)

    p = sub.add_parser("onboard", help="自报家门 + 怎么搭手 + 复述确认", parents=[common])
    p.set_defaults(func=cmd_onboard)

    p = sub.add_parser("dispatch", help="刘邦派工", parents=[common])
    p.add_argument("--to", required=True)
    p.add_argument("--task", required=True)
    p.add_argument("--acceptance", required=True)
    p.set_defaults(func=cmd_dispatch)

    p = sub.add_parser("handoff", help="自动流转：杜绝人工传话", parents=[common])
    p.add_argument("--from", dest="src", required=True)
    p.add_argument("--to", dest="dst", required=True)
    p.add_argument("--file")
    p.set_defaults(func=cmd_handoff)

    p = sub.add_parser("capture", help="干成事儿立刻存成技能", parents=[common])
    p.add_argument("--name", required=True)
    p.add_argument("--from-task", required=True)
    p.add_argument("--method", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_capture)

    p = sub.add_parser("reuse", help="用这个技能干 XX", parents=[common])
    p.add_argument("--name", required=True)
    p.add_argument("--task", required=True)
    p.set_defaults(func=cmd_reuse)

    p = sub.add_parser("review", help="定期查岗迭代", parents=[common])
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("verify", help="硬闸门（退出码 1 阻断）", parents=[common])
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("status", help="团队概览", parents=[common])
    p.set_defaults(func=cmd_status)
    return ap


if __name__ == "__main__":
    args = build_parser().parse_args()
    raise SystemExit(args.func(args))
