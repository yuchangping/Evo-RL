# Evo-RL 论文整合版结果填空与收尾清单

> 时间基准：2026-04-02  
> 关联文档：`Evo-RL论文整合版.md`、`实验计划表.md`、`RQ1_relabeling与标签统计实施方案.md`  
> 重要约束：**本文件只做论文整理，不修改任何代码文件。**  
> 目标：把整合版论文中还缺的 `结果数值 / 图表 / citation / appendix / 投稿收尾动作` 压成一份可直接执行的清单。

---

## 0. 这份文档解决什么问题

你现在已经有一份可以连续通读的主论文草稿：

- [Evo-RL论文整合版.md](/home/jy/Data/YCP/Evo-RL/Evo-RL论文整合版.md)

它的优点是：

- 结构完整
- 方法叙事完整
- 实验章节骨架完整
- 讨论和结论已经成文

它目前最缺的，不是“论文怎么写”，而是下面四类硬缺口：

1. **主结果表的真实数值**
2. **图 1 到图 5 的正式图稿**
3. **Related Work 与 Introduction 里的正式 citation**
4. **Appendix 和实验细节的可提交化补齐**

所以这份文档的作用，不是再重写一遍论文，而是把整合版推进到下面这个状态：

```text
连续草稿
    ->
结果填空
    ->
图表落位
    ->
引用补齐
    ->
appendix 补齐
    ->
投稿前润色
```

---

## 1. 当前整合版还缺什么

结合 [Evo-RL论文整合版.md](/home/jy/Data/YCP/Evo-RL/Evo-RL论文整合版.md) 当前内容，真正还需要落地的内容可以分成五层。

### 1.1 第一层：主文必须有的硬结果

- `TBL-1` Main Task Performance
- `TBL-2` Recovery and Correction
- `TBL-3` Human Budget Efficiency
- `TBL-4` Unified Ablation
- `FIG-1` Framework Overview
- `FIG-2` Intervention Semantics
- `FIG-3` Recovery Performance
- `FIG-4` Success vs Human Budget
- `FIG-5` Qualitative Rollouts

### 1.2 第二层：正文里需要替换的“空结果句”

整合版中很多段落已经写成了投稿口吻，但数值还是空位，例如：

- “As shown in Table 1”
- “improves over”
- “becomes more pronounced”
- “achieves a better trade-off”

这些句子不需要重写结构，只需要在真实实验完成后，把：

- 相对表述改成定量表述
- “consistently improves” 改成具体百分点
- “better trade-off” 改成曲线面积、固定预算成功率或监控时间减少比例

### 1.3 第三层：正式引用

当前整合版已经有 Related Work 结构，但缺：

- 真实文献条目
- 每一段里更精确的 citation 分布
- 方法差异点的引文支撑

### 1.4 第四层：Appendix 补全

Appendix 现在只有计划，还没有真正成文。投稿前至少要补：

- semantic label rule table
- trigger threshold details
- hardware and rollout setup
- extra metric tables
- more qualitative cases

### 1.5 第五层：投稿前风格收口

最后一轮需要做的不是大改方法，而是：

- 统一方法名
- 统一表格命名
- 统一 metric 名称
- 统一数据集和任务描述
- 统一 “we aim to / we show / we evaluate” 的语气

---

## 2. 主结果表填空模板

这一节的目标不是给你最终数值，而是把表结构固定下来。  
你后面拿到实验结果后，直接把数值填进去即可。

## 2.1 `TBL-1` Main Task Performance

### 论文作用

回答 `RQ1`：

- Intervention-aware relabeling 是否优于原始 binary ACP？

### 推荐表题

`Table 1. Main task performance under nominal and perturbed evaluations.`

### 推荐列设计

| Method | Scenario | K1 Success Rate | K2 Avg Episode Length | K3 Intervention Frame Ratio | K12 Advantage-Label Quality |
| --- | --- | --- | --- | --- | --- |
| `M0` BC | `S1` Nominal | `--` | `--` | `--` | `--` |
| `M1` ACP-Base | `S1` Nominal | `--` | `--` | `--` | `--` |
| `M2` ACP-InterventionPositive | `S1` Nominal | `--` | `--` | `--` | `--` |
| `M4` IA-ACP | `S1` Nominal | `--` | `--` | `--` | `--` |
| `M0` BC | `S2` Perturbed | `--` | `--` | `--` | `--` |
| `M1` ACP-Base | `S2` Perturbed | `--` | `--` | `--` | `--` |
| `M2` ACP-InterventionPositive | `S2` Perturbed | `--` | `--` | `--` | `--` |
| `M4` IA-ACP | `S2` Perturbed | `--` | `--` | `--` | `--` |

### 主文应写出的结论

- `M4` 相比 `M1` 在 nominal 和 perturbed 下是否都更优
- `M2` 是否说明 “all intervention = positive” 不足够
- `K12` 是否支持语义标签确实有质量

### 推荐正文句式模板

```text
As shown in Table 1, IA-ACP improves success rate from [x] to [y] under nominal rollout and from [x] to [y] under perturbed initialization, outperforming both binary ACP and the intervention-all-positive heuristic. The gains are accompanied by improved label quality statistics, suggesting that the semantic relabeling captures more informative supervision than binary conditioning alone.
```

## 2.2 `TBL-2` Recovery and Correction

### 论文作用

回答 `RQ2`：

- correction distillation 是否真正提升恢复能力？

### 推荐表题

`Table 2. Recovery and correction performance in perturbed and near-failure evaluations.`

### 推荐列设计

| Method | Scenario | K5 Recovery Success Rate | K6 Post-Intervention Success | K11 Correction Gap | Notes |
| --- | --- | --- | --- | --- | --- |
| `M1` ACP-Base | `S2` Perturbed | `--` | `--` | `--` | `--` |
| `M4` IA-ACP | `S2` Perturbed | `--` | `--` | `--` | `--` |
| `M5` IA-ACP + Corr | `S2` Perturbed | `--` | `--` | `--` | `--` |
| `M1` ACP-Base | `S3` Near-Failure | `--` | `--` | `--` | `--` |
| `M4` IA-ACP | `S3` Near-Failure | `--` | `--` | `--` | `--` |
| `M5` IA-ACP + Corr | `S3` Near-Failure | `--` | `--` | `--` | `--` |

### 主文应写出的结论

- `M5` 是否显著提高 recovery success
- `M5` 的收益是否主要体现在 recovery-heavy 场景
- `K11` 是否能支持“确实学到了纠正而不是只学到了更多 imitation”

### 推荐正文句式模板

```text
Table 2 shows that adding correction distillation substantially improves recovery-oriented metrics, especially in forced near-failure scenarios. This suggests that proposal-correction pairing provides supervision that is complementary to semantic relabeling alone.
```

## 2.3 `TBL-3` Human Budget Efficiency

### 论文作用

回答 `RQ3`：

- learned query 是否能减少人类成本？

### 推荐表题

`Table 3. Human-budget efficiency under fixed monitoring constraints.`

### 推荐列设计

| Method | Budget Setting | K7 Monitoring Time | K8 Success Under Fixed Budget | K9 Precision | K10 Recall |
| --- | --- | --- | --- | --- | --- |
| Always Monitor | `B1` | `--` | `--` | `--` | `--` |
| `M8` Heuristic-Query | `B1` | `--` | `--` | `--` | `--` |
| `M7` Full / Learned Query | `B1` | `--` | `--` | `--` | `--` |
| Always Monitor | `B2` | `--` | `--` | `--` | `--` |
| `M8` Heuristic-Query | `B2` | `--` | `--` | `--` | `--` |
| `M7` Full / Learned Query | `B2` | `--` | `--` | `--` | `--` |

### 主文应写出的结论

- learned query 在相同预算下是否最优
- 如果 success 相近，它是否监控时间更少
- precision 和 recall 是否说明它不是“多报求稳”

### 推荐正文句式模板

```text
Compared with heuristic querying, the learned trigger achieves a better success-versus-monitoring trade-off, preserving more task performance under the same human budget while maintaining higher precision in selecting informative intervention moments.
```

## 2.4 `TBL-4` Unified Ablation

### 论文作用

回答 `RQ4`：

- 三个模块联合是否优于单独使用？

### 推荐表题

`Table 4. Unified ablation of semantic relabeling, correction distillation, and learned querying.`

### 推荐列设计

| Method | IA Relabel | Corr Distill | Query | K1 Success Rate | K5 Recovery Success | K8 Success Under Budget |
| --- | --- | --- | --- | --- | --- | --- |
| `M4` IA-ACP | Yes | No | No | `--` | `--` | `--` |
| `M5` IA-ACP + Corr | Yes | Yes | No | `--` | `--` | `--` |
| `M6` IA-ACP + Query | Yes | No | Yes | `--` | `--` | `--` |
| `M7` Full | Yes | Yes | Yes | `--` | `--` | `--` |

### 主文应写出的结论

- `M4` 主要改善监督质量
- `M5` 主要改善 recovery
- `M6` 主要改善 budget efficiency
- `M7` 是否在三类指标上综合最好

---

## 3. 图稿制作模板

## 3.1 `FIG-1` Framework Overview

### 作用

让 reviewer 第一眼看懂你不是三个散点技巧，而是一条闭环链：

```text
rollout collection
    ->
value inference
    ->
semantic relabeling
    ->
correction distillation
    ->
policy training
    ->
query-efficient deployment
    ->
next round rollout
```

### 图中必须出现的元素

- observation / task text
- policy-proposed action
- executed action
- human intervention
- value inference
- semantic tags
- correction loss
- request-for-help trigger

### 推荐 caption 模板

```text
Figure 1. Overview of CHILO. Human takeover trajectories are converted into three aligned supervision signals: intervention-aware semantic relabeling for policy conditioning, proposal-correction pairs for correction distillation, and deployment-time risk signals for query-efficient assistance.
```

## 3.2 `FIG-2` Intervention Semantics

### 作用

服务 `RQ1`，证明 semantic label 不是拍脑袋分类。

### 推荐做成两部分

- `FIG-2(a)` 典型 rollout 时间线
- `FIG-2(b)` label distribution / label-quality statistics

### 需要的数据

- label 数量占比
- 每种 label 对应的 mean advantage
- 每种 label 对应的 mean correction gap
- 每种 label 所在 episode 的 success ratio

### 推荐 caption 模板

```text
Figure 2. Intervention-aware semantic relabeling. Left: an example rollout with autonomous, correction-onset, recovery-positive, and recovery-tail segments. Right: label statistics showing that the proposed semantic tags align with advantage, correction magnitude, and episode outcome.
```

## 3.3 `FIG-3` Recovery Performance

### 作用

服务 `RQ2`，让 correction distillation 的优势不仅停留在表格里。

### 推荐形式

- bar chart: recovery success rate
- line / bar: post-intervention success
- 可补一个 rollout case timeline

### 推荐 caption 模板

```text
Figure 3. Recovery-oriented evaluation. Correction distillation improves the policy's ability to return to successful execution after entering difficult or failure-prone states.
```

## 3.4 `FIG-4` Success vs Human Budget

### 作用

服务 `RQ3`，这是 query-efficient deployment 的核心图。

### 推荐横纵轴

- x 轴：monitoring budget
- y 轴：success rate

或者：

- x 轴：monitoring time
- y 轴：task success

### 同图曲线

- Always Monitor
- Heuristic Query
- Learned Query / Full

### 推荐 caption 模板

```text
Figure 4. Success versus human monitoring budget. The learned trigger preserves higher task performance under limited supervision and provides a better trade-off than heuristic querying.
```

## 3.5 `FIG-5` Qualitative Rollouts

### 作用

服务 `RQ5` 和 Discussion，体现系统行为层面的差异。

### 推荐案例类型

- 一个成功但需要短暂接管的案例
- 一个 correction distillation 成功恢复的案例
- 一个 query 及时触发避免失败的案例
- 一个 false positive 或 false negative 案例

### 推荐 caption 模板

```text
Figure 5. Qualitative rollout timelines. The examples illustrate how semantic relabeling, correction-aware learning, and learned assistance triggering alter the temporal structure of deployment behavior.
```

---

## 4. 正文逐节补齐清单

这一节对应 [Evo-RL论文整合版.md](/home/jy/Data/YCP/Evo-RL/Evo-RL论文整合版.md) 的实际收尾。

## 4.1 Title

要最终定三件事：

- 是否保留 `CHILO`
- 标题更偏算法还是更偏系统
- 副标题是否显式点出 human takeovers

### 当前最稳的两个选择

1. `A Unified Framework for Learning from Human Corrections in Closed-Loop Robot Deployment`
2. `Closed-Loop Robot Learning from Human Takeovers: Semantic Conditioning, Action Correction, and Query-Efficient Assistance`

## 4.2 Abstract

Abstract 现在结构已经完整，但投稿前要补：

- 真实平台与任务一句
- 真实结果一句
- 一个最关键定量 improvement

### 应补充的结果位

```text
Compared with binary ACP, CHILO improves [metric] by [x] while reducing [human-cost metric] by [y].
```

## 4.3 Introduction

Introduction 当前最缺的是：

- 1 到 2 个最强定量 teaser
- 更精确的 citation 支撑

建议第一段末尾或第二段加入一句：

```text
On a real dual-arm handover task, our full method improves [recovery success / fixed-budget success] by [x] over [baseline].
```

## 4.4 Related Work

Related Work 不建议继续加新方向，先把已有三块写实：

- human-in-the-loop robot learning
- learning from corrections
- value-guided relabeling / data reweighting
- budget-aware querying / request-for-help

这里最重要的不是篇数多，而是每一块都能明确写出：

- prior work 做了什么
- 还缺什么
- 你和它的差别是什么

## 4.5 Method

Method 现在已经足够成文，投稿前主要做四件事：

- 统一记号
- 补一个训练算法框图或 pseudo-code
- 明确 `q_t` 和 `r_t` 的定义是 learned 还是 calibrated heuristic
- 明确 correction head 是 residual head 还是 auxiliary loss

## 4.6 Experiments

Experiments 现在最缺的是实锤：

- 每个场景的 episode 数
- 每个 baseline 的训练轮数
- 人类预算单位
- evaluation seeds / repeated trials

### 最容易被 reviewer 问到的问题

- 真实机器人实验总共多少条 rollout？
- 每个方法是否使用相同人类数据预算？
- fixed budget 的定义是什么？
- 是否有不同操作者？

## 4.7 Results

Results 章节现在已经有完整论述顺序，但每一节都需要插入：

- 至少 1 个核心定量句
- 至少 1 个和 baseline 的直接对比句
- 至少 1 个场景差异句

### 推荐写法

每个小节按这个顺序写：

1. 先报一个最强结果
2. 再解释为何支持你的 claim
3. 最后补一个 failure mode 或边界说明

## 4.8 Discussion / Limitations / Future Work

这三节当前已经够完整。  
投稿前只需要：

- 删掉和 Results 重复太多的句子
- 把 limitations 写得更具体
- future work 保留 2 到 3 条最像下一篇论文的方向

---

## 5. 引用补齐矩阵

这一节不是正式 bibliography，而是一个“你该去补哪些类文献”的导航表。

## 5.1 Human-in-the-Loop Robot Learning

这一类用于支撑：

- human intervention 在真实机器人部署中的必要性
- interactive data collection / iterative improvement 的合理性

### 你在正文里需要这些引用的位置

- Introduction 第一页
- Related Work 2.1
- Experiments 中对 HIL setup 的合理性说明

## 5.2 Learning from Corrections / Interventions

这一类用于支撑：

- proposal-correction pairing 不是凭空来的
- correction 比单纯 demonstration 更有结构信息

### 你在正文里需要这些引用的位置

- Related Work 2.2
- Method 4.2 前一段
- Results 6.2 的解释段

## 5.3 Value-Guided Relabeling / Reward-Aware Training

这一类用于支撑：

- ACP / RA-BC / SARM 一类方法的背景
- value / reward / stage 信号可作为策略监督

### 你在正文里需要这些引用的位置

- Related Work 2.3
- Method 4.1
- Baselines 5.2

## 5.4 Query-Efficient Assistance / Budget-Aware Querying

这一类用于支撑：

- request-for-help 的必要性
- limited human budget 是一个真实系统问题

### 你在正文里需要这些引用的位置

- Related Work 2.4
- Method 4.3
- Results 6.3

## 5.5 系统和真实机器人部署类引用

如果你最终想把文章更偏系统化，就补这类引用：

- real-world deployment
- scalable robot data collection
- human supervision bottleneck
- multi-round improvement pipeline

---

## 6. Appendix 最低补齐标准

如果时间有限，Appendix 不要追求大而全，先保证 reviewer 想看的最低信息都能找到。

## 6.1 Appendix A: Semantic Relabeling Details

至少放：

- 5 类标签定义表
- onset / recovery / tail 判定规则
- advantage threshold 说明
- correction gap 统计定义

## 6.2 Appendix B: Experimental Details

至少放：

- 机器人平台简介
- 三相机配置
- teleoperation 方式
- rollout round 数
- 每轮采集数量
- 训练超参数摘要

## 6.3 Appendix C: Additional Quantitative Results

至少放：

- 全指标详细表
- 每个场景分开结果
- 方差或 repeated-trial 结果
- query threshold sweep

## 6.4 Appendix D: Qualitative Cases

至少放：

- 典型成功案例
- 恢复失败案例
- false positive query
- false negative query

---

## 7. 投稿前两周执行顺序

如果你准备把这篇稿子真正收口，我建议按下面顺序推进。

## 7.1 第一阶段：先补最缺的主结果

- 完成 `RQ1` 的 relabeling 统计
- 填 `TBL-1`
- 画 `FIG-2`
- 完成 `RQ2` 核心恢复评测
- 填 `TBL-2`
- 画 `FIG-3`

## 7.2 第二阶段：补 query 和统一 ablation

- 定义 monitoring budget
- 完成 `RQ3`
- 填 `TBL-3`
- 画 `FIG-4`
- 完成 `RQ4`
- 填 `TBL-4`

## 7.3 第三阶段：补图、引用和 appendix

- 画 `FIG-1`
- 选 `FIG-5` 案例
- 补 bibliography
- 写 Appendix A-D

## 7.4 第四阶段：最后一轮语言润色

- Abstract 补定量
- Introduction 加 teaser result
- Results 中每节都加明确数字
- 压缩重复句
- 统一方法名与表述

---

## 8. 最终投稿检查表

- [ ] 标题是否已经最终确定
- [ ] `CHILO` 是否保留为正式方法名
- [ ] `TBL-1 ~ TBL-4` 是否全部有真实数值
- [ ] `FIG-1 ~ FIG-5` 是否全部有正式图稿
- [ ] Introduction 是否有 teaser result
- [ ] Abstract 是否有至少一个明确百分点提升
- [ ] Related Work 是否每段都有 citation 支撑
- [ ] 方法部分是否与真实实现保持一致
- [ ] query 触发机制是否说清 learned / heuristic / calibrated
- [ ] 实验预算定义是否清晰
- [ ] Appendix 是否补齐 label rule 和实验细节
- [ ] 所有指标名是否统一
- [ ] 所有 baseline 名称是否统一
- [ ] 任务名 `bi_so101_handover_cube` 是否统一出现

---

## 9. 一句话结论

整合版论文现在已经不是“缺结构”，而是“缺证据”。  
你接下来最应该做的，不是再改写章节，而是按照这份清单把 `TBL-1 ~ TBL-4`、`FIG-1 ~ FIG-5`、citation 和 appendix 一次性补齐。
