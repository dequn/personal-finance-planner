# Personal Finance Planning Core

[English](README.md) | 简体中文

Personal Finance Planning Core 是一个面向 Codex、Claude、Hermes 等 Agent
宿主的隐私优先理财规划 Plugin。它把用户提供的财务概况、目标和约束整理为
结构化规划状态，通过确定性计算器生成可检查的测算结果和资产配置建议。

“Planning Core”这一名称是有意收窄的：它是可复用的理财规划内核，不是财富
顾问、产品商城、投资组合管理器、券商连接器或交易 Agent。

## 隐私优先：个人数据只保存在本地

**本 Plugin 持久化的所有个人理财数据，只会写入用户明确选择的本地
Workspace。** Plugin 不包含遥测或远程个人数据仓库，不会自行发现私人目录，
也不会把本地 Workspace 数据打包进发行版本。

需要了解资产时，只提供完成规划所必需的资产概况，例如：

- 资产类别及大致金额或区间；
- 币种、流动性、到期时间和信息观察日期；
- 理财目标、时间期限、风险约束和确认状态；
- 用于区分已确认事实与估算值的来源信息。

请永远不要提供或保存：

- 密码、支付密码、一次性验证码或安全问题答案；
- 完整的银行卡、券商、信用卡或支付账户号码；
- API Key、访问令牌、Cookie、私钥或助记词；
- 身份证件号码或规划不需要的身份证明材料；
- 含个人标识的原始账单、截图或账户导出文件。

只有在确实需要区分两项资产时，才使用脱敏后的机构名称或局部标识。制定理财
计划不需要登录凭据，也不需要授权 Plugin 访问银行或券商账户。

> **宿主边界：** 本地持久化不等于所有对话一定在本机处理。如果通过云端模型
> 使用本 Plugin，发送给 Agent 宿主的文本可能按照宿主和模型提供商的隐私政策
> 被处理。不要在 Prompt 中粘贴密码或其他秘密。若要实现端到端本地处理，还需
> 同时使用本地 Agent Runtime 和本地模型。

详细边界见 [PRIVACY.md](PRIVACY.md) 和 [SECURITY.md](SECURITY.md)。

## 当前能力

- 渐进式财务概况收集；
- 中立的目标确认和目标冲突检查；
- 确定性的规划阶段路由；
- 财务独立、阶段里程碑和可选住房情景计算器；
- 目标资产结构和现金流动性政策校验；
- 经用户明确确认的本地 Workspace 状态；
- 版本化的专业知识和中国大陆公开规则；
- 合成评测，以及不包含任何交易执行工具。

产品筛选、实时账户读取、税务或保险建议、自动再平衡和金融交易不在当前范围内。

## 数据与安全模型

```text
用户提供的规划事实
        |
        v
Agent 宿主 + Plugin Skills
        |
        v
确定性 MCP 校验与计算
        |
        v
用户确认 -> 本地 Workspace
```

- Prompt 和 Skill 可以提出建议或澄清问题；
- 确定性 Tool 负责校验计算结果和结构化状态；
- 只有用户明确确认后，才会写入已确认状态；
- Plugin 不提供交易、赎回、申购、换汇、杠杆、凭据收集或自动转移资金工具。

## 仓库结构

```text
.agents/plugins/marketplace.json        # 本地 Marketplace 元数据
plugins/personal-finance-planner/       # 可安装的 Plugin 包
  skills/                               # 可复用规划工作流
  mcp/                                  # 确定性工具和资源
  schemas/                              # 结构化契约
  knowledge/                            # 版本化公开知识卡
  evals/                                # 合成评测案例
tests/                                  # 仓库级 smoke tests
```

用户可见名称是 **Personal Finance Planning Core**。为保持兼容，Plugin 技术 ID
和 MCP server ID 仍为 `personal-finance-planner`。

## 本地验证

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py \
  plugins/personal-finance-planner

uv run --project plugins/personal-finance-planner/mcp \
  python -m unittest discover -s tests
```

每个候选版本还必须通过 fixture 分类、禁止个人数据、symlink、secret、包边界和
暂存差异隐私检查。

## 发布状态

本仓库当前是私有 Release Candidate。存在 Git 仓库、Marketplace manifest 或
版本标签，都不代表已经公开发布到 Marketplace。分发任何构建前都必须检查隐私
与安全文档。

本 Plugin 只用于规划和教育，不提供受监管的个性化金融建议，也不授权任何交易。
