# Credit Risk Plugin

信贷变量挖掘智能伙伴 - 提供数据探索、变量设计、效果评估的通用工作流。

## 安装

### 方式一：从 GitHub 克隆后本地加载

```bash
# 1. 克隆仓库
git clone https://github.com/frankawp/credit-risk-poc.git
cd credit-risk-poc

# 2. 切换到插件分支
git checkout refactor/skills-abstraction

# 3. 在目标工程中加载插件
cd /path/to/your-project
claude --plugin-dir /path/to/credit-risk-poc/credit-risk-plugin
```

### 方式二：直接引用远程仓库

如果目标工程已有 git 仓库，可以将此插件作为子目录：

```bash
# 在目标工程中
cd /path/to/your-project

# 创建插件目录
mkdir -p .claude/plugins

# 克隆插件到临时目录
git clone --depth 1 --branch refactor/skills-abstraction https://github.com/frankawp/credit-risk-poc.git /tmp/credit-risk-poc

# 复制插件目录
cp -r /tmp/credit-risk-poc/credit-risk-plugin .claude/plugins/

# 清理临时目录
rm -rf /tmp/credit-risk-poc
```

### 方式三：复制到用户级插件目录

```bash
# 克隆仓库
git clone --branch refactor/skills-abstraction https://github.com/frankawp/credit-risk-poc.git

# 复制到用户插件目录
mkdir -p ~/.claude/plugins
cp -r credit-risk-poc/credit-risk-plugin ~/.claude/plugins/

# 所有项目自动可用
claude
```

## 使用方法

### 调用技能

```
/credit-risk:mining
```

### 核心功能

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

## 快速测试

在任意项目中测试插件：

```bash
# 创建测试目录
mkdir -p /tmp/test-plugin/data

# 放入一些 CSV 数据文件
# ...

# 启动 Claude Code 加载插件
claude --plugin-dir ~/.claude/plugins/credit-risk-plugin

# 在 Claude Code 中调用
/credit-risk:mining 帮我探索 data 目录
```
