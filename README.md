# ArcheBase Visual Design Skill

Design-method application layer for ArcheBase / 智域基石. `SKILL.md` is authoritative for agent behaviour; this README is the repository-level orientation only and no agent rule lives here alone.

## Dependency and installation

`archebase-vi-guide` is the required base skill for ArcheBase brand work. `archebase-visual-design` is the optional design-method companion.

- Minimum installation: install `archebase-vi-guide`.
- Recommended installation for posters, covers, infographics and visual design critique: install both skills.
- When both are installed, `archebase-vi-guide` loads first and owns mode selection, route selection, brand facts, official assets, Guide evidence, channel rules and the final release verdict. This skill owns composition, hierarchy, grid, visual direction, color application, legibility and design critique.
- Do not install or use this skill alone for ArcheBase-branded work. If the base skill is missing or its pinned identity cannot be verified, block the brand route rather than inventing brand facts or claiming VI compliance.

Official brand facts, assets, evidence, tokens, route playbooks, validators and release gates stay upstream:

- Repository: https://github.com/archebase/archebase-vi-guide
- Baseline: tag `v3.5.4`, commit `918d0ec8f05f775d1f34370e0c38fc796da8b83b`

Resolve it with `git clone --branch v3.5.4 https://github.com/archebase/archebase-vi-guide` and verify `git -C archebase-vi-guide rev-parse HEAD` against the commit above. This repository does not copy or redistribute upstream VI assets or evidence, and it is not itself a brand authority.

Other declared dependencies are listed in `skill-dependencies.json`.

## Scope

This repository is the application layer. It does not contain the official VI PDF, CSS, tokens, logo assets or evidence register, and it does not contain internal contracts, HR, finance, legal, sales or operations documents.

## Layout

```text
SKILL.md                agent-facing contract: triggers, boundary, workflow, gates
references/             design methods, brand restatement, source boundaries,
                         general method-fit audit and VI PDF method translation
templates/              briefs, IR records, retrieval/candidate records, spec, spatial-fidelity spec, decision trace
evals/                  runnable regression + brand-fact + spatial-fidelity checker, and an unexecuted A/B protocol
skill-dependencies.json pinned dependencies and non-goals
NOTICE.md  LICENSE      notices and licence (internal use)
```

## Checks

```sh
python3 evals/check_brand_facts.py          # restated brand facts vs the pinned upstream
python3 evals/check_routing.py             # index-level routing reachability vs the vi-guide boundary
python3 evals/check_spatial_spec.py --spec <spec.json>   # reference fidelity and worn-geometry spec
python3 evals/check_spatial_spec.py --self-test          # positive fixtures pass, negative ones must fail
python3 evals/run_visual_design_benchmark.py # retrieval and design-space regression
```

All read `ARCHEBASE_VI_GUIDE` / `ARCHEBASE_DESIGN_IR`, falling back to sibling directories, and report `待确认` instead of silently passing when a dependency is unreachable. `check_spatial_spec.py` reads only the spec file it is given (or its bundled fixtures) and needs no dependency at all.

### Renderer warning

The gradient logo SVGs use multiple stops with `stop-opacity`; ImageMagick's internal SVG renderer renders them incorrectly (darker, partially flattened). Use `rsvg-convert` or a browser engine, or the bundled PNG. Never use `magick file.svg` for a logo.

## Status

Internal application-layer skill, published as a **publicly readable** repository (matching the sibling VI skill repos) so that teams and agents can load it by repository and commit. Public visibility is not a redistribution grant.

Third-party permissions for the design-source methods were confirmed by the brand owner on 2026-09-27; the decision and per-source terms are recorded in the internal repository `archebase/archebase-design-workspace` (`sources/AUTHORIZATION.md`, `PUBLICATION-STATUS.md`). The optional Design IR route resolves that repository's `ir/` directory and, without access to it, stops with 待确认 — everything else in this skill works without it. Attribution to each source stays in the reference files. The upstream VI Guide dependency is proprietary and separately governed.
