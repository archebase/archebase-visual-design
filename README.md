# ArcheBase Visual Design Skill

Design-method application layer for ArcheBase / 智域基石. `SKILL.md` is authoritative for agent behaviour; this README is the repository-level orientation only and no agent rule lives here alone.

## Dependency

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
references/             design methods, brand restatement, source boundaries
templates/              briefs, IR records, retrieval/candidate records, spec, decision trace
evals/                  runnable regression + brand-fact checker, and an unexecuted A/B protocol
skill-dependencies.json pinned dependencies and non-goals
NOTICE.md  LICENSE      notices and licence (internal use)
```

## Checks

```sh
python3 evals/check_brand_facts.py          # restated brand facts vs the pinned upstream
python3 evals/run_visual_design_benchmark.py # retrieval and design-space regression
```

Both read `ARCHEBASE_VI_GUIDE` / `ARCHEBASE_DESIGN_IR`, falling back to sibling directories, and report `待确认` instead of silently passing when a dependency is unreachable.

### Renderer warning

The gradient logo SVGs use multiple stops with `stop-opacity`; ImageMagick's internal SVG renderer renders them incorrectly (darker, partially flattened). Use `rsvg-convert` or a browser engine, or the bundled PNG. Never use `magick file.svg` for a logo.

## Status

Internal application-layer skill; the repository is **private**. A pre-publication exposure review (2026-09-27) found third-party derivative-permission items that must be resolved before making it public — the list lives in `archebase/archebase-design-workspace` → `PUBLICATION-BLOCKERS.md` (items 4–7: `references/grid-systems.md`, `references/vignelli-principles.md`, `references/legibility.md`, `references/image-and-information-design.md`). Until then: internal use only, and the `author` field plus the licence wording must be reviewed before any public release.
