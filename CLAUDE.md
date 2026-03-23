# Credit Risk Plugin Maintainers Guide

本仓库不是通用软件工程模板，而是一个面向 Claude Code 的信贷变量挖掘 Skill 工程。维护时优先保证：

1. Claude 能按文档找到正确入口。
2. 样例代码能被 Claude 正确模仿。
3. 辅助脚本可直接运行。
4. 归档不会破坏 Skill 本体。

## Source Of Truth

- 唯一公开技能入口：`/credit-risk:mining`
- 运行时技能定义：`credit-risk-plugin/skills/mining/SKILL.md`
- 方法论文档：`credit-risk-plugin/skills/mining/references/`
- 辅助脚本：`credit-risk-plugin/skills/mining/scripts/`
- prompt asset / 样例：`credit-risk-plugin/skills/mining/examples/`

不要再在文档里写不存在的 `credit-risk-plugin/scripts/`、`credit-risk-plugin/references/` 或 `skills/feature-mining/`。

## 维护约定

- `SKILL.md` 负责运行时行为、输出目录和工作流约束。
- `credit-risk-plugin/README.md` 负责安装、调用方式和辅助脚本入口。
- 根 `README.md` 只负责工程概览和公开入口。
- examples 是 Claude 会模仿的 prompt asset，必须与当前 API 保持一致，可运行优先于花哨写法。

## 依赖约束

- 基础依赖：`pandas`、`numpy`、`scikit-learn`
- `featuretools` 是自动特征和 EntitySet 构建的可选依赖
- 未安装 `featuretools` 时，语义特征路径和纯文档/脚本路径必须仍然可用

## 版本管理

每次对插件公开行为或修复发布时，同步更新：

1. `credit-risk-plugin/.claude-plugin/plugin.json`
2. `.claude-plugin/marketplace.json`

版本建议：

- patch：修复脚本、样例、文档、非破坏性行为
- minor：公开命令、公开目录结构或用户可见能力变化
- major：不兼容的入口或行为变化

## 发布前检查

```bash
python3 -m pytest
python3 credit-risk-plugin/skills/mining/scripts/feature_registry.py --help
python3 credit-risk-plugin/skills/mining/scripts/archive_run.py --help
```

如果环境里安装了 Claude Code，再额外做一次本地安装冒烟，确认公开入口仍是 `/credit-risk:mining`。
