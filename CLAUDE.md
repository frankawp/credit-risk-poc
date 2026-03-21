# Credit Risk Plugin - 信贷变量挖掘 Claude Code 插件

## 工程定位

本工程是一个 **Claude Code 插件**，提供信贷变量挖掘的通用工作流和工具。

### 主要交付物

**credit-risk-plugin**：一个可独立安装的 Claude Code 插件，提供：
- 数据探索工具
- 变量设计方法论
- 变量评估工具
- 归档管理工具

### 核心特点

- **无外部包依赖**：插件仅依赖基础数据分析库（pandas, numpy, scikit-learn）
- **通用工具**：脚本适用于任何变量挖掘场景，不耦合具体业务
- **业务示例独立**：示例代码展示如何使用插件

---

## 项目结构

```
credit-risk-poc/
├── credit-risk-plugin/              # 插件目录
│   ├── .claude-plugin/
│   │   └── plugin.json              # 插件清单
│   ├── skills/
│   │   └── mining/
│   │       └── SKILL.md             # 核心技能定义
│   ├── scripts/                     # 通用工具
│   │   ├── data_explorer.py         # 数据探索
│   │   ├── feature_evaluator.py     # 变量评估
│   │   ├── feature_registry.py      # 变量注册
│   │   ├── archive_run.py           # 归档工具
│   │   └── auto_features.py         # 自动特征（可选）
│   └── references/                  # 参考文档
│       ├── methodology.md
│       └── variable_design_guide.md
├── examples/                        # 业务示例
│   └── home_credit/
│       ├── features/                # 变量实现模板
│       └── README.md
├── data/                            # 数据文件（gitignore）
├── outputs/                         # 输出产物（gitignore）
└── archives/                        # 归档目录（gitignore）
```

---

## 使用方法

### 加载插件

```bash
claude --plugin-dir ./credit-risk-plugin
```

### 调用技能

```
/credit-risk:mining
```

### 使用工具脚本

```bash
# 数据探索
python credit-risk-plugin/scripts/data_explorer.py data/raw/

# 变量评估
python credit-risk-plugin/scripts/feature_evaluator.py outputs/features.parquet --target TARGET

# 变量注册
python credit-risk-plugin/scripts/feature_registry.py register --name my_feature --theme velocity --hypothesis "业务假设"
```

---

## 开发规范

### 变量设计

- 每个新变量需记录：变量名、计算逻辑、业务假设、预期效果
- 变量命名：`{theme}_{具体含义}_{时间窗口}`
- 效果验证后更新状态（proposed/implemented/validated/selected/rejected）

### 代码风格

- 中文注释和文档
- 类型注解
- 通用性：不耦合具体业务数据

### 文档更新

- 新增变量时更新 `outputs/proposed_features/registry.json`
- 方法论变更时更新 `credit-risk-plugin/references/`

---

## AI 在变量挖掘中的角色

AI 不是"脚本调度器"，而是"变量挖掘伙伴"。

### 核心能力

1. **数据理解**：主动探索数据结构、分布、业务含义
2. **假设设计**：基于业务知识提出变量假设
3. **代码实现**：动态生成 Python 函数实现变量
4. **效果验证**：评估变量效果，迭代优化
5. **知识沉淀**：记录假设来源、迭代过程、效果证据

### 工作原则

- 先理解数据，再设计变量
- 每个变量都有业务假设支撑
- 效果不好时主动调整策略
- 对用户的业务问题保持敏感
