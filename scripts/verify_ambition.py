#!/usr/bin/env python3
"""野心升级校验闸门（V0.0.4）

判定 task_plan.md 的「0. 野心升级」三维度（高度/深度/广度）是否已填写完整。
设计目的：把"有野心地定目标"从口号变成每次任务都绕不过去的硬检查。

用法:
    python3 verify_ambition.py <任务目录 | task_plan.md 路径>
    python3 verify_ambition.py agent-tasks/20261106-0210-改写Q4文案

退出码:
    0 = 通过（三维度全部填写，可开工 / 可交付）
    1 = 未通过（三维度有空白或占位符，阻断）
    2 = 用法错误或找不到文件

判定规则（严格）:
    - 必须存在 AMBITION_BLOCK_START / AMBITION_BLOCK_END 标记
    - 三个维度标题必须齐全
    - 每个维度的字段行数不少于模板定义（高度2 / 深度3 / 广度2）
    - 每条字段内容不得为空、不得残留【待填】占位符、不得少于 2 个字符
"""
import re
import sys
from pathlib import Path

START = "AMBITION_BLOCK_START"
END = "AMBITION_BLOCK_END"
PLACEHOLDER = "【待填】"
# 维度名 -> 该维度最少必须填写的字段条数
REQUIRED = {"高度": 2, "深度": 3, "广度": 2}


def check_plan(path: Path):
    """返回 (ok: bool, results: list[(维度, 通过, 说明)])"""
    results = []
    if not path.is_file():
        return False, [("文件", False, f"找不到文件：{path}")]

    text = path.read_text(encoding="utf-8")

    if START not in text or END not in text:
        return False, [("结构", False, "缺少「0. 野心升级」区块标记，模板版本过旧或区块被删除")]

    block = text.split(START, 1)[1].split(END, 1)[0]

    # 按 ### 维度标题切分
    sections = re.split(r"^###\s+", block, flags=re.M)
    dim_blocks = {}
    for sec in sections[1:]:
        head = sec.splitlines()[0].strip()
        for dim in REQUIRED:
            if head.startswith(dim):
                dim_blocks[dim] = sec

    for dim, minimum in REQUIRED.items():
        if dim not in dim_blocks:
            results.append((dim, False, "缺该维度章节"))
            continue
        lines = [ln for ln in dim_blocks[dim].splitlines()[1:]
                 if ln.strip().startswith("- ")]
        fields = []
        for ln in lines:
            # 取冒号后的内容
            body = re.split(r"[：:]", ln.strip().lstrip("- ").strip(), 1)
            val = body[1].strip() if len(body) > 1 else ""
            fields.append(val)

        filled = [v for v in fields
                  if v and PLACEHOLDER not in v and len(v.strip()) >= 2]
        if len(lines) < minimum:
            results.append((dim, False, f"字段不足：需要 ≥{minimum} 条，实际 {len(lines)} 条"))
        elif len(filled) < minimum:
            blank = len(lines) - len(filled)
            results.append((dim, False, f"有 {blank} 条未填写或仍为【待填】占位符"))
        else:
            results.append((dim, True, f"{len(filled)} 条已填写"))

    ok = all(r[1] for r in results)
    return ok, results


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: python3 verify_ambition.py <任务目录 | task_plan.md 路径>")
        return 2

    raw = Path(sys.argv[1]).expanduser()
    path = raw / "task_plan.md" if raw.is_dir() else raw
    if not path.is_file():
        print(f"[x] 找不到 task_plan.md：{path}")
        return 2

    ok, results = check_plan(path)
    print(f"野心升级校验：{path}")
    for dim, passed, note in results:
        print(f"  {'[OK]' if passed else '[NG]'} {dim}：{note}")
    if ok:
        print("→ 通过：三维度齐全，可进入阶段 1 / 可交付。")
        return 0
    print("→ 未通过：请补全【待填】项后再开工或交付（本检查用于阻断浅层执行）。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
