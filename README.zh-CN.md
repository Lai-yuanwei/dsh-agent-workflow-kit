# dsh-agent-workflow-kit（中文说明）

这是一套社区维护的团队模板，用来在 **DeepSeek Harness（DSH）** 中把
**BMAD Method** 的角色技能与 **AgentTeams** 的任务调度组合成四人软件开发团队。

本仓库只提供"协作约定"：BMAD 提供角色技能，AgentTeams 提供任务与质量门禁，
本套件提供团队画像、文档模板与审查纪律。

> **当前状态：GitHub 公开预览，真实 DSH/AgentTeams 集成验收尚未完成。** 本项目原创内容已采用 MIT 许可证，
> 版权署名为 Lai-yuanwei。本套件是独立社区项目，不代表 BMAD、AgentTeams 或 DSH 官方，
> 详情见 [LICENSE](./LICENSE) 与 [LICENSING.md](./LICENSING.md)。

## 包含内容

| 模块 | 文件 |
| --- | --- |
| 团队画像 | `./templates/team-profile.yml`（四成员、Captain 统一派单、K1–K4、`approval="required"`） |
| 项目规范 | `./templates/AGENTS.example.md`、`./templates/TEAM_SPEC.template.md` |
| 跨会话交接 | `./templates/START-HERE.template.md`、`./templates/HANDOFF.template.md`、`./templates/DISCOVERY.template.md` |
| 团队管理 Skill | `./skills/agent-team-manager/SKILL.md` |
| 可选治理检查器 | `./governance/`（事后范围/独立审查/交付哈希检查） |
| 指南 | `./docs/installation.md`、`workflow.md`、`configuration.md`、`limitations.md` |
| 示例 | `./examples/demo-project/`（通用任务清单小程序） |

**不包含**：BMAD 技能源码、AgentTeams 插件源码、DSH 文件；也不包含任务调度器或
"自动开发"能力。依赖请通过官方安装方式获取。

## 三种模式与四个关卡

| 模式 | 用途 |
| --- | --- |
| A | 交互式需求讨论：每轮一个决策；K1 前不建团队、不写正式 SPEC |
| B | 随时技术咨询：默认只读，任何阶段可问 |
| C | 正式开发执行：仅在明确关卡批准后建队 |

| 关卡 | 批准含义 |
| --- | --- |
| K1 | 需求访谈结束，允许编制正式 SPEC |
| K2 | SPEC 获批，允许开始完整架构设计 |
| K3 | 架构获批，允许编码与相应测试 |
| K4 | 用户确认最终交付 |

Captain 只负责派单与汇报，不替专业成员批准其环节；审查任务不得派给实现者。

## 快速开始

1. 阅读 `./docs/limitations.md`，了解门禁的能力边界。
2. 通过官方方式安装 BMAD 技能与 AgentTeams 插件。
3. 把模板复制到项目：`AGENTS.example.md` → `./AGENTS.md`，其余放入 `./docs/team/`。
4. 把 `./templates/team-profile.yml` 合并进 DSH 插件配置（先备份，重启 DSH）。
5. 用 `./templates/START-HERE.template.md` 末尾的提示词启动新会话。

## 文档

- 安装、备份、回滚：[`docs/installation.md`](./docs/installation.md)
- 工作流、证据要求：[`docs/workflow.md`](./docs/workflow.md)
- 配置项与路径约定：[`docs/configuration.md`](./docs/configuration.md)
- 能力边界（必须读）：[`docs/limitations.md`](./docs/limitations.md)
- 治理命令与离线回归案例：[`governance/README.md`](./governance/README.md)
- 跨会话恢复、返修与真实集成验收：[`docs/recovery.md`](./docs/recovery.md)

## 许可证

本项目原创内容采用 [MIT 许可证](./LICENSE)，版权署名为 Lai-yuanwei（2026 年）。
仓库当前已公开，但真实 DSH/AgentTeams 集成验收尚待完成。第三方依赖的版权与许可保持独立，
详见 [`LICENSING.md`](./LICENSING.md)。