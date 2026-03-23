# Credit Risk Plugin

信贷变量挖掘智能伙伴。唯一公开技能入口为 `/credit-risk:mining`。

## 安装

```bash
# 在 Claude Code 中添加市场
/plugin marketplace add https://github.com/frankawp/credit-risk-poc

# 安装插件
/plugin install credit-risk@credit-risk-marketplace
```

本地调试时也可以直接添加本仓库作为市场：

```bash
git clone https://github.com/frankawp/credit-risk-poc.git
cd credit-risk-poc
/plugin marketplace add .
/plugin install credit-risk@credit-risk-marketplace
```

## 使用

安装完成后，直接在 Claude Code 中输入：

```text
/credit-risk:mining
```

然后给出业务目标、目标变量和数据位置。Skill 会按“探索 → 设计 → 实现 → 验证 → 迭代”推进，并把当前轮次的产物写到 `outputs/`。

## 目录说明

```text
credit-risk-plugin/
├── .claude-plugin/plugin.json
├── engine/                         # 通用引擎
└── skills/mining/
    ├── SKILL.md                    # 运行时技能定义
    ├── references/                 # 方法论和主题设计
    ├── scripts/
    │   ├── feature_registry.py     # 变量注册表
    │   └── archive_run.py          # 归档当前 outputs/
    └── examples/home_credit/       # 阶段化样例
```

## 辅助脚本

```bash
# 查看或更新变量注册表
python3 credit-risk-plugin/skills/mining/scripts/feature_registry.py --help

# 仅在用户明确要求时归档当前 outputs/
python3 credit-risk-plugin/skills/mining/scripts/archive_run.py --help
```

## 依赖

基础依赖：

```bash
pip install pandas numpy scikit-learn
```

自动特征引擎额外依赖：

```bash
pip install featuretools
```

## 示例

可复制的阶段化样例位于 [skills/mining/examples/home_credit](./skills/mining/examples/home_credit/README.md)。
