#!/usr/bin/env python3
"""路由用例检查：本 Skill 的索引层可见性与与上游 VI 权威的边界。

只读、确定性、无网络。检查发生在“加载之前”的层面：

1. 计算每个 Skill 描述经 loader 截断后真正进入索引的窗口
   （默认 60 字符，`desc[:limit-3] + '...'`，与 Hermes loader 的
   `SKILL_PROMPT_DESC_LIMIT` / `extract_skill_description` 一致）。
2. 对每个用例做字面判定：
   - expect=visual-design：查询必须命中本 Skill 窗口内的 key term，
     否则该请求在索引层根本无法被本 Skill 接住（FAIL）。
   - expect=vi-guide / neither：查询若命中本 Skill 的 key term，说明边界在索引层
     不可区分（WARN；`ambiguity` 用例只报 WARN 不报 FAIL）。
3. 结构性检查：SKILL.md 正文必须存在边界句（boundary terms），
   否则加载后的行为也无从裁定（FAIL）。

退出码：0 = 无 FAIL；1 = 存在 FAIL；2 = 依赖不可解析（上游 Skill 缺失）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_CASES = Path(__file__).with_name("route_cases.json")
DEFAULT_LIMIT = 60
UPSTREAM_ENV = "ARCHEBASE_VI_GUIDE"


def resolve_upstream(explicit: str | None, skill_dir: Path) -> Path | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get(UPSTREAM_ENV)
    if env:
        candidates.append(Path(env))
    for base in (skill_dir, skill_dir.parent, skill_dir.parent.parent, Path.home(), Path.home() / "Books"):
        candidates.append(base / "archebase-vi-guide")
    for candidate in candidates:
        if (candidate / "SKILL.md").is_file():
            return candidate
    return None


def read_frontmatter_description(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n(.*?)\n---\s*\n", text, re.S | re.M)
    if not match:
        raise SystemExit(f"FAIL 无法解析 frontmatter：{skill_md}")
    block = match.group(1)
    line = re.search(r"^description:\s*(.+)$", block, re.M)
    if not line:
        raise SystemExit(f"FAIL frontmatter 缺少 description：{skill_md}")
    raw = line.group(1).strip()
    if len(raw) > 1 and raw[0] == raw[-1] and raw[0] in "\"'":
        try:
            value = json.loads(raw) if raw[0] == '"' else raw[1:-1]
        except Exception:
            value = raw[1:-1]
    else:
        value = raw
    return value


def visible_window(description: str, limit: int) -> str:
    return description[: limit - 3] + "..." if len(description) > limit else description


def window_body(description: str, limit: int) -> str:
    window = visible_window(description, limit)
    return window[:-3] if window.endswith("...") else window


def load_cases(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check index-level routing reachability and the vi-guide boundary")
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--skill", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--upstream", default=None)
    parser.add_argument("--limit", type=int, default=None, help="loader 的描述字符上限（默认读用例文件的 loader.desc_char_limit）")
    parser.add_argument("--print-window", action="store_true", help="只打印各 Skill 的索引窗口")
    args = parser.parse_args()

    cases_path = Path(args.cases).resolve()
    data = load_cases(cases_path)
    skill_dir = Path(args.skill).resolve()
    limit = args.limit or int(data.get("loader", {}).get("desc_char_limit", DEFAULT_LIMIT))

    skill_conf = data["skills"]["visual-design"]
    local_md = (cases_path.parent / skill_conf["skill_md"]).resolve()
    if not local_md.is_file():
        print(f"FAIL 找不到本地 SKILL.md：{local_md}")
        return 2
    local_desc = read_frontmatter_description(local_md)
    local_window = window_body(local_desc, limit)

    upstream_dir = resolve_upstream(args.upstream, skill_dir)
    upstream_md = upstream_dir / "SKILL.md" if upstream_dir else None
    upstream_window = ""
    if upstream_md and upstream_md.is_file():
        upstream_window = window_body(read_frontmatter_description(upstream_md), limit)

    if args.print_window:
        print(f"loader 描述上限：{limit}（超出部分不参与路由）")
        print(f"[visual-design] 完整 {len(local_desc)} 字符；窗口：{local_window}")
        print(f"[vi-guide] 窗口：{upstream_window or '（未解析到上游）'}")
        return 0

    key_terms = [t for t in skill_conf["key_terms"]]
    visible_terms = [t for t in key_terms if t in local_window]
    invisible_terms = [t for t in key_terms if t not in local_window]
    boundary_terms = [t for t in skill_conf.get("boundary_terms", [])]
    body = local_md.read_text(encoding="utf-8")
    missing_boundary = [t for t in boundary_terms if t not in body]

    rows: list[tuple[str, str, str, str, str]] = []

    def add(status: str, case_id: str, expect: str, detail: str, evidence: str = "") -> None:
        rows.append((status, case_id, expect, detail, evidence))

    if missing_boundary:
        add("FAIL", "structure:boundary", "-", f"SKILL.md 正文缺少边界用语 {missing_boundary}", str(local_md))
    else:
        add("OK", "structure:boundary", "-", "SKILL.md 正文存在边界用语 " + "、".join(boundary_terms), str(local_md))
    if invisible_terms:
        add("WARN", "structure:window", "-", f"key term 不在索引窗口内（加载后才可见）：{invisible_terms}", f"窗口={local_window}")
    else:
        add("OK", "structure:window", "-", f"全部 key term 都在索引窗口内：{visible_terms}", f"窗口={local_window}")

    for case in data["cases"]:
        case_id = case["id"]
        query = case["query"]
        expect = case["expect"]
        hits = [t for t in visible_terms if t in query]
        upstream_hits = [t for t in skill_conf.get("key_terms", []) if t in query]
        ambiguity = bool(case.get("ambiguity"))
        if expect == "visual-design":
            if hits:
                add("OK", case_id, expect, f"命中窗口内 key term：{hits}")
            else:
                add("FAIL", case_id, expect, f"查询未命中任何窗口内 key term（可命中的：{visible_terms}）", query)
        elif expect == "vi-guide":
            if hits:
                status = "WARN" if ambiguity else "WARN"
                note = "（已知难例：字面撞车，需模型依据边界语义裁决）" if ambiguity else "（边界在索引层不可区分，需加载后依据 SKILL.md 分工边界裁决）"
                add(status, case_id, expect, f"查询同时命中本 Skill 的 key term：{hits} {note}", query)
            else:
                add("OK", case_id, expect, "查询未撞上本 Skill 的 key term；上游窗口：" + (upstream_window or "未解析"))
        else:
            shared = [t for t in ["ArcheBase", "智域基石"] if t in query]
            if hits or shared:
                add("WARN", case_id, expect, f"无关请求命中触发词：{hits + shared}", query)
            else:
                add("OK", case_id, expect, "未命中任何触发词", query)

    width = max(len(r[1]) for r in rows)
    print(f"loader 描述上限 {limit}；窗口内容：{local_window}")
    print(f"{'判定':6} {'用例':{width}} 期望              说明")
    print("-" * 100)
    for status, case_id, expect, detail, evidence in rows:
        print(f"{status:6} {case_id:{width}} {expect:18} {detail}")
        if evidence and status != "OK":
            print(f"{'':6} {'':{width}} {'':18}   → {evidence}")

    fails = [r for r in rows if r[0] == "FAIL"]
    warns = [r for r in rows if r[0] == "WARN"]
    print("-" * 100)
    print(f"汇总：FAIL {len(fails)} 项，WARN {len(warns)} 项，用例 {len(data['cases'])} 个；窗口内可命中的 key term：{visible_terms}")
    if fails:
        print("结论：存在索引层不可达或边界缺失，必须修复后重新运行。")
        return 1
    print("结论：正例在索引层可达；边界用例需由模型按 SKILL.md 分工边界裁决（字面检查无法判定）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
