# 2026-09-11 第二批任务准入与修复

本批从 main `3069479717c2d0db0b040babb42390bdcbb60cb1` 出发。#80 的原始 head
`4bb95061846a28a3025f4eb05cdd52210e12b11a` 保留为祖先；其余未通过准入的任务只发布独立修复分支。
合并前仍须完成当前源码的全局冻结证据及 GitHub CI，最终合并记录以集成 PR 为准。
库存为 86 题：42 optimization、44 discovery，5 certified、81 candidate。
新任务的 candidate 准入不是外部认证，也不证明长时反馈收益。

## 本批准入决定

| PR | 固定实测结果与修复 | 决定 |
|---|---|---|
| #80 SparseVectorAudit | 完整 positional reference 0.819398 / 0.729870；7 个固定方法各双跑，18 世界均有效、完整指标确定；每项能力消融降低开发分；151 项 Linux 回归和独立 13-call 贡献门通过；3 个独立有效首提案开发分 0.216592、0.276135、0.265220，均低于完整参考 | 候选准入，完成全局冻结与 CI 后合入；独立隐私领域评审待完成 |
| #72 DarkMatterRecoilAttribution | 补齐参考能力并完成预算、FDR 与隔离验证后，39 项 Linux 回归通过；3 次首提案完整保留：第 0 次 56/56 世界有效且开发 0.585543 高于参考 0.548640；第 1 次仅 49/56 有效、触发预算；第 2 次 0.280270 有效 | D16 失败，保持 open；修复分支 `codex/pr72-admission-fixes` |
| #79 LDMismatchFineMapping | 补齐 masking-aware 标准能力后参考 0.961834 / 0.945518；3 个首提案均 18/18 有效并精确追平参考。另修复 FDR 为 false valid claims / valid claims，旧错误拒答率独立命名；32 项 Linux 回归通过，baseline/reference 各双跑，全部非 FDR 科学字段与历史构造一致 | D16 失败，保持 open；修复分支 `codex/pr79-admission-fixes` |
| #82 CacheReplacementPolicyID | 修复独立世界会话、sticky budget、共享 wrapper 与 claim-denominator FDR；28 项 Linux fixture 回归通过。完整 permutation 参考已提供，但 `expected_score: null`，贡献门明确 incomplete | 完整参考、捷径和首提案标定未完成；修复分支 `codex/pr82-admission-fixes` |
| #47 F6SpinGlassGroundState | 148 项 Linux 回归通过，5 个程序各双跑；参考 0.986111，去 replica exchange 为 0.984568，去 quench 与参考同分 | 捷径分离和有效消融未通过；修复分支 `codex/pr47-admission-fixes` |
| #56 / #57 | Football 的完整参考/首提案证据不足；SortingNetwork 独立构造 0.016667 明显低于查表 0.496667，能力消融未建立 | 保持 open，不以查表成绩证明算法难度 |
| #83 ClockSyncInversion | 已复现负物理时延、沙箱 LP 后端失败；数值等价修复单列，完整多世界参考仍需验收 | 完整参考及 C/D 未通过前保持 open，失败不作为低科学分数 |

三个任务共 9 个预定首提案，全部保留：8 个完整有效、1 个部分无效。
#80 / #72 / #79 的 provider-reported returned-proposal token 分别为 52,280 / 44,696 / 52,200。
这些数不包含不可获得的失败 HTTP 请求用量，价格 unavailable，不能视为零费用。
没有根据 heldout 或失败结果选择候选、重试模型提案、调整阈值或重签旧测量。

## 系统修复与证据边界

20 个旧 evaluator 在独立世界入口启动新的候选进程和 tmpfs；同世界的多次 callback、控制器轨迹与远程 callable 状态保留。
修复前 20/20 实际泄漏测试失败，修复后 20/20 通过，另 1 项同世界状态回归通过；共检查 44 个世界边界和 88 次测试 callback。
这组测试验证隔离，不计作科学任务评测。实际修复为 20 个 evaluator 各 3 行，无世界、科学公式或分数更改。

HeatExchanger 和 Truss 的两份既有冻结候选分别在旧 main 与本批源码上双跑，8 次实际 sandbox 评测均有效。
完整指标与逐实例指标在前后四次结果间完全相同，支持这两份固定产物的兼容迁移，不能外推成所有程序等价。
原始产物、旧 metrics、source/runtime/hash 均保留；新兼容记录另存。

#80 首提案原始源为 c02e402。随后只更新 TASK_CARD 和 known_best 的记录，未改变 Task.md、候选可见契约、oracle、参考、世界、预算或分数。
固定计划另将三份原始程序各重评两次，逐键对比原回执；六次结果全部有效且完整指标均与原回执一致；该计划是文档更新后的兼容性检查，模型调用为 0。
公开结果见 `experiments/sparse_vector_first_draw_compatibility_2026-09-11.json`。
完整私有指标和模型响应保存在源树外的 0700 目录；公开证据只含汇总、分母、文件哈希和来源绑定。

审计代码将已移除的 `ast.Str` 检查替换为 `ast.Constant` 字符串检查，保持 Python 3.8 兼容并修复 Python 3.14 审计失败。
新增 docstring 与数字/bytes 常量的区别回归。便携卡片/库存/分类回归 20 passed，另 5 subtests。
CI 固定要求执行 #80 的 18 项检查及旧任务隔离的 20 项检查，缺收集或跳过均不能算通过。

## 保留的队列与后续条件

新的 GitHub 快照记录 34 个 open PR、15 个 draft，原始 head 未按本地修复分支改写。
#74 固定策略分离仍不满足；#73 付费代数策略较强；#60 缺少历史更强策略的精确源码；#30 LP 失败不能被当作数学方案无效。
#17 的运行时修复与 family/lifetime-credit 提案保持独立；本批没有启用其语义。
其他未复验投稿保留 `unreviewed` 或既有 blocker，不因旧 CI 绿色而自动合入。
