#!/usr/bin/env python3
"""校验「参考图保真与佩戴几何」规格（spatial-fidelity spec）。

只读、确定性、无网络、不依赖第三方包。用法：

    python3 evals/check_spatial_spec.py --spec path/to/spec.json
    python3 evals/check_spatial_spec.py --self-test

`--self-test` 用内置正例与反例证明检查可失败（反例必须被拦下）。退出码：
0 = 全部通过；1 = 存在 FAIL 或自检不符预期；2 = 输入不可解析。

本检查只覆盖可机检的部分（字段齐全、姿态声明、不变式可证伪、展示驱动措辞、
绝对路径、交付门）。它无法判断器件是否真的长得像参考图——那要靠裁切复核与人工评审。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CASES_PATH = Path(__file__).resolve().parent / "spatial-spec-cases.json"

SUBJECT_KINDS = {"device_on_person", "device_only", "environment"}
REFERENCE_ROLES = {
    "head_device",
    "wrist_left",
    "wrist_right",
    "device_detail",
    "other_device",
    "environment",
    "subject_portrait",
}
DEVICE_ROLES = {"head_device", "wrist_left", "wrist_right", "device_detail", "other_device"}
INVARIANT_STATUS = {"pending", "pass", "fail", "待确认"}
CANDIDATE_STATUS = {"accepted", "rejected", "pending"}

REQUIRED = (
    "version",
    "project",
    "asset",
    "subject",
    "references",
    "invariants",
    "posture_geometry_check",
    "occlusion_policy",
    "candidate_log",
)

# 本机绝对路径不得写进规格（规格要能在别的机器与仓库里复现）。
ABS_PATH = re.compile(r"(^|[\s\"'(\[])(/Users/|/home/|/Volumes/|[A-Za-z]:\\|~/)")
# 不可证伪的形容词，不能充当不变式判据。
VAGUE = ("更真实", "更自然", "更高级", "更好看", "更专业", "更有质感", "更精致", "更有科技感")
# 为了展示器件而扭曲姿态：本 Skill 明确禁止。
DISPLAY_DRIVEN = re.compile(
    r"(确保|必须|务必|一定要|要让|需要)[^。；;\n]{0,12}(镜头|相机|摄像头|传感器|模块)"
    r"[^。；;\n]{0,10}(可见|露出|朝前|面向(观众|镜头)|朝向观众)"
)
# 未经批准的品牌名称写法。
BAD_NAME = re.compile(r"Archebase|ARCHEBASE|Arche Base|ArchebaseVR|archebase_visual")


def check_spec(spec: object) -> list[tuple[str, str, str]]:
    """返回 (status, code, detail) 行；status ∈ PASS/FAIL/WARN/SKIP。"""
    rows: list[tuple[str, str, str]] = []

    def add(status: str, code: str, detail: str) -> None:
        rows.append((status, code, detail))

    if not isinstance(spec, dict):
        add("FAIL", "S1", "规格根节点必须是 JSON 对象")
        return rows

    missing = [key for key in REQUIRED if key not in spec]
    add(
        "FAIL" if missing else "PASS",
        "S1",
        f"缺少必填字段：{', '.join(missing)}" if missing else "必填字段齐全",
    )

    subject = spec.get("subject") if isinstance(spec.get("subject"), dict) else {}
    kind = subject.get("kind")
    add(
        "PASS" if kind in SUBJECT_KINDS else "FAIL",
        "S2",
        f"subject.kind={kind!r}；须为 {' / '.join(sorted(SUBJECT_KINDS))} 之一",
    )

    pose = str(subject.get("pose") or "").strip()
    if kind == "device_on_person":
        add(
            "PASS" if pose else "FAIL",
            "S3",
            "佩戴整机任务必须声明 subject.pose（姿态优先于措辞）" if not pose else f"已声明姿态：{pose[:48]}",
        )
    else:
        add("SKIP", "S3", "非佩戴主体任务，跳过姿态必填检查")

    refs = spec.get("references")
    if not isinstance(refs, list) or not refs:
        add("FAIL", "S4", "references 必须是非空数组（一张参考图一个角色）")
    else:
        ids = [str(r.get("id") or "") for r in refs if isinstance(r, dict)]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        bad_role = [str(r.get("role")) for r in refs if not isinstance(r, dict) or r.get("role") not in REFERENCE_ROLES]
        add("PASS" if not dup else "FAIL", "S4a", f"参考图 id 重复：{dup}" if dup else f"{len(refs)} 个参考角色，id 唯一")
        add("PASS" if not bad_role else "FAIL", "S4b", f"非法角色：{bad_role}" if bad_role else "角色取值合法")

        missing_excl = []
        missing_imm = []
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            rid = ref.get("id", "?")
            if not isinstance(ref.get("immutable"), list) or not ref.get("immutable"):
                missing_imm.append(str(rid))
            if not isinstance(ref.get("excluded"), list) or not ref.get("excluded"):
                missing_excl.append(str(rid))
        add("PASS" if not missing_imm else "FAIL", "S5", f"未登记不可变特征：{missing_imm}" if missing_imm else "每个角色都登记了不可变特征")
        add("PASS" if not missing_excl else "FAIL", "S6", f"未登记不得复现项：{missing_excl}" if missing_excl else "每个角色都登记了不得复现项")

        if kind == "device_on_person":
            has_device = any(isinstance(r, dict) and r.get("role") in DEVICE_ROLES for r in refs)
            add("PASS" if has_device else "FAIL", "S7", "佩戴任务缺少器件角色参考" if not has_device else "含至少一个器件角色")

    invariants = spec.get("invariants")
    if not isinstance(invariants, list) or not invariants:
        add("FAIL", "S8", "invariants 必须是非空数组")
        invariants = []
    else:
        iids = [str(i.get("id") or "") for i in invariants if isinstance(i, dict)]
        dup = sorted({i for i in iids if iids.count(i) > 1})
        incomplete = []
        bad_status = []
        for inv in invariants:
            if not isinstance(inv, dict):
                continue
            if not all(str(inv.get(k) or "").strip() for k in ("statement", "observation", "prompt_clause")):
                incomplete.append(str(inv.get("id", "?")))
            if inv.get("status") not in INVARIANT_STATUS:
                bad_status.append(f"{inv.get('id', '?')}={inv.get('status')!r}")
        add("PASS" if not dup else "FAIL", "S8a", f"不变式 id 重复：{dup}" if dup else f"{len(invariants)} 条不变式，id 唯一")
        add("PASS" if not incomplete else "FAIL", "S8b", f"缺少 statement/observation/prompt_clause：{incomplete}" if incomplete else "每条不变式都有判据、复核位置与提示词对应句")
        add("PASS" if not bad_status else "FAIL", "S8c", f"非法状态：{bad_status}" if bad_status else "状态取值合法")

        vague = [str(i.get("id", "?")) for i in invariants if isinstance(i, dict) and any(w in str(i.get("statement", "")) for w in VAGUE)]
        add("PASS" if not vague else "FAIL", "S9", f"不变式含不可证伪表述（{', '.join(VAGUE[:4])} 等）：{vague}" if vague else "无不可证伪表述")

    posture = spec.get("posture_geometry_check") if isinstance(spec.get("posture_geometry_check"), dict) else {}
    assertion = str(posture.get("assertion") or "").strip()
    violates = str(posture.get("violates_if") or "").strip()
    add("PASS" if assertion else "FAIL", "S10", "缺少 posture_geometry_check.assertion（姿态成立条件）" if not assertion else "已声明姿态成立条件")
    if kind == "device_on_person":
        add("PASS" if violates else "FAIL", "S10b", "佩戴任务缺少 violates_if（什么姿态会使不变式失效）" if not violates else "已声明失效姿态")

    occlusion = str(spec.get("occlusion_policy") or "").strip()
    add("PASS" if occlusion else "FAIL", "S11", "缺少 occlusion_policy" if not occlusion else "已声明遮挡策略")
    if occlusion and not any(w in occlusion for w in ("遮挡", "挡住", "背对", "不可见", "被手", "袖口")):
        add("WARN", "S11b", "遮挡策略未提到允许遮挡；真实佩戴中遮挡是正常结果")

    candidates = spec.get("candidate_log")
    if not isinstance(candidates, list) or not candidates:
        add("FAIL", "S12", "candidate_log 必须是非空数组（单变量迭代记录）")
    else:
        cids = [str(c.get("id") or "") for c in candidates if isinstance(c, dict)]
        dup = sorted({i for i in cids if cids.count(i) > 1})
        bad_status = []
        no_reason = []
        for cand in candidates:
            if not isinstance(cand, dict):
                continue
            cid = str(cand.get("id", "?"))
            if cand.get("status") not in CANDIDATE_STATUS:
                bad_status.append(f"{cid}={cand.get('status')!r}")
            if cand.get("status") == "rejected":
                failed = cand.get("invariants_failed")
                if not (str(cand.get("reason") or "").strip() or (isinstance(failed, list) and failed)):
                    no_reason.append(cid)
        add("PASS" if not dup else "FAIL", "S12a", f"候选 id 重复：{dup}" if dup else f"{len(candidates)} 个候选，id 唯一")
        add("PASS" if not bad_status else "FAIL", "S12b", f"非法候选状态：{bad_status}" if bad_status else "候选状态合法")
        add("PASS" if not no_reason else "FAIL", "S12c", f"淘汰候选缺少理由或失败不变式：{no_reason}" if no_reason else "每个淘汰候选都有理由")

        accepted = [c for c in candidates if isinstance(c, dict) and c.get("status") == "accepted"]
        failed = [str(i.get("id", "?")) for i in invariants if isinstance(i, dict) and i.get("status") == "fail"]
        if accepted:
            blockers = list(failed)
            for cand in accepted:
                blockers.extend(str(v) for v in (cand.get("invariants_failed") or []))
            add("PASS" if not blockers else "FAIL", "S13", f"存在 accepted 候选但不变式仍失败：{sorted(set(blockers))}" if blockers else "交付门通过：accepted 候选无失败不变式")
        else:
            add("SKIP", "S13", "尚无 accepted 候选，交付门未触发")

    limits = spec.get("known_limits")
    if not isinstance(limits, list) or not limits:
        add("WARN", "S14", "未登记 known_limits：任何器件复刻都存在无法消除的偏差，应如实登记")
    else:
        add("PASS", "S14", f"已登记 {len(limits)} 条已知限制")

    text = json.dumps(spec, ensure_ascii=False)
    display = DISPLAY_DRIVEN.findall(text)
    add(
        "PASS" if not display else "FAIL",
        "S15",
        "无展示驱动措辞" if not display else "含「为展示器件而要求可见/朝前」的措辞；应改姿态或接受遮挡",
    )
    paths = ABS_PATH.findall(text)
    add(
        "PASS" if not paths else "FAIL",
        "S16",
        "无本机绝对路径" if not paths else "含本机绝对路径，规格不可跨机器复现",
    )
    names = BAD_NAME.findall(text)
    add(
        "PASS" if not names else "FAIL",
        "S17",
        "品牌名称写法合规" if not names else f"品牌名称写法未获批准：{sorted(set(names))}",
    )

    return rows


def has_fail(rows: list[tuple[str, str, str]]) -> bool:
    return any(status == "FAIL" for status, _, _ in rows)


def render(rows: list[tuple[str, str, str]], title: str) -> None:
    icon = {"PASS": "PASS", "FAIL": "FAIL", "WARN": "WARN", "SKIP": "SKIP"}
    print(f"\n{title}")
    for status, code, detail in rows:
        print(f"  [{icon[status]:4}] {code:6} {detail}")


def run_self_test(cases_path: Path) -> int:
    try:
        payload = json.loads(cases_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL 无法读取用例文件 {cases_path}：{exc}", file=sys.stderr)
        return 2

    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list) or not cases:
        print(f"FAIL 用例文件格式不正确：{cases_path}", file=sys.stderr)
        return 2

    def deep_merge(base: object, patch: object) -> object:
        if isinstance(base, dict) and isinstance(patch, dict):
            merged = dict(base)
            for key, value in patch.items():
                merged[key] = deep_merge(base.get(key), value) if key in base else value
            return merged
        return patch

    resolved: dict[str, object] = {}
    mismatched = []
    for case in cases:
        name = str(case.get("name", "?"))
        parent = case.get("inherit")
        if parent is not None:
            if parent not in resolved:
                print(f"FAIL 用例 {name} 继承了未定义或晚于自身的用例 {parent}", file=sys.stderr)
                return 2
            spec = deep_merge(resolved[parent], case.get("patch") or {})
        else:
            spec = case.get("spec")
            if spec is None:
                print(f"FAIL 用例 {name} 缺少 spec 或 inherit", file=sys.stderr)
                return 2
        resolved[name] = spec
        expect = case.get("expect")
        rows = check_spec(spec)
        actual = "fail" if has_fail(rows) else "pass"
        failed_codes = sorted({code for status, code, _ in rows if status == "FAIL"})
        expected_codes = sorted(set(case.get("expect_codes") or []))
        ok = actual == expect and set(expected_codes).issubset(failed_codes)
        if not ok:
            mismatched.append((name, expect, actual, failed_codes, expected_codes))
        print(f"  [{'OK ' if ok else 'BAD'}] {name:34} expect={expect:4} actual={actual:4} fail_codes={failed_codes}")

    positives = sum(1 for c in cases if c.get("expect") == "pass")
    negatives = sum(1 for c in cases if c.get("expect") == "fail")
    print(f"\n自检：正例 {positives} 个 / 反例 {negatives} 个；不符预期 {len(mismatched)} 个")
    if mismatched:
        for name, expect, actual, failed, expected in mismatched:
            print(f"  FAIL {name}: 期望 {expect}，实得 {actual}；失败码 {failed}，需含 {expected}", file=sys.stderr)
        print("FAIL 自检未通过：检查存在漏洞或未按预期拦截反例", file=sys.stderr)
        return 1
    print("PASS 自检通过：正例放行，反例全部拦下（检查具备可证伪性）")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="校验参考图保真与佩戴几何规格")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--spec", type=Path, help="spatial-fidelity spec JSON 路径")
    group.add_argument("--self-test", action="store_true", help="跑内置正/反例自检")
    parser.add_argument("--cases", type=Path, default=CASES_PATH, help="自检用例文件路径")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test(args.cases)

    assert args.spec is not None
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL 无法读取规格 {args.spec}：{exc}", file=sys.stderr)
        return 2

    rows = check_spec(spec)
    render(rows, f"spatial-fidelity spec：{args.spec}")
    fails = [code for status, code, _ in rows if status == "FAIL"]
    warns = [code for status, code, _ in rows if status == "WARN"]
    print(f"\n结果：{'FAIL' if fails else 'PASS'}（失败 {len(fails)}，警告 {len(warns)}）")
    if fails:
        print(f"失败项：{', '.join(fails)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
