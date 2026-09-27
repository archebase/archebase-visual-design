#!/usr/bin/env python3
"""archebase-visual-design 直接回归基准：检索（query.py）+ 设计空间（jspace.py）。

只读：不写回 Design IR store，不修改本 Skill 的任何文件。
每个案例都会报告候选池大小（pool）与可证伪性；池不足的案例不计分并计入 integrity_failures。
"""
import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
SKILL_DIR = EVALS_DIR.parent
DEFAULT_CASE_FILE = EVALS_DIR / 'visual-design-benchmark.json'
STORE_DIRNAME = 'archebase-design-ir'
STORE_REQUIRED = ('query.py', 'jspace.py', 'axes.json')
STORE_INDEX = 'design_ir.sqlite3'  # 构建产物：clone 后需先跑 build_index.py
DIST_TOL = 5e-5  # jspace.py 报告的 distance 只保留 4 位小数


def store_candidates(cli_path):
    """按顺序返回候选 store：(来源说明, 路径)。不含机器绝对路径默认值。"""
    out = []
    if cli_path:
        out.append(('--store', Path(cli_path).expanduser()))
    env = os.environ.get('ARCHEBASE_DESIGN_IR')
    if env:
        out.append(('env ARCHEBASE_DESIGN_IR', Path(env).expanduser()))
    roots = [
        ('Skill 目录', SKILL_DIR),
        ('Skill 上级目录', SKILL_DIR.parent),
        ('Skill 上级目录的上级', SKILL_DIR.parent.parent),
        ('$HOME', Path.home()),
        ('$HOME/Books', Path.home() / 'Books'),
    ]
    for label, root in roots:
        if root.name == STORE_DIRNAME:
            out.append((f'{label}本身 {root}', root))
        out.append((f'{label} 下的 {STORE_DIRNAME}（{root}）', root / STORE_DIRNAME))
    return out


def resolve_store(cli_path):
    tried = []
    for label, path in store_candidates(cli_path):
        if path.is_dir() and all((path / f).is_file() for f in STORE_REQUIRED):
            return path, label, tried
        tried.append(f'{label}（{"不存在" if not path.is_dir() else "缺少 " + "/".join(STORE_REQUIRED)}）')
    return None, None, tried


def die_unresolved(kind, tried, env_var, hint):
    print(f'[待确认] 未解析到 {kind}。', file=sys.stderr)
    print(f'  缺少 {kind} 时不得用记忆或臆造数据替代。', file=sys.stderr)
    print('  已尝试：', file=sys.stderr)
    for item in tried:
        print(f'    - {item}', file=sys.stderr)
    print(f'  修复：export {env_var}=<路径>，或把 {hint} 放在上述同级目录之一。', file=sys.stderr)
    raise SystemExit(2)


def run_json(cmd, cwd):
    proc = subprocess.run(cmd, text=True, capture_output=True, cwd=str(cwd))
    if proc.returncode != 0:
        raise RuntimeError(f'{cmd}\nexit={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}')
    return json.loads(proc.stdout)


def query_ids(store, case, limit):
    cmd = [sys.executable, str(store / 'query.py'), case['query'], '--limit', str(limit)]
    if case.get('channel'):
        cmd += ['--channel', case['channel']]
    if case.get('kind'):
        cmd += ['--kind', case['kind']]
    if case.get('exclude_kind'):
        for kind in case['exclude_kind']:
            cmd += ['--exclude-kind', kind]
    result = run_json(cmd, store)
    return [row['id'] for row in result.get('results', [])]


def evaluate_retrieval(case, store, k, pool_limit):
    k = int(case.get('k', k)) if k is None else int(k)
    expect = case.get('expect_within_k') or []
    forbidden = case.get('must_not_be_first') or []
    top_k = query_ids(store, case, k)
    pool_ids = query_ids(store, case, pool_limit)
    pool = len(pool_ids)
    rank_in_pool = {item: pool_ids.index(item) + 1 for item in (expect + forbidden) if item in pool_ids}
    ranks = [top_k.index(item) + 1 for item in expect if item in top_k]
    first_rank = min(ranks) if ranks else None

    assertions = []
    if expect:
        assertions.append({
            'assertion': 'expect_within_k',
            'pass': bool(ranks),
            'detail': {'expected': expect, 'first_rank': first_rank, 'ranks_in_pool': rank_in_pool},
        })
    if forbidden:
        top = pool_ids[0] if pool_ids else None
        assertions.append({
            'assertion': 'must_not_be_first',
            'pass': top not in forbidden,
            'detail': {'forbidden': forbidden, 'top': top},
        })

    discrimination_rule = 'pool > k' if expect else 'pool >= 2'
    discriminating = pool > k if expect else pool >= 2
    passed = all(item['pass'] for item in assertions) and bool(assertions)
    known_failing = bool(case.get('known_failing'))
    return {
        'id': case['id'],
        'intent': case.get('intent', ''),
        'query': case['query'],
        'channel': case.get('channel', ''),
        'kind_filter': case.get('kind'),
        'k': k,
        'pool': pool,
        'discrimination_rule': discrimination_rule,
        'discriminating': discriminating,
        'status': 'pass' if passed else 'fail',
        'unexpected': (not passed) and not known_failing,
        'known_failing': known_failing,
        'expected_failure_observed': (not passed) and known_failing,
        'improvement': passed and known_failing,
        'first_rank': first_rank,
        'first_rank_in_pool': min(rank_in_pool[item] for item in expect) if any(i in rank_in_pool for i in expect) else None,
        'reciprocal_rank': round(1.0 / first_rank, 4) if first_rank else (0.0 if expect else None),
        'expected_ranks_in_pool': rank_in_pool,
        'top_k': top_k,
        'assertions': assertions,
        'note': case.get('note', ''),
    }


def expected_distance(vector, target):
    """复现 jspace.py 的距离语义：单目标用绝对差，多目标用目标轴上的欧氏距离。"""
    if len(target) == 1:
        axis, value = next(iter(target.items()))
        return abs(float(vector.get(axis, 0.0)) - float(value))
    return math.sqrt(sum((float(vector.get(axis, 0.0)) - float(value)) ** 2 for axis, value in target.items()))


def evaluate_jspace(case, store, k, pool_limit, axes):
    k = int(case.get('k', k)) if k is None else int(k)
    axis_ids = [axis['id'] for axis in axes['axes']]
    coords = axes['coordinates']
    args = list(case.get('args') or [])
    top = run_json([sys.executable, str(store / 'jspace.py'), *args, '--limit', str(k)], store)
    full = run_json([sys.executable, str(store / 'jspace.py'), *args, '--limit', str(pool_limit)], store)
    rows = top.get('results', [])
    all_rows = full.get('results', [])
    ranking = [row['id'] for row in all_rows]
    pool = full.get('count', 0)
    target = top.get('target', {})

    unknown = [row['id'] for row in all_rows if row['id'] not in coords]
    incomplete = [row['id'] for row in all_rows if set(row.get('coordinates', {})) != set(axis_ids)]
    coord_mismatch = [row['id'] for row in all_rows if row.get('coordinates') != coords.get(row['id'])]
    dist_mismatch = []
    for row in rows:
        if row['id'] not in coords:
            continue
        want = expected_distance(coords[row['id']], target)
        if abs(float(row['distance']) - want) > DIST_TOL:
            dist_mismatch.append({'id': row['id'], 'reported': row['distance'], 'recomputed': round(want, 6)})
    distances = [float(row['distance']) for row in rows]
    ordered = all(distances[i] <= distances[i + 1] + DIST_TOL for i in range(len(distances) - 1))

    pairs = []
    for pair in case.get('pairwise') or []:
        higher, lower = pair['higher'], pair['lower']
        if higher in ranking and lower in ranking:
            ok = ranking.index(higher) < ranking.index(lower)
            detail = {'higher_rank': ranking.index(higher) + 1, 'lower_rank': ranking.index(lower) + 1}
        else:
            ok = False
            detail = {'missing': [x for x in (higher, lower) if x not in ranking]}
        pairs.append({'higher': higher, 'lower': lower, 'pass': ok, 'reason': pair.get('reason', ''), 'detail': detail})

    invariants = [
        {'assertion': 'returned_ids_known_in_axes_json', 'pass': not unknown, 'detail': {'unknown': unknown}},
        {'assertion': 'vector_complete_over_all_axes', 'pass': not incomplete, 'detail': {'axes': axis_ids, 'incomplete': incomplete}},
        {'assertion': 'coordinates_match_axes_json', 'pass': not coord_mismatch, 'detail': {'mismatch': coord_mismatch}},
        {'assertion': 'distance_matches_jspace_semantics', 'pass': not dist_mismatch, 'detail': {'mismatch': dist_mismatch, 'target': target}},
        {'assertion': 'distance_order_nonincreasing', 'pass': ordered, 'detail': {'distances': distances}},
        {'assertion': 'count_equals_min_k_pool', 'pass': top.get('count') == min(k, pool), 'detail': {'count': top.get('count'), 'k': k, 'pool': pool}},
        {'assertion': 'pool_ge_2', 'pass': pool >= 2, 'detail': {'pool': pool}},
    ]
    passed = all(item['pass'] for item in invariants + pairs)
    return {
        'id': case['id'],
        'intent': case.get('intent', ''),
        'args': args,
        'k': k,
        'target': target,
        'pool': pool,
        'discriminating': pool >= 2,
        'status': 'pass' if passed else 'fail',
        'unexpected': not passed,
        'top_k': [{'id': row['id'], 'distance': row['distance']} for row in rows],
        'invariants': invariants,
        'pairwise': pairs,
        'note': case.get('note', ''),
    }


def main():
    parser = argparse.ArgumentParser(description='archebase-visual-design 直接回归基准（检索 + 设计空间）')
    parser.add_argument('--cases', default=str(DEFAULT_CASE_FILE))
    parser.add_argument('--k', type=int, default=None, help='覆盖案例文件中的 k 默认值；池 ≤ k 的案例会被报告为不可证伪')
    parser.add_argument('--store', default=None, help='Design IR store 路径；默认读 ARCHEBASE_DESIGN_IR 或同级目录')
    parser.add_argument('--strict', action='store_true',
                        help='状态为 FAIL 时退出码为 1（默认始终 0，只报告）；PASS_WITH_KNOWN_FAILURES 不算失败')
    args = parser.parse_args()

    store, label, tried = resolve_store(args.store)
    if store is None:
        die_unresolved('Design IR store', tried, 'ARCHEBASE_DESIGN_IR', STORE_DIRNAME)
    index = store / STORE_INDEX
    if not index.is_file() or index.stat().st_size == 0:
        print(f'[待确认] store 索引未生成：{index}', file=sys.stderr)
        print(f'  索引是构建产物（仓库 https://github.com/archebase/archebase-design-ir 不随包分发），'
              f'先运行：python3 {store / "build_index.py"}', file=sys.stderr)
        raise SystemExit(2)

    case_path = Path(args.cases)
    if not case_path.is_file():
        print(f'[待确认] 案例文件不存在：{case_path}', file=sys.stderr)
        raise SystemExit(2)
    data = json.loads(case_path.read_text(encoding='utf-8'))
    default_k = int(data.get('k_default', 5))
    k = args.k  # None 表示使用案例文件里的 k / k_default
    pool_limit = int(data.get('pool_limit', 1000))
    axes = json.loads((store / 'axes.json').read_text(encoding='utf-8'))
    cases = data['cases']

    try:
        retrieval = [evaluate_retrieval(case, store, k if k is not None else default_k, pool_limit) for case in cases['retrieval']]
        jspace = [evaluate_jspace(case, store, k if k is not None else default_k, pool_limit, axes) for case in cases['jspace']]
    except RuntimeError as error:
        print(f'[待确认] Design IR store 调用失败；不得凭记忆替代：\n{error}', file=sys.stderr)
        raise SystemExit(2)

    positives = [row for row in retrieval if row['discriminating'] and any(a['assertion'] == 'expect_within_k' for a in row['assertions'])]
    decoys = [row for row in retrieval if row['discriminating'] and any(a['assertion'] == 'must_not_be_first' for a in row['assertions'])]
    non_discriminating = [row['id'] for row in retrieval if not row['discriminating']]
    regressions = [row['id'] for row in retrieval if row['unexpected']] + [row['id'] for row in jspace if row['unexpected']]
    jspace_failures = [row['id'] for row in jspace if row['status'] == 'fail']
    integrity_failures = non_discriminating + [row['id'] for row in jspace if not row['discriminating']]

    known_failing_observed = [row['id'] for row in retrieval if row['expected_failure_observed']]

    def mean(values):
        return round(sum(values) / len(values), 4) if values else None

    output = {
        'benchmark': data['benchmark'],
        'skill': data['skill'],
        'store': {'path': str(store), 'resolved_from': label, 'required_files': list(STORE_REQUIRED)},
        'k_default': default_k,
        'k_override': k,
        'pool_limit': pool_limit,
        'status': ('FAIL' if (regressions or integrity_failures or jspace_failures)
                   else ('PASS_WITH_KNOWN_FAILURES' if known_failing_observed else 'PASS')),
        'metrics': {
            'retrieval_cases': len(retrieval),
            'scored_positive_cases': len(positives),
            'hit_at_k': mean([1.0 if row['first_rank'] else 0.0 for row in positives]),
            'mrr_at_k': mean([row['reciprocal_rank'] for row in positives]),
            'decoy_cases': len(decoys),
            'decoy_pass_rate': mean([1.0 if all(a['pass'] for a in row['assertions'] if a['assertion'] == 'must_not_be_first') else 0.0 for row in decoys]),
            'jspace_cases': len(jspace),
            'jspace_pass_rate': mean([1.0 if row['status'] == 'pass' else 0.0 for row in jspace]),
            'known_failing_cases': known_failing_observed,
            'improvements': [row['id'] for row in retrieval if row['improvement']],
            'regressions': regressions,
            'non_discriminating_cases': non_discriminating,
            'integrity_failures': integrity_failures,
        },
        'retrieval': retrieval,
        'jspace': jspace,
        'limitations': [
            '直接应用层回归，不是 with/without 因果对比，也不证明任何效果提升。',
            '语料只有 12 条记录（其中 case 记录 status=proposed、anti_pattern 记录 1 条）；排序由 query.py 的字符/词项重叠 + bm25 决定，不是 embedding 语义检索。',
            '查询是开发期构造的，接近记录原文；pool 逐案报告，池 ≤ k 的案例不计分（计入 integrity_failures），因此 hit@k 高只说明排序在这些查询上未失败。',
            'hit_at_k 在当前语料上已饱和（多为 1.0）；可证伪信号来自 per-case first_rank/MRR、反例（must_not_be_first）与 integrity_failures。',
            '不度量人类视觉质量、渲染产物、上游 VI Guide 正确性或字体/Logo 渲染。',
            'known_failing 标记的案例是当前已知缺陷（见各案例 note），失败可复现；它们从 pass 翻转为 fail 才算 regression。',
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if args.strict and output['status'] == 'FAIL':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
