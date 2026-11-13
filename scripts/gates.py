#!/usr/bin/env python3
"""V0.0.6 双闸门：入口「反向提问」 + 出口「智囊团排雷」

把两条高阶提示词从"建议"变成每次绕不过去的机器校验：
  - clarify 校验 task_plan.md「0.1 反向提问」四段闭环，未闭环阻断开工
  - council 校验 progress.md「智囊团排雷」5 镜头 + 裁决，缺项阻断交付
  - verify  一次跑完两道（交付总检）
  - seed    给 V0.0.5 及更早的任务目录补齐两个区块，不覆盖已有内容

用法:
    python3 gates.py clarify <任务目录 | task_plan.md 路径>
    python3 gates.py council <任务目录 | progress.md 路径>
    python3 gates.py verify  <任务目录>
    python3 gates.py seed    <任务目录>

退出码:
    0 = 通过          1 = 未通过（阻断）        2 = 用法/路径错误
"""
import argparse
import re
import sys
from pathlib import Path

PLACEHOLDER = "【待填】"
C_START, C_END = "CLARIFY_BLOCK_START", "CLARIFY_BLOCK_END"
K_START, K_END = "COUNCIL_BLOCK_START", "COUNCIL_BLOCK_END"
B_SEP = "｜若不确认会："
TRI_SEP = "｜"
LENSES = ("L1", "L2", "L3", "L4", "L5")
VERDICT = "裁决与修订"
SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "assets" / "templates"


def valid(v: str) -> bool:
    """一条填写是否有效：非空、无占位符、至少 2 个字符。"""
    v = (v or "").strip()
    return bool(v) and PLACEHOLDER not in v and len(v) >= 2


def field_value(line: str) -> str:
    """取『标签：内容』里冒号后的内容。"""
    parts = re.split(r"[：:]", line.strip(), 1)
    return parts[1].strip() if len(parts) > 1 else ""


def bullets(body) -> list:
    return [ln.strip()[2:].strip() for ln in body if ln.strip().startswith("- ")]


def split_sections(block: str) -> dict:
    """按 ### 标题切分区块，返回 {标题: 正文行列表}。"""
    parts = re.split(r"^###\s+", block, flags=re.M)
    out = {}
    for p in parts[1:]:
        lines = p.splitlines()
        if lines:
            out[lines[0].strip()] = lines[1:]
    return out


def section(secs: dict, prefix: str):
    for head, body in secs.items():
        if head.startswith(prefix):
            return body
    return None


def extract_block(text: str, start: str, end: str):
    if start not in text or end not in text:
        return False, ""
    return True, text.split(start, 1)[1].split(end, 1)[0]


def check_clarify(plan: Path):
    """返回 (ok, results[(项, 通过, 说明)]）。"""
    if not plan.is_file():
        return False, [("文件", False, f"找不到：{plan}")]
    found, block = extract_block(plan.read_text(encoding="utf-8"), C_START, C_END)
    if not found:
        return False, [("结构", False, "缺少 CLARIFY 区块标记（模板过旧？跑 gates.py seed 补齐）")]

    secs = split_sections(block)
    results = []
    bodies = {}
    for key in ("A", "B", "C", "D"):
        body = section(secs, key)
        bodies[key] = body
        results.append((f"{key} 段", body is not None, "已存在" if body is not None else "缺该段，必须补齐"))
    if any(b is None for b in bodies.values()):
        return False, results

    # A 自查已解决：≥1 条，且没有残留空/占位条目
    a_items = bullets(bodies["A"])
    a_vals = [field_value(x) for x in a_items]
    ok_a = len(a_vals) >= 1 and all(valid(v) for v in a_vals)
    results.append(("A 自查", ok_a,
                    f"{sum(valid(v) for v in a_vals)}/{len(a_vals)} 条有效（≥1 且无占位符）"))

    # B 高杠杆模糊点：每条必须含分隔符，且两侧都填实
    b_items = bullets(bodies["B"])
    b_ok = len(b_items) >= 1
    for b in b_items:
        if B_SEP not in b:
            b_ok = False
            break
        left, right = b.split(B_SEP, 1)
        if not (valid(field_value(left)) and valid(right)):
            b_ok = False
            break
    results.append(("B 高杠杆模糊点", b_ok,
                    f"{len(b_items)} 条，每条须写『模糊点｜若不确认会：后果』且两侧填实"))

    # C 一次性提问批次：Q1..Qn，编号连续、内容填实
    c_items = bullets(bodies["C"])
    qnums, c_ok = [], len(c_items) >= 1
    for c in c_items:
        m = re.match(r"^Q(\d+)\s*[：:]", c.strip())
        if not m or not valid(field_value(c)):
            c_ok = False
            break
        qnums.append(int(m.group(1)))
    if c_ok:
        c_ok = (len(set(qnums)) == len(qnums) and qnums == list(range(1, len(qnums) + 1)))
    results.append(("C 一次性提问批次", c_ok,
                    f"Q 编号={qnums}（须 Q1 起连续、内容填实）"))

    # D 处置状态：C 的每个编号都要闭环，且所有条目填实
    d_items = bullets(bodies["D"])
    d_map = {}
    d_ok = True
    for d in d_items:
        m = re.match(r"^Q(\d+)\s*→\s*(.*)$", d.strip(), flags=re.S)
        if not m or not valid(m.group(2)):
            d_ok = False
            continue
        d_map[int(m.group(1))] = m.group(2)
    if not qnums or any(q not in d_map for q in qnums):
        d_ok = False
    missing = [q for q in qnums if q not in d_map]
    results.append(("D 处置闭环", d_ok,
                    f"已闭环 {len(d_map)}/{len(qnums)} 条" + (f"，缺 Q{missing}" if missing else "（答复或标 [假设]）")))

    return all(r[1] for r in results), results


def triplet_ok(line: str) -> bool:
    """每条排雷条目须为 问题｜查证动作/证据｜处置 三段，且三段都填实。"""
    parts = re.split(r"｜", line.strip())
    if len(parts) != 3:
        return False
    return all(valid(field_value(p)) for p in parts)


def check_council(progress: Path):
    """返回 (ok, results[(项, 通过, 说明)]）。"""
    if not progress.is_file():
        return False, [("文件", False, f"找不到：{progress}")]
    found, block = extract_block(progress.read_text(encoding="utf-8"), K_START, K_END)
    if not found:
        return False, [("结构", False, "缺少 COUNCIL 区块标记（模板过旧？跑 gates.py seed 补齐）")]

    secs = split_sections(block)
    results = []
    for lens in LENSES:
        body = section(secs, lens)
        if body is None:
            results.append((lens, False, "缺该镜头"))
            continue
        items = bullets(body)
        ok = len(items) >= 1 and all(triplet_ok(x) for x in items)
        results.append((lens, ok, f"{sum(triplet_ok(x) for x in items)}/{len(items)} 条有效（须 问题｜证据动作｜处置 三段填实）"))

    vbody = section(secs, VERDICT)
    if vbody is None:
        results.append((VERDICT, False, "缺「裁决与修订」段"))
    else:
        v_items = bullets(vbody)
        v_ok = len(v_items) >= 1 and all(valid(field_value(x)) for x in v_items)
        results.append((VERDICT, v_ok, f"{sum(valid(field_value(x)) for x in v_items)}/{len(v_items)} 条有效（≥1）"))

    return all(r[1] for r in results), results


def resolve(raw: Path, filename: str):
    """目录 → 文件；支持传父目录时自动下探唯一的 agent-tasks/<任务>/。"""
    raw = raw.expanduser()
    if raw.is_file():
        return raw
    if not raw.is_dir():
        return None
    direct = raw / filename
    if direct.is_file():
        return direct
    base = raw / "agent-tasks"
    if base.is_dir():
        cands = sorted(p / filename for p in base.iterdir() if p.is_dir() and (p / filename).is_file())
        if len(cands) == 1:
            return cands[0]
        if len(cands) > 1:
            print(f"[!] {base} 下有 {len(cands)} 个任务目录，使用最新的 {cands[-1].parent.name}")
            return cands[-1]
    return None


def template_block(tpl: Path, start_heading: str, end_heading: str) -> str:
    text = tpl.read_text(encoding="utf-8")
    s, e = text.find(start_heading), text.find(end_heading)
    if s < 0 or e < 0 or e <= s:
        raise RuntimeError(f"模板锚点异常：{tpl.name} / {start_heading}")
    return text[s:e].rstrip() + "\n"


def seed(task_dir: Path) -> int:
    """给旧任务目录补齐两个区块，绝不覆盖已有内容。"""
    plan, prog = task_dir / "task_plan.md", task_dir / "progress.md"
    if not plan.is_file() or not prog.is_file():
        print(f"[x] 目录内缺 task_plan.md / progress.md：{task_dir}")
        return 2
    added = []
    ptxt = plan.read_text(encoding="utf-8")
    if C_START not in ptxt:
        plan.write_text(ptxt.rstrip() + "\n\n" +
                        template_block(TEMPLATES / "task_plan.md", "## 0.1", "## 1.") + "\n",
                        encoding="utf-8")
        added.append("task_plan.md「0.1 反向提问」")
    ptxt = prog.read_text(encoding="utf-8")
    if K_START not in ptxt:
        prog.write_text(ptxt.rstrip() + "\n\n" +
                        template_block(TEMPLATES / "progress.md", "## 智囊团排雷", "## 下一步") + "\n",
                        encoding="utf-8")
        added.append("progress.md「智囊团排雷」")
    print(f"区块补齐：{task_dir}")
    for a in added:
        print(f"  + {a}")
    if not added:
        print("  = 两个区块已存在，未改动任何内容")
    return 0


def report(title: str, results) -> bool:
    print(title)
    ok = True
    for name, passed, note in results:
        print(f"  {'[OK]' if passed else '[NG]'} {name}：{note}")
        ok = ok and passed
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="V0.0.6 入口/出口双闸门")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("clarify", "council", "verify", "seed"):
        sub.add_parser(name).add_argument("path", nargs="?", default=".", help="任务目录 / 文件路径")
    args = ap.parse_args()

    raw = Path(args.path)
    if args.cmd == "seed":
        if not raw.is_dir():
            print(f"[x] 任务目录不存在：{raw}")
            return 2
        return seed(raw)

    if args.cmd == "clarify":
        p = resolve(raw, "task_plan.md")
        if p is None:
            print(f"[x] 找不到 task_plan.md：{raw}")
            return 2
        ok = report("入口闸门 · 反向提问：" + str(p), check_clarify(p)[1])
        print("→ 通过：模糊点已批量问清并闭环，可开工。" if ok else
              "→ 未通过：先自查、批量问一次、逐条闭环，别脑补着开工（阻断）。")
        return 0 if ok else 1

    if args.cmd == "council":
        p = resolve(raw, "progress.md")
        if p is None:
            print(f"[x] 找不到 progress.md：{raw}")
            return 2
        ok = report("出口闸门 · 智囊团排雷：" + str(p), check_council(p)[1])
        print("→ 通过：5 镜头排雷 + 裁决齐全，可交付。" if ok else
              "→ 未通过：补齐 5 镜头条目与裁决修订，别让带病结论出门（阻断）。")
        return 0 if ok else 1

    # verify：两道一起跑
    pl, pr = resolve(raw, "task_plan.md"), resolve(raw, "progress.md")
    if pl is None or pr is None:
        print(f"[x] 任务目录内缺三文件：{raw}（缺 {('task_plan.md' if pl is None else 'progress.md')}）")
        return 2
    print(f"交付总检 · 双闸门：{raw.resolve()}")
    ok1 = report("  [入口] 反向提问", check_clarify(pl)[1])
    ok2 = report("  [出口] 智囊团排雷", check_council(pr)[1])
    print("→ 通过：入口已澄清、出口已排雷。" if (ok1 and ok2) else
          "→ 未通过：任一闸门未过即阻断交付。")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
