#!/usr/bin/env python3
"""校验本 Skill 重述的品牌事实与上游 archebase-vi-guide 一致。

只读、确定性、无网络：不修改任何文件，不联网，不依赖外部包。
上游目录由 ARCHEBASE_VI_GUIDE 环境变量解析，否则按同级/上级/$HOME 候选目录查找；
解析不到时以 `待确认` 停止（退出码 2），不得凭记忆替代。

用法（在 Skill 根目录）：
    python3 evals/check_brand_facts.py
    python3 evals/check_brand_facts.py --upstream /path/to/archebase-vi-guide --skill .
退出码：0 = 无分歧；1 = 存在分歧（逐项表格见输出）；2 = 上游不可达（待确认）。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
SKILL_DIR = EVALS_DIR.parent
SELF = Path(__file__).resolve()
CANONICAL = 'references/brand-system.md'
UPSTREAM_DIRNAME = 'archebase-vi-guide'
UPSTREAM_REQUIRED = (
    'tokens/archebase.tokens.json',
    'assets/guide-evidence.json',
    'references/visual-grammar.md',
    'references/asset-governance.md',
    # v3.5.5/v3.5.10 起才有：资产实测的 Logo 运营规则与授权组合矩阵。
    # 列入完整性门槛后，v3.5.4 及更早的本地副本会因缺文件被判身份不符，而不是被当成权威。
    'references/logo-usage-rules.md',
    'references/logo-combination-matrix.md',
)
SCAN_SUFFIXES = ('.md', '.json', '.yaml', '.yml')

HEX = re.compile(r'#[0-9A-Fa-f]{6}\b')
NON_BRAND_SOURCE = re.compile(r'(assets/[A-Za-z0-9_.-]+|scripts/[A-Za-z0-9_.-]+|https?://|渠道实现|渠道仓库|渠道 CSS)')
TOKEN_HEX_RATIO = re.compile(r'`?(AB_BLUE_[0-9])`?[^0-9%\n]{0,14}?([0-9]{1,3})\s?%')
WRONG_NAME = re.compile(r'(?<![A-Za-z0-9_])(Archebase|ARCHEBASE|Arche\s+Base|Arche-Base|Arche_base|ArcheBaseAI)(?![A-Za-z0-9_])')
WRONG_DOMAIN = re.compile(r'(?<![A-Za-z0-9_/])(Archebase|ARCHEBASE|Arche-Base)\.(?:com|cn|io|ai|dev|org|co)\b')
CODE_SPAN_TECHNICAL = re.compile(r'`[^`]*(?:[/:@]|\.[A-Za-z]{2,6}\b|_[A-Z])[^`]*`')
# 用法/提及区分：否定语句里列举的“未批准写法”是示例，不是品牌声明
NAME_MENTION_ONLY = re.compile(r'未批准|不得使用|禁止使用|错误写法|违例|forbidden')
NAME_ASSERTION = re.compile(r'(公开名称|批准名称|public\s+name)[^。\n]{0,16}(?:必须|应为|是|为)\s*`?(?:Archebase|ARCHEBASE|Arche\s+Base|Arche-Base|Arche_base|ArcheBaseAI)')
EVIDENCE_REF = re.compile(r'\b(?:id|evidence)\s+`([A-Za-z][A-Za-z0-9_.-]*)`')
PAGES = re.compile(r'\bp{1,2}\.\s*([0-9][0-9,、/\-]*)')
LOGO_WORD = r'(?:logo|标志|图形标|clear\s?space|minimum\s+size|最小尺寸)'
METRIC = r'[0-9]+(?:\.[0-9]+)?\s?(?:px|mm|dp|pt|em|×\s*图形标)'
# 只有与 Logo 语境同现的数值才算“臆造 Logo 度量”：印刷版心安全区、最小字号等不属于此
LOGO_METRIC = re.compile(rf'(?:{LOGO_WORD}[^。\n]{{0,40}}{METRIC})|(?:{METRIC}[^。\n]{{0,40}}{LOGO_WORD})', re.I)
# Logo 运营规则（资产实测，非 Guide 条文）：出现数值时必须在同一行指到上游规则文件
OPERATING_REF = re.compile(r'references/logo-(?:usage-rules\.md|combination-matrix\.(?:md|json))')
# 把资产实测规则写成 Guide 条文才算冒充；同一行是否定表述（不得/不是/未定义等）则不算
GUIDE_DEFINES = re.compile(r'(?:VI\s*Guide|Guide)\s*(?:规定|定义|要求|明确|条文)|Guide\s*p{1,2}\.\s*[0-9]')
ATTRIBUTION_NEGATED = re.compile(r'不得|禁止|不是|并非|未定义|而非|no Guide|not\s+defined', re.I)
# 描述规则本身的行（例如「Guide 只列 5 种形式」「没有 Guide 页面证据」）不是冒充，也要放行
COLOUR_NEGATED = re.compile(r'不得|禁止|不是|并非|而非|没有|只列|本地增补|owner\s*签发|签发范围|no Guide', re.I)
SIXTH_COLOUR = '黑色渐变'
CSS_WEIGHT = re.compile(r'font-weight\s*:?\s*[0-9]{3}')

def add(status, item, expected, found, where=''):
    """构造一行检查结果：(判定, 项, 上游（来源）, 本 Skill, 位置)。"""
    return (status, item, expected, found, where)


# ---------------------------------------------------------------- upstream

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


def resolve_upstream(cli_path, pin_commit=None):
    """选完整候选；若给了 pin，优先选身份与 pin 一致的候选，其次才用第一个完整候选。

    本地 clone 只是缓存，身份必须可核对：同机可能存在旧副本（例如 /tmp 下的历史导出），
    不能因为它在候选顺序里靠前就当作权威。
    """
    tried = []
    complete = []
    for label, path in upstream_candidates(cli_path):
        if path.is_dir() and all((path / name).is_file() for name in UPSTREAM_REQUIRED):
            complete.append((label, path))
            continue
        if path.is_dir():
            missing = [name for name in UPSTREAM_REQUIRED if not (path / name).is_file()]
            tried.append(f'{label}（缺少 {", ".join(missing)}）')
        else:
            tried.append(f'{label}（不存在）')
    if not complete:
        return None, None, tried
    if pin_commit:
        for label, path in complete:
            head, _ = upstream_identity(path)
            if head == pin_commit:
                return path, label, tried
        tried = [f'{label}（完整但身份与 pin 不一致）' for label, _ in complete] + tried
    label, path = complete[0]
    return path, label, tried


def die_unresolved(tried):
    print('[待确认] 未解析到上游 archebase-vi-guide。', file=sys.stderr)
    print('  品牌事实以上游为准；上游不可达时不得凭记忆或臆造数值通过校验。', file=sys.stderr)
    print('  已尝试：', file=sys.stderr)
    for item in tried:
        print(f'    - {item}', file=sys.stderr)
    print('  修复：export ARCHEBASE_VI_GUIDE=<archebase-vi-guide 路径> 后重试。', file=sys.stderr)
    raise SystemExit(2)


def load_upstream(path):
    tokens = json.loads((path / 'tokens/archebase.tokens.json').read_text(encoding='utf-8'))
    evidence = json.loads((path / 'assets/guide-evidence.json').read_text(encoding='utf-8'))
    grammar = (path / 'references/visual-grammar.md').read_text(encoding='utf-8').splitlines()
    governance = (path / 'references/asset-governance.md').read_text(encoding='utf-8')
    by_id = {item['id']: item for item in evidence['evidence']}
    typed = tokens['type']
    facts = {
        'colors': {key: value.upper() for key, value in tokens['colors'].items()},
        'ratio_map': tokens['color_ratio']['mapping_percent'],
        'ratio_total': tokens['color_ratio']['labeled_percent_total'],
        'ratio_unmapped': tokens['color_ratio']['unmapped_percent'],
        'neutral_base': by_id['neutral.background']['base_hex'].upper(),
        'neutral_background': tokens['neutral_levels']['background_percent'],
        'neutral_text': tokens['neutral_levels']['text_percent'],
        'type_zh': typed['zh'],
        'type_latin': typed['latin'],
        'weights_zh': typed['displayed_weights']['zh'],
        'weights_latin': typed['displayed_weights']['latin'],
        'evidence': by_id,
        'unconfirmed': tokens['unconfirmed'],
    }
    rules_text = (path / 'references/logo-usage-rules.md').read_text(encoding='utf-8')
    facts['operational'] = evidence.get('operational_rules') or {}
    first_line = rules_text.splitlines()[0] if rules_text else ''
    facts['operating_rules_header_signed'] = bool(re.search(r'已签发', first_line))
    name = re.search(r'approved public `([^`]+)`', governance)
    facts['approved_name'] = name.group(1) if name else None
    # 上游自洽性：visual-grammar 的 token 行必须与 tokens json 一致
    grammar_tokens = {}
    for line in grammar:
        match = re.match(r'-\s+`(AB_[A-Z_0-9]+)`\s+`(#[0-9A-Fa-f]{6})`', line.strip())
        if match:
            grammar_tokens[match.group(1)] = match.group(2).upper()
    return facts, grammar_tokens


# ---------------------------------------------------------------- skill scan

def scanned_files(skill_dir):
    out = []
    for path in sorted(skill_dir.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if '.git' in path.parts or path.resolve() == SELF:
            continue
        out.append(path)
    return out


def lines_of(path):
    return path.read_text(encoding='utf-8').splitlines()


def strip_code_and_urls(line):
    """去掉 URL/路径/环境变量/标识符，保留纯文字与 `ArcheBase` 这类名称字面量。"""
    line = re.sub(r'https?://\S+', 'URL', line)
    line = re.sub(r'[A-Za-z0-9_.-]+\.[a-z]{2,}(?:/\S*)?', 'URL', line)
    return CODE_SPAN_TECHNICAL.sub('`code`', line)


def read_skill(skill_dir):
    docs = {}
    for path in scanned_files(skill_dir):
        rel = path.relative_to(skill_dir).as_posix()
        docs[rel] = lines_of(path)
    return docs


def page_numbers(line):
    pages = []
    for raw in PAGES.findall(line):
        for chunk in re.split(r'[、,/]', raw):
            chunk = chunk.strip()
            if not chunk:
                continue
            if '-' in chunk:
                start, _, end = chunk.partition('-')
                if start.isdigit() and end.isdigit():
                    pages.extend(range(int(start), int(end) + 1))
            elif chunk.isdigit():
                pages.append(int(chunk))
    return pages


# ---------------------------------------------------------------- checks

def check_upstream_self_consistency(facts, grammar_tokens, rows):
    for token, hex_value in sorted(facts['colors'].items()):
        if token not in grammar_tokens:
            rows.append(add('WARN', f'upstream:{token}', f'tokens json {hex_value}', 'visual-grammar.md 未列出该 token', 'visual-grammar.md:5-8'))
        elif grammar_tokens[token] != hex_value:
            rows.append(add('WARN', f'upstream:{token}', f'tokens json {hex_value}', f'visual-grammar.md {grammar_tokens[token]}', 'visual-grammar.md:5-8'))


def check_hexes(docs, facts, rows):
    token_hexes = set(facts['colors'].values())
    seen = {}
    for rel, lines in sorted(docs.items()):
        for number, line in enumerate(lines, 1):
            for match in HEX.finditer(line):
                value = match.group(0).upper()
                if value in token_hexes:
                    continue
                attributed = bool(NON_BRAND_SOURCE.search(line))
                brand_claim = bool(re.search(r'白色|token|色板|品牌|色彩角色|主色', line))
                seen.setdefault(value, []).append((rel, number, attributed, brand_claim))
    for value, places in sorted(seen.items()):
        unattributed = [f'{rel}:{number}' for rel, number, attributed, _ in places if not attributed]
        attributed = [f'{rel}:{number}' for rel, number, attributed, _ in places if attributed]
        if unattributed:
            rows.append(add('FAIL', f'hex:{value}', f'上游 token 只有 {", ".join(sorted(token_hexes))}',
                            '该色值不见于上游，且本行未声明渠道/非品牌来源', ', '.join(unattributed)))
        canonical_claim = [f'{rel}:{number}' for rel, number, _, brand_claim in places if rel == CANONICAL and brand_claim]
        if canonical_claim:
            rows.append(add('FAIL', f'hex:{value}:canonical', '唯一品牌事实重述处只能出现上游 token',
                            '本文件以品牌色板口径出现该非上游色值', ', '.join(canonical_claim)))
        elif attributed:
            rows.append(add('WARN', f'hex:{value}', '不属于上游品牌 token',
                            '已标注为非品牌来源（渠道实现等），非品牌 token', ', '.join(attributed)))


def check_token_table(docs, facts, rows):
    canonical = docs.get(CANONICAL)
    if canonical is None:
        rows.append(add('FAIL', 'canonical_file', CANONICAL, '文件缺失', CANONICAL))
        return
    text = '\n'.join(canonical)
    for token, value in sorted(facts['colors'].items()):
        pair = re.search(rf'{token}`?[^|\n]{{0,8}}\|?\s*`?(#[0-9A-Fa-f]{{6}})', text)
        if f'{token}' not in text:
            rows.append(add('FAIL', f'token:{token}', f'{token} {value}', '本 Skill 未重述该 token', CANONICAL))
        elif pair is None:
            rows.append(add('FAIL', f'token:{token}', f'{token} {value}', '找不到 token 与色值的配对声明', CANONICAL))
        elif pair.group(1).upper() != value:
            rows.append(add('FAIL', f'token:{token}', f'{token} {value}', f'本 Skill 写作 {pair.group(1).upper()}', CANONICAL))
        else:
            rows.append(add('OK', f'token:{token}', f'{token} {value}', f'{pair.group(1).upper()}', CANONICAL))
    five = re.search(r'(五个|5\s?个)\s*token', text)
    no_white = re.search(r'(没有|不含|无|不存在)\s*白色', text)
    if five and no_white:
        rows.append(add('OK', 'palette_cardinality', '色板只有五个 token 且无白色 token', '已声明', CANONICAL))
    else:
        rows.append(add('FAIL', 'palette_cardinality', '必须声明色板只有五个 token 且没有白色 token',
                        f'命中五个 token= {bool(five)}；命中白色否定= {bool(no_white)}', CANONICAL))


def check_ratio(docs, facts, rows):
    canonical = docs.get(CANONICAL, [])
    text = '\n'.join(canonical)
    missing = []
    for token, percent in sorted(facts['ratio_map'].items(), key=lambda item: item[0]):
        found = re.search(rf'{token}`?[^0-9%\n]{{0,14}}?{percent}\s?%', text)
        if found:
            continue
        missing.append(f'{token}={percent}%')
    if missing:
        rows.append(add('FAIL', 'ratio_map', '、'.join(f'{t} {p}%' for t, p in sorted(facts['ratio_map'].items())),
                        f'本 Skill 未按上游标注：{", ".join(missing)}', CANONICAL))
    else:
        rows.append(add('OK', 'ratio_map', '、'.join(f'{t} {p}%' for t, p in sorted(facts['ratio_map'].items())),
                        '逐项一致', CANONICAL))

    for token, percent in sorted(facts['ratio_map'].items(), key=lambda item: item[0]):
        for rel, lines in sorted(docs.items()):
            for number, line in enumerate(lines, 1):
                for match in TOKEN_HEX_RATIO.finditer(line):
                    if match.group(1) == token and int(match.group(2)) != percent:
                        rows.append(add('FAIL', f'ratio:{token}', f'{token} {percent}%',
                                        f'{match.group(2)}%', f'{rel}:{number}'))

    total = f'{facts["ratio_total"]}%'
    unmapped = f'{facts["ratio_unmapped"]}%'
    has_total = total in text
    has_unmapped = unmapped in text and re.search(r'未指派|未在 Guide|不得自行分配|不得分配', text)
    if has_total and has_unmapped:
        rows.append(add('OK', 'ratio_total_and_unmapped', f'标注合计 {total}，剩余 {unmapped} 未指派', '已声明', CANONICAL))
    else:
        rows.append(add('FAIL', 'ratio_total_and_unmapped', f'标注合计 {total}，剩余 {unmapped} 未指派',
                        f'合计={has_total}；未指派表述={bool(has_unmapped)}', CANONICAL))


def check_neutral(docs, facts, rows):
    canonical = docs.get(CANONICAL, [])
    text = '\n'.join(canonical)
    base = facts['neutral_base']
    allowed = {str(value) for value in facts['neutral_background'] + facts['neutral_text']}
    background_ok = all(f'{value}%' in text for value in facts['neutral_background'])
    text_ok = all(f'{value}%' in text for value in facts['neutral_text'])
    if background_ok and text_ok:
        rows.append(add('OK', 'neutral_levels', f'{base} 背景 {facts["neutral_background"]}%，文字 {facts["neutral_text"]}%',
                        '已声明', CANONICAL))
    else:
        rows.append(add('FAIL', 'neutral_levels', f'{base} 背景 {facts["neutral_background"]}%，文字 {facts["neutral_text"]}%',
                        f'背景档位={background_ok}；文字档位={text_ok}', CANONICAL))
    percents_in_window = re.compile(r'([0-9]{1,3})\s?%')
    for rel, lines in sorted(docs.items()):
        for number, line in enumerate(lines, 1):
            if base not in line.upper():
                continue
            # 只看紧跟在基准色值后的档位描述，避免把同一行里其他 token 的比例算进来
            invalid = []
            for match in re.finditer(re.escape(base), line, re.IGNORECASE):
                window = re.split(r'[；。—]|）|\)|；', line[match.end():match.end() + 48])[0]
                invalid.extend(value for value in percents_in_window.findall(window) if value not in allowed)
            if not invalid:
                continue
            context = bool(re.search(r'中性|档位|级|level', line))
            rows.append(add('FAIL' if context else 'WARN', f'neutral_percent:{invalid[0]}%',
                            f'{base} 只确认 {sorted(allowed)}%',
                            f'该色值附近出现 {", ".join(invalid)}%（未在上游证据内）', f'{rel}:{number}'))


def check_type(docs, facts, rows):
    canonical = docs.get(CANONICAL, [])
    text = '\n'.join(canonical)
    for item, expected in (
        ('type_zh', facts['type_zh']),
        ('type_latin', facts['type_latin']),
        ('weights_zh', ' / '.join(facts['weights_zh'])),
        ('weights_latin', ' / '.join(facts['weights_latin'])),
    ):
        values = [expected] if item.startswith('type_') else expected.split(' / ')
        missing = [value for value in values if value not in text]
        if missing:
            rows.append(add('FAIL', item, expected, f'缺失：{", ".join(missing)}', CANONICAL))
        else:
            rows.append(add('OK', item, expected, '已声明', CANONICAL))
    for rel, lines in sorted(docs.items()):
        for number, line in enumerate(lines, 1):
            if CSS_WEIGHT.search(line) and rel == CANONICAL:
                rows.append(add('WARN', 'font_weight_number', '上游未确认 CSS 字重数值',
                                CSS_WEIGHT.search(line).group(0), f'{rel}:{number}'))


def check_name(docs, facts, rows):
    canonical = docs.get(CANONICAL, [])
    text = '\n'.join(canonical)
    approved = facts['approved_name']
    if approved and approved in text:
        rows.append(add('OK', 'approved_public_name', approved, '已声明', CANONICAL))
    else:
        rows.append(add('FAIL', 'approved_public_name', approved or '（上游未解析到）', '本 Skill 未声明批准公开名称', CANONICAL))
    for rel, lines in sorted(docs.items()):
        for number, line in enumerate(lines, 1):
            clean = strip_code_and_urls(line)
            asserting = bool(NAME_ASSERTION.search(clean))
            for match in list(WRONG_NAME.finditer(clean)) + list(WRONG_DOMAIN.finditer(line)):
                wrong = match.group(1)
                if facts['approved_name'] and wrong == facts['approved_name']:
                    continue
                start, end = match.span()
                window = line[max(0, start - 16):end + 16]
                if NAME_MENTION_ONLY.search(window) and not asserting:
                    continue  # 否定语句里列举的写法是示例，不是品牌声明
                rows.append(add('FAIL', f'public_name:{wrong}', approved, f'出现未批准写法 {wrong}', f'{rel}:{number}'))


def check_evidence_refs(docs, facts, rows):
    known = set(facts['evidence'])
    seen = set()
    for rel, lines in sorted(docs.items()):
        for number, line in enumerate(lines, 1):
            for ref in EVIDENCE_REF.findall(line):
                seen.add(ref)
                if ref not in known:
                    rows.append(add('FAIL', f'evidence_id:{ref}', f'上游已知 id：{", ".join(sorted(known))}',
                                    '本 Skill 引用了上游不存在的 evidence id', f'{rel}:{number}'))
                    continue
                pages = set(page_numbers(line))
                expected_pages = set(facts['evidence'][ref].get('pages') or [])
                if not pages:
                    rows.append(add('FAIL', f'citation_pages:{ref}', f'{ref} 位于 Guide p.{sorted(expected_pages)}',
                                    '引用该 id 的行没有页码', f'{rel}:{number}'))
                elif expected_pages and not (pages & expected_pages):
                    rows.append(add('FAIL', f'citation_pages:{ref}', f'{ref} 位于 Guide p.{sorted(expected_pages)}',
                                    f'本行页码 {sorted(pages)} 与该证据不符', f'{rel}:{number}'))
    if seen:
        rows.append(add('OK', 'evidence_ids', f'{len(known)} 个上游 id 可解析', f'引用 {len(seen)} 个：{", ".join(sorted(seen))}', ''))
        checked = len(seen) - len({row[1].split(':')[1] for row in rows if row[0] == 'FAIL' and row[1].startswith('citation_pages:')})
        rows.append(add('OK', 'citation_pages', '每个 evidence 引用都要有与上游 pages 相符的页码',
                        f'{checked}/{len(seen)} 个引用的页码命中上游', ''))


def check_logo_metrics(docs, facts, rows):
    """Logo 度量：`v3.5.10` 起上游运营规则可被引用，但只能标为资产实测规则，不得冒充 Guide 条文。"""
    for rel, lines in sorted(docs.items()):
        for number, line in enumerate(lines, 1):
            match = LOGO_METRIC.search(line)
            if not match:
                continue
            where = f'{rel}:{number}'
            if OPERATING_REF.search(line):
                rows.append(add('OK', 'logo_operating_rule', 'Logo 尺寸/安全带/间距类数值必须指到上游运营规则文件',
                                f'已标注上游运营规则：{match.group(0)}', where))
                continue
            if '待确认' in line or 'do not infer' in line.lower():
                continue
            if GUIDE_DEFINES.search(line) and not ATTRIBUTION_NEGATED.search(line):
                rows.append(add('FAIL', 'operating_rule_as_guide_fact',
                                '资产实测的 Logo 运营规则不得表述为 VI Guide 规定',
                                match.group(0), where))
                continue
            rows.append(add('FAIL', 'unconfirmed_logo_metric',
                            'Logo 安全区/最小尺寸等数值必须标为上游运营规则或 待确认',
                            match.group(0), where))


def check_sixth_colour(docs, facts, rows):
    """第 6 个色值 黑色渐变 是 owner 签发的本地增补，没有 Guide 页面证据（Guide logo.forms 只列 5 种形式）。"""
    for rel, lines in sorted(docs.items()):
        for number, line in enumerate(lines, 1):
            if SIXTH_COLOUR not in line:
                continue
            if 'logo.forms' not in line and not GUIDE_DEFINES.search(line):
                continue
            if COLOUR_NEGATED.search(line):
                continue
            rows.append(add('FAIL', 'sixth_colour_as_guide_form',
                            'Guide logo.forms 只列 5 种形式；黑色渐变无 Guide 页面证据',
                            '该行把 黑色渐变 与 Guide 证据并列且没有否定说明', f'{rel}:{number}'))


def check_operating_rule_status(facts, rows):
    """上游自身的运营规则签发状态；不一致时本 Skill 只能按待确认保留，不得替上游裁定。"""
    status = (facts.get('operational') or {}).get('status')
    header_signed = facts.get('operating_rules_header_signed')
    if status and header_signed and '待' in str(status):
        rows.append(add('WARN', 'operating_rules_status', '上游运营规则签发状态应自洽',
                        f'规则文件标题=已签发；assets/guide-evidence.json operational_rules.status={status}（本 Skill 不改写、不裁定）',
                        'references/logo-usage-rules.md'))
    elif status:
        rows.append(add('OK', 'operating_rules_status', f'operational_rules.status={status}',
                        '已记录', 'assets/guide-evidence.json'))


# ---------------------------------------------------------------- output

def width(text):
    return sum(2 if unicodedata.east_asian_width(char) in 'WF' else 1 for char in text)


def pad(text, size):
    text = str(text)
    if size is None:
        return text
    while width(text) > size:
        text = text[:-2]
    return text + ' ' * max(0, size - width(text))


def render(rows, columns=(6, 22, 34, 52, None)):
    out = ['  '.join(pad(title, size) for title, size in zip(('判定', '项', '上游（来源）', '本 Skill', '位置'), columns))]
    out.append('  '.join('-' * size if size else '-' * 30 for size in columns))
    for row in rows:
        out.append('  '.join(pad(cell, size) for cell, size in zip(row, columns)))
    return '\n'.join(out)


def pin_from_dependencies():
    """从 skill-dependencies.json 读上游 pin（单一来源），返回 (tag, commit)。"""
    path = SKILL_DIR / 'skill-dependencies.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None, None
    for dep in data.get('dependencies', []):
        if dep.get('name') == 'archebase-vi-guide':
            return dep.get('tag'), dep.get('commit')
    return None, None


def upstream_identity(path):
    """返回 (head_sha, 说明)。本地 clone 只是缓存，身份必须可核对。"""
    if not (path / '.git').exists():
        return None, '不是 git 仓库（身份不可核对）'
    try:
        head = subprocess.run(['git', '-C', str(path), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True, timeout=15)
        if head.returncode != 0:
            return None, 'git rev-parse 失败'
        return head.stdout.strip(), ''
    except Exception as exc:  # pragma: no cover - 环境相关
        return None, f'git 调用失败：{exc}'


def main():
    parser = argparse.ArgumentParser(description='校验本 Skill 重述的品牌事实与上游 VI Guide 是否一致（只读、无网络）')
    parser.add_argument('--skill', default=str(SKILL_DIR), help='Skill 根目录，默认脚本所在 Skill')
    parser.add_argument('--upstream', default=None, help='上游 archebase-vi-guide 路径；默认读 ARCHEBASE_VI_GUIDE 或同级目录')
    parser.add_argument('--all', action='store_true', help='同时输出 OK 行')
    parser.add_argument('--allow-unpinned', action='store_true',
                        help='上游身份与 pin 不一致或不可核对时仍继续比较（结果只能视为待确认）')
    args = parser.parse_args()

    skill_dir = Path(args.skill).expanduser().resolve()
    pin_tag, pin_commit = pin_from_dependencies()
    upstream, label, tried = resolve_upstream(args.upstream, pin_commit)
    if upstream is None:
        die_unresolved(tried)

    head, note = upstream_identity(upstream)
    if pin_commit and head == pin_commit:
        identity_ok = True
        identity_text = f'{head}（与 pin 一致）'
    else:
        identity_ok = False
        if head is None:
            identity_text = f'未核对（{note}；pin {pin_tag or "?"} / {pin_commit or "?"}）'
        else:
            identity_text = f'{head}（与 pin {pin_commit or "?"} 不一致）'
    if not identity_ok and not args.allow_unpinned:
        print(f'上游：{upstream}（解析自 {label}）')
        print(f'上游身份：{identity_text}')
        print('结论：上游缓存的身份与 pin 不一致或不可核对，无法据此判定品牌事实；按待确认停止（退出码 2）。')
        print('提示：用 --upstream 指向 tag/commit 与 pin 一致的上游 clone，或加 --allow-unpinned 仅做参考比较。')
        raise SystemExit(2)

    facts, grammar_tokens = load_upstream(upstream)
    docs = read_skill(skill_dir)

    rows = []
    check_upstream_self_consistency(facts, grammar_tokens, rows)
    check_hexes(docs, facts, rows)
    check_token_table(docs, facts, rows)
    check_ratio(docs, facts, rows)
    check_neutral(docs, facts, rows)
    check_type(docs, facts, rows)
    check_name(docs, facts, rows)
    check_evidence_refs(docs, facts, rows)
    check_logo_metrics(docs, facts, rows)
    check_sixth_colour(docs, facts, rows)
    check_operating_rule_status(facts, rows)
    if not identity_ok:
        rows.insert(0, add('WARN', 'upstream_identity', f'pin {pin_tag} / {pin_commit}',
                           f'本次使用 {identity_text}，结果只能视为待确认', str(upstream)))
    # 上游若连批准公开名称都读不出来，说明该副本内容不可用，不能据此判本 Skill 有分歧
    upstream_unusable = facts.get('approved_name') is None
    if upstream_unusable:
        rows.insert(0, add('FAIL', 'upstream_unusable', '上游应可读出批准公开名称',
                           '该上游副本读不到批准公开名称（版本过旧或文件不完整）', str(upstream / 'references/asset-governance.md')))

    fails = [row for row in rows if row[0] == 'FAIL']
    warns = [row for row in rows if row[0] == 'WARN']
    shown = rows if args.all else fails + warns
    print(f'上游：{upstream}（解析自 {label}）')
    print(f'上游身份：{identity_text}')
    print(f'本 Skill：{skill_dir}')
    print(f'扫描：{len(docs)} 个文件（{", ".join(SCAN_SUFFIXES)}），只读、无网络')
    print()
    print(render(shown) if shown else '（无 FAIL/WARN 行）')
    print()
    print(f'汇总：FAIL {len(fails)} 项，WARN {len(warns)} 项，检查项 {len(rows)} 项')
    if upstream_unusable:
        print('结论：上游副本不可用（读不到批准公开名称），结论待确认（退出码 2）；请使用与 pin 一致的上游 clone。')
        raise SystemExit(2)
    if fails:
        print('结论：发现品牌事实分歧，必须修复后重新运行（退出码 1）。')
        raise SystemExit(1)
    print('结论：本 Skill 重述的品牌事实与上游一致（WARN 为待复核项，不阻断）。')
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
