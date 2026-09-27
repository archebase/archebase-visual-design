# 来源与证据边界

## Brand authority and GitHub dependency

The canonical VI Skill is the GitHub repository:

```text
https://github.com/archebase/archebase-vi-guide
```

Compatibility baseline: `v3.5.4` at commit `918d0ec8f05f775d1f34370e0c38fc796da8b83b`. A local clone is only a cache and must not be used as the source identity. Do not create, install, copy, or synthesize another `archebase-vi-guide` under `~/.hermes/skills` or this project. Do not copy its tokens, evidence register, logo assets, page records, validators, or release gates.

The external design-book work in this project is an application/reference layer only. It may declare the GitHub VI Skill as a dependency, but it must not become a second VI authority. When the upstream tag or commit changes, rerun upstream validators/evals before updating the dependency baseline.

## 渠道实现

微信公众号标题、引用、表格、深色模块和 CSS 兼容限制来自现有公众号 VI CSS。它们不自动泛化为海报、PPT、网站和空间导视的固定尺寸规则。

## 综合工作方法

本 Skill 的构成、网格、字体、可读性、色彩、图像与信息设计、无障碍和生产方法综合自公开的平面设计文献与教学资料，只作为操作方法使用：不声称它们是智域基石 VI 的原始条文，也不复述原文。第三方素材在内部默认按已获授权处理，本 Skill 不维护逐来源的许可台账；对外发布前由发布方确认授权。

经验性规则必须在当前项目的真实媒介、真实尺寸和当前标准下复核，尤其是印刷与文件生产（历史性的 72 PPI、具体设备和 PDF/X 示例）、可读性与对比度、以及图像与信息设计的媒介差异。

## 技能默认值

“三方向草案”“输出合同”“质量门顺序”等是为了稳定执行而设定的流程默认值，不是原作者或品牌方规定。

## 待确认

以下 7 项与上游未确认清单一一对应（上游 `assets/guide-evidence.json` 字段 `unconfirmed`；`tokens/archebase.tokens.json` 字段 `unconfirmed`）。补齐后由 [brand-system.md](brand-system.md) 单一重述，本文件不复述数值。

1. p.28 百分比色带的语义角色名称与按组件分配（上游 `assets/guide-evidence.json`；Guide p.28，evidence `color.ratio`）。
2. 中性色阶的精确合成方式与 CSS alpha 实现（上游 `assets/guide-evidence.json`；Guide pp.30-32，evidence `neutral.background`、`neutral.text`）。
3. Logo 安全区与最小尺寸（上游 `assets/guide-evidence.json`；Guide pp.1-5，evidence `logo.forms`）。
4. 字体许可、确切生产文件与生产字重映射（上游 `assets/guide-evidence.json`；Guide pp.6/10/14/26，evidence `typography.specimens`）。
5. 特定场景下的 ArcheBase 组合锁定与域名应用（上游 `assets/guide-evidence.json`；Guide pp.33-36，evidence `naming.examples`）。
6. 媒介色彩转换与印刷转换（上游 `assets/guide-evidence.json`；`tokens/archebase.tokens.json` 字段 `unconfirmed`）。
7. 视觉应用板的分渠道应用规则（上游 `assets/guide-evidence.json`；Guide pp.37-46，evidence `application.boards`）。

缺少以上信息时不得臆测为正式规范，也不得为这些项填入具体数值、比例或对应色。
