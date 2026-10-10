# AlphaMosaic 审计与升级报告

审计日期：2026-10-10
审计范围：源码、测试、插件、文档、构建配置、工作区卫生和 Git 发布准备。

## 结论

项目结构符合 src-layout，`ApplicationService` 是 CLI 与 MCP 的共同编排入口，领域代码未发现对 CLI/MCP/供应商实现的反向依赖。研究与纸面评估边界清晰，没有发现 broker 下单路由或凭据提交实现。

本次验证结果：Ruff 通过、Pyright 通过、pytest 通过（当前测试集 10 项）。本地工作区已移除缓存、残留虚拟环境和临时构建目录；运行时报告目录保留，因为其中可能包含可追溯的研究证据。

## 风险与缺口

1. 已验证 SiriZhao/alpha-mosaic 为私有仓库且当前用户拥有 ADMIN 权限。远端与本地 main 历史独立；本次审计发布至独立分支，不覆盖远端回测成果。
2. 当前研究数据仍存在生存者偏差、重建历史数据 PIT/公司行动覆盖不足、基本面与事件数据不完整等限制。
3. OpenBB、TradingAgents、Danelfin 的真实外部验收与远程 ChatGPT MCP 调用仍未验证；未配置时必须继续保持 `NOT_CONFIGURED`/`NOT_VERIFIED`。
4. CI 文件已被 Git 跟踪，但没有可验证的远端运行结果；发布前必须取得实际 CI 证据。
5. 测试覆盖基础契约和集成边界，仍应补充数据质量、PIT、风险边界、MCP 认证和安装后 CLI/MCP 冒烟路径。

## 保留与清理决策

- 保留 `tests/`：这些是有效的回归和集成边界，不属于无用测试。
- 保留 `docs/acceptance/`：它是已记录的验收证据。
- 删除缓存与临时目录：`.pytest_cache`、`.ruff_cache`、残留虚拟环境、多个 `*-cache`、`final-*` 临时目录。
- 保留 `runtime/`：它被 `.gitignore` 忽略，但可能包含研究报告和运行证据，不能按“临时文件”盲删。

## 下一步升级顺序

1. 恢复 GitHub CLI 登录，核对目标仓库为私有且归属正确；再添加 remote。
2. 在干净环境执行 lint、类型检查、测试、wheel/sdist 构建、清洁安装及 CLI/MCP 冒烟。
3. 增加显式 opt-in 的真实网络验收快照，并为 PIT、证券身份、交易所、币种、调整策略和陈旧数据增加失败测试。
4. 接入有许可的 PIT 基本面、公司行动、新闻和事件数据；在独立历史快照验证前，不提升策略状态。
5. 配置 GitHub Actions 后，以实际运行结果记录 CI；部署远程 MCP 前保持本地绑定、Bearer 认证和 HTTPS 前置要求。

## 可执行 Codex 指令

```text
审计 E:\CSDIY\Vibe Coding Project\AlphaMosaic：先验证仓库根目录、Git remote 所有权和当前分支；运行 ruff、pyright、pytest、wheel/sdist 构建、清洁安装、CLI doctor/providers 和本地 stdio/HTTP MCP 冒烟。只删除已确认的缓存和临时构建物，不删除 tests、docs/acceptance、runtime 证据或未知文件。修复真实缺陷后更新 CURRENT_STATE.md、NEXT_STEPS.md 和 AUDIT_REPORT.md，扫描 staged 文件中的凭据与运行时数据，提交自包含变更；只有在 GitHub 私有仓库归属、认证和远端 HEAD 均验证成功后才推送，并报告本地与远端 SHA。
```
