# Evo-RL 论文初稿版（Related Work + Experiments）

> 时间基准：2026-04-02  
> 承接文档：`Evo-RL论文初稿版_Introduction_Method.md`、`Evo-RL论文大纲版.md`、`实验计划表.md`  
> 用途：承接现有 `Introduction + Method`，继续补成论文初稿的 `Related Work + Experiments` 部分。  
> 写法说明：正文尽量采用论文英文风格；中文备注用于帮助你后续改稿与对齐实验实现。

---

## 0. 使用说明

这份文档默认和 [Evo-RL论文初稿版_Introduction_Method.md](/home/jy/Data/YCP/Evo-RL/Evo-RL论文初稿版_Introduction_Method.md) 一起使用。

推荐拼接顺序是：

1. Title
2. Abstract
3. Introduction
4. Related Work
5. Problem Setup / Method
6. Experiments
7. Limitations / Conclusion

也就是说，这份文档主要解决两个问题：

- 论文里别人做过什么，你和他们差在哪
- 你的实验应该怎么组织成 reviewer 容易接受的结构

---

## 1. Related Work Draft

### 1.1 Section Opening Paragraph

#### English Draft

Human intervention has played an increasingly important role in real-world robot learning, especially in settings where pure offline training is insufficient for robust deployment. Prior work has explored human-in-the-loop reinforcement learning, interactive imitation learning, intervention-aware policy learning, and assistance-trigger mechanisms. However, these directions have largely evolved in parallel. Some methods use interventions mainly as corrective demonstrations, some focus on sample-efficient policy improvement with humans in the loop, and others study when the robot should request help during deployment. In contrast, our work argues that a human takeover trajectory contains at least three reusable signals at once: semantic information about failure and recovery, action-level correction supervision, and deployment-time evidence that autonomous execution has become unreliable. We therefore position our work at the intersection of human-in-the-loop robot learning, learning from corrections, value-guided policy improvement, and query-efficient deployment.

#### 作者备注

- 这段的任务不是塞 citation，而是先把“相关工作被分裂成几条线，而你把它们统一了”说出来。
- 这句话很关键：
  - `a human takeover trajectory contains at least three reusable signals`
- 它能把你三条方法线自然统一到 related work 里。

---

## 1.2 Human-in-the-Loop Robot Learning and Deployment

### English Draft

Human-in-the-loop robot learning has been explored as a practical strategy for improving performance in real-world manipulation, where fully autonomous training remains difficult and costly. Interactive imitation learning and deployment-time correction have shown that human supervision can significantly improve robustness and data efficiency relative to pure offline imitation. More recent systems such as Sirius and HIL-SERL highlight the importance of intervention during real-world training and deployment, demonstrating that human guidance can help the robot recover from failures, explore more safely, and improve sample efficiency. These works provide strong evidence that human takeover is valuable in practice.

However, most of these approaches primarily treat intervention as a mechanism for collecting better trajectories or guiding policy updates, rather than as a structured object of analysis. In particular, intervention frames are often consumed either as additional demonstrations or as online corrections without explicitly distinguishing takeover onset, recovery dynamics, and low-value post-recovery segments. Our work builds on the same practical motivation as these methods, but takes a different view: instead of using intervention only as additional supervision, we reinterpret intervention trajectories as structured signals that can be relabeled, distilled, and reused across training and deployment.

### 可引用工作

- `Sirius: Robot Learning on the Job`
- `HIL-SERL`
- 其他 human-in-the-loop robot learning / interactive imitation learning 工作

### 作者备注

- 这一节要强调：
  - 你不是否定 HIL-SERL 这类工作
  - 你是在它们基础上进一步挖 intervention 的结构
- 推荐句式：
  - `While prior work demonstrates the utility of human intervention, we focus on extracting richer supervisory structure from intervention trajectories themselves.`

---

## 1.3 Learning from Corrections and Interventions

### English Draft

Another line of work studies how robot policies can learn directly from corrections or imperfect demonstrations. Intervention-aware learning, counterfactual imitation, and correction-based policy updates all share the intuition that what the human does during recovery is especially informative. In particular, recent work such as Counter-BC emphasizes that imperfect demonstrations still contain recoverable intent, while intervention-based methods show that human overrides can guide the robot away from failure states.

Our work is closely related to this literature, but differs in an important respect. Existing approaches typically observe the corrected action alone, or treat intervention as a standalone supervisory event. In our setting, the system records both the policy-proposed action and the executed human-corrected action during deployment. This paired structure enables a stronger form of supervision: not only can we learn what action was taken, but we can also learn how the deployed policy should have changed its decision in the same state. This is the basis of our counterfactual human correction distillation objective.

### 可引用工作

- `Counter-BC`
- intervention-aware imitation / learning from corrections
- emergency-stop or human override learning papers

### 作者备注

- 这一节最应该突出的差别是：
  - `corrected action only`
  - vs
  - `policy proposal + corrected action pair`
- 你最强的一句话可以是：
  - `Our setting provides paired rollout-time counterfactual supervision rather than correction-only supervision.`

---

## 1.4 Value-Guided Policy Improvement and Reward-Aware Data Reweighting

### English Draft

Value-guided and reward-aware policy improvement methods aim to improve policy learning by distinguishing higher-quality from lower-quality trajectory segments. Advantage-conditioned policy training, reward-aware behavior cloning, and stage-aware reward modeling all follow this general principle: rather than imitating all data uniformly, they attempt to prioritize samples that are more useful for improving policy quality. These ideas are particularly attractive for robot learning, where data collection is expensive and not all frames contribute equally to downstream performance.

Our work is aligned with this perspective, but extends it in two ways. First, we argue that binary advantage labels are insufficient in human-in-the-loop rollout datasets because intervention trajectories contain semantically different states that should not be collapsed into the same supervision class. Second, we connect value-guided relabeling to both action-level correction learning and deployment-time request-for-help decisions. In this sense, our method does not replace value-guided policy improvement; rather, it enriches it with intervention semantics and closes the loop between relabeling, training, and deployment.

### 可引用工作

- ACP / advantage-conditioned training
- RA-BC
- SARM
- DataMIL

### 作者备注

- 这一节的关键定位是：
  - 你不是跟 ACP 对立
  - 你是 `binary ACP -> intervention-aware ACP`
- 这句话很适合放最后：
  - `We extend value-guided relabeling from a scalar quality signal to a structured supervision signal grounded in human intervention dynamics.`

---

## 1.5 Assistance Trigger and Query-Efficient Deployment

### English Draft

When to request human help is itself a central question in deployment-time robot learning. Prior work in interactive imitation learning and budget-aware supervision, such as ThriftyDAgger and more recent robot-gated assistance mechanisms, studies how to reduce human burden by intervening only when necessary. These methods show that selective querying can substantially improve the efficiency of human supervision.

Our work shares this motivation but differs in the source of the trigger signal. Rather than treating assistance as a standalone decision problem, we derive request-for-help decisions from the same closed-loop signals that also support relabeling and correction learning, including value-based risk, action disagreement, and intervention history. As a result, assistance triggering becomes part of a unified intervention-aware pipeline rather than a separate module. This enables us to ask not only whether the robot can request help efficiently, but whether doing so also improves the usefulness of the data collected for the next training round.

### 可引用工作

- `ThriftyDAgger`
- `AIM`
- runtime monitoring / interactive imitation learning
- uncertainty-based robot-gated assistance

### 作者备注

- 这一节不要写成“我们第一个研究 request-for-help”，那样容易被 reviewer 直接反驳。
- 更稳妥的写法是：
  - `We integrate assistance triggering into the same intervention-aware closed-loop learning pipeline.`

---

## 1.6 Related Work Closing Paragraph

### English Draft

In summary, prior work has established that human intervention is valuable for real-world robot learning, that corrections can improve policy robustness, that value-guided relabeling can improve training, and that selective querying can reduce supervision cost. Our contribution is to unify these observations within a single closed-loop framework. Instead of using intervention as only a demonstration, only a correction, or only a request signal, we treat takeover trajectories as structured supervision that simultaneously supports semantic relabeling, correction distillation, and query-efficient deployment.

### 作者备注

- 这段建议直接作为 `Related Work` 结尾。
- 它能非常自然地把读者从别人的工作拉回你的方法。

---

## 2. Experiments Draft

## 2.1 Section Opening Paragraph

### English Draft

We evaluate CHILO in a real-world closed-loop human-in-the-loop manipulation setting. Our experiments are designed to answer five questions: (1) whether intervention-aware relabeling improves over standard binary advantage conditioning, (2) whether correction distillation improves recovery behavior, (3) whether learned request-for-help reduces human supervision cost, (4) whether the three components are complementary, and (5) under which scenarios the gains are most pronounced. To this end, we evaluate the method under nominal execution, perturbed initial states, forced near-failure recovery scenarios, and constrained human-budget deployment settings.

### 作者备注

- 这一段建议直接作为 `Experiments` 开头。
- 它已经和你实验计划表里的 `RQ1-RQ5` 对齐了。

---

## 2.2 Experimental Setup

### English Draft

#### Tasks and platform

We perform experiments on a real dual-arm SO101 platform equipped with three RGB cameras and a human teleoperation interface. Our primary task is `bi_so101_handover_cube`, in which the robot must pick up a cube with the left arm and hand it to the right arm. This task is particularly suitable for evaluating intervention-aware learning because it is long-horizon, requires coordination across both arms, and often exhibits recovery-critical failure modes.

#### Closed-loop pipeline

We follow a closed-loop training protocol. Starting from demonstration data, we train an initial policy and deploy it with human-in-the-loop correction. The resulting rollout data are merged into the training pool, used to train a value function, and relabeled with frame-level value, advantage, and intervention-aware semantic labels. Policies are then trained from these relabeled data and redeployed in the next round. This setup matches the practical training loop used in our system and allows us to measure not only final policy performance but also the quality of the iterative improvement process.

#### Evaluation scenarios

We evaluate the method under four deployment settings. In **nominal rollout**, policies are evaluated from standard initial states without artificial disturbance. In **perturbed-init evaluation**, the task begins from more challenging initial configurations to test robustness. In **forced near-failure evaluation**, the robot is deliberately brought close to states that previously triggered human takeover, and success is measured after recovery. In **fixed-budget deployment**, the amount of human supervision is constrained to evaluate the request-for-help mechanism under limited intervention resources.

### 作者备注

- 目前这一节先按你现有真实平台写。
- 如果后面你补第二任务，这里再扩成：
  - `We evaluate on two dual-arm manipulation tasks...`
- 当前最重要的是把 4 个场景写清楚：
  - nominal
  - perturbed
  - recovery-heavy
  - fixed-budget

---

## 2.3 Baselines

### English Draft

We compare CHILO against several baselines representing different uses of rollout supervision. **BC** performs standard behavior cloning on the collected dataset without value-based relabeling. **ACP-Base** uses standard binary advantage-conditioned policy training. **ACP-InterventionPositive** assigns all intervention frames to the positive class, testing whether a simple intervention heuristic is sufficient. **RA-BC / SARM** represents reward-aware or stage-aware reweighting baselines already supported in our training stack. For the assistance-trigger experiments, we additionally compare against **Always Monitor**, in which a human continuously supervises deployment, and **Heuristic Query**, which requests assistance based on a fixed hand-designed rule. Finally, we evaluate ablations of our method corresponding to intervention-aware relabeling only, relabeling plus correction distillation, relabeling plus learned query, and the full model.

### 作者备注

- 这段建议和 [实验计划表.md](/home/jy/Data/YCP/Evo-RL/实验计划表.md) 的 `M0-M8` 编号配套使用。
- 真正写论文时，最好在段末注明：
  - all methods use the same base policy architecture
  - all methods use comparable data budgets

---

## 2.4 Metrics

### English Draft

We report three groups of metrics. **Task performance** includes task success rate and average episode length. **Recovery performance** includes recovery success rate and post-intervention success rate, measuring whether the policy can return to successful execution after entering difficult states. **Human-cost metrics** include intervention frame ratio, intervention count per episode, monitoring time, success under fixed human budget, and request-for-help precision and recall. Together, these metrics capture not only how well the robot solves the task, but also how efficiently it uses human supervision during deployment.

### 作者备注

- 这一节的关键词不是“指标越多越好”，而是：
  - `task performance`
  - `recovery`
  - `human cost`
- 这三组指标正好对应你三条方法线。

---

## 2.5 RQ1: Does Intervention-Aware Relabeling Improve over Binary ACP?

### English Draft

We first evaluate whether intervention-aware relabeling improves policy learning relative to standard binary advantage conditioning. This comparison isolates the contribution of richer semantic supervision while keeping the underlying policy architecture fixed. We compare BC, ACP-Base, ACP-InterventionPositive, and Intervention-Aware ACP under nominal rollout and, when possible, perturbed initial conditions.

Beyond final task performance, we analyze the semantic label distribution and its quality. Specifically, we report how often each label occurs and how each label correlates with frame-level advantage, action-correction magnitude, and episode success. These statistics help determine whether intervention-aware relabeling captures meaningful structure rather than introducing arbitrary label fragmentation.

Our hypothesis is that intervention-aware relabeling improves over binary ACP because it distinguishes autonomous progress from corrective intervention and separates useful recovery segments from low-value takeover tails. If this hypothesis holds, we expect improved success rates and cleaner supervision statistics relative to the binary and intervention-all-positive baselines.

### 对应主文输出

- `TBL-1`
- `FIG-2`

### 作者备注

- `RQ1` 一定要强调：
  - no architecture change
  - only relabeling change
- 否则 reviewer 很容易说，你的提升是不是来自别的地方。

---

## 2.6 RQ2: Does Correction Distillation Improve Recovery?

### English Draft

We next study whether explicit correction distillation improves recovery behavior. To do so, we compare ACP-Base, Intervention-Aware ACP, and Intervention-Aware ACP with correction distillation in settings where the policy must recover from difficult or previously failure-prone states. In particular, we use perturbed initial states and forced near-failure scenarios to test the ability of each method to return to successful execution after the policy begins to drift.

The main metrics for this study are recovery success rate, post-intervention success rate, and the magnitude of the action correction gap. These experiments directly test the core premise of correction distillation: access to paired policy-proposed and human-corrected actions should improve the policy's ability to learn how to repair its own mistakes.

### 对应主文输出

- `TBL-2`
- `FIG-3`

### 作者备注

- 这一节需要强依赖 recovery-heavy 场景，不然很难把 `Corr` 的价值讲清楚。
- 如果主文篇幅有限，`correction gap` 可以放附录，主文重点保留：
  - recovery success
  - post-intervention success

---

## 2.7 RQ3: Can Learned Request-for-Help Reduce Human Cost?

### English Draft

We then evaluate whether the learned request-for-help mechanism reduces human supervision cost during deployment. We compare Always Monitor, Heuristic Query, and the learned trigger under fixed human-budget settings. The key question is whether the robot can preserve task performance while asking for less human attention, or equivalently achieve better performance under the same monitoring budget.

We measure monitoring time, success under fixed human budget, and request-for-help precision and recall. These metrics assess not only whether the trigger fires, but whether it fires at the right moments. Importantly, this experiment treats assistance triggering as part of the closed-loop system rather than as a standalone classifier: a useful trigger should both reduce human burden and focus intervention on informative states for future training.

### 对应主文输出

- `TBL-3`
- `FIG-4`

### 作者备注

- 这里最好明确 budget 单位，比如：
  - human monitoring time
  - maximum intervention frames
  - maximum takeover count
- 论文里一定要固定一个主 budget 定义，不然 reviewer 会觉得不严谨。

---

## 2.8 RQ4: Are the Three Components Complementary?

### English Draft

Finally, we evaluate whether the three components of CHILO are complementary. We compare intervention-aware relabeling only, relabeling plus correction distillation, relabeling plus learned query, and the full model. These experiments test whether the framework behaves as a coherent closed-loop system rather than a collection of unrelated heuristics.

Our expectation is that semantic relabeling primarily improves supervision quality, correction distillation primarily improves recovery, and learned query primarily improves human-budget efficiency. The full model should therefore provide the best trade-off across task success, recovery robustness, and supervision cost.

### 对应主文输出

- `TBL-4`

### 作者备注

- `RQ4` 的任务就是证明统一框架成立。
- 这节建议写得简洁，不要再引入太多新指标。

---

## 2.9 RQ5: Under Which Scenarios Are the Gains Largest?

### English Draft

To better understand when CHILO is most beneficial, we perform additional analyses across different scenario types, including intervention-heavy trajectories, perturbed starts, and low-budget deployment settings. This analysis is intended to reveal whether the proposed framework is especially useful in recovery-critical regimes, which would be consistent with its design motivation.

### 对应输出

- `FIG-5`
- Appendix qualitative analysis

### 作者备注

- `RQ5` 主要是为了防 reviewer 说“这方法只在某个小场景有效”。
- 如果篇幅紧，这节可以压缩到分析段或附录。

---

## 2.10 Qualitative Results

### English Draft

In addition to quantitative metrics, we provide qualitative rollout analyses that visualize value estimates, intervention timing, policy proposals, executed actions, and request-for-help decisions over time. These case studies are useful for showing failure modes that are difficult to capture with scalar metrics alone, such as delayed intervention, successful human-guided recovery, or false-positive help requests. We find that qualitative timelines are especially informative for understanding how semantic relabeling and correction distillation change the behavior of the policy during difficult execution segments.

### 作者备注

- 定性图里最建议标这几条：
  - `policy_action`
  - `executed action`
  - `intervention on/off`
  - `value / risk`
  - `query trigger`

---

## 3. 主文表格草稿文字版

这一节不是论文正文，但能帮你后面更快排版。

### 3.1 Table 1 Caption 草稿

> **Table 1.** Main task performance under nominal rollout and perturbed initial states. Intervention-aware relabeling improves over binary ACP and intervention-all-positive baselines while using the same base policy architecture.

### 3.2 Table 2 Caption 草稿

> **Table 2.** Recovery and correction analysis. Using paired policy-proposed and human-corrected actions improves the policy's ability to recover from difficult states.

### 3.3 Table 3 Caption 草稿

> **Table 3.** Human-budget efficiency during deployment. The learned request-for-help mechanism achieves better success under constrained human supervision than heuristic or always-monitor baselines.

### 3.4 Table 4 Caption 草稿

> **Table 4.** Ablation study of the proposed framework. The three components of CHILO are complementary and jointly provide the best trade-off across task performance, recovery, and supervision efficiency.

---

## 4. 主文图标题草稿

### 4.1 Figure 1

> **Figure 1.** Overview of CHILO. Human-in-the-loop rollout data are relabeled with intervention-aware semantics, distilled into action-level correction supervision, and reused for query-efficient deployment in the next iteration.

### 4.2 Figure 2

> **Figure 2.** Intervention-aware semantic relabeling and label statistics. The proposed relabeling separates autonomous progress, takeover onset, recovery-positive segments, and recovery tails.

### 4.3 Figure 3

> **Figure 3.** Recovery performance under perturbed and near-failure conditions. Correction distillation improves the policy's ability to return to successful execution.

### 4.4 Figure 4

> **Figure 4.** Success versus human monitoring budget. The learned trigger achieves a better trade-off between task success and supervision cost.

### 4.5 Figure 5

> **Figure 5.** Qualitative rollout timelines showing intervention, policy proposals, executed actions, value trends, and request-for-help decisions.

---

## 5. 这一版初稿还需要你后面补什么

当前这份 `Related Work + Experiments` 初稿已经能作为写稿骨架，但还缺下面几类信息：

### 5.1 正式引用

你后面需要把下面这些文献真正接进去：

- `Sirius`
- `HIL-SERL`
- `Counter-BC`
- `ThriftyDAgger`
- `AIM`
- `DataMIL`
- `SARM`

### 5.2 真实实验细节

需要在实验 setup 里补：

- rollout 次数
- 每个方法训练步数
- 每个方法使用的数据规模
- 每个 budget setting 的具体定义

### 5.3 结果占位符

当前草稿里还没有具体数值，后面你拿到结果后要替换：

- `improves success rate by ...`
- `reduces monitoring time by ...`
- `improves recovery success by ...`

---

## 6. 最顺的下一步

如果你接下来继续按“只写文档，不动代码”的方式推进，我建议下一个最顺的动作是：

1. 用 [RQ1_relabeling与标签统计实施方案.md](/home/jy/Data/YCP/Evo-RL/RQ1_relabeling与标签统计实施方案.md) 先把 `RQ1` 的实施路线钉死
2. 再回到 [实验计划表.md](/home/jy/Data/YCP/Evo-RL/实验计划表.md)，把 `RQ1` 的 checklist 状态补上
3. 最后把这一份 `Related Work + Experiments` 和前面的 `Introduction + Method` 合并成完整初稿框架

---

## 7. 一句话总结

这份文档的核心作用，是把论文后半部分也收束成统一叙事：  
**别人分别讨论了 intervention、correction、value-guided learning 和 assistance trigger，而你的论文要证明的是，这四件事在真实机器人闭环里其实应该被统一看待。**
