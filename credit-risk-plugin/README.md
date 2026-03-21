# Credit Risk Plugin

信贷变量挖掘智能伙伴 - 提供数据探索、变量设计、效果评估的通用工作流。

## 安装

### 步骤 1：添加插件市场

```bash
# 在 Claude Code 中运行
/plugin marketplace add https://github.com/frankawp/credit-risk-poc
```

或指定分支：

```bash
/plugin marketplace add https://github.com/frankawp/credit-risk-poc --ref refactor/skills-abstraction
```

### 步骤 2：安装插件

添加市场后，安装插件：

```bash
/plugin install credit-risk@credit-risk-marketplace
```

### 步骤 3：使用技能

```
/credit-risk:mining
```

---

## 本地测试

在发布前可以本地测试：

```bash
# 克隆仓库
git clone --branch refactor/skills-abstraction https://github.com/frankawp/credit-risk-poc.git

# 添加本地市场
/plugin marketplace add ./credit-risk-poc

# 安装插件
/plugin install credit-risk@credit-risk-marketplace
```

---

## 核心功能

1. **数据探索** - 自动分析数据目录结构和质量
2. **变量设计** - 基于业务假设设计变量
3. **效果评估** - 评估变量预测能力
4. **归档管理** - 归档分析产物

## 依赖

### 基础依赖（必需）

```bash
pip install pandas numpy scikit-learn
```

### 可选依赖

```bash
# 自动特征生成功能
pip install featuretools
```

## 目录结构

```
credit-risk-plugin/
├── .claude-plugin/
│   └── plugin.json          # 插件清单
├── skills/
│   └── mining/
│       └── SKILL.md         # 核心技能定义
├── scripts/                 # 工具脚本
│   ├── data_explorer.py     # 数据探索
│   ├── feature_evaluator.py # 变量评估
│   ├── feature_registry.py  # 变量注册
│   ├── archive_run.py       # 归档工具
│   └── auto_features.py     # 自动特征（可选）
├── references/              # 参考文档
│   ├── methodology.md
│   └── variable_design_guide.md
└── README.md
```

## 工作流

```
探索 → 设计 → 实现 → 验证 → 迭代
```

1. **探索**：理解数据结构和业务含义
2. **设计**：提出变量假设
3. **实现**：编写变量计算代码
4. **验证**：评估变量效果
5. **迭代**：根据效果优化

## 示例

参见 [examples/home_credit/](../examples/home_credit/) 目录下的业务案例。

---

## 常用命令

```bash
# 查看已添加的市场
/plugin marketplace list

# 更新市场
/plugin marketplace update credit-risk-marketplace

# 查看已安装的插件
/plugin list

# 卸载插件
/plugin uninstall credit-risk@credit-risk-marketplace
```
