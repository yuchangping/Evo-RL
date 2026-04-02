# Evo-RL 论文初稿版（Introduction + Method）

> 时间基准：2026-04-02  
> 承接文档：`Evo-RL论文大纲版.md`、`Evo-RL论文方向梳理.md`  
> 用途：这是一份可以继续往英文论文正文扩写的初稿，当前先覆盖 `Introduction + Method`。  
> 写法说明：正文部分尽量按英文论文风格撰写；必要处保留少量占位符，便于你后续替换实验结果、方法名和引用。

---

## 0. 使用说明

这份文档分成两部分：

1. **英文正文初稿**  
   这一部分尽量按论文可以直接继续写的口吻组织。

2. **作者备注**  
   这一部分不属于论文正文，只是帮你后面继续改稿时快速对齐叙事、公式和实验结果。

为了让全文更顺，目前我暂时给整套方法起一个工作名：

**CHILO: Closed-loop Human Intervention Learning and Optimization**

这个名字只是内部草稿名，后面你完全可以替换。

---

## 1. Working Title

下面给出三个最适合当前正文的工作标题：

1. `A Unified Framework for Learning from Human Corrections in Closed-Loop Robot Deployment`
2. `From Human Takeovers to Better Policies: Intervention-Aware Closed-Loop Robot Learning`
3. `Closed-Loop Robot Learning from Human Takeovers: Semantic Conditioning, Action Correction, and Query-Efficient Assistance`

如果你希望标题更稳，我建议当前正文先按第 1 个标题写。

---

## 2. Introduction Draft

### 2.1 English Draft

Real-world robot deployment remains brittle even when powerful vision-language-action policies are available. In practical manipulation settings, policies frequently encounter distribution shift, compounding execution errors, unmodeled contacts, and long-horizon failure modes that are difficult to eliminate through offline training alone. As a result, human intervention remains a central mechanism for improving success, safety, and throughput during deployment. In many real systems, a human operator monitors the robot, temporarily takes over when the policy begins to fail, and then returns control once the task is back on track. Such human-in-the-loop interaction is not an edge case; it is often the default mode through which real-world robot policies are iteratively improved.

Recent work has demonstrated the value of demonstrations, interventions, and deployment-time supervision for robot learning. Interactive imitation learning and human-in-the-loop reinforcement learning can substantially reduce data requirements and improve robustness in real-world settings. However, most existing approaches exploit only part of the information contained in intervention trajectories. Some methods treat human takeovers simply as additional demonstrations. Others focus on deciding when human help is needed but do not explicitly learn from the structure of the correction itself. Still others learn from interventions at the action level but do not connect those signals to closed-loop data relabeling and future deployment decisions. Consequently, current pipelines often miss an opportunity to treat intervention not merely as supervision after failure, but as a structured signal for understanding when a policy drifts, how it should be corrected, and when the system should proactively ask for help.

This gap is especially visible in closed-loop robot learning pipelines that already record rich rollout data. In such systems, one can often access not only the executed action, but also the action originally proposed by the deployed policy, frame-level intervention annotations, episode outcomes, and value-based trajectory annotations computed after the rollout. Yet these signals are typically used in isolation. For example, advantage-conditioned policy training may compress rollout quality into a binary tag, while intervention frames are heuristically treated as positive examples. This design is effective as a first approximation, but it collapses semantically distinct events, such as autonomous progress, takeover onset, corrective recovery, and low-value post-recovery tail segments, into the same label space. Likewise, when both the policy-proposed action and the human-executed action are available, the discrepancy between them provides a direct supervision signal for learning correction, but standard policy training usually ignores it.

In this paper, we argue that human takeover should be modeled as structured supervision for closed-loop robot learning. We build on a real-world robot learning system that records policy proposals, executed actions, intervention states, value annotations, and episode outcomes across iterative deployment rounds. Based on this observation, we propose CHILO, a unified framework that leverages human intervention signals at three complementary levels. First, we introduce **Intervention-Aware Advantage Conditioning**, which augments standard advantage-conditioned policy training with semantic tags derived from intervention dynamics rather than relying solely on a binary positive/negative indicator. Second, we introduce **Counterfactual Human Correction Distillation**, which explicitly learns from the pair consisting of the policy-proposed action and the human-corrected executed action, enabling the policy to better recover from states where the deployed controller would otherwise drift or fail. Third, we introduce **Query-Efficient Human-in-the-Loop Deployment**, which uses value-based risk signals, action disagreement, and intervention history to decide when the robot should actively request help during deployment, thereby reducing human monitoring burden while collecting more informative data for the next iteration.

Our framework is motivated by a simple but important view of intervention trajectories. A human takeover simultaneously reveals three pieces of information: a semantic event about policy failure or recovery, an action-level correction signal, and a deployment-time indicator that autonomous execution has become unreliable. Existing methods typically use at most one of these aspects. In contrast, CHILO turns all three into reusable learning signals within a single closed-loop pipeline. This integration is particularly appealing in real-world settings because it does not require replacing the underlying robot learning stack. Instead, it upgrades how data are relabeled, how supervision is extracted from rollouts, and how assistance is requested during deployment.

We evaluate the proposed framework on real-world manipulation tasks in a closed-loop human-in-the-loop setting. Compared with standard behavior cloning, original advantage-conditioned policy training, and simple intervention-weighted baselines, our method aims to improve not only task success but also recovery performance and human-budget efficiency. The intended outcome is not merely a stronger policy after one round of training, but a better iterative learning process in which the system learns more effectively from human corrections and requests assistance more selectively. Our experiments are designed to answer three core questions: whether intervention-aware relabeling improves policy learning, whether correction distillation enhances recovery ability, and whether learned request-for-help decisions can reduce monitoring cost without sacrificing performance.

Our contributions are threefold. First, we present an intervention-aware semantic relabeling strategy that turns human takeover trajectories into richer conditioning signals for policy learning. Second, we propose a correction distillation objective that directly exploits the gap between policy proposals and human-executed actions. Third, we introduce a query-efficient deployment mechanism that leverages risk signals to request human assistance only when needed. Taken together, these components recast human intervention from a passive safety mechanism into an active source of structured supervision for closed-loop real-world robot learning.

### 2.2 Introduction 末尾 Contributions 可直接使用版

如果你后面想把 Introduction 结尾单独拉出 contribution list，可以直接用下面这个版本：

> Our contributions are as follows.  
> First, we propose an intervention-aware semantic relabeling strategy that enriches advantage-conditioned policy training with structured takeover semantics.  
> Second, we introduce a counterfactual human correction distillation objective that directly learns from paired policy proposals and human-executed corrective actions.  
> Third, we develop a query-efficient human-in-the-loop deployment mechanism that predicts when the robot should request human assistance based on deployment-time risk signals.  
> Finally, we instantiate these ideas in a real-world closed-loop robot learning system and show how human intervention can serve as a reusable supervision signal for both training and deployment.

### 2.3 作者备注

- 第一段已经把“真实机器人部署仍脆弱”讲出来了，后面你写摘要和 introduction 基本都可以复用。
- 第二段把现有工作的问题写成“只利用了 intervention 的一部分信息”，这样你统一三条方法会更自然。
- 第三段故意把“binary ACP”“policy proposal / executed action pairing”两个缺口提前埋进去，方便接到 Method。
- 第五段最好等你真实实验结果出来后，替换成更强的结果导向说法，比如：
  - `improves success rate by X%`
  - `reduces monitoring time by Y%`
  - `improves recovery success by Z%`

---

## 3. Problem Setup Draft

### 3.1 English Draft

We consider a closed-loop real-world robot learning setting in which a policy is iteratively deployed, corrected by a human when necessary, and retrained using accumulated rollout data. At each time step `t`, the robot observes a multimodal input `o_t`, receives a task description `tau`, and produces a policy-proposed action `a_t^pi`. During autonomous execution, the executed action equals the proposed action. When human takeover is activated, however, the executed action `a_t^e` is provided by the human operator and may differ substantially from `a_t^pi`. We denote the intervention indicator by `i_t in {0,1}`, where `i_t = 1` means that the human is currently intervening.

Each rollout trajectory additionally contains metadata that are available in our closed-loop system: frame-level intervention annotations, the policy-proposed action, the executed action, episode-level success labels, and post-hoc value annotations written back to the dataset after value inference. Specifically, after each deployment round we compute a frame-level value estimate `v_t`, an advantage target `A_t`, and a standard ACP indicator derived from the inferred trajectory quality. Unlike standard pipelines, we do not treat these quantities as isolated signals. Instead, we use them jointly to construct semantic conditioning labels, correction supervision targets, and deployment-time assistance triggers.

Formally, the dataset for one closed-loop round is a collection

`D_k = {(o_t, tau_t, a_t^pi, a_t^e, i_t, y_ep, v_t, A_t)}`

where `y_ep` denotes the episode outcome. Our goal is to learn a policy `pi_{k+1}` that improves three aspects simultaneously: task performance, correction and recovery capability, and human-budget efficiency during deployment. To achieve this, we introduce a unified learning framework that transforms intervention trajectories into structured supervision at the semantic, action, and deployment levels.

### 3.2 作者备注

- 这一节相当于论文里的 `Problem Setup and System` 开头部分。
- 你后面如果决定把系统实现单独拆成 subsection，可以在这里后面补一段：
  - dataset fields
  - value inference pipeline
  - training / deployment loop
- 数据公式里目前已经把 `policy_action`、`is_intervention`、`episode_success`、`value / advantage` 都接进来了，和你仓库现状是对齐的。

---

## 4. Method Draft

### 4.1 Section Opening Paragraph

### 4.1.1 English Draft

The key idea of CHILO is to reinterpret human takeover as a structured signal rather than a binary event. A takeover not only indicates that autonomous execution has become unreliable, but also reveals how the policy should be corrected and whether the system should continue to operate autonomously in similar states. We therefore design CHILO around three coupled components. Intervention-Aware Advantage Conditioning enriches trajectory relabeling and policy conditioning with intervention semantics. Counterfactual Human Correction Distillation extracts action-level correction supervision from the discrepancy between policy proposals and executed actions. Query-Efficient Human-in-the-Loop Deployment uses deployment-time risk signals to decide when the system should actively request assistance. Together, these components improve both sides of the closed loop: the quality of supervision used for training and the quality of data collected during deployment.

### 4.1.2 作者备注

- 这段基本可以作为 Method 章节总起始段。
- 最重要的是最后一句：`improve both sides of the closed loop`，它把 train 和 collect 两侧统一起来了。

---

## 4.2 Intervention-Aware Advantage Conditioning

### 4.2.1 English Draft

Standard advantage-conditioned policy training uses a binarized indicator to distinguish high-quality and low-quality trajectory segments. While effective, this binary view is too coarse in the presence of human takeovers. In particular, intervention trajectories contain several semantically distinct regimes: autonomous progress before failure, the onset of human correction, active recovery under human control, and low-value tail segments after the trajectory has already been rescued. Treating all intervention frames as uniformly positive supervision can therefore dilute the learning signal and obscure which parts of a takeover are actually useful for future policy improvement.

To address this issue, we replace the binary conditioning label with an intervention-aware semantic tag. For each frame, we combine the inferred advantage `A_t`, the intervention indicator `i_t`, the discrepancy between the policy proposal and executed action, and short-horizon temporal context to assign a semantic label

`s_t = g(A_t, i_t, ||a_t^e - a_t^pi||, h_t),`

where `h_t` denotes local trajectory context such as recent intervention history or value trend. In practice, we instantiate `s_t` using a small discrete label set that distinguishes, for example, autonomous-positive, correction-onset, recovery-positive, recovery-tail, and autonomous-negative states. This semantic label is then injected into the task prompt rather than the model architecture, preserving compatibility with text-conditioned robot policies.

Concretely, given an original task description `tau_t`, we construct an intervention-aware conditioned task

`tau_t' = concat(tau_t, Tag(s_t)).`

This design retains the simplicity of prompt-based advantage conditioning while substantially increasing the expressiveness of the supervision signal. Importantly, it also makes ablations clean: the underlying policy architecture remains unchanged, and only the conditioning signal differs. As a result, performance gains can be attributed to improved supervision rather than model scaling or architectural changes.

The intervention-aware relabeling mechanism serves two purposes. First, it provides a more informative training signal for learning which states and trajectory segments should be imitated. Second, it creates a semantic bridge between rollout outcomes and deployment-time intervention events, which later supports both correction distillation and request-for-help prediction. In this sense, semantic relabeling is the front end of the entire framework: it transforms raw rollout logs into structured learning targets that better reflect how humans actually collaborate with the robot.

### 4.2.2 Optional Formula Variant

如果你后面想在论文里把标签规则写得更清楚，可以用下面这种形式：

`delta_t = ||a_t^e - a_t^pi||_2`

`m_t = onset / active / release / none`

`s_t = Relabel(A_t, i_t, delta_t, m_t, Delta v_t)`

其中：

- `delta_t` 表示纠正幅度
- `m_t` 表示接管状态机语义
- `Delta v_t` 表示局部 value 变化趋势

### 4.2.3 作者备注

- 这一节最关键的点不是“标签有几个类别”，而是你要让 reviewer 接受：  
  `binary ACP 在 intervention 数据上太粗糙`
- 如果你担心标签类别太多会显得复杂，可以在正文先写 4 类，附录里再放更细版本。
- 这一节最好强调：
  - `no architecture change`
  - `only improved conditioning signal`

---

## 4.3 Counterfactual Human Correction Distillation

### 4.3.1 English Draft

Human takeovers provide more than semantic information: they also provide direct action-level corrections to the deployed policy. When the robot is under autonomous control, the proposed action `a_t^pi` reflects the policy's current belief about how the task should proceed. During intervention, the executed action `a_t^e` instead reflects how a human corrects that belief in the current state. The discrepancy between these two actions therefore forms a counterfactual supervision signal: it tells us not only what action was executed, but how the policy should have changed its decision under the same observation.

We exploit this paired structure through a correction distillation objective. Let the target correction be

`delta_t^* = a_t^e - a_t^pi.`

We introduce a correction predictor `c_theta` that takes the observation, the intervention-aware conditioned task, and optionally the proposed action as input, and predicts a residual correction `hat(delta_t)`. The corrected action is then

`hat(a_t^e) = a_t^pi + hat(delta_t).`

The correction loss is applied primarily on intervention frames:

`L_corr = (1 / N) * sum_t i_t * ||hat(delta_t) - delta_t^*||_1.`

This objective can be implemented either as a lightweight residual head attached to the policy or as an auxiliary training objective that regularizes the policy toward human-corrected execution. In either case, the key idea is the same: intervention segments should not be treated merely as demonstrations to imitate, but as explicit evidence of how the deployed policy ought to be repaired in states where it would otherwise fail.

The correction objective is combined with the standard policy loss:

`L_total = L_policy(tau_t') + lambda_corr * L_corr.`

Here `L_policy(tau_t')` denotes the original policy training objective under intervention-aware task conditioning. This formulation keeps the overall method modular. If the base policy is already strong enough, the correction term acts as a targeted auxiliary signal on hard states. If the base policy is weak, the same term provides a direct mechanism for learning recovery behaviors from human takeovers. In both cases, the objective explicitly links rollout-time mistakes to future policy updates.

An additional benefit of this design is that it naturally supports recovery-centric evaluation. Because the model is trained on proposal-correction pairs, we can test not only whether it succeeds from nominal initial states, but also whether it can return to successful execution after perturbations or after states that previously required human takeover. This makes correction distillation especially relevant for long-horizon manipulation, dual-arm coordination, and other settings in which error recovery is essential.

### 4.3.2 Optional Ranking Variant

如果你后面想把 correction 学习再写得更强一点，可以在附录里增加一个 value-guided 版本：

`L_rank = max(0, margin - V(o_t, a_t^e) + V(o_t, a_t^pi))`

它的含义是：

- 人类纠正后的动作应当比 policy 原始动作具有更高的后续价值

不过正文里建议先不把方法做太重，主文保留 residual correction 版本就够了。

### 4.3.3 作者备注

- 这一节的关键词是 `counterfactual`。  
  因为你不是只知道人做了什么，而是知道“policy 在同一状态下本来会做什么”。
- 你后面实验里一定要配一个“恢复能力”评测，不然 correction 这条线会显得没有落点。
- 如果实现上暂时不想改 policy 主干，就把这条先写成 auxiliary loss，会更稳。

---

## 4.4 Query-Efficient Human-in-the-Loop Deployment

### 4.4.1 English Draft

Even with improved supervision, continuously requiring a human to monitor deployment is expensive and limits scalability. A practical closed-loop system should therefore learn not only from human intervention, but also when to request it. We formulate this as a deployment-time assistance problem. At each time step, the robot computes a risk score indicating how likely autonomous execution is to become unreliable in the near future. Human assistance is requested only when this score exceeds a threshold, optionally under a fixed intervention budget.

The risk score is computed from deployment-time signals that are already available in the closed-loop pipeline. These include the inferred value or risk-aware value estimate `v_t`, the disagreement between conditioned and unconditioned policy predictions, and recent intervention history. Let `a_t^cond` and `a_t^uncond` denote the actions predicted with and without semantic conditioning. Their discrepancy

`d_t = ||a_t^cond - a_t^uncond||_2`

serves as a measure of action instability or conditional sensitivity. We then define

`r_t = h(-v_t, d_t, bar(i)_{t-k:t-1}, u_t),`

where `u_t` optionally denotes uncertainty and `bar(i)_{t-k:t-1}` summarizes recent intervention history. A help request is triggered when

`q_t = 1[r_t > eta],`

subject to a deployment budget if desired.

This mechanism improves deployment in two ways. First, it reduces the need for constant human attention by concentrating intervention on states that are likely to cause failure. Second, it improves the quality of future data collection by biasing human supervision toward informative failure or near-failure states rather than uniformly monitoring the entire rollout. In other words, the query policy is not just a safety tool; it is also a data curation mechanism for the next round of closed-loop learning.

We emphasize that this module is intentionally lightweight. It can be implemented as a small trigger network or as a calibrated score with a threshold. The goal is not to solve general active learning for robotics, but to provide a deployment-time mechanism that is directly compatible with the existing human-in-the-loop control loop. Because the underlying system already records intervention events and conditioned policy outputs, the trigger can be trained and evaluated without redesigning the entire deployment stack.

### 4.4.2 作者备注

- 这节要注意别写成“我们提出一个特别复杂的 query policy”，否则论文会散。
- 更好的写法是：
  - `deployment-time assistance trigger`
  - `budget-aware request-for-help`
- 这样 reviewer 会觉得它是主框架的一部分，而不是另一篇独立工作。

---

## 4.5 Closed-Loop Training and Deployment Algorithm

### 4.5.1 English Draft

The full CHILO pipeline alternates between deployment, relabeling, training, and redeployment. Starting from a policy `pi_k`, we collect human-in-the-loop rollouts in the real world while recording observations, policy-proposed actions, executed actions, intervention indicators, and episode outcomes. We then run value inference on the collected data to obtain frame-level value and advantage estimates. These signals are combined with intervention annotations to generate intervention-aware semantic tags. The resulting relabeled dataset is used to train the next policy using both the conditioned policy objective and the correction distillation loss. During deployment of `pi_{k+1}`, a learned or calibrated assistance trigger determines when human help should be requested. Newly collected data are merged back into the dataset for the next round.

This procedure can be summarized as

`D_{k+1} = D_k U Collect(pi_k, q_k),`

`S_{k+1} = Relabel(D_{k+1}, V_phi),`

`pi_{k+1} = Train(S_{k+1}).`

The central point is that CHILO improves both `Relabel` and `Collect`. Intervention-aware relabeling and correction distillation improve how existing rollout data are converted into supervision, while query-efficient deployment improves which data are acquired in the next round. This dual improvement is particularly important in real-world robot learning, where both human time and deployment opportunities are limited.

### 4.5.2 作者备注

- 这一节最好配算法框图或 pseudo-code。
- 你后面如果想在论文里放 `Algorithm 1`，这里基本就可以直接扩成算法环境。

---

## 5. Method Summary Paragraph

这一段可以放在 Method 最后一节结尾，作为收束。

### 5.1 English Draft

Taken together, the proposed framework turns a human takeover trajectory into three aligned supervision signals: a semantic label for conditioning policy training, an action-level correction target for learning recovery behavior, and a deployment-time signal for deciding when human help should be requested. This unified view is what distinguishes CHILO from existing approaches that use interventions either as demonstrations, as risk labels, or as action corrections in isolation. By coupling these signals within a single closed-loop pipeline, CHILO aims to improve not only the policy obtained after one round of training, but also the quality and efficiency of the iterative learning process itself.

### 5.2 作者备注

- 这段很好用，后面可以直接放到 Method 最后一小节结尾。
- 如果你希望整篇文章更聚焦“闭环学习”，这段也可以轻微改写后拿去做 Introduction 最后一段。

---

## 6. 当前初稿还缺什么

这份初稿现在已经能支持你继续往前写，但还有几块内容需要等实验或实现更明确后再补：

1. **Related Work 过渡句**  
   当前正文里还没有正式引用，需要你后面把 `Sirius / HIL-SERL / ThriftyDAgger / AIM / Counter-BC / DataMIL` 接进来。

2. **方法名最终确定**  
   `CHILO` 只是草稿名，后面可以再换。

3. **实验结果占位符**  
   Introduction 里关于结果的句子，目前还没有具体数值。

4. **标签规则实现细节**  
   主文只写了方法思想，具体 relabeling 规则最好放进附录。

---

## 7. 下一步最顺的写作顺序

如果你接下来继续往论文正文推进，我建议顺序是：

1. 写 `Related Work`
2. 写 `Experiments` 的 setup 和 RQ 小节骨架
3. 再回头精修 `Introduction` 第一段和最后一段
4. 最后统一术语：
   - intervention
   - takeover
   - correction
   - request-for-help

---

## 8. 一句话版本总结

这份初稿的核心写法已经确定了：  
**你的论文不是在讲三个分散技巧，而是在讲如何把真实机器人闭环中的人类接管转化为语义监督、纠正监督和主动求助监督。**
