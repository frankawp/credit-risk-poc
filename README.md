# Credit Risk POC

信贷变量挖掘 Claude Code 插件工程。

## 简介

本工程提供了一套完整的信贷变量挖掘工作流，包括数据探索、变量设计、效果评估和归档管理工具。

## 快速开始

### 安装插件

```bash
# 添加插件市场
/plugin marketplace add https://github.com/frankawp/credit-risk-poc

# 安装插件
/plugin install credit-risk@credit-risk-marketplace
```

### 开始挖掘

```
/credit-risk:mining
```

然后描述你的业务问题和数据位置，AI 会引导你完成完整的变量挖掘流程。

## 核心功能

| 功能 | 说明 |
|------|------|
| 数据探索 | 自动分析数据目录结构和质量 |
| 变量设计 | 基于业务假设设计新变量 |
| 效果评估 | 计算 IV、PSI 等评估指标 |
| 归档管理 | 归档分析产物和变量注册 |

## 目录结构

```
credit-risk-poc/
├── credit-risk-plugin/         # 插件目录
│   ├── skills/                 # 技能定义
│   ├── scripts/                # 工具脚本
│   └── references/             # 参考文档
├── data/                       # 数据文件
├── outputs/                    # 输出产物
└── archives/                   # 归档目录
```

## 依赖

```bash
pip install pandas numpy scikit-learn
```

可选：`pip install featuretools`（自动特征生成）

## 开发规范

- 变量命名：`{主题}_{具体含义}_{时间窗口}`
- 每次推送前更新版本号
- 中文注释和文档

## 文档

- [CLAUDE.md](./CLAUDE.md) - 开发规范和工程说明
- [插件 README](./credit-risk-plugin/README.md) - 插件使用指南
