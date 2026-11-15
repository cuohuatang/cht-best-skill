#!/usr/bin/env python3
"""V0.0.7 决策关：元层回看 + 三阶段裁决 + 反转条件监控

两条高含金量提示词的合并落点。**默认不启用**，只在高利害分叉点触发：
  - scan   跨目录扫 agent-tasks/*/ 的决策记录与 [假设]，给 S0 元层回看供素材
  - init   幂等追加决策关区块到 progress.md（模板本身不内置 → 未触发零负担）
  - verify 校验五段完整、S1 禁支持性措辞、S3 禁和稀泥且须给明确倾向、R 须有可观测反转条件

用法:
    python3 decision.py scan   <agent-tasks 的父目录>        # 默认当前目录
    python3 decision.py init   <任务目录>
    python3 decision.py verify <任务目录> [--required]

退出码:
    0 = 通过 / 未启用（属预期） / 扫描完成
    1 = 未通过（阻断决策定稿） / 显式要求但未启用
    2 = 用法或路径错误
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

START, END = "DECISION_BLOCK_START", "DECISION_BLOCK_END"
PLACEHOLDER = "【待填】"
SKILL_ROOT = Path(__file__).resolve().parent.parent
BLOCK_TPL = SKILL_ROOT / "assets" / "templates" / "decision-block.md"
SECTIONS = ("S0", "S1", "S2", "S3", "R")

S1_FIELDS = ("遗漏的事实", "过度乐观假设", "不可逆成本", "机会成本", "最坏风险", "情绪带来的认知偏差")
# 反方位禁止出现的支持性措辞（只查条目值，不查字段名）
S1_BANNED = ("建议采纳", "值得推进", "应该做", "利大于弊", "总体可行", "我支持",
             "赞成这个决定", "推荐执行", "不妨做", "确实更好", "可以放心",
             "完全合理", "没有明显问题", "支持该决定")
# 裁判位禁止的和稀泥措辞
S3_BANNED = ("五五开", "各有道理", "难分伯仲", "不分伯仲", "见仁见智", "难分高下",
             "势均力敌", "无法判断哪边", "两边都差不多", "持平", "不分上下", "视情况而定")
# 「哪边证据占优」必须给出明确倾向
S3_STANCE = ("反方", "支持", "需补证据", "暂缓")
# 反转条件必须可观测，不能写不可核验的模糊话
R_BANNED = ("视情况而定", "风险变大时", "看情况", "酌情", "必要时", "适当时候")

try:  # 复用 V0.0.6 双闸门的通用解析，单独拷走时也有兜底
    from gates import valid, field_value, bullets, split_sections, section, extract_block
except ImportError:
    def valid(v):
        v = (v or "").strip()
        return bool(v) and PLACEHOLDER not in v and len(v) >= 2

    def field_value(line):
        parts = re.split(r"[：:]", line.strip(), 1)
        return parts[1].strip() if len(parts) > 1 else ""

    def bullets(body):
        return [ln.strip()[2:].strip() for ln in body if ln.strip().startswith("- ")]

    def split_sections(block):
        parts = re.split(r"^###\s+", block, flags=re.M)
        return {p.splitlines()[0].strip(): p.splitlines()[1:]
                for p in parts[1:] if p.splitlines()}

    def section(secs, prefix):
        for head, body in secs.items():
            if head.startswith(prefix):
                return body
        return None

    def extract_block(text, start, end):
        if start not in text or end not in text:
            return False, ""
        return True, text.split(start, 1)[1].split(end, 1)[0]


def resolve_task(raw: Path):
    """任务目录 → 含 progress.md 的目录；传父目录时下探唯一的 agent-tasks/ 子目录。"""
    raw = raw.expanduser()
    if raw.is_dir() and (raw / "progress.md").is_file():
        return raw
    base = raw / "agent-tasks"
    if base.is_dir():
        cands = sorted(p for p in base.iterdir() if p.is_dir() and (p / "progress.md").is_file())
        if len(cands) == 1:
            return cands[0]
        if len(cands) > 1:
            print(f"[x] {base} 下有 {len(cands)} 个任务目录，决策关是高利害操作，请明确指定其一：")
            for c in cands:
                print(f"    {c}")
            return None
    return None


# ---------------------------------------------------------------- scan
def scan(base: Path) -> int:
    root = base if (base.name == "agent-tasks" and base.is_dir()) else base / "agent-tasks"
    if not root.is_dir():
        print(f"[x] 找不到任务根目录：{root}")
        print("    用法：python3 decision.py scan <agent-tasks 的父目录>")
        return 2
    dirs = sorted(p for p in root.iterdir() if p.is_dir())
    rejected, hypotheses, slugs = Counter(), Counter(), Counter()
    decisions = []

    for d in dirs:
        slugs[re.sub(r"^\d{8}-\d{4}-", "", d.name)] += 1
        prog = d / "progress.md"
        if prog.is_file():
            for ln in prog.read_text(encoding="utf-8").splitlines():
                s = ln.strip()
                if not (s.startswith("|") and s.count("|") >= 5):
                    continue
                cells = [c.strip() for c in s.strip("|").split("|")]
                if len(cells) < 4 or not cells[0] or cells[0] == "时间":
                    continue
                if set(cells[0]) <= set("-: "):  # 分隔行 |---|---|
                    continue
                decisions.append((d.name, cells))
                if cells[3] and cells[3] not in ("-", "—", ""):
                    rejected[cells[3]] += 1
        find = d / "findings.md"
        if find.is_file():
            for ln in find.read_text(encoding="utf-8").splitlines():
                s = ln.strip()
                if "[假设]" not in s:
                    continue
                # 模板里的规则说明行（如「推测必须标 [假设]」）不是事实假设，排除
                if s.startswith(">") or any(w in s for w in
                                            ("【待填】", "示例", "例如", "规则", "必须标", "说明")):
                    continue
                hypotheses[s.lstrip("- ").strip()] += 1

    print(f"元层回看扫描：{root}")
    print(f"  任务目录 {len(dirs)} 个 · 决策记录 {len(decisions)} 条 · [假设] {sum(hypotheses.values())} 条")
    signals = 0

    print("\n[反复被否掉]（跨目录出现 ≥2 次）")
    hits = [(k, v) for k, v in rejected.most_common() if v >= 2]
    for k, v in hits:
        signals += 1
        print(f"  - {k[:70]}  ×{v}")
    if not hits:
        print("  （无）")

    print("\n[反复出现的假设]（跨目录出现 ≥2 次）")
    hits = [(k, v) for k, v in hypotheses.most_common() if v >= 2 and len(k) > 4]
    for k, v in hits:
        signals += 1
        print(f"  - {k[:70]}  ×{v}")
    if not hits:
        print("  （无）")

    print("\n[疑似返工]（同名任务 ≥2 次）")
    hits = [(k, v) for k, v in slugs.most_common() if v >= 2]
    for k, v in hits:
        signals += 1
        print(f"  - {k}  ×{v}")
    if not hits:
        print("  （无）")

    if decisions:
        print("\n[落盘决策记录]（S0 的原始素材）")
        for name, cells in decisions[-12:]:
            print(f"  - {name}: {cells[1][:36]} ｜否掉：{cells[3][:36]}")

    print("\n→ " + ("发现反复模式，请把最像「一直绕着走、没问出口」的那条写进 S0。" if signals
                    else "未发现明显反复模式；S0 可如实判定「当前问题即真问题」，不要硬编一个深刻问题（心法 03）。"))
    return 0


# ---------------------------------------------------------------- init
def init(task_dir: Path) -> int:
    prog = task_dir / "progress.md"
    if not prog.is_file():
        print(f"[x] 找不到 progress.md：{task_dir}")
        return 2
    if not BLOCK_TPL.is_file():
        print(f"[x] 决策关区块模板缺失：{BLOCK_TPL}")
        return 2
    t = prog.read_text(encoding="utf-8")
    if START in t:
        print(f"决策关区块已存在，未改动任何内容：{task_dir}")
        return 0
    prog.write_text(t.rstrip() + "\n\n" + BLOCK_TPL.read_text(encoding="utf-8").rstrip() + "\n",
                    encoding="utf-8")
    print(f"决策关已启用（追加区块，未覆盖原内容）：{task_dir}")
    print("  按 assets/prompts/decision.md 填 S0 → S1 → S2 → S3 → R")
    print(f"  校验：python3 {Path(__file__).resolve()} verify \"{task_dir}\" --required")
    return 0


# ---------------------------------------------------------------- verify
def check(progress: Path, required: bool):
    """返回 (ok, results, enabled)。"""
    t = progress.read_text(encoding="utf-8")
    if START not in t or END not in t:
        if required:
            return False, [("启用", False, "已声明高利害决策，但未跑 decision.py init 追加决策关区块")], False
        return True, [("启用", True, "未启用决策关（按触发条件，属预期）→ 放行")], False
    found, block = extract_block(t, START, END)
    if not found:
        return False, [("结构", False, "区块标记损坏（START/END 不完整）")], True

    secs = split_sections(block)
    results, bodies = [], {}
    for key in SECTIONS:
        body = section(secs, key)
        bodies[key] = body
        results.append((f"{key} 段", body is not None, "已存在" if body is not None else "缺该段"))
    if any(b is None for b in bodies.values()):
        return False, results, True

    # S0 元层回看：4 条全填实
    s0 = bullets(bodies["S0"])
    s0v = [field_value(x) for x in s0]
    results.append(("S0 元层回看", len(s0v) >= 4 and all(valid(v) for v in s0v),
                    f"{sum(valid(v) for v in s0v)}/{len(s0v)} 条有效（需 4 条：信号 / 真问题 / 继续·重构·终止 / 回写位置）"))

    # S1 反方位：6 项齐全 + 全填实 + 禁支持性措辞
    s1 = bullets(bodies["S1"])
    s1v = [field_value(x) for x in s1]
    labels = [x.split("：", 1)[0] for x in s1]
    missing = [f for f in S1_FIELDS if not any(f in lb for lb in labels)]
    supporting = [w for v in s1v for w in S1_BANNED if w in v]
    ok_s1 = (not missing and len(s1v) >= 6 and all(valid(v) for v in s1v) and not supporting)
    note = f"{sum(valid(v) for v in s1v)}/{len(s1v)} 条有效"
    if missing:
        note += f" · 缺项：{missing}"
    if supporting:
        note += f" · 反方位出现支持性措辞：{supporting}"
    results.append(("S1 反方位（禁支持）", ok_s1, note))

    # S2 支持位：≥1 条
    s2v = [field_value(x) for x in bullets(bodies["S2"])]
    results.append(("S2 支持位", len(s2v) >= 1 and all(valid(v) for v in s2v),
                    f"{sum(valid(v) for v in s2v)}/{len(s2v)} 条有效（≥1）"))

    # S3 裁判位：3 条 + 明确倾向 + 禁和稀泥
    s3 = bullets(bodies["S3"])
    s3v = [field_value(x) for x in s3]
    mush = [w for v in s3v for w in S3_BANNED if w in v]
    stance_val = s3v[0] if s3v else ""
    has_stance = any(w in stance_val for w in S3_STANCE)
    ok_s3 = (len(s3v) >= 3 and all(valid(v) for v in s3v) and has_stance and not mush)
    note = f"{sum(valid(v) for v in s3v)}/{len(s3v)} 条有效"
    if not has_stance:
        note += " · 「哪边证据占优」未给明确倾向（反方/支持/需补证据/暂缓）"
    if mush:
        note += f" · 和稀泥措辞：{mush}"
    results.append(("S3 裁判位（拒绝五五开）", ok_s3, note))

    # R 反转条件：≥1 条可观测结构 + 监控方式
    r = bullets(bodies["R"])
    rev = [x for x in r if "出现时" in x and "反转为" in x]
    mon = [x for x in r if "监控方式" in x]
    vague = [w for x in r for w in R_BANNED if w in x]
    ok_r = (len(rev) >= 1 and all(valid(field_value(x)) for x in rev)
            and len(mon) >= 1 and all(valid(field_value(x)) for x in mon) and not vague)
    note = f"反转条件 {len(rev)} 条（须「当X出现时→反转为Y」）· 监控方式 {len(mon)} 条"
    if vague:
        note += f" · 不可观测措辞：{vague}"
    results.append(("R 反转条件与监控", ok_r, note))

    # 全局占位符残留
    leftover = block.count(PLACEHOLDER)
    results.append(("占位符残留", leftover == 0,
                    f"区块内残留 {leftover} 处 {PLACEHOLDER}" if leftover else "无残留"))

    return all(r[1] for r in results), results, True


def main() -> int:
    ap = argparse.ArgumentParser(description="V0.0.7 决策关：元层回看 + 三阶段裁决 + 反转条件")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_scan = sub.add_parser("scan", help="跨目录扫描，给 S0 供素材")
    p_scan.add_argument("path", nargs="?", default=".", help="agent-tasks 的父目录")
    p_init = sub.add_parser("init", help="幂等追加决策关区块")
    p_init.add_argument("path", help="任务目录")
    p_verify = sub.add_parser("verify", help="校验决策关")
    p_verify.add_argument("path", help="任务目录")
    p_verify.add_argument("--required", action="store_true",
                          help="显式声明本次为高利害决策：未启用区块也返回 1")
    args = ap.parse_args()

    if args.cmd == "scan":
        return scan(Path(args.path).expanduser().resolve())

    task = resolve_task(Path(args.path))
    if task is None:
        print(f"[x] 找不到任务目录或 progress.md：{args.path}")
        return 2

    if args.cmd == "init":
        return init(task)

    ok, results, enabled = check(task / "progress.md", args.required)
    print(f"决策关校验：{task}")
    for name, passed, note in results:
        print(f"  {'[OK]' if passed else '[NG]'} {name}：{note}")
    if not enabled:
        if ok:
            print("→ 未启用决策关（默认关闭，按触发条件启用才需要本关）→ 放行。")
        else:
            print("→ 未通过：已声明高利害决策（--required），但未跑 decision.py init 启用决策关（阻断）。")
        return 0 if ok else 1
    print("→ 通过：真问题已回看、正反裁决与反转条件齐全，决策可定稿（拍板权仍在人）。" if ok else
          "→ 未通过：补齐五段后再定稿；AI 只给证据优势判断，不替人拍板（阻断）。")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
