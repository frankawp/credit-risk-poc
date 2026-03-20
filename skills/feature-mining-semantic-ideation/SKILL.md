---
name: feature-mining-semantic-ideation
description: 当用户想围绕 consistency、velocity、cashout、collusion 设计信贷反欺诈语义变量、扩展变量思路或区分已实现与未实现方向时使用。
---

# 语义变量探索

全程使用中文。

## 什么时候用

- 用户说“帮我想一批 consistency/velocity/cashout/collusion 变量”
- 用户想知道当前哪些语义变量已经实现，哪些还只是方向
- 用户希望从业务机制而不是字段枚举来设计变量

## 工作方式

1. 先按业务目标归到四个主题之一或几个主题组合。
2. 先读 `../feature-mining-orchestrator/references/themes.md`。
3. 需要判断已实现状态时，再读 `../feature-mining-orchestrator/references/implemented_features.md`。
4. 输出时必须分成三类：
   - `已实现变量`
   - `候选变量`
   - `尚未实现但建议尝试`

## 约束

- 不要把 `collusion` 说成当前已经能计算。
- 不要直接承诺模型收益，只说明业务假设和可验证方向。
- 如果用户要执行当前已实现主题，交给总控 skill 或仓库脚本处理。
