# 微信公众号渠道

本文件是渠道实现规则，不是所有媒介的全局品牌定律。

## 渠道来源

- 渠道 CSS 与配套规则来自 `https://github.com/archebase/archebase-wechat-layout.git`，固定到 commit `37f9b0bb3a289950c1e0be49d00c7d6138da9a9d`（`main` 分支）。
- 该仓库当前**没有任何 tag**，因此只能按仓库 URL + commit 引用，不得写成 tag 或浮动分支；本地 clone 只是缓存，不是来源身份。
- 下文 `assets/archebase-wechat-safe.css:<行>`、`references/layout-rules.md:<行>`、`scripts/validate_inkpost_css.py:<行>` 均指上述 commit 的行号。
- 品牌事实不在本文件定义：色值角色、比例、中性级见 [brand-system.md](brand-system.md)（上游 `tokens/archebase.tokens.json`；Guide p.28，evidence `color.ratio`）。本文件出现的浅色 tint 值属于渠道实现，不是品牌 token。
- 渠道 CSS 中的品牌色值与上游 token 一致：`#0032FF` `#7172FA` `#619AFD` `#46CFFF` `#1E2124`（上游 `tokens/archebase.tokens.json`；Guide p.28，evidence `color.ratio`；中性级 pp.30-32，evidence `neutral.background`/`neutral.text`）。

## 文章视觉

- 白底正文：文字 `#1E2124`、背景 `#FFFFFF`（`assets/archebase-wechat-safe.css:5-6`）。
- H1：左脊柱 `6px solid #0032FF`、下边线 `2px solid #46CFFF`、背景面 `#F3F5FF`（`assets/archebase-wechat-safe.css:19-21`）。
- H2：左线 `4px solid #0032FF`、下边线 `1px solid #BFC8FF`（`assets/archebase-wechat-safe.css:31-32`）。
- H3：只有左线 `3px solid #46CFFF`；该 CSS 未定义 H3 下边线（`assets/archebase-wechat-safe.css:42`）。
- 表头：文字 `#FFFFFF`、背景 `#1E2124`、`font-weight: 700`（`assets/archebase-wechat-safe.css:115-118`）。
- 表格单元格边框 `1px solid #BFC8FF`，偶数行底 `#F7F8FF`（`assets/archebase-wechat-safe.css:123,127`）。
- 深色模块 `.block-3` / `.danger`：底 `#1E2124`、反白文字 `#F4F7FF`、左边线 `4px solid #46CFFF`（`assets/archebase-wechat-safe.css:171-173`）。
- `#46CFFF` 在该 CSS 中只作边线（H1 下边线、H3 左线、深色模块左线），未作文字色（`assets/archebase-wechat-safe.css:20,42,173`）。
- H1/H2 的浅色面与浅色线来自渠道 tint 家族 `#F3F5FF`、`#BFC8FF`、`#F2F5FF`、`#E9EDFF`、`#F7F8FF`；这是**渠道实现**的浅底映射，不是品牌核心色。同一 commit 的 `scripts/validate_inkpost_css.py:10-14` 只把这组 tint 与五个品牌色、`#FFFFFF` 一起列为允许色值。
- 图片 `max-width: 100%`、`height: auto`（`assets/archebase-wechat-safe.css:67-68`）；小字、细线和 Logo 不按照片分辨率栅格化（`references/production-preflight.md:8`）。

## 字体回退

以下为渠道实现细节，不是品牌字体规则：

- 中文回退栈取自 CSS `body`：`"Source Han Sans SC", "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif`（`assets/archebase-wechat-safe.css:2`）。
- 上游只确认中文 `思源黑体` 与拉丁 `Poppins` ExtraBold/SemiBold/Regular 的展示字重（上游 Guide pp.6,10,14,26，evidence `typography.specimens`）；生产字体文件、CSS 字重映射与授权 待确认（上游 `assets/guide-evidence.json` unconfirmed: font license, exact files and production weight mapping）。
- 不得由回退栈推断生产字体文件或授权，也不得把回退栈写成品牌字体事实。

## 兼容限制

来源为渠道仓库的微信安全属性清单（`references/layout-rules.md:46-54`）与 CSS 校验器（`scripts/validate_inkpost_css.py:15-19`）。

默认不依赖：

- `display: flex` / `grid` / `inline-flex` / `inline-grid`
- `position: fixed` / `sticky`
- `animation`、`transition`、`transform`、`filter`、`backdrop-filter`
- `mask`、`clip-path`、`columns`、`object-fit`、`writing-mode`
- 以渐变作为普通文章布局的依赖

- `:has` 与 `clamp` 未在渠道仓库记录，也未进入该校验器 → 待确认。
- 复杂双栏和浮动结构需在微信手机端实测；必要时改为块级单栏。
- 细线、tint 浅色与 `#46CFFF` 在不同屏幕上的减弱程度无渠道记录 → 待确认，交付前看实际预览截图。

## 选择器冲突处理

现有 CSS 对不同强调使用不同色值：`strong` 用 `#0032FF`（`assets/archebase-wechat-safe.css:52`）、`em` 用 `#7172FA`（`:57`）、`a` 用 `#0032FF`（`:61`）、`code` 用 `#0032FF`（`:86`）。以上位规则为准：白底正文强调用 `#0032FF`，`#46CFFF` 与辅助蓝不用于白底小正文——色值角色见 [brand-system.md](brand-system.md)（上游 `tokens/archebase.tokens.json`；Guide p.28，evidence `color.ratio`）。渠道浅色 tint（如 H1 的 `#F3F5FF`）是安全映射，不自动成为新的核心品牌色；核心品牌色仍只有五个（上游 `tokens/archebase.tokens.json`）。

## 微信交付检查

- iOS 与 Android 预览。
- 小屏行长、标题换行、表格横向溢出。
- 深底模块反白文字对比。
- 图片压缩后的细线和小标签。
- 复制粘贴后样式是否被编辑器剥离。
- 渲染前跑渠道仓库 `scripts/validate_inkpost_css.py` 与 `references/release-checklist.md`。
