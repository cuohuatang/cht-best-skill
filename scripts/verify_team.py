#!/usr/bin/env python3
"""帝王团队硬闸门（V0.0.5）— 独立 CLI 入口

判定团队是否"真能落实干活"而非空壳：
  常设岗 3-5、三才齐备、职责契约完整、独立 outbox、定时合法、
  入职契约已确认（含 AI 复述）、任务有验收标准与证据路径。

用法:
    python3 verify_team.py <团队目录>      # 默认 ./agent-team
退出码: 0=通过 / 1=未通过（阻断派工与交付） / 2=路径错误
"""
import sys
from pathlib import Path

try:
    from pstack import verify_team as _check
except ImportError:  # 兼容从其他目录调用
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pstack import verify_team as _check


def main() -> int:
    raw = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.cwd()
    if not raw.is_dir():
        print(f"[x] 团队目录不存在：{raw}")
        print("    先跑：python3 pstack.py init")
        return 2
    # 自动探测：传父目录时下探到默认的 agent-team/
    team = raw
    if not (team / "manifest.json").is_file() and (raw / "agent-team" / "manifest.json").is_file():
        team = raw / "agent-team"
    if not (team / "manifest.json").is_file():
        print(f"[x] {team} 未组建团队（缺 manifest.json）")
        print("    先跑：python3 pstack.py init")
        return 2
    ok, problems = _check(team)
    print(f"帝王团队硬闸门：{team}")
    if ok:
        print("  [OK] 3-5 常设岗 · 三才齐备 · 职责契约完整 · 身份隔离 · 定时合法")
        print("  [OK] 入职契约已确认 · 任务验收与证据齐全")
        print("→ 通过：班子可用，可派工 / 可交付。")
        return 0
    for p in problems:
        print(f"  [NG] {p}")
    print(f"→ 未通过（{len(problems)} 项）：先补齐，别急着派活。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
