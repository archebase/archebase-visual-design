# Notices

## Upstream brand dependency

ArcheBase brand facts, official assets, evidence, tokens, route playbooks, validators and release gates are maintained in the separate proprietary repository:

https://github.com/archebase/archebase-vi-guide

Pinned baseline: tag `v3.5.4`, commit `918d0ec8f05f775d1f34370e0c38fc796da8b83b`. This repository references that dependency but does not include or redistribute its proprietary assets.

## Other declared dependencies

See `skill-dependencies.json`:

- `archebase/archebase-wechat-layout` — the channel CSS behind `references/channel-wechat.md`, pinned by commit `37f9b0bb3a289950c1e0be49d00c7d6138da9a9d`; that repository has no tags yet, so no tag can be pinned.
- Design IR store — the workspace repository `archebase/archebase-design-workspace`, used via its `ir/` directory; resolved from `ARCHEBASE_DESIGN_IR`, the workspace layout, or a pinned clone. It is a derived consumer of brand facts and is never cited as brand evidence.

## Source-derived design methods

Reference files in this repository contain synthesized design-method guidance, not the original books or full source texts. The methods are distilled from public graphic-design literature and teaching material, with attribution kept in the referencing file. Third-party permissions were confirmed by the brand owner on 2026-09-27 (`archebase/archebase-design-workspace` → `sources/AUTHORIZATION.md`); per-source licence terms are recorded in that workspace's `sources/source-ledger.csv`. Rights for material added to a deliverable remain the publisher's responsibility.
