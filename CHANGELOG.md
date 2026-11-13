# Changelog · cht-best-skill

| 版本 | 日期 | 内容 |
|---|---|---|
| **V0.0.6** | 2026-11-14 | **双闸门层（Ask-first & Council）**：把两条高阶提示词做成入口/出口两道可执行硬闸门，而非第七篇心法。① **反向提问**（入口）：`task_plan.md` 模板内置「0.1 反向提问」四段（A 自查 / B 高杠杆模糊点含"若不确认会" / C 一次性提问批次 Q1…Qn / D 逐条闭环，未答标 `[假设]`）；② **智囊团排雷**（出口）：`progress.md` 模板内置「智囊团排雷」5 镜头（挑错 / 追问本质 / 找反例 / 查证据 / 推落地，每条须「问题 + 证据动作 + 处置」三段）+ 裁决与修订。新增 `scripts/gates.py`（clarify / council / verify / seed，`seed` 可给旧目录补齐区块且不覆盖）、`assets/prompts/reverse-questions.md`、`assets/prompts/council.md`、`references/clarify-council.md`；`init_task.py` 每次生成后同时递出两道闸门的校验命令。两处关键调和：**反向提问 vs 心法 06**（不是多问，是"自查→只问高杠杆→批量一次→问完放手"，反对边做边问）；**5 位顾问 vs 不设角色**（5 个审查镜头＝槽位 ID，不是人设台词，同 V0.0.3/0.0.4/0.0.5 逻辑）。不新增第四个记忆文件，三文件结构不变；消除档/轻量档跳过两道闸门。 |
| **V0.0.5** | 2026-11-08 | **帝王团队层（Emperor Team / 组织层）**：把"AI 当员工养、刘邦式治理"做成**可执行编排引擎**而非文档。`scripts/pstack.py`（init/hire/onboard/dispatch/handoff/capture/reuse/review/verify/status + `manifest.json` 落盘状态机 + 每角色独立 outbox/inbox + 自动流转 + 技能库 + 查岗表）与 `scripts/verify_team.py` 硬闸门（3-5 常设岗、三才齐备、职责契约五字段、身份隔离、定时合法、复述确认、done 必有证据）。新增 `references/emperor-team.md`。原型 Lauren Tan（SpaceX/Grok Bot）七条方法 + 三层架构 + pstack；映射张良(天才/决策)、韩信(地才/执行)、萧何(人才/编排)、刘邦(人/只定方向)。关键调和：**职责契约(接口字段) ≠ 角色人设(形容词)**，与 V0.0.3「不设角色」、V0.0.4「不演专家」不冲突。47 项回归测试全通过。 |
| **V0.0.4** | 2026-11-06 | **野心层（Ambition）**：接活前置的高度/深度/广度三维度。做成硬闸门——`task_plan.md` 模板内置「0. 野心升级」区块（每次 init 必生成）+ `verify_ambition.py` 校验（未填退出码 1，阻断开工与交付）+ 执行循环新增第 0 步。新增 `references/ambition.md`（三个通用模板、五条深挖要点、与黄仁勋"不设角色"的调和）。修正 init 脚本路径旧名 `agent-playbook` → `cht-best-skill`。 |
| **V0.0.3** | 2026-11-06 | **辩论层（Debate）**：黄仁勋 AI 辩论核验法——自查→互驳→裁决，三条即用提示词；`references/debate.md`。 |
| **V0.0.2** | 2026-11-04 | 嫁接入元技能系统三枚镜片：M1 启用三档闸门、M2 IPO 基元链 ≤5、M4 六元操作词典。 |
| **V0.0.1** | 2026-11-03 | 首个版本：10 条协作心法 + task_plan/findings/progress 三文件记忆系统；`init_task.py` 一键生成骨架；格赖斯沟通层同期并入。 |

## 体系层次演进

```
V0.0.1  心法(怎么指挥) + 三文件(怎么记住)
  +格赖斯沟通层(怎么说)
V0.0.2  + M1/M2/M4 元技能镜片(该不该用 / 怎么拆 / 动作语法)
V0.0.3  + 辩论层(怎么验)
V0.0.4  + 野心层(敢要什么) ← 硬闸门
V0.0.5  + 帝王团队层(让一队 AI 真干活) ← 可执行编排引擎，非文档
V0.0.6  + 双闸门层(入口问清 / 出口排雷) ← 两道每次必过的硬闸门
```
