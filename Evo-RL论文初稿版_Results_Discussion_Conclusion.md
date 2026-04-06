# Evo-RL 论文初稿版（Results + Discussion + Conclusion）

> 时间基准：2026-04-02  
> 承接文档：`Evo-RL论文初稿版_Introduction_Method.md`、`Evo-RL论文初稿版_RelatedWork_Experiments.md`、`实验计划表.md`  
> 用途：补齐论文初稿的后续部分，覆盖 `Results 写法模板 + Discussion / Limitations + Conclusion + Appendix 组织建议`。  
> 写法说明：正文尽量采用英文论文风格；中文备注用于帮助你在有实验结果后快速替换成终稿。

---

## 0. 使用说明

到目前为止，你已经有了三份前序文档：

- [Evo-RL论文初稿版_Introduction_Method.md](/home/jy/Data/YCP/Evo-RL/Evo-RL论文初稿版_Introduction_Method.md)
- [Evo-RL论文初稿版_RelatedWork_Experiments.md](/home/jy/Data/YCP/Evo-RL/Evo-RL论文初稿版_RelatedWork_Experiments.md)
- [实验计划表.md](/home/jy/Data/YCP/Evo-RL/实验计划表.md)

这份文档接的就是后半段最缺的部分：

1. 实验结果出来以后，`Results` 应该怎么写
2. `Discussion / Limitations` 怎么收
3. `Conclusion` 怎么写得有力但不过度夸张
4. 附录该放什么

换句话说，这份文档的作用不是重新设计实验，而是：

**把“有了结果以后怎么写论文”这件事先搭好脚手架。**

---

## 1. Results 写作总原则

### 1.1 整体思路

你的 `Results` 部分最好不要写成：

- 先扔一堆表
- 然后逐个复述数字

更好的结构是：

1. 先回答一个 research question
2. 再给表 / 图
3. 最后解释这个结果为什么支持你的核心论点

也就是说，每个结果小节都应该遵循：

```text
Question
    ->
Result summary
    ->
Evidence from table/figure
    ->
Interpretation
```

### 1.2 你的结果部分真正要证明什么

整篇文章最终不是要证明“我们做了三个模块”，而是要证明下面三件事：

1. **semantic relabeling 让训练 supervision 更好**
2. **correction distillation 让恢复能力更强**
3. **query-efficient deployment 让人类成本更低**

所以 `Results` 里每一节都要尽量紧扣这三句话。

### 1.3 最容易犯的错

你后面真正写结果时，尽量避免：

- 只复述数字，不解释原因
- 同一个结论在 3 张表里重复说
- 一上来就讨论细节，不先说主结论

更好的写法是先给一句结论：

> CHILO consistently improves task success under the same data and policy budget.

然后再跟：

> As shown in Table 1, ...

---

## 2. Main Results Draft

这一节给的是主文 `Results` 的英文草稿骨架。你现在可以先保留结构，等数值出来以后把占位符替换掉。

## 2.1 Overall Performance

### English Draft

We begin by evaluating overall task performance under nominal rollout and perturbed initial conditions. As shown in Table 1, intervention-aware relabeling consistently improves over standard behavior cloning and binary advantage-conditioned policy training. In particular, our intervention-aware variant achieves higher success while maintaining comparable or better episode efficiency. These gains suggest that the richer semantic labels provide more informative supervision than either uniform imitation or binary ACP.

The gap between Intervention-Aware ACP and the intervention-all-positive baseline is especially important. Simply treating all intervention frames as positive supervision improves over vanilla BC in some cases, but remains inferior to explicitly separating corrective and recovery-related semantics. This result supports our central claim that human takeover trajectories should not be collapsed into a single positive class.

Under perturbed initial states, the advantage of intervention-aware relabeling becomes more pronounced. This suggests that semantic relabeling is particularly helpful when the deployed policy encounters states that differ from the nominal training distribution. Rather than merely improving average performance, the method appears to improve the quality of supervision in precisely those regimes where human intervention is most informative.

### 对应主文表图

- `TBL-1`
- `FIG-2`

### 可替换占位符

后面结果出来以后，把下面这些内容补进去：

- `improves success by X points over ACP-Base`
- `improves success by Y points over BC`
- `maintains / reduces episode length by Z%`

### 作者备注

- 这一小节是全篇最重要的开门结果。
- 第一段一定要直接说：`semantic relabeling works`
- 第二段一定要点名：
  - intervention-all-positive 不够好
  - semantic label 才是关键

---

## 2.2 Recovery and Correction Results

### English Draft

We next evaluate whether correction distillation improves recovery behavior in difficult states. Table 2 and Figure 3 show that adding correction distillation improves both recovery success rate and post-intervention success, particularly in forced near-failure and perturbed-init evaluations. These results indicate that paired policy-proposed and human-corrected actions provide useful supervision beyond semantic relabeling alone.

The improvement is most evident in states that already caused the deployed policy to drift away from successful execution. In such situations, a standard policy objective may still encourage imitation of the corrected action, but it does not explicitly model how the original policy should have changed its decision. By contrast, correction distillation directly exploits the gap between the proposed and executed actions, making it better suited for learning recovery behavior.

This result is important for the broader closed-loop setting. Human takeovers do not merely provide more data; they provide *structured correction signals*. Our findings suggest that explicitly learning from these proposal-correction pairs helps the policy repair mistakes that would otherwise recur in future deployment rounds.

### 对应主文表图

- `TBL-2`
- `FIG-3`

### 可替换占位符

- `improves recovery success from X to Y`
- `improves post-intervention success by Z points`
- `reduces correction gap / improves return after takeover`

### 作者备注

- 这一节要强调：
  - 不是“多了个 loss 所以更强”
  - 而是“paired correction supervision 比单纯 imitation 更适合 recovery”
- 如果你后面有一个很漂亮的恢复案例图，这一节会非常强。

---

## 2.3 Human Budget and Query Efficiency

### English Draft

We then turn to the deployment-time assistance mechanism. Table 3 and Figure 4 show that the learned request-for-help trigger achieves a better trade-off between task success and human supervision cost than heuristic or always-monitor baselines. Under fixed supervision budgets, the learned trigger preserves more task performance, while under comparable success levels it requires less monitoring time.

The precision-recall results further suggest that the learned trigger is not merely querying more often. Instead, it appears to concentrate human assistance on states that are both difficult and informative. This is consistent with our design goal: the trigger should not only improve deployment safety, but also improve the quality of the data collected for the next round of training.

These findings highlight an important practical point. In real-world robot deployment, the bottleneck is often not only policy quality, but also the amount of human attention required to sustain iterative learning. By learning when to request help, the system moves closer to a scalable human-in-the-loop training process rather than a fully human-monitored pipeline.

### 对应主文表图

- `TBL-3`
- `FIG-4`

### 可替换占位符

- `reduces monitoring time by X%`
- `improves success under fixed budget by Y points`
- `achieves precision / recall of ...`

### 作者备注

- 这一节不要写成“我们的 trigger 很智能”。
- 更稳妥的写法是：
  - `better trade-off`
  - `human-budget efficiency`
  - `concentrates supervision on informative states`

---

## 2.4 Unified Ablation

### English Draft

Finally, Table 4 evaluates whether the three components of CHILO are complementary. Intervention-aware relabeling alone improves supervision quality and yields a strong performance gain over binary ACP. Adding correction distillation further improves recovery-related metrics, while adding the learned trigger improves human-budget efficiency. The full model achieves the strongest overall trade-off across task success, recovery robustness, and supervision cost.

This ablation is important because it demonstrates that CHILO is not simply a bundle of independent heuristics. Instead, the three components operate at different points in the closed-loop pipeline: semantic relabeling improves how rollout data are interpreted, correction distillation improves how hard states are learned from, and query-efficient deployment improves which states receive human supervision in future rounds. Their gains are therefore additive rather than redundant.

### 对应主文表图

- `TBL-4`

### 可替换占位符

- `full model achieves best overall success`
- `A+B improves recovery while A+C improves budget efficiency`
- `full model dominates single-component variants on ...`

### 作者备注

- 这一节就是统一框架成立的证据。
- 你要反复强调一个点：
  - the components act on different stages of the closed loop

---

## 2.5 Qualitative Analysis

### English Draft

We additionally provide qualitative rollout analyses to better illustrate how the proposed framework behaves during difficult execution segments. Figure 5 visualizes intervention timing, policy-proposed actions, executed actions, value trends, and request-for-help decisions. These case studies reveal several recurring patterns. First, intervention-aware labels tend to align with meaningful transition points such as takeover onset and successful recovery. Second, policies trained with correction distillation more often return to successful execution after drift. Third, the learned trigger tends to activate near failure-critical states rather than uniformly throughout the trajectory.

Qualitative analysis is particularly useful here because some of the most important differences between methods are temporal and structural rather than scalar. A trajectory in which the robot briefly drifts, requests timely help, and successfully recovers may look only modestly different in aggregate statistics, yet it reflects a substantially more useful closed-loop behavior. These qualitative examples therefore complement the quantitative results by making the intervention dynamics directly visible.

### 对应主文表图

- `FIG-5`

### 作者备注

- 定性图尽量少但精。
- 最好挑 3 种案例：
  - 成功恢复
  - 失败恢复
  - 正确请求帮助

---

## 3. Discussion Draft

## 3.1 What the Results Mean

### English Draft

Taken together, the experimental results support a simple interpretation: human takeovers are more useful when treated as structured supervision rather than raw corrective demonstrations. Intervention-aware relabeling improves how rollout quality is represented during policy training, correction distillation improves how the policy learns to repair its own mistakes, and query-efficient deployment improves how human effort is allocated during rollout collection. This combination leads not only to a stronger policy, but also to a more effective iterative learning process.

An important implication of these findings is that the value of human intervention in robot learning is not limited to safety or short-term task completion. Human intervention also shapes the future training distribution. By selectively preserving the semantics of corrective segments, explicitly learning from proposal-correction pairs, and requesting help only when necessary, the system converts human supervision into a reusable asset for closed-loop improvement. In this sense, our results suggest that human intervention should be viewed as a first-class training signal in real-world robot deployment.

### 作者备注

- 这一节不是复读结果，而是解释结果背后的意义。
- 最值得强调的是：
  - human intervention changes future training distribution

---

## 3.2 Why the Unified View Matters

### English Draft

One of the central motivations of this work is that intervention, correction, and assistance triggering are often studied separately even though they occur in the same rollout. Our results suggest that this separation is artificial in closed-loop robot learning. A single takeover event simultaneously reveals that the policy has entered a difficult state, that a corrective action is needed, and that this state may warrant future assistance requests. Modeling these aspects jointly yields a more coherent and data-efficient learning process than treating them as unrelated problems.

This unified view is especially relevant in real-world robotics, where data collection opportunities are limited and human time is expensive. In such settings, methods that improve only training or only deployment may leave substantial efficiency gains unrealized. CHILO instead improves both how supervision is extracted from collected rollouts and how the next rollouts are collected.

### 作者备注

- 这节是你全文最“论文味”的一段。
- 重点是把三条线重新统一成一句话：
  - same takeover event -> multiple reusable signals

---

## 4. Limitations Draft

## 4.1 English Draft

Despite the encouraging results, our study has several limitations. First, the framework still relies on human intervention data, and its effectiveness depends on the quality, consistency, and coverage of the collected takeover trajectories. If interventions are sparse, delayed, or highly inconsistent across operators, the semantic relabeling and correction targets may become noisy.

Second, while our experiments focus on real-world closed-loop deployment, they currently cover a limited number of tasks and embodiments. The benefits of intervention-aware relabeling and correction distillation are likely to be strongest in recovery-critical, long-horizon settings, but additional multi-task and cross-embodiment evaluation would be needed to establish broader generality.

Third, the request-for-help mechanism depends on deployment-time risk signals such as value estimates, action disagreement, and intervention history. If these signals are poorly calibrated, the trigger may become overly conservative or overly permissive. Although our lightweight trigger is attractive from a systems perspective, more principled uncertainty modeling may further improve reliability.

Finally, our method is designed to remain compatible with existing text-conditioned robot policies and therefore prioritizes minimal architectural change. This design choice improves modularity and makes ablations cleaner, but it may also limit the extent to which richer structured intervention signals can be exploited compared with more specialized policy architectures.

### 4.2 可直接放进论文的 Limitations 小节末尾

> More broadly, our results should be interpreted as evidence that structured intervention supervision is promising, rather than as a complete solution to human-in-the-loop robot deployment. Future work should study how these ideas scale to larger task sets, multiple operators, and broader robot embodiments.

### 4.3 作者备注

- Limitations 一定要主动写，不要等 reviewer 替你写。
- 最推荐主动承认的三件事：
  - task 数量有限
  - 依赖 intervention 质量
  - trigger calibration 还不完美

---

## 5. Broader Discussion / Future Work Draft

### English Draft

Our work opens several directions for future research. One natural extension is to replace discrete intervention-aware labels with richer structured representations, such as stage-aware or uncertainty-aware semantic tags. Another direction is to use intervention supervision not only for policy improvement but also for data valuation, selectively prioritizing rollout segments that contribute most to future gains. It would also be valuable to study whether the semantics of intervention transfer across embodiments, tasks, or operators, which could help build more general closed-loop learning systems.

From a systems perspective, a particularly promising direction is to unify correction learning and assistance triggering more tightly. For example, a future system could use the same risk signal both to decide when to request help and to predict what type of correction is likely to be needed. This would move closed-loop deployment closer to a collaborative setting in which the robot not only asks for help at the right time, but also learns to anticipate the structure of the help it will receive.

### 作者备注

- 未来工作不要写得太散。
- 最适合你这篇论文的 future work 只有 3 个方向：
  - richer semantic tags
  - data valuation
  - broader generalization

---

## 6. Conclusion Draft

### 6.1 English Draft

In this paper, we presented CHILO, a unified framework for closed-loop real-world robot learning from human takeovers. Our key premise is that a takeover trajectory contains more than a corrective demonstration: it also reveals semantic information about failure and recovery, action-level evidence of how the policy should change its decision, and deployment-time cues about when human help is needed. We operationalized this view through intervention-aware semantic relabeling, counterfactual correction distillation, and query-efficient human-in-the-loop deployment.

By integrating these components into a single closed-loop pipeline, CHILO improves not only policy learning from collected rollouts but also the quality and efficiency of future rollout collection. This perspective shifts human intervention from a passive safety fallback to an active and reusable supervision source for robot learning. We hope this work helps move real-world robot deployment toward more scalable, data-efficient, and collaborative forms of continual improvement.

### 6.2 更短更稳的 Conclusion 版本

如果你后面想要更短一点的 conclusion，可以用这个版本：

> We showed that human takeovers can be reused as structured supervision for closed-loop robot learning. By combining intervention-aware relabeling, correction distillation, and query-efficient deployment, CHILO improves how robot policies are trained from rollout data and how human effort is allocated during deployment. More broadly, our results suggest that the future of real-world robot learning may depend not only on larger models and more data, but also on better ways of understanding and reusing human intervention.

### 6.3 作者备注

- 结论一定不要只写“我们提出了一个方法”。
- 更好的结论是：
  - restate the premise
  - restate the system-level significance

---

## 7. Appendix 组织建议

这部分不是主文正文，但现在先整理好，后面你写稿会省很多时间。

### 7.1 Appendix A: Semantic Relabeling Details

建议放：

- label definitions
- rule table
- threshold selection
- example trajectories

### 7.2 Appendix B: Additional Experimental Details

建议放：

- training steps
- rollout budget
- hardware setup
- camera setup
- policy checkpoint details

### 7.3 Appendix C: Additional Quantitative Results

建议放：

- full metric tables
- per-scenario results
- per-label statistics

### 7.4 Appendix D: Additional Qualitative Cases

建议放：

- rollout timelines
- failure cases
- false-positive / false-negative trigger examples

### 7.5 作者备注

- 附录最重要的作用不是“塞没地方放的内容”，而是：
  - 让主文保持干净
  - 同时让 reviewer 看到你做得足够扎实

---

## 8. 主文拼接建议

如果你现在要把几份初稿整合成一篇完整草稿，建议顺序如下：

1. [Evo-RL论文初稿版_Introduction_Method.md](/home/jy/Data/YCP/Evo-RL/Evo-RL论文初稿版_Introduction_Method.md)
2. [Evo-RL论文初稿版_RelatedWork_Experiments.md](/home/jy/Data/YCP/Evo-RL/Evo-RL论文初稿版_RelatedWork_Experiments.md)
3. 本文件 [Evo-RL论文初稿版_Results_Discussion_Conclusion.md](/home/jy/Data/YCP/Evo-RL/Evo-RL论文初稿版_Results_Discussion_Conclusion.md)

拼起来以后，论文完整骨架就变成：

- Title
- Abstract
- Introduction
- Related Work
- Problem Setup
- Method
- Experiments
- Results
- Discussion
- Limitations
- Conclusion
- Appendix

---

## 9. 你下一步最该做什么

如果还继续只用文档推进、不动代码，我最建议下一步做两件事：

1. 新建一份 `结果填空版.md`
   - 专门用来把 `TBL-1 ~ TBL-4` 和 `FIG-1 ~ FIG-5` 的结果占位先填出来

2. 新建一份 `论文整合版.md`
   - 把现在三份初稿正式合并成一份连续文稿

这样你后面无论是继续实现、开始写稿，还是给导师看，都会更顺。

---

## 10. 一句话总结

这份文档的核心作用，是让你在真正拿到实验结果之后，不会卡在“结果该怎么讲、局限性该怎么写、结论该怎么收”这几个最常见的写稿瓶颈上。  
**你现在已经不只是有选题和方法了，而是已经有了一套几乎完整的论文写作骨架。**
