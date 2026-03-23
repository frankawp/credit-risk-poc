# Credit Risk POC

面向 Claude Code 的信贷变量挖掘 Skill 工程。

## 唯一公开入口

安装插件后，通过下面的技能入口发起变量挖掘：

```text
/credit-risk:mining
```

## 安装

```bash
# 添加插件市场
/plugin marketplace add https://github.com/frankawp/credit-risk-poc

# 安装插件
/plugin install credit-risk@credit-risk-marketplace
```

安装完成后，直接描述业务问题和数据位置即可，例如：`帮我做信贷变量挖掘，数据在 data/ 目录下`。

## 工程结构

```text
credit-risk-poc/
├── credit-risk-plugin/
│   ├── .claude-plugin/plugin.json
│   ├── engine/                         # 通用引擎
│   └── skills/mining/
│       ├── SKILL.md                    # 运行时行为和输出约束
│       ├── references/                 # 方法论与主题设计文档
│       ├── scripts/                    # registry/archive 等辅助脚本
│       └── examples/home_credit/       # 可复制的阶段化样例
├── data/                               # 本地数据（gitignore）
├── outputs/                            # 当前轮次产物（gitignore）
└── archives/                           # 归档产物（gitignore）
```

## 依赖

```bash
pip install pandas numpy scikit-learn
```

如需自动特征引擎，再额外安装：

```bash
pip install featuretools
```

## 文档

- [CLAUDE.md](./CLAUDE.md)：维护约定、版本同步和文档职责
- [credit-risk-plugin/README.md](./credit-risk-plugin/README.md)：插件安装、调用和辅助脚本入口
- [credit-risk-plugin/skills/mining/SKILL.md](./credit-risk-plugin/skills/mining/SKILL.md)：Claude 运行时技能定义
