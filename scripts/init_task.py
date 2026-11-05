#!/usr/bin/env python3
"""生成三文件记忆骨架：task_plan.md / findings.md / progress.md

用法:
    python3 init_task.py "改写Q4产品文案"            # 在当前目录建 agent-tasks/<日期>-<任务名>/
    python3 init_task.py "改写Q4产品文案" --dir ~/work/proj
    python3 init_task.py "改写Q4产品文案" --root memory --force
"""
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "assets" / "templates"
FILES = ["task_plan.md", "findings.md", "progress.md"]


def slugify(name: str) -> str:
    s = re.sub(r'[\\/:*?"<>|\s]+', "-", name.strip())
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return (s[:60] or "task")


def main() -> int:
    ap = argparse.ArgumentParser(description="生成三文件记忆骨架")
    ap.add_argument("task", help="任务名，用作目录名")
    ap.add_argument("--dir", default=".", help="父目录，默认当前目录")
    ap.add_argument("--root", default="agent-tasks", help="任务根目录名，默认 agent-tasks")
    ap.add_argument("--force", action="store_true", help="目录已存在时覆盖文件")
    args = ap.parse_args()

    if not TEMPLATES.is_dir():
        print(f"[x] 模板目录缺失: {TEMPLATES}", file=sys.stderr)
        return 1

    now = datetime.now()
    stamp = now.strftime("%Y%m%d-%H%M")
    task_dir = Path(args.dir).expanduser().resolve() / args.root / f"{stamp}-{slugify(args.task)}"
    task_dir.mkdir(parents=True, exist_ok=True)

    created, skipped = [], []
    for fname in FILES:
        tpl = TEMPLATES / fname
        if not tpl.is_file():
            print(f"[x] 模板缺失: {tpl}", file=sys.stderr)
            return 1
        out = task_dir / fname
        if out.exists() and not args.force:
            skipped.append(fname)
            continue
        text = tpl.read_text(encoding="utf-8")
        text = (text.replace("{{TASK}}", args.task)
                    .replace("{{DATE}}", now.strftime("%Y-%m-%d %H:%M"))
                    .replace("{{DIR}}", str(task_dir)))
        out.write_text(text, encoding="utf-8")
        created.append(fname)

    print(f"任务目录: {task_dir}")
    for f in created:
        print(f"  + {f}")
    for f in skipped:
        print(f"  = {f} 已存在，跳过（--force 可覆盖）")

    # 接活前置：每次生成都把「野心升级」闸门递到手上（刚生成必然待填，故不阻断）
    try:
        from verify_ambition import check_plan
    except ImportError:  # 兼容单独拷走本脚本的场景
        check_plan = None

    plan = task_dir / "task_plan.md"
    verify_cmd = f"python3 {SKILL_ROOT / 'scripts' / 'verify_ambition.py'} \"{task_dir}\""
    if check_plan and plan.is_file():
        ok, results = check_plan(plan)
        if ok:
            print("\n[野心升级] 三维度已填写 ✓")
        else:
            print("\n[接活前置·必做] 野心升级三维度待填（预期状态，未填不得开工）:")
            for dim, passed, note in results:
                print(f"    - {dim}: {note}")
            print("  ① 填 task_plan.md「0. 野心升级」的高度/深度/广度三项")
            print("  ② 校验通过后再填目标与验收标准，进入阶段 1")
            print(f"  ③ 校验命令：{verify_cmd}")
    print("\n下一步：先完成上面的野心升级，再填目标与验收标准，然后开工。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
