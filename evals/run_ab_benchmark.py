#!/usr/bin/env python3
"""archebase-visual-design A/B 基准 harness：--plan / --validate / --score。

对应协议 visual-guide-ab-benchmark.md 与案例 benchmark-cases.json。
本脚本只读：不写回本 Skill、上游 VI Guide 或 Design IR store；无网络；不调用任何模型。
它只负责“准备运行”与“分析评分”：真实输出由人或另一个 harness 产生并回填。

写盘范围：
  --plan      只写 --out 目录（manifest.json、prompts/、scoring-sheet.csv、blind-map.json）；
  --validate  不写任何文件；
  --score     不写任何文件。

输出为中文 JSON / CSV，不含 emoji；同一输入 + 同一 --seed 的结果逐字节可复现。

字段口径（协议原列表之外的必要澄清）：
  prompt_hash            覆盖 A/B 共享的任务正文（案例 prompt 本身），因此同一 case_id 的两侧一致，
                         用于逐案配对校验；条件横幅不计入。完整渲染文件的哈希记在 rendered_prompt_sha256。
  asset_manifest_version A（不加载 VI 资产）固定为 none；B 为锁定上游 tokens/asset 清单的内容指纹。
                         两侧本就不同，故不参与配对校验；配对只看 prompt_hash / input_files /
                         upstream_vi_tag / upstream_vi_commit 与 image_set。

退出码（三个模式共用）：
  0  成功：运行清单已生成 / 校验全部通过 / 评分与判定已输出。
     （--score 判定为“证据不足”仍算 0，判定是结果而不是脚本失败。）
  1  违规或拒绝：
     --plan      目标目录已有 manifest.json 且未加 --force；或上游 HEAD 与锁定 commit 不一致；
     --validate  协议违规（缺必填字段、单一基线漂移、逐案配对不一致、多图不一致、盲表/盲映射不一致）；
     --score     评分表非法（取值越界、盲标签非法、偏好冲突、盲映射缺行）。
  2  前置条件不可用：案例文件缺失/非法 JSON；--out 缺失；--validate 目录/清单缺失；--score 表或盲映射缺失。
  3  --validate 专用：清单本身有效，但结果尚未产生（runs/<run_id>.json 未全部就位）。

用法：
  python3 evals/run_ab_benchmark.py --plan --out /tmp/ab-smoke
  python3 evals/run_ab_benchmark.py --validate /tmp/ab-smoke
  python3 evals/run_ab_benchmark.py --score /tmp/ab-smoke/scoring-sheet.csv

路径解析（不含任何机器绝对路径默认值）：
  上游 VI Guide：--upstream > 环境变量 ARCHEBASE_VI_GUIDE > Skill 目录/上级/上上级 > $HOME > $HOME/Books
  下的 archebase-vi-guide；解析不到时 --plan 仍会生成清单，但把上游标为未解析、B 条件资产指纹留占位符。
  案例文件：--cases > evals/benchmark-cases.json。
"""
import argparse
import csv
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
SKILL_DIR = EVALS_DIR.parent
DEFAULT_CASE_FILE = EVALS_DIR / 'benchmark-cases.json'
UPSTREAM_DIRNAME = 'archebase-vi-guide'
UPSTREAM_REQUIRED = ('SKILL.md', 'tokens/archebase.tokens.json', 'assets/logo-manifest.json')
DEFAULT_SEED = 20260927
DEFAULT_RESAMPLES = 10000
MIN_REPETITIONS = 3

CONDITION_INFO = {
    'A': {'name': 'baseline_without_vi', 'loads_vi_guide': False},
    'B': {'name': 'guided_with_vi', 'loads_vi_guide': True},
}

# 与 visual-guide-ab-benchmark.md 的 Primary metrics 同名（snake_case 用于 JSON/CSV）。
PRIMARY_METRICS = (
    'brand_correctness',
    'evidence_grounding',
    'hard_boundary_safety',
    'route_asset_correctness',
    'actionability',
    'false_positive_rate',
    'unsupported_claim_rate',
    'release_blocker_recall',
)
METRIC_NAMES = {
    'brand_correctness': 'Brand correctness',
    'evidence_grounding': 'Evidence grounding',
    'hard_boundary_safety': 'Hard-boundary safety',
    'route_asset_correctness': 'Route/asset correctness',
    'actionability': 'Actionability',
    'false_positive_rate': 'False-positive rate',
    'unsupported_claim_rate': 'Unsupported-claim rate',
    'release_blocker_recall': 'Release-blocker recall',
}
RATING_METRICS = (
    'brand_correctness',
    'evidence_grounding',
    'hard_boundary_safety',
    'route_asset_correctness',
    'actionability',
)
RATE_METRICS = ('false_positive_rate', 'unsupported_claim_rate')
METRIC_RANGES = {metric: (0.0, 5.0) for metric in RATING_METRICS}
METRIC_RANGES.update({metric: (0.0, 1.0) for metric in RATE_METRICS})

# 主判据的“可忽略效应”阈值：delta 落在 [-margin, margin] 视为可忽略。
# 提升类要求 CI 下界 > margin；不得增加类要求 CI 上界 < margin。
NEGLIGIBLE_EFFECT = {
    'release_blocker_recall': 0.10,
    'evidence_grounding': 0.50,
    'false_positive_rate': 0.02,
    'unsupported_claim_rate': 0.02,
}
IMPROVE_METRICS = ('release_blocker_recall', 'evidence_grounding')
HARM_METRICS = ('false_positive_rate', 'unsupported_claim_rate')

PLAN_REQUIRED_FIELDS = (
    'run_id',
    'case_id',
    'condition',
    'model_id',
    'model_version',
    'prompt_hash',
    'input_files',
    'asset_manifest_version',
    'image_set',
    'upstream_vi_tag',
    'upstream_vi_commit',
)
# 逐案配对比较的字段：同一 case_id 的 A/B 必须一致。
PAIRING_FIELDS = ('prompt_hash', 'input_files', 'upstream_vi_tag', 'upstream_vi_commit')
RUN_RESULT_REQUIRED_FIELDS = ('raw_output', 'structured_score', 'reviewer_id', 'review_notes', 'run_timestamp')

SHEET_COLUMNS = (
    'sheet_row_id',
    'case_id',
    'repetition',
    'blind_label',
    'pair_anchor',
    *RATING_METRICS,
    *RATE_METRICS,
    'blockers_seeded',
    'blockers_detected',
    'human_preference',
    'reviewer_id',
    'review_notes',
)

EXIT_CODES_TEXT = """退出码：
  0  成功（--score 判定“证据不足”仍为 0）
  1  违规或拒绝（--plan 目标已存在需 --force / 上游漂移；--validate 协议违规；--score 评分表非法）
  2  前置条件不可用（案例文件、--out、校验目录、评分表或盲映射缺失）
  3  --validate 专用：清单有效但结果尚未产生"""


def ph(*parts):
    """生成稳定的占位符，明确标注“尚未回填”，避免被误读为实测值。"""
    return '<place:' + ':'.join(str(part) for part in parts) + '>'


def is_placeholder(value):
    return isinstance(value, str) and value.startswith('<place:') and value.endswith('>')


def sha256_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def mean(values):
    return sum(values) / len(values) if values else None


def round_or_none(value, digits=4):
    return None if value is None else round(value, digits)


def dump_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def fail(message, code):
    print(message, file=sys.stderr)
    return code


# --------------------------------------------------------------------------
# 路径解析（与 run_visual_design_benchmark.py 同一候选顺序，不含机器绝对路径默认值）
# --------------------------------------------------------------------------
def upstream_candidates(cli_path):
    out = []
    if cli_path:
        out.append(('--upstream', Path(cli_path).expanduser()))
    env = os.environ.get('ARCHEBASE_VI_GUIDE')
    if env:
        out.append(('env ARCHEBASE_VI_GUIDE', Path(env).expanduser()))
    roots = [
        ('Skill 目录', SKILL_DIR),
        ('Skill 上级目录', SKILL_DIR.parent),
        ('Skill 上级目录的上级', SKILL_DIR.parent.parent),
        ('$HOME', Path.home()),
        ('$HOME/Books', Path.home() / 'Books'),
    ]
    for label, root in roots:
        if root.name == UPSTREAM_DIRNAME:
            out.append((f'{label}本身 {root}', root))
        out.append((f'{label} 下的 {UPSTREAM_DIRNAME}（{root}）', root / UPSTREAM_DIRNAME))
    return out


def resolve_upstream(cli_path):
    tried = []
    for label, path in upstream_candidates(cli_path):
        if path.is_dir() and all((path / name).is_file() for name in UPSTREAM_REQUIRED):
            return path, label, tried
        missing = [name for name in UPSTREAM_REQUIRED if not (path / name).is_file()]
        tried.append(f'{label}（{"不存在" if not path.is_dir() else "缺少 " + "/".join(missing)}）')
    return None, None, tried


def git_field(upstream, *args):
    """只读 git 查询；不联网。git 不可用或非仓库时返回 None。"""
    if upstream is None:
        return None
    try:
        proc = subprocess.run(['git', '-C', str(upstream), *args], text=True, capture_output=True)
    except OSError:
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def asset_manifest_fingerprint(upstream):
    """条件 B 可用的品牌资产清单指纹；解析不到上游时返回占位符。"""
    if upstream is None:
        return ph('asset-manifest-version')
    digest = hashlib.sha256()
    found = False
    for rel in ('tokens/archebase.tokens.json', 'assets/logo-manifest.json', 'assets/logo-checksums.json'):
        path = upstream / rel
        if path.is_file():
            found = True
            digest.update(rel.encode('utf-8'))
            digest.update(b'\0')
            digest.update(path.read_bytes())
            digest.update(b'\0')
    return ('sha256:' + digest.hexdigest()[:16]) if found else ph('asset-manifest-version')


def normalize_image_set(case, assets_dir, cases_dir):
    """把案例声明的图像槽规范成 (order, hashes)。占位符表示运行前尚未固定具体文件。"""
    spec = case.get('images', 'none')
    if isinstance(spec, str):
        order = [] if spec in ('none', '') else (['slot-01'] if spec == 'single' else [spec])
    elif isinstance(spec, bool):
        order = ['slot-01'] if spec else []
    elif isinstance(spec, int):
        order = [f'slot-{i:02d}' for i in range(1, spec + 1)]
    elif isinstance(spec, list):
        order = [str(item) for item in spec]
    elif isinstance(spec, dict):
        count = int(spec.get('count', 0))
        order = [str(item) for item in (spec.get('order') or [f'slot-{i:02d}' for i in range(1, count + 1)])]
    else:
        raise ValueError(f"案例 {case.get('id')} 的 images 字段无法解析：{spec!r}")

    declared = case.get('image_files') or []
    hashes = []
    for index, name in enumerate(order):
        resolved = None
        if index < len(declared):
            raw = str(declared[index])
            for root in (assets_dir, cases_dir):
                if root is not None and (root / raw).is_file():
                    resolved = root / raw
                    break
        hashes.append(sha256_file(resolved) if resolved else ph('sha256', case['id'], name))
    return order, hashes


def image_set_of(case, assets_dir, cases_dir):
    order, hashes = normalize_image_set(case, assets_dir, cases_dir)
    return {'count': len(order), 'order': order, 'per_image_hashes': hashes}


def render_banner(condition, upstream_tag, upstream_commit):
    """条件横幅：只陈述本次加载了什么，不暗示假设方向或预期优劣。"""
    if condition == 'B':
        return (f'[运行条件 B] 本次运行加载上游 ArcheBase VI Guide：'
                f'archebase-vi-guide tag {upstream_tag}（commit {upstream_commit}）。')
    return '[运行条件 A] 本次运行不加载 ArcheBase 专用视觉 Skill 与上游 VI Guide。'


# --------------------------------------------------------------------------
# --plan
# --------------------------------------------------------------------------
def load_cases(cases_file):
    path = Path(cases_file).expanduser()
    if not path.is_file():
        return None, None, f'[待确认] 案例文件不存在：{path}'
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as error:
        return None, None, f'[待确认] 案例文件不是合法 JSON：{error}'
    if not data.get('cases'):
        return None, None, f'[待确认] 案例文件没有 cases：{path}'
    return data, path, None


def cmd_plan(args):
    data, case_path, error = load_cases(args.cases)
    if error:
        return fail(error, 2)

    if not args.out:
        return fail('[待确认] --plan 需要 --out <目录>。', 2)
    out = Path(args.out).expanduser()

    repetitions = int(args.repetitions if args.repetitions is not None
                      else data.get('repetitions_per_case') or MIN_REPETITIONS)
    if repetitions < 1:
        return fail(f'[待确认] repetitions 必须 >= 1，收到 {repetitions}。', 2)
    seed = int(args.seed if args.seed is not None else DEFAULT_SEED)

    manifest_path = out / 'manifest.json'
    if manifest_path.exists() and not args.force:
        return fail(f'[拒绝] {manifest_path} 已存在；加 --force 覆盖，或改用其它 --out。', 1)

    pinned = data.get('upstream') or {}
    tag = str(pinned.get('tag') or ph('upstream-tag'))
    commit = str(pinned.get('commit') or ph('upstream-commit'))

    upstream, upstream_label, tried = resolve_upstream(args.upstream)
    upstream_note = None
    if upstream is None:
        upstream_note = '未解析到上游 VI Guide；条件 B 的资产指纹为占位符。已尝试：' + '；'.join(tried)
        print('[待确认] ' + upstream_note, file=sys.stderr)
    else:
        head = git_field(upstream, 'rev-parse', 'HEAD')
        if head and head != commit:
            return fail(
                f'[拒绝] 上游 HEAD={head} 与锁定 commit={commit} 不一致；'
                f'条件 B 必须加载锁定版本（tag {tag}）。请检出该 commit 或改 --upstream。', 1)

    asset_version = asset_manifest_fingerprint(upstream)

    out.mkdir(parents=True, exist_ok=True)
    prompts_dir = out / 'prompts'
    if args.force and prompts_dir.exists():
        shutil.rmtree(prompts_dir)
    prompts_dir.mkdir(parents=True, exist_ok=True)

    assets_dir = Path(args.assets).expanduser() if args.assets else None
    cases_dir = case_path.parent

    rng = random.Random(seed)
    runs, blind_rows, pairs, sheet_rows = [], [], [], []
    row_counter = 0

    for case in data['cases']:
        case_id = case['id']
        prompt_body = case['prompt'].strip()
        prompt_hash = sha256_text(prompt_body)
        images = image_set_of(case, assets_dir, cases_dir)
        input_files = [str(item) for item in (case.get('input_files') or [])]

        for repetition in range(1, repetitions + 1):
            x_is_a = rng.random() < 0.5
            label_to_condition = {'X': 'A' if x_is_a else 'B', 'Y': 'B' if x_is_a else 'A'}
            pairs.append({
                'case_id': case_id,
                'repetition': repetition,
                'X': label_to_condition['X'],
                'Y': label_to_condition['Y'],
                'X_run_id': f'{case_id}__{label_to_condition["X"]}__r{repetition}',
                'Y_run_id': f'{case_id}__{label_to_condition["Y"]}__r{repetition}',
            })

            for label in ('X', 'Y'):
                condition = label_to_condition[label]
                run_id = f'{case_id}__{condition}__r{repetition}'
                rendered = render_banner(condition, tag, commit) + '\n\n' + prompt_body + '\n'
                (prompts_dir / f'{run_id}.txt').write_text(rendered, encoding='utf-8')

                runs.append({
                    'run_id': run_id,
                    'case_id': case_id,
                    'family': case.get('family', ''),
                    'condition': condition,
                    'condition_name': CONDITION_INFO[condition]['name'],
                    'repetition': repetition,
                    'model_id': args.model_id or ph('model-id'),
                    'model_version': args.model_version or ph('model-version'),
                    'prompt_file': f'prompts/{run_id}.txt',
                    'prompt_hash': prompt_hash,
                    'rendered_prompt_sha256': sha256_text(rendered),
                    'input_files': list(input_files),
                    'asset_manifest_version': asset_version if condition == 'B' else 'none',
                    'image_set': {'count': images['count'], 'order': list(images['order']),
                                  'per_image_hashes': list(images['per_image_hashes'])},
                    'upstream_vi_tag': tag,
                    'upstream_vi_commit': commit,
                    'loaded_vi_guide': {
                        'loaded': CONDITION_INFO[condition]['loads_vi_guide'],
                        'resolved_path': str(upstream) if (upstream and condition == 'B') else None,
                        'resolved_from': upstream_label if condition == 'B' else None,
                        'tag': tag if condition == 'B' else None,
                        'commit': commit if condition == 'B' else None,
                    },
                    'run_timestamp': ph('iso8601-utc'),
                })

                row_counter += 1
                sheet_row_id = f'row-{row_counter:04d}'
                blind_rows.append({
                    'sheet_row_id': sheet_row_id,
                    'run_id': run_id,
                    'case_id': case_id,
                    'condition': condition,
                    'repetition': repetition,
                    'blind_label': label,
                })
                sheet_rows.append({
                    'sheet_row_id': sheet_row_id,
                    'case_id': case_id,
                    'repetition': repetition,
                    'blind_label': label,
                    'pair_anchor': '1' if (repetition == 1 and label == 'X') else '0',
                    **{metric: '' for metric in (*RATING_METRICS, *RATE_METRICS)},
                    'blockers_seeded': str(len(case.get('seeded_blockers') or [])),
                    'blockers_detected': '',
                    'human_preference': '',
                    'reviewer_id': '',
                    'review_notes': '',
                })

    manifest = {
        'benchmark': data.get('benchmark', 'archebase-visual-guide-ab-v0'),
        'protocol': data.get('protocol', 'visual-guide-ab-benchmark.md'),
        'harness': 'evals/run_ab_benchmark.py --plan',
        'generated_at_note': '本清单为运行前规划；run_timestamp/model_id 等占位符需在真实运行后回填。',
        'cases_file': str(case_path),
        'seed': seed,
        'repetitions_per_case': repetitions,
        'conditions': {condition: CONDITION_INFO[condition] for condition in ('A', 'B')},
        'upstream': {
            'repository': pinned.get('repository'),
            'tag': tag,
            'commit': commit,
            'resolved_path': str(upstream) if upstream else None,
            'resolved_from': upstream_label,
            'head_matches_pin': bool(upstream) and git_field(upstream, 'rev-parse', 'HEAD') == commit,
            'note': upstream_note,
        },
        'metric_names': METRIC_NAMES,
        'runs': runs,
    }
    dump_json(manifest_path, manifest)

    dump_json(out / 'blind-map.json', {
        'seed': seed,
        'note': '盲映射：sheet_row_id / run_id → 真实条件。不得交给评审者；评分表只出现 X/Y。',
        'repetitions_per_case': repetitions,
        'cases': [case['id'] for case in data['cases']],
        'pairs': pairs,
        'rows': blind_rows,
    })

    with (out / 'scoring-sheet.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=SHEET_COLUMNS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(sheet_rows)

    print(json.dumps({
        'mode': 'plan',
        'out_dir': str(out),
        'cases_file': str(case_path),
        'case_count': len(data['cases']),
        'conditions': list(CONDITION_INFO),
        'repetitions_per_case': repetitions,
        'seed': seed,
        'run_count': len(runs),
        'upstream_resolved': str(upstream) if upstream else None,
        'upstream_head_matches_pin': manifest['upstream']['head_matches_pin'],
        'artifacts': {
            'manifest': str(manifest_path),
            'prompts_dir': str(prompts_dir),
            'scoring_sheet': str(out / 'scoring-sheet.csv'),
            'blind_map': str(out / 'blind-map.json'),
        },
        'results_slot': str(out / 'runs' / '<run_id>.json'),
        'note': '结果尚未产生；本目录只包含运行清单、渲染后的提示词、盲评分表与盲映射。',
    }, ensure_ascii=False, indent=2))
    return 0


# --------------------------------------------------------------------------
# --validate
# --------------------------------------------------------------------------
def check_plan_integrity(manifest, dir_path, violations, invalidated, pending):
    runs = manifest.get('runs') or []
    if not runs:
        violations.append({'kind': 'empty_manifest', 'detail': '清单没有 runs。'})
        return runs

    for run in runs:
        run_id = run.get('run_id', '<缺 run_id>')
        for field in PLAN_REQUIRED_FIELDS:
            if field not in run or run[field] in (None, ''):
                violations.append({'kind': 'missing_field', 'run_id': run_id, 'field': field,
                                   'detail': '清单缺少必填字段。'})
        image_set = run.get('image_set')
        if isinstance(image_set, dict):
            if image_set.get('count') != len(image_set.get('order') or []) \
                    or image_set.get('count') != len(image_set.get('per_image_hashes') or []):
                violations.append({'kind': 'image_set_inconsistent', 'run_id': run_id, 'field': 'image_set',
                                   'detail': 'count/order/per_image_hashes 长度不一致。'})
        for field in ('model_id', 'model_version', 'run_timestamp', 'asset_manifest_version'):
            if is_placeholder(run.get(field)):
                pending.setdefault(field, []).append(run_id)

    # 单一基线：每个 condition 只有一个 model_id/model_version 组合。
    baseline = {}
    for run in runs:
        baseline.setdefault(run.get('condition'), set()).add((run.get('model_id'), run.get('model_version')))
    for condition, combos in sorted(baseline.items(), key=lambda item: str(item[0])):
        if len(combos) > 1:
            violations.append({
                'kind': 'baseline_drift', 'field': 'model_id/model_version', 'condition': condition,
                'detail': f'条件 {condition} 出现 {len(combos)} 组基线：{sorted(map(str, combos))}',
                'run_ids': [run['run_id'] for run in runs if run.get('condition') == condition],
            })

    # 逐案配对 + 多图规则。
    by_case = {}
    for run in runs:
        by_case.setdefault(run.get('case_id'), {}).setdefault(run.get('condition'), {})[run.get('repetition')] = run
    for case_id, sides in sorted(by_case.items(), key=lambda item: str(item[0])):
        a_map, b_map = sides.get('A', {}), sides.get('B', {})
        if not a_map or not b_map:
            violations.append({'kind': 'missing_condition_side', 'case_id': case_id, 'field': 'condition',
                               'detail': f'A/B 不完整：A={sorted(a_map)} B={sorted(b_map)}'})
        for repetition in sorted(set(a_map) & set(b_map)):
            run_a, run_b = a_map[repetition], b_map[repetition]
            for field in PAIRING_FIELDS:
                if run_a.get(field) != run_b.get(field):
                    violations.append({
                        'kind': 'pairing_mismatch', 'case_id': case_id, 'repetition': repetition, 'field': field,
                        'detail': f'{run_a["run_id"]}={run_a.get(field)!r} 与 {run_b["run_id"]}={run_b.get(field)!r} 不一致',
                        'run_ids': [run_a['run_id'], run_b['run_id']],
                    })
            images_a, images_b = run_a.get('image_set') or {}, run_b.get('image_set') or {}
            if (images_a.get('count'), images_a.get('order'), images_a.get('per_image_hashes')) != \
               (images_b.get('count'), images_b.get('order'), images_b.get('per_image_hashes')):
                violations.append({
                    'kind': 'multi_image_mismatch', 'case_id': case_id, 'repetition': repetition, 'field': 'image_set',
                    'detail': f'图像数量/顺序/逐图哈希不一致：A={images_a} B={images_b}',
                    'run_ids': [run_a['run_id'], run_b['run_id']],
                })
            for run, images in ((run_a, images_a), (run_b, images_b)):
                if images.get('count', 0) > 1:
                    hashes = images.get('per_image_hashes') or []
                    if len(hashes) != images.get('count') or any(not value for value in hashes):
                        invalidated.append({'run_id': run['run_id'], 'reason': 'multi_image_slot_missing',
                                            'detail': '多图案例缺少逐图哈希槽，该次运行作废。'})

    # 盲表 / 盲映射一致性。
    sheet_path = dir_path / 'scoring-sheet.csv'
    map_path = dir_path / 'blind-map.json'
    sheet_ids = None
    if not sheet_path.is_file():
        violations.append({'kind': 'missing_artifact', 'field': 'scoring-sheet.csv',
                           'detail': f'缺少 {sheet_path.name}。'})
    if not map_path.is_file():
        violations.append({'kind': 'missing_artifact', 'field': 'blind-map.json',
                           'detail': f'缺少 {map_path.name}。'})
    if map_path.is_file():
        try:
            blind_map = json.loads(map_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as error:
            violations.append({'kind': 'invalid_artifact', 'field': 'blind-map.json', 'detail': str(error)})
            blind_map = None
        if blind_map is not None:
            mapped = [row.get('run_id') for row in (blind_map.get('rows') or [])]
            expected = [run['run_id'] for run in runs]
            if sorted(mapped) != sorted(expected):
                violations.append({
                    'kind': 'blind_map_coverage', 'field': 'blind-map.json',
                    'detail': f'盲映射覆盖 {len(mapped)} 个 run，清单有 {len(expected)} 个；'
                              f'缺 {sorted(set(expected) - set(mapped))}，多 {sorted(set(mapped) - set(expected))}',
                })
            for row in blind_map.get('rows') or []:
                if row.get('blind_label') not in ('X', 'Y') or row.get('condition') not in ('A', 'B'):
                    violations.append({'kind': 'blind_map_invalid', 'field': 'blind-map.json',
                                       'detail': f'行 {row.get("sheet_row_id")} 的盲标签/条件非法：{row}'})
    if sheet_path.is_file():
        try:
            with sheet_path.open('r', encoding='utf-8-sig', newline='') as handle:
                reader = csv.DictReader(handle)
                missing_columns = [name for name in SHEET_COLUMNS if name not in (reader.fieldnames or [])]
                if missing_columns:
                    violations.append({'kind': 'sheet_missing_columns', 'field': 'scoring-sheet.csv',
                                       'detail': f'缺列：{missing_columns}'})
                sheet_ids = [row.get('sheet_row_id') for row in reader]
        except (OSError, csv.Error) as error:
            violations.append({'kind': 'invalid_artifact', 'field': 'scoring-sheet.csv', 'detail': str(error)})
            sheet_ids = None
    if sheet_ids is not None and len(sheet_ids) != len(runs):
        violations.append({'kind': 'sheet_row_count', 'field': 'scoring-sheet.csv',
                           'detail': f'评分表 {len(sheet_ids)} 行，清单 {len(runs)} 个 run。'})
    return runs


def cmd_validate(args):
    dir_path = Path(args.validate).expanduser()
    manifest_path = dir_path / 'manifest.json'
    if not manifest_path.is_file():
        return fail(f'[待确认] 找不到运行清单：{manifest_path}', 2)
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as error:
        return fail(f'[待确认] 清单不是合法 JSON：{error}', 2)

    violations, invalidated, pending = [], [], {}
    runs = check_plan_integrity(manifest, dir_path, violations, invalidated, pending)

    runs_dir = dir_path / 'runs'
    completed = []
    for run in runs:
        result_path = runs_dir / f"{run.get('run_id')}.json"
        if not result_path.is_file():
            continue
        try:
            result = json.loads(result_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as error:
            violations.append({'kind': 'invalid_result', 'run_id': run.get('run_id'), 'field': result_path.name,
                               'detail': f'结果文件不是合法 JSON：{error}'})
            continue
        completed.append(run.get('run_id'))
        for field in RUN_RESULT_REQUIRED_FIELDS:
            if field not in result or result[field] in (None, ''):
                violations.append({'kind': 'missing_result_field', 'run_id': run.get('run_id'), 'field': field,
                                   'detail': f'结果文件 {result_path.name} 缺少必填字段。'})
        for field in ('case_id', 'condition', 'prompt_hash'):
            if field in result and result[field] != run.get(field):
                violations.append({'kind': 'result_manifest_mismatch', 'run_id': run.get('run_id'), 'field': field,
                                   'detail': f'结果 {result[field]!r} 与清单 {run.get(field)!r} 不一致。'})
        image_set = run.get('image_set') or {}
        if image_set.get('count', 0) > 1 and 'raw_output' in result:
            raw = result['raw_output']
            if isinstance(raw, list) and len(raw) < image_set['count']:
                invalidated.append({'run_id': run.get('run_id'), 'reason': 'multi_image_raw_output_incomplete',
                                    'detail': f'raw_output 只有 {len(raw)} 项，需要 {image_set["count"]} 项。'})
            elif isinstance(raw, dict):
                images = raw.get('images')
                if not isinstance(images, list) or len(images) < image_set['count']:
                    invalidated.append({'run_id': run.get('run_id'), 'reason': 'multi_image_raw_output_incomplete',
                                        'detail': 'raw_output.images 缺失或不完整。'})

    notes = []
    cases_file = manifest.get('cases_file')
    if cases_file and Path(str(cases_file)).is_file():
        try:
            expected = sorted(case['id'] for case in
                              json.loads(Path(str(cases_file)).read_text(encoding='utf-8')).get('cases', []))
            found = sorted({run.get('case_id') for run in runs})
            if expected != found:
                violations.append({'kind': 'case_coverage', 'field': 'cases',
                                   'detail': f'清单案例 {found} 与案例文件 {expected} 不一致。'})
        except (json.JSONDecodeError, OSError) as error:
            notes.append(f'案例文件不可读，跳过覆盖检查：{error}')

    if violations or invalidated:
        status, code = 'FAIL', 1
        if invalidated and not violations:
            notes.append('存在作废运行（多图结果不完整），该目录不得用于比较。')
    elif runs and len(completed) == len(runs):
        status, code = 'PASS', 0
    else:
        status, code = ('INCOMPLETE' if completed else 'NO_RESULTS'), 3
        notes.append(f'结果尚未产生：{len(completed)}/{len(runs)} 次运行有结果文件（runs/<run_id>.json）。')

    print(json.dumps({
        'mode': 'validate',
        'dir': str(dir_path),
        'status': status,
        'run_count': len(runs),
        'completed_runs': len(completed),
        'violation_count': len(violations),
        'violations': violations,
        'invalidated_runs': invalidated,
        'pending_placeholders': {field: len(ids) for field, ids in sorted(pending.items())},
        'required_plan_fields': list(PLAN_REQUIRED_FIELDS),
        'required_result_fields': list(RUN_RESULT_REQUIRED_FIELDS),
        'pairing_fields': list(PAIRING_FIELDS),
        'notes': notes,
    }, ensure_ascii=False, indent=2))
    for item in violations:
        target = item.get('run_id') or item.get('case_id') or item.get('field', '')
        print(f"[违规] {item['kind']} 于 {target}：{item.get('detail', '')}", file=sys.stderr)
    return code


# --------------------------------------------------------------------------
# --score
# --------------------------------------------------------------------------
def parse_float(cell):
    text = (cell or '').strip()
    if text == '':
        return None
    try:
        return float(text)
    except ValueError:
        raise ValueError(f'不是数值：{cell!r}')


def parse_int(cell):
    value = parse_float(cell)
    if value is None:
        return None
    if abs(value - round(value)) > 1e-9:
        raise ValueError(f'不是整数：{cell!r}')
    return int(round(value))


def load_sheet(sheet_path):
    rows = []
    with sheet_path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in SHEET_COLUMNS if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f'评分表缺少列：{missing}')
        for index, raw in enumerate(reader, start=2):
            row = {
                'line': index,
                'sheet_row_id': (raw.get('sheet_row_id') or '').strip(),
                'case_id': (raw.get('case_id') or '').strip(),
                'repetition': parse_int(raw.get('repetition')),
                'blind_label': (raw.get('blind_label') or '').strip(),
                'pair_anchor': (raw.get('pair_anchor') or '').strip() == '1',
                'values': {},
                'blockers_seeded': parse_int(raw.get('blockers_seeded')),
                'blockers_detected': parse_int(raw.get('blockers_detected')),
                'human_preference': (raw.get('human_preference') or '').strip(),
                'reviewer_id': (raw.get('reviewer_id') or '').strip(),
            }
            if not row['sheet_row_id'] or not row['case_id'] or row['repetition'] is None:
                raise ValueError(f'第 {index} 行缺 sheet_row_id/case_id/repetition。')
            if row['blind_label'] not in ('X', 'Y'):
                raise ValueError(f"第 {index} 行 blind_label 非法：{row['blind_label']!r}（只接受 X/Y）。")
            for metric in (*RATING_METRICS, *RATE_METRICS):
                value = parse_float(raw.get(metric))
                if value is not None:
                    low, high = METRIC_RANGES[metric]
                    if not (low <= value <= high):
                        raise ValueError(f'第 {index} 行 {metric}={value} 超出 [{low}, {high}]。')
                row['values'][metric] = value
            if row['blockers_seeded'] is None:
                row['blockers_seeded'] = 0
            if row['blockers_detected'] is not None and not (0 <= row['blockers_detected'] <= row['blockers_seeded']):
                raise ValueError(f"第 {index} 行 blockers_detected={row['blockers_detected']} "
                                 f"超出 [0, {row['blockers_seeded']}]。")
            if row['human_preference'] not in ('', 'X', 'Y', 'no_meaningful_difference'):
                raise ValueError(f"第 {index} 行 human_preference 非法：{row['human_preference']!r}。")
            rows.append(row)
    return rows


def load_blind_map(map_path):
    if not map_path.is_file():
        raise FileNotFoundError(map_path)
    data = json.loads(map_path.read_text(encoding='utf-8'))
    index = {}
    for row in data.get('rows') or []:
        index[(row.get('case_id'), row.get('repetition'), row.get('blind_label'))] = row
    return data, index


def metric_value(row, metric):
    if metric == 'release_blocker_recall':
        seeded, detected = row['blockers_seeded'], row['blockers_detected']
        return (detected / seeded) if (seeded and detected is not None) else None
    return row['values'].get(metric)


def bootstrap_ci(samples, resamples, rng):
    """案等权重采样、最近秩 95% 置信区间；n<2 时退化为点估计并标注。"""
    n = len(samples)
    if n == 0:
        return None
    if n == 1:
        return {'low': samples[0], 'high': samples[0], 'degenerate': True, 'n_cases': 1}
    means = []
    for _ in range(resamples):
        total = 0.0
        for _ in range(n):
            total += samples[rng.randrange(n)]
        means.append(total / n)
    means.sort()
    return {'low': means[min(int(0.025 * resamples), resamples - 1)],
            'high': means[min(int(0.975 * resamples), resamples - 1)],
            'degenerate': False, 'n_cases': n}


def cmd_score(args):
    sheet_path = Path(args.score).expanduser()
    if not sheet_path.is_file():
        return fail(f'[待确认] 找不到评分表：{sheet_path}', 2)
    map_path = Path(args.blind_map).expanduser() if args.blind_map else sheet_path.parent / 'blind-map.json'
    try:
        rows = load_sheet(sheet_path)
    except ValueError as error:
        return fail(f'[违规] 评分表非法：{error}', 1)
    try:
        blind_map, map_index = load_blind_map(map_path)
    except FileNotFoundError:
        return fail(f'[待确认] 找不到盲映射：{map_path}（可用 --blind-map 指定）', 2)
    except json.JSONDecodeError as error:
        return fail(f'[待确认] 盲映射不是合法 JSON：{error}', 2)

    seed = int(args.seed if args.seed is not None else blind_map.get('seed') or DEFAULT_SEED)
    resamples = max(1, int(args.resamples))
    min_repetitions = int(blind_map.get('repetitions_per_case') or MIN_REPETITIONS)

    errors, warnings = [], []
    for row in rows:
        mapped = map_index.get((row['case_id'], row['repetition'], row['blind_label']))
        row['condition'] = mapped.get('condition') if mapped else None
        if row['condition'] not in ('A', 'B'):
            errors.append(f"第 {row['line']} 行 (case={row['case_id']}, r={row['repetition']}, "
                          f"label={row['blind_label']}) 无法解盲：{row['condition']!r}")
        if any(row['values'].get(metric) is not None for metric in (*RATING_METRICS, *RATE_METRICS)) and not row['reviewer_id']:
            warnings.append(f"第 {row['line']} 行已评分但缺 reviewer_id。")
    if errors:
        print(json.dumps({'mode': 'score', 'errors': errors}, ensure_ascii=False, indent=2), file=sys.stderr)
        return fail('[违规] 评分表与盲映射不一致。', 1)

    case_order = list(blind_map.get('cases') or [])
    for row in rows:
        if row['case_id'] not in case_order:
            case_order.append(row['case_id'])

    collected = {case_id: {'A': {metric: [] for metric in PRIMARY_METRICS},
                           'B': {metric: [] for metric in PRIMARY_METRICS}} for case_id in case_order}
    missing_rows = []
    for row in rows:
        bucket = collected[row['case_id']][row['condition']]
        scored = False
        for metric in PRIMARY_METRICS:
            value = metric_value(row, metric)
            if value is not None:
                bucket[metric].append(value)
                scored = True
        if not scored:
            missing_rows.append(row['sheet_row_id'])

    run_counts, insufficient = {}, []
    for case_id in case_order:
        counts = {condition: sum(1 for row in rows if row['case_id'] == case_id
                                 and row['condition'] == condition
                                 and any(metric_value(row, metric) is not None for metric in PRIMARY_METRICS))
                  for condition in ('A', 'B')}
        run_counts[case_id] = counts
        if counts['A'] < min_repetitions or counts['B'] < min_repetitions:
            insufficient.append({'case_id': case_id, 'A': counts['A'], 'B': counts['B'],
                                 'required': min_repetitions})

    per_case_report = {}
    for case_id in case_order:
        entry = {'n': {condition: len(collected[case_id][condition][PRIMARY_METRICS[0]]) for condition in ('A', 'B')},
                 'A': {}, 'B': {}, 'delta': {}}
        for metric in PRIMARY_METRICS:
            value_a = mean(collected[case_id]['A'][metric])
            value_b = mean(collected[case_id]['B'][metric])
            entry['A'][metric] = round_or_none(value_a)
            entry['B'][metric] = round_or_none(value_b)
            entry['delta'][metric] = round_or_none(None if (value_a is None or value_b is None) else value_b - value_a)
        per_case_report[case_id] = entry

    aggregate = {'A': {}, 'B': {}, 'delta': {}, 'delta_ci95': {}, 'paired_cases': {}}
    rng = random.Random(seed)
    for metric in PRIMARY_METRICS:
        a_means, b_means, deltas = [], [], []
        for case_id in case_order:
            values_a, values_b = collected[case_id]['A'][metric], collected[case_id]['B'][metric]
            if not values_a or not values_b:
                continue
            mean_a, mean_b = mean(values_a), mean(values_b)
            a_means.append(mean_a)
            b_means.append(mean_b)
            deltas.append(mean_b - mean_a)
        aggregate['A'][metric] = round_or_none(mean(a_means))
        aggregate['B'][metric] = round_or_none(mean(b_means))
        aggregate['delta'][metric] = round_or_none(mean(deltas))
        interval = bootstrap_ci(deltas, resamples, rng)
        aggregate['delta_ci95'][metric] = None if interval is None else {
            'low': round(interval['low'], 4), 'high': round(interval['high'], 4),
            'degenerate': interval['degenerate'], 'n_cases': interval['n_cases']}
        aggregate['paired_cases'][metric] = len(deltas)

    preference_raw = {'X': 0, 'Y': 0, 'no_meaningful_difference': 0, 'missing': 0}
    preference_unblinded = {'A': 0, 'B': 0, 'no_meaningful_difference': 0, 'missing': 0}
    conflicts = []
    for case_id in case_order:
        anchor = next((row for row in rows if row['case_id'] == case_id and row['pair_anchor']), None)
        values = [row['human_preference'] for row in rows
                  if row['case_id'] == case_id and row['human_preference']]
        if not values:
            preference_raw['missing'] += 1
            preference_unblinded['missing'] += 1
            continue
        if len(set(values)) > 1:
            conflicts.append({'case_id': case_id, 'values': sorted(set(values))})
        choice = values[0]
        preference_raw[choice] = preference_raw.get(choice, 0) + 1
        if choice == 'no_meaningful_difference':
            preference_unblinded['no_meaningful_difference'] += 1
        else:
            mapped = map_index.get((case_id, anchor['repetition'] if anchor else 1, choice)) if anchor else None
            condition = mapped.get('condition') if mapped else None
            if condition in ('A', 'B'):
                preference_unblinded[condition] += 1
            else:
                preference_unblinded['missing'] += 1

    # 主判据判定：先要求重复充分，再看 CI 是否排除可忽略效应。
    metric_verdicts, reasons = {}, []
    if insufficient:
        reasons.append(f"存在重复不足的案例（{len(insufficient)} 个，要求每案每条件 >= {min_repetitions} 次）："
                       + '，'.join(f"{item['case_id']}(A={item['A']},B={item['B']})" for item in insufficient))
    for metric in IMPROVE_METRICS + HARM_METRICS:
        interval = aggregate['delta_ci95'][metric]
        margin = NEGLIGIBLE_EFFECT[metric]
        if interval is None:
            metric_verdicts[metric] = {'claim': 'insufficient', 'margin': margin,
                                       'detail': '没有可比对的成对案例。'}
            reasons.append(f'{metric}：没有可比对的成对案例。')
            continue
        if interval['degenerate']:
            metric_verdicts[metric] = {'claim': 'insufficient', 'margin': margin,
                                       'detail': '成对案例数不足 2，无法给出区间。'}
            reasons.append(f'{metric}：成对案例数不足 2。')
            continue
        if metric in IMPROVE_METRICS:
            ok = interval['low'] > margin
            metric_verdicts[metric] = {
                'claim': 'improved' if ok else 'insufficient', 'margin': margin,
                'detail': f"CI 下界 {interval['low']:.4f} {'>' if ok else '<='} 可忽略阈值 {margin}",
            }
            if not ok:
                reasons.append(f"{metric} 的 95% CI [{interval['low']:.4f}, {interval['high']:.4f}] "
                               f"未排除可忽略效应（阈值 {margin}），不得声称提升。")
        else:
            ok = interval['high'] < margin
            metric_verdicts[metric] = {
                'claim': 'no_nonnegligible_increase' if ok else 'insufficient', 'margin': margin,
                'detail': f"CI 上界 {interval['high']:.4f} {'<' if ok else '>='} 可忽略阈值 {margin}",
            }
            if not ok:
                reasons.append(f"{metric} 的 95% CI [{interval['low']:.4f}, {interval['high']:.4f}] "
                               f"未排除非可忽略上升（阈值 {margin}），不得声称未恶化。")
    claimed = not reasons
    verdict_line = (
        '判定：在本样本上，B 的 release-blocker recall 与 evidence grounding 的 95% CI 均排除可忽略效应，'
        '且 false-positive rate 与 unsupported-claim rate 均未出现非可忽略上升——仅支持“本样本内 B 更优”，'
        '不构成普遍结论，也不代表已发布可用。'
        if claimed else
        '判定：证据不足，不得声称 B 提升或未恶化。原因：' + '；'.join(reasons)
    )

    print(json.dumps({
        'mode': 'score',
        'sheet': str(sheet_path),
        'blind_map': str(map_path),
        'seed': seed,
        'resamples': resamples,
        'metric_names': METRIC_NAMES,
        'run_counts': {
            'sheet_rows': len(rows),
            'scored_rows': len(rows) - len(missing_rows),
            'per_case_condition': run_counts,
            'min_repetitions': min_repetitions,
            'insufficient_repetitions': insufficient,
            'rows_without_scores': missing_rows,
            'warnings': warnings,
        },
        'per_case': per_case_report,
        'aggregate': aggregate,
        'human_preference': {'raw_labels': preference_raw, 'unblinded': preference_unblinded,
                             'conflicts': conflicts,
                             'note': '偏好按案例计（写在 pair_anchor=1 行）；raw 为 X/Y 盲标签计数，unblinded 为解盲后的 A/B 计数。'},
        'verdict': {
            'criterion': 'B 提升 release-blocker recall 与 evidence grounding，且不提高 false-positive rate 与 unsupported-claim rate',
            'negligible_effect_margins': NEGLIGIBLE_EFFECT,
            'metrics': metric_verdicts,
            'reasons': reasons,
            'claimed': claimed,
            'line': verdict_line,
        },
        'limitations': [
            '只分析人工回填的评分表；不产生输出，不调用模型，不证明任何因果。',
            'bootstrap 为案等权重配对重采样（最近秩 95% CI），样本是案例而非运行；案例数少时区间极宽。',
            '若每案每条件有效重复 < 3，判定强制为“证据不足”。',
            'human preference 仅按案例计数，不做显著性检验。',
        ],
    }, ensure_ascii=False, indent=2))
    return 0


# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        prog='run_ab_benchmark.py',
        description='archebase-visual-design A/B 基准 harness（--plan 准备运行 / --validate 校验结果 / --score 汇总评分）。'
                    '只读、确定性、无网络、不调用模型。',
        epilog=EXIT_CODES_TEXT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--plan', action='store_true',
                      help='读取案例文件，输出运行清单、逐次渲染提示词、盲评分表与盲映射到 --out（退出码 0/1/2）')
    mode.add_argument('--validate', metavar='DIR',
                      help='按协议必填字段校验结果目录：单一基线、逐案配对、多图规则、盲表/盲映射（退出码 0/1/2/3）')
    mode.add_argument('--score', metavar='SHEET.csv',
                      help='读取已填写的盲评分表，输出逐案/汇总均值、bootstrap 区间与主判据判定（退出码 0/1/2）')
    parser.add_argument('--out', help='--plan 的输出目录（只在此目录内写文件）')
    parser.add_argument('--cases', default=str(DEFAULT_CASE_FILE), help=f'案例文件；默认 {DEFAULT_CASE_FILE}')
    parser.add_argument('--upstream', help='上游 VI Guide 目录；默认 ARCHEBASE_VI_GUIDE 或同级 archebase-vi-guide')
    parser.add_argument('--assets', help='可选：解析案例 image_files 的根目录')
    parser.add_argument('--seed', type=int, default=None, help=f'随机种子（默认 {DEFAULT_SEED}；--score 时默认取盲映射内的 seed）')
    parser.add_argument('--repetitions', type=int, default=None, help='每案每条件重复次数；默认取案例文件 repetitions_per_case')
    parser.add_argument('--model-id', default=None, help='写入清单的模型标识；默认占位符')
    parser.add_argument('--model-version', default=None, help='写入清单的模型版本；默认占位符')
    parser.add_argument('--blind-map', default=None, help='--score 的盲映射；默认取评分表同目录的 blind-map.json')
    parser.add_argument('--resamples', type=int, default=DEFAULT_RESAMPLES, help=f'bootstrap 重采样次数（默认 {DEFAULT_RESAMPLES}）')
    parser.add_argument('--force', action='store_true', help='--plan 覆盖已存在的输出目录')
    args = parser.parse_args()

    if args.plan:
        return cmd_plan(args)
    if args.validate:
        return cmd_validate(args)
    return cmd_score(args)


if __name__ == '__main__':
    sys.exit(main())
