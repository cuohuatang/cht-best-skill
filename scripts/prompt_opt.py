#!/usr/bin/env python3
"""V0.0.8 Step -1：输入分流 + 提示词优化（条件触发，SKIP 默认零负担）

核心不是"把提示词写漂亮"，而是**先判断该不该优化**：
  - classify  纯文本分流（建目录之前就能跑）→ VERDICT=SKIP / OPTIMIZE
  - init      仅 OPTIMIZE 时幂等追加区块到 task_plan.md，逐字留档用户原文
  - verify    九段硬闸门；S 段写成 SKIP 直接阻断（禁止优化的输入被优化了）
  - profiles  只列可验证的平台差异，未知平台一律回退通用档

用法:
    python3 prompt_opt.py classify "<用户原文>" [--force]
    python3 prompt_opt.py init     <任务目录> [--input "<用户原文>"]
    python3 prompt_opt.py verify   <任务目录> [--required]
    python3 prompt_opt.py profiles

退出码:
    classify / profiles  恒 0（查询）
    init / verify        0 = 通过 / 幂等 · 1 = 阻断或拒绝 · 2 = 用法或路径错误
"""
import argparse
import re
import sys
from pathlib import Path

START, END = "PROMPT_OPT_BLOCK_START", "PROMPT_OPT_BLOCK_END"
PLACEHOLDER = "【待填】"
SKILL_ROOT = Path(__file__).resolve().parent.parent
BLOCK_TPL = SKILL_ROOT / "assets" / "templates" / "prompt-opt-block.md"
SECTIONS = ("S.", "A.", "B.", "C.", "D.", "V1.", "V2.", "E.", "F.")

# ------------------------------------------------------------------ 分流规则
GREET_WORDS = (
    "你好", "您好", "hi", "hello", "hey", "谢谢", "多谢", "感谢", "辛苦了", "辛苦",
    "早上好", "下午好", "晚上好", "好的", "收到", "明白", "ok", "okay", "thx",
    "thanks", "拜拜", "再见", "嗯", "哦", "好", "行", "赞", "收到谢谢", "多谢啦",
    "谢谢啦", "谢谢你", "感谢感谢", "辛苦啦",
)
# 纯事实问答 / 翻译 / 摘要（轻量转换，不含产出物）
S2_PATTERNS = (
    r"^什么是", r"^谁是", r"是什么[？?]?$", r"是什么意思[？?]?$", r"^多少[钱个]",
    r"^(翻译|译成|把.{0,30}翻译|把.{0,30}译成|.{0,20}译成|translate|摘要|摘要一下|"
    r"概括一下|总结一下|提炼要点)",
)
# 延续性修改（须同时不含任务动词）
S3_PATTERN = (r"^(继续|接着|然后|再|同上|按上面|按刚才|按上一版|还是|撤回|撤销|重做|"
              r"换成|改成|改为|调大|调小|再短|再长|换个|把第.{1,4}[行段句]|第.{1,4}[行段句])")
# 用户已点名技能或文件（引用已有锚点，不是"要产出 report.md"）
S4_PATTERN = (r"(@skill:|/skill|/commit|cht-best-skill|用.{0,10}技能|按.{0,10}技能|"
              r"用这个技能|这个技能|参考.{0,8}文件|按这个文件|~/|/workspace/|/root/|"
              r"(?:^|\s)@[\w./-]+\.(?:md|py|json|yml|yaml))")
# 只要判断 / 显式禁止优化
S5_PATTERN = (r"(不要优化|别优化|不用优化|禁止优化|无需优化|不要生成提示词|只要判断|"
              r"只给判断|有.{0,10}嫁接点|你怎么看|这个方案如何|合不合适|直接给结论)")
# 任务型动词（用户点名：下任务 / 归纳总结 / 生成 / 安装 / 修复 / 转换 / 推送 / 产出文件…）
TASK_VERBS = (
    "下任务", "归纳总结", "生成", "安装", "修复", "转换", "推送", "产出", "落地", "迭代",
    "嫁接", "打包", "创建", "部署", "重构", "排查", "撰写", "实现", "开发", "制作",
    "整理成", "输出文件", "发布", "上线", "导出", "清洗", "爬取", "写一份", "做一个",
    "造一个", "建个", "搭个", "帮我做", "帮我写", "帮我建", "帮我搭", "帮我改",
    "帮我弄", "改造成", "交付", "完成任务", "优化这段", "做完",
)
# 常见无效指令 / 人设形容词（verify 用）
PERSONA_PATTERNS = tuple(re.compile(p) for p in (
    r"顶级", r"顶尖", r"资深", r"专家", r"大师", r"权威", r"世界级", r"第一流",
    r"扮演", r"化身", r"作为一位", r"作为资深", r"你是.{0,10}(?:专家|顾问|架构师|大师)",
))

PROFILES = (
    ("通用档", "纯文本 + 结构化 Markdown，明确输出契约", "任何依赖特定工具的指令"),
    ("Claude Code / harness", "有文件系统与 shell：可写 @路径、要求落盘并用命令输出自证",
     "「请想象文件内容」"),
    ("ChatGPT", "默认无持久文件系统：单段自包含、可直接粘贴", "「把结果写到 ~/xxx.md」"),
    ("豆包 / DeepSeek / Kimi", "长上下文、工具能力随版本变化：分段输入 + 明确输出契约",
     "假设一定有文件写入或联网能力"),
    ("未列出的平台", "一律回退通用档", "编造「该平台支持 XX 插件 / 数据源」"),
)

try:  # 复用 V0.0.6 双闸门的通用解析；单独拷走本脚本时也有兜底
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


def has_task(text: str) -> bool:
    return any(v in text for v in TASK_VERBS)


def classify_text(raw: str, force: bool = False):
    """返回 (verdict, rule, reason, hints)。判定顺序即用户给的优先级。"""
    text = (raw or "").strip()
    if force:
        return "OPTIMIZE", "显式强制", "用户写了「优化这段」或 --force", []
    if not text:
        return "SKIP", "空输入", "没有内容可优化", []

    hits = []
    cleaned = re.sub(r"[\s，,。.!！~、:：;；?？\[\]【】()（）\U0001F300-\U0001FAFF]", "", text).lower()
    task = has_task(text)

    # S1 寒暄致谢：整体是客套，或短句以客套开头且不含任务动词
    if cleaned in GREET_WORDS or (
        len(cleaned) <= 10 and not task and any(cleaned.startswith(g) for g in GREET_WORDS)
    ):
        return "SKIP", "S1 寒暄致谢", "纯客套，不含任务动词；优化只会得到更长的废话", hits

    # S3a 承接上文的方案编号短指令（「落地A」「选 B」「用方案 2」）——上文已有全部约束
    if re.fullmatch(r"(?:落地|选择|选|用方案|采用|就按)?\s*[A-Da-d1-4１-４]\s*[\s。.!！~、]*", text):
        return "SKIP", "S3 延续性修改", "承接上文的方案编号短指令，重新生成会丢失已定稿上下文", hits

    # S2 纯事实问答 / 翻译 / 摘要
    for pat in S2_PATTERNS:
        if re.search(pat, text) and not task:
            return "SKIP", "S2 纯事实问答 / 翻译 / 摘要", "轻量转换，没有隐性需求可补", hits

    # S4 用户已点名技能或文件（绝对 SKIP：执行路径已定死）
    m = re.search(S4_PATTERN, text)
    if m:
        return "SKIP", "S4 已点名技能或文件", f"命中锚点「{m.group(0)[:24]}」，直接按用户指定路径执行", hits

    # S5 只要判断 / 显式禁止优化
    m = re.search(S5_PATTERN, text)
    if m:
        return "SKIP", "S5 只要判断不要优化", f"命中「{m.group(0)[:20]}」，用户要的是结论不是提示词", hits

    # S3 延续性修改（仅在无任务动词时 SKIP）
    if re.search(S3_PATTERN, text) and not task:
        return "SKIP", "S3 延续性修改", "上文已有全部约束，重新生成会丢失上下文、推翻已定稿内容", hits

    # T 任务型
    if task:
        found = [v for v in TASK_VERBS if v in text]
        hits = found[:4]
        return "OPTIMIZE", "T 任务型", "命中任务动词：" + " / ".join(hits), hits

    return "SKIP", "默认 SKIP", "未命中任务型动词或判定模糊 → 宁可不优化（M1 消除档 / 心法 06）", hits


# ------------------------------------------------------------------ classify
def cmd_classify(text: str, force: bool) -> int:
    verdict, rule, reason, hits = classify_text(text, force)
    shown = text.strip().replace("\n", " / ")
    if len(shown) > 100:
        shown = shown[:100] + "…"
    print(f"输入：{shown}")
    print(f"VERDICT={verdict}")
    print(f"结论：{verdict} —— 命中「{rule}」")
    print(f"规则：{reason}")
    if verdict == "SKIP":
        print("动作：原样透传，一个字不改；不生成任何版本、不落任何文件、")
        print("      不加「我帮你优化了一下」。到此为止，直接按原输入执行/回应。")
    else:
        print("动作：① init_task.py 建目录 → ② prompt_opt.py init <目录> --input \"<原文>\"")
        print("      ③ 填 S/A/B/C/D/V1/V2/E/F → ④ verify --required")
        print("提示：补齐项逐条标 [假设]；职责契约禁人设形容词；高阶版接野心层高度/深度/广度。")
    return 0


# ------------------------------------------------------------------ profiles
def cmd_profiles() -> int:
    print("平台适配档位（只列可验证差异；未知一律回退通用档，不编造适配规则）\n")
    print(f"{'档位':<28}{'可写进提示词':<58}{'不能写'}")
    print("-" * 120)
    for name, can, cannot in PROFILES:
        print(f"{name:<28}{can:<58}{cannot}")
    print("\n共同规避：自相矛盾的双重约束 · 无法验证的动作 · 与「不凑字数」冲突的「尽可能详细」")
    print("          · 抬高讨好属性的人设 · 凭空指定的插件或数据源")
    return 0


# ------------------------------------------------------------------ 路径解析
def resolve_task(raw: Path):
    """任务目录 → 含 task_plan.md 的目录；传父目录时下探唯一的 agent-tasks/ 子目录。"""
    raw = raw.expanduser()
    if raw.is_dir() and (raw / "task_plan.md").is_file():
        return raw
    base = raw / "agent-tasks"
    if base.is_dir():
        cands = sorted(p for p in base.iterdir() if p.is_dir() and (p / "task_plan.md").is_file())
        if len(cands) == 1:
            return cands[0]
        if len(cands) > 1:
            print(f"[x] {base} 下有 {len(cands)} 个任务目录，请明确指定其一：")
            for c in cands:
                print(f"    {c}")
            return None
    return None


# ------------------------------------------------------------------ init
def cmd_init(task_dir: Path, raw_input: str, force: bool) -> int:
    plan = task_dir / "task_plan.md"
    if not plan.is_file():
        print(f"[x] 找不到 task_plan.md：{task_dir}")
        return 2
    if not BLOCK_TPL.is_file():
        print(f"[x] 优化区块模板缺失：{BLOCK_TPL}")
        return 2

    if raw_input:
        verdict, rule, _, _ = classify_text(raw_input, force)
        if verdict == "SKIP":
            print(f"[x] 拒绝创建优化区块：该输入判为 SKIP（{rule}）")
            print("    禁止优化的输入必须原样透传，不得改写、不得生成版本、不得落文件。")
            print("    → 未改动任何文件。若确需强制，请让用户显式说「优化这段」或加 --force。")
            return 1

    text = plan.read_text(encoding="utf-8")
    if START in text:
        print(f"提示词优化区块已存在，未改动任何内容：{task_dir}")
        return 0

    block = BLOCK_TPL.read_text(encoding="utf-8").rstrip()
    if raw_input:
        one_line = raw_input.strip().replace("\n", " / ")
        block = block.replace("- 输入原文：【待填】", f"- 输入原文：{one_line}")
        _, rule, _, _ = classify_text(raw_input, force)
        block = block.replace("｜命中规则：【待填】", f"｜命中规则：{rule}")

    plan.write_text(text.rstrip() + "\n\n" + block + "\n", encoding="utf-8")
    print(f"提示词优化已启用（追加「00」区块，未覆盖原内容）：{task_dir}")
    if raw_input:
        print("  用户原文已逐字留档；自动补齐项请逐条标 [假设]。")
    else:
        print("  未提供 --input，请手动补「S. 输入原文」并确认分类为 OPTIMIZE。")
    print(f"  校验：python3 {Path(__file__).resolve()} verify \"{task_dir}\" --required")
    return 0


# ------------------------------------------------------------------ verify
def check(plan: Path, required: bool):
    """返回 (ok, results, enabled)。"""
    t = plan.read_text(encoding="utf-8")
    if START not in t or END not in t:
        if required:
            return False, [("启用", False, "已声明本次需要优化，但未跑 prompt_opt.py init 追加「00」区块")], False
        return True, [("启用", True, "未启用提示词优化（SKIP / 未触发，属预期）→ 放行")], False
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

    # S：原文逐字留档 + 分类必须 OPTIMIZE（禁止优化的输入被优化 → 硬阻断）
    s = bullets(bodies["S."])
    sv = [field_value(x) for x in s]
    cls_line = next((x for x in s if x.startswith("分类")), "")
    cls_val = field_value(cls_line) if cls_line else ""
    bad_cls = ("SKIP" in cls_val.upper()) or not cls_val.upper().startswith("OPTIMIZE")
    ok_s = (len(sv) >= 3 and all(valid(v) for v in sv) and not bad_cls)
    note = f"{sum(valid(v) for v in sv)}/{len(sv)} 条有效（原文 / 分类 / 留档声明）"
    if bad_cls:
        note += " · 分类不是 OPTIMIZE：SKIP 类输入禁止优化"
    results.append(("S 分流结论与原文留档", ok_s, note))

    # A：隐性需求逐条标 [假设]
    a = bullets(bodies["A."])
    av = [field_value(x) for x in a]
    ok_a = len(a) >= 3 and all("[假设]" in x for x in a) and all(valid(v) for v in av)
    results.append(("A 隐性需求逐条标 [假设]", ok_a,
                    f"{len(a)} 条 · 带标记 {sum('[假设]' in x for x in a)} 条 · 有效值 {sum(valid(v) for v in av)} 条（需 ≥3）"))

    # B：职责契约，禁人设形容词
    b = bullets(bodies["B."])
    bv = [field_value(x) for x in b]
    persona = sorted({p.pattern for x in bv for p in PERSONA_PATTERNS if p.search(x)})
    ok_b = len(bv) >= 1 and all(valid(v) for v in bv) and not persona
    note = f"{sum(valid(v) for v in bv)}/{len(bv)} 条有效（职责 / 输出 / 验收）"
    if persona:
        note += f" · 出现人设词：{persona}"
    results.append(("B 职责契约（禁人设形容词）", ok_b, note))

    # C / D
    for key, label in (("C.", "C 风格约束"), ("D.", "D 输出格式")):
        vals = [field_value(x) for x in bullets(bodies[key])]
        results.append((label, len(vals) >= 1 and all(valid(v) for v in vals),
                        f"{sum(valid(v) for v in vals)}/{len(vals)} 条有效"))

    # V1 / V2：正文填实、≥8 字、两者互异
    def main_body(key):
        for x in bullets(bodies[key]):
            if x.startswith("提示词正文"):
                return field_value(x)
        return ""

    v1, v2 = main_body("V1."), main_body("V2.")
    ok_v1 = valid(v1) and len(v1) >= 8
    ok_v2 = valid(v2) and len(v2) >= 8
    distinct = bool(v1) and bool(v2) and v1 != v2
    results.append(("V1 精简通用版", ok_v1, f"提示词正文 {len(v1)} 字（需 ≥8 且非占位符）"))
    results.append(("V2 高阶顶配版", ok_v2, f"提示词正文 {len(v2)} 字（需 ≥8 且非占位符）"))
    results.append(("两版互异（禁止复制粘贴）", distinct,
                    "两版正文不同" if distinct else "两版正文相同或未填，高阶版不能只是多加形容词"))

    # V2 须真正接野心层三维与沟通层四准则（字段名固定，值须填实）
    v2_all = bullets(bodies["V2."])
    tri = next((x for x in v2_all if x.startswith("高度 / 深度 / 广度")), "")
    four = next((x for x in v2_all if x.startswith("沟通层四准则")), "")
    ok_link = valid(field_value(tri)) and valid(field_value(four))
    results.append(("V2 接野心层三维 + 沟通层四准则", ok_link,
                    "高度/深度/广度与四准则均已填实（不另造顶配标准）" if ok_link else "三维或四准则未填实"))

    # E：平台适配，未知须回退通用档
    e = bullets(bodies["E."])
    ev = [field_value(x) for x in e]
    fallback = any("通用档" in x for x in e)
    ok_e = len(ev) >= 2 and all(valid(v) for v in ev[:2]) and fallback
    note = f"{sum(valid(v) for v in ev)}/{len(ev)} 条有效"
    if not fallback:
        note += " · 缺「未知平台回退通用档」声明"
    results.append(("E 平台适配（不编造规则）", ok_e, note))

    # F：无效指令与逻辑漏洞自检
    f = bullets(bodies["F."])
    fv = [field_value(x) for x in f]
    results.append(("F 漏洞与无效指令自检", len(fv) >= 2 and all(valid(v) for v in fv),
                    f"{sum(valid(v) for v in fv)}/{len(fv)} 条有效（已剔除 / 已规避 各 ≥1）"))

    leftover = block.count(PLACEHOLDER)
    results.append(("占位符残留", leftover == 0,
                    f"区块内残留 {leftover} 处 {PLACEHOLDER}" if leftover else "无残留"))
    return all(r[1] for r in results), results, True


def cmd_verify(task: Path, required: bool) -> int:
    ok, results, enabled = check(task / "task_plan.md", required)
    print(f"提示词优化校验：{task}")
    for name, passed, note in results:
        print(f"  {'[OK]' if passed else '[NG]'} {name}：{note}")
    if not enabled:
        print("→ 放行：本次为 SKIP / 未触发，原样透传，零改动零文件。" if ok else
              "→ 未通过：已声明需要优化（--required），但未跑 prompt_opt.py init（阻断）。")
        return 0 if ok else 1
    print("→ 通过：两版齐备、假设可改、无人设、已接野心层，可拿高阶版进 0 野心升级。" if ok else
          "→ 未通过：补齐九段后再开工；优化产物只是可修改的草稿，用哪版由人定（阻断）。")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="V0.0.8 Step -1：输入分流 + 提示词优化（条件触发）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_cls = sub.add_parser("classify", help="纯文本分流：SKIP 原样透传 / OPTIMIZE 才优化")
    p_cls.add_argument("text", help="用户原文")
    p_cls.add_argument("--force", action="store_true", help="用户显式说「优化这段」时强制 OPTIMIZE")

    p_init = sub.add_parser("init", help="仅 OPTIMIZE 时幂等追加「00」区块到 task_plan.md")
    p_init.add_argument("path", help="任务目录")
    p_init.add_argument("--input", dest="raw_input", default="", help="用户原文（逐字留档）")
    p_init.add_argument("--force", action="store_true", help="强制 OPTIMIZE（配合 --input）")

    p_ver = sub.add_parser("verify", help="校验优化区块；无区块默认放行")
    p_ver.add_argument("path", help="任务目录")
    p_ver.add_argument("--required", action="store_true", help="显式声明本次需要优化：缺区块也返回 1")

    sub.add_parser("profiles", help="列出可验证的平台适配档位")
    args = ap.parse_args()

    if args.cmd == "classify":
        return cmd_classify(args.text, args.force)
    if args.cmd == "profiles":
        return cmd_profiles()

    task = resolve_task(Path(args.path))
    if task is None:
        print(f"[x] 找不到任务目录或 task_plan.md：{args.path}")
        return 2
    if args.cmd == "init":
        return cmd_init(task, args.raw_input, args.force)
    return cmd_verify(task, args.required)


if __name__ == "__main__":
    raise SystemExit(main())
