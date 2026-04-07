# Evo-RL 论文整合版

> 时间基准：2026-04-02  
> 整合来源：`Evo-RL论文初稿版_Introduction_Method.md`、`Evo-RL论文初稿版_RelatedWork_Experiments.md`、`Evo-RL论文初稿版_Results_Discussion_Conclusion.md`  
> 用途：这是一份连续可通读的论文整合草稿，按正式论文顺序组织。  
> 当前状态：方法、实验结构、结果写法、讨论和结论都已连成一稿；结果数值与正式 citation 仍需后续补齐。

---

## Title

`A Unified Framework for Learning from Human Corrections in Closed-Loop Robot Deployment`

备选标题：

- `From Human Takeovers to Better Policies: Intervention-Aware Closed-Loop Robot Learning`
- `Closed-Loop Robot Learning from Human Takeovers: Semantic Conditioning, Action Correction, and Query-Efficient Assistance`

---

## Abstract

Real-world robot deployment remains brittle even when powerful vision-language-action policies are available. In practical manipulation settings, policies frequently encounter distribution shift, compounding execution errors, and recovery-critical failure modes that are difficult to eliminate through offline training alone. As a result, human intervention remains a central mechanism for improving performance and safety during deployment. However, existing human-in-the-loop robot learning methods often exploit only part of the information contained in intervention trajectories: some treat takeovers as additional demonstrations, some focus on action-level corrections, and others study when the robot should request help. In this paper, we argue that a human takeover trajectory should instead be modeled as structured supervision for closed-loop robot learning.

We present CHILO, a unified framework that leverages human intervention signals at three complementary levels. First, we introduce **Intervention-Aware Advantage Conditioning**, which augments standard advantage-conditioned policy training with semantic tags derived from intervention dynamics rather than relying solely on a binary positive/negative indicator. Second, we introduce **Counterfactual Human Correction Distillation**, which explicitly learns from the pair of policy-proposed and human-corrected executed actions, enabling the policy to better recover from difficult states. Third, we introduce **Query-Efficient Human-in-the-Loop Deployment**, which uses deployment-time risk signals to decide when the robot should actively request human assistance, thereby reducing monitoring burden while improving the quality of future rollout data.

We evaluate the proposed framework in a real-world closed-loop human-in-the-loop manipulation setting. Compared with behavior cloning, binary advantage-conditioned policy training, and simple intervention heuristics, our method aims to improve not only task success but also recovery performance and human-budget efficiency. More broadly, our results support the view that human intervention should not be treated merely as a safety fallback or an extra demonstration source, but as a reusable structured supervision signal for real-world robot learning.

---

## 1. Introduction

Real-world robot deployment remains brittle even when powerful vision-language-action policies are available. In practical manipulation settings, policies frequently encounter distribution shift, compounding execution errors, unmodeled contacts, and long-horizon failure modes that are difficult to eliminate through offline training alone. As a result, human intervention remains a central mechanism for improving success, safety, and throughput during deployment. In many real systems, a human operator monitors the robot, temporarily takes over when the policy begins to fail, and then returns control once the task is back on track. Such human-in-the-loop interaction is not an edge case; it is often the default mode through which real-world robot policies are iteratively improved.

Recent work has demonstrated the value of demonstrations, interventions, and deployment-time supervision for robot learning. Interactive imitation learning and human-in-the-loop reinforcement learning can substantially reduce data requirements and improve robustness in real-world settings. However, most existing approaches exploit only part of the information contained in intervention trajectories. Some methods treat human takeovers simply as additional demonstrations. Others focus on deciding when human help is needed but do not explicitly learn from the structure of the correction itself. Still others learn from interventions at the action level but do not connect those signals to closed-loop data relabeling and future deployment decisions. Consequently, current pipelines often miss an opportunity to treat intervention not merely as supervision after failure, but as a structured signal for understanding when a policy drifts, how it should be corrected, and when the system should proactively ask for help.

This gap is especially visible in closed-loop robot learning pipelines that already record rich rollout data. In such systems, one can often access not only the executed action, but also the action originally proposed by the deployed policy, frame-level intervention annotations, episode outcomes, and value-based trajectory annotations computed after the rollout. Yet these signals are typically used in isolation. For example, advantage-conditioned policy training may compress rollout quality into a binary tag, while intervention frames are heuristically treated as positive examples. This design is effective as a first approximation, but it collapses semantically distinct events, such as autonomous progress, takeover onset, corrective recovery, and low-value post-recovery tail segments, into the same label space. Likewise, when both the policy-proposed action and the human-executed action are available, the discrepancy between them provides a direct supervision signal for learning correction, but standard policy training usually ignores it.

In this paper, we argue that human takeover should be modeled as structured supervision for closed-loop robot learning. We build on a real-world robot learning system that records policy proposals, executed actions, intervention states, value annotations, and episode outcomes across iterative deployment rounds. Based on this observation, we propose **CHILO** (Closed-loop Human Intervention Learning and Optimization), a unified framework that leverages human intervention signals at three complementary levels. First, we introduce **Intervention-Aware Advantage Conditioning**, which augments standard advantage-conditioned policy training with semantic tags derived from intervention dynamics rather than relying solely on a binary positive/negative indicator. Second, we introduce **Counterfactual Human Correction Distillation**, which explicitly learns from the pair consisting of the policy-proposed action and the human-corrected executed action, enabling the policy to better recover from states where the deployed controller would otherwise drift or fail. Third, we introduce **Query-Efficient Human-in-the-Loop Deployment**, which uses value-based risk signals, action disagreement, and intervention history to decide when the robot should actively request help during deployment, thereby reducing human monitoring burden while collecting more informative data for the next iteration.

Our framework is motivated by a simple but important view of intervention trajectories. A human takeover simultaneously reveals three pieces of information: a semantic event about policy failure or recovery, an action-level correction signal, and a deployment-time indicator that autonomous execution has become unreliable. Existing methods typically use at most one of these aspects. In contrast, CHILO turns all three into reusable learning signals within a single closed-loop pipeline. This integration is particularly appealing in real-world settings because it does not require replacing the underlying robot learning stack. Instead, it upgrades how data are relabeled, how supervision is extracted from rollouts, and how assistance is requested during deployment.

We evaluate the proposed framework on real-world manipulation tasks in a closed-loop human-in-the-loop setting. Compared with standard behavior cloning, original advantage-conditioned policy training, and simple intervention-weighted baselines, our method aims to improve not only task success but also recovery performance and human-budget efficiency. The intended outcome is not merely a stronger policy after one round of training, but a better iterative learning process in which the system learns more effectively from human corrections and requests assistance more selectively.

Our contributions are threefold:

1. We propose an intervention-aware semantic relabeling strategy that enriches advantage-conditioned policy training with structured takeover semantics.
2. We introduce a counterfactual human correction distillation objective that directly learns from paired policy proposals and human-executed corrective actions.
3. We develop a query-efficient human-in-the-loop deployment mechanism that predicts when the robot should request human assistance based on deployment-time risk signals.

---

## 2. Related Work

Human intervention has played an increasingly important role in real-world robot learning, especially in settings where pure offline training is insufficient for robust deployment. Prior work has explored human-in-the-loop reinforcement learning, interactive imitation learning, intervention-aware policy learning, and assistance-trigger mechanisms. However, these directions have largely evolved in parallel. Some methods use interventions mainly as corrective demonstrations, some focus on sample-efficient policy improvement with humans in the loop, and others study when the robot should request help during deployment. In contrast, our work argues that a human takeover trajectory contains at least three reusable signals at once: semantic information about failure and recovery, action-level correction supervision, and deployment-time evidence that autonomous execution has become unreliable. We therefore position our work at the intersection of human-in-the-loop robot learning, learning from corrections, value-guided policy improvement, and query-efficient deployment.

### 2.1 Human-in-the-Loop Robot Learning and Deployment

Human-in-the-loop robot learning has been explored as a practical strategy for improving performance in real-world manipulation, where fully autonomous training remains difficult and costly. Interactive imitation learning and deployment-time correction have shown that human supervision can significantly improve robustness and data efficiency relative to pure offline imitation. More recent systems such as Sirius and HIL-SERL highlight the importance of intervention during real-world training and deployment, demonstrating that human guidance can help the robot recover from failures, explore more safely, and improve sample efficiency. These works provide strong evidence that human takeover is valuable in practice.

However, most of these approaches primarily treat intervention as a mechanism for collecting better trajectories or guiding policy updates, rather than as a structured object of analysis. In particular, intervention frames are often consumed either as additional demonstrations or as online corrections without explicitly distinguishing takeover onset, recovery dynamics, and low-value post-recovery segments. Our work builds on the same practical motivation as these methods, but takes a different view: instead of using intervention only as additional supervision, we reinterpret intervention trajectories as structured signals that can be relabeled, distilled, and reused across training and deployment.

### 2.2 Learning from Corrections and Interventions

Another line of work studies how robot policies can learn directly from corrections or imperfect demonstrations. Intervention-aware learning, counterfactual imitation, and correction-based policy updates all share the intuition that what the human does during recovery is especially informative. In particular, recent work such as Counter-BC emphasizes that imperfect demonstrations still contain recoverable intent, while intervention-based methods show that human overrides can guide the robot away from failure states.

Our work is closely related to this literature, but differs in an important respect. Existing approaches typically observe the corrected action alone, or treat intervention as a standalone supervisory event. In our setting, the system records both the policy-proposed action and the executed human-corrected action during deployment. This paired structure enables a stronger form of supervision: not only can we learn what action was taken, but we can also learn how the deployed policy should have changed its decision in the same state. This is the basis of our counterfactual human correction distillation objective.

### 2.3 Value-Guided Policy Improvement and Reward-Aware Data Reweighting

Value-guided and reward-aware policy improvement methods aim to improve policy learning by distinguishing higher-quality from lower-quality trajectory segments. Advantage-conditioned policy training, reward-aware behavior cloning, and stage-aware reward modeling all follow this general principle: rather than imitating all data uniformly, they attempt to prioritize samples that are more useful for improving policy quality. These ideas are particularly attractive for robot learning, where data collection is expensive and not all frames contribute equally to downstream performance.

Our work is aligned with this perspective, but extends it in two ways. First, we argue that binary advantage labels are insufficient in human-in-the-loop rollout datasets because intervention trajectories contain semantically different states that should not be collapsed into the same supervision class. Second, we connect value-guided relabeling to both action-level correction learning and deployment-time request-for-help decisions. In this sense, our method does not replace value-guided policy improvement; rather, it enriches it with intervention semantics and closes the loop between relabeling, training, and deployment.

### 2.4 Assistance Trigger and Query-Efficient Deployment

When to request human help is itself a central question in deployment-time robot learning. Prior work in interactive imitation learning and budget-aware supervision, such as ThriftyDAgger and more recent robot-gated assistance mechanisms, studies how to reduce human burden by intervening only when necessary. These methods show that selective querying can substantially improve the efficiency of human supervision.

Our work shares this motivation but differs in the source of the trigger signal. Rather than treating assistance as a standalone decision problem, we derive request-for-help decisions from the same closed-loop signals that also support relabeling and correction learning, including value-based risk, action disagreement, and intervention history. As a result, assistance triggering becomes part of a unified intervention-aware pipeline rather than a separate module. This enables us to ask not only whether the robot can request help efficiently, but whether doing so also improves the usefulness of the data collected for the next training round.

In summary, prior work has established that human intervention is valuable for real-world robot learning, that corrections can improve policy robustness, that value-guided relabeling can improve training, and that selective querying can reduce supervision cost. Our contribution is to unify these observations within a single closed-loop framework. Instead of using intervention as only a demonstration, only a correction, or only a request signal, we treat takeover trajectories as structured supervision that simultaneously supports semantic relabeling, correction distillation, and query-efficient deployment.

---

## 3. Problem Setup

We consider a closed-loop real-world robot learning setting in which a policy is iteratively deployed, corrected by a human when necessary, and retrained using accumulated rollout data. At each time step `t`, the robot observes a multimodal input `o_t`, receives a task description `tau`, and produces a policy-proposed action `a_t^pi`. During autonomous execution, the executed action equals the proposed action. When human takeover is activated, however, the executed action `a_t^e` is provided by the human operator and may differ substantially from `a_t^pi`. We denote the intervention indicator by `i_t in {0,1}`, where `i_t = 1` means that the human is currently intervening.

Each rollout trajectory additionally contains metadata that are available in our closed-loop system: frame-level intervention annotations, the policy-proposed action, the executed action, episode-level success labels, and post-hoc value annotations written back to the dataset after value inference. Specifically, after each deployment round we compute a frame-level value estimate `v_t`, an advantage target `A_t`, and a standard ACP indicator derived from the inferred trajectory quality. Unlike standard pipelines, we do not treat these quantities as isolated signals. Instead, we use them jointly to construct semantic conditioning labels, correction supervision targets, and deployment-time assistance triggers.

Formally, the dataset for one closed-loop round is a collection

`D_k = {(o_t, tau_t, a_t^pi, a_t^e, i_t, y_ep, v_t, A_t)}`

where `y_ep` denotes the episode outcome. Our goal is to learn a policy `pi_{k+1}` that improves three aspects simultaneously: task performance, correction and recovery capability, and human-budget efficiency during deployment. To achieve this, we introduce a unified learning framework that transforms intervention trajectories into structured supervision at the semantic, action, and deployment levels.

---

## 4. Method

The key idea of CHILO is to reinterpret human takeover as a structured signal rather than a binary event. A takeover not only indicates that autonomous execution has become unreliable, but also reveals how the policy should be corrected and whether the system should continue to operate autonomously in similar states. We therefore design CHILO around three coupled components. Intervention-Aware Advantage Conditioning enriches trajectory relabeling and policy conditioning with intervention semantics. Counterfactual Human Correction Distillation extracts action-level correction supervision from the discrepancy between policy proposals and executed actions. Query-Efficient Human-in-the-Loop Deployment uses deployment-time risk signals to decide when the system should actively request assistance. Together, these components improve both sides of the closed loop: the quality of supervision used for training and the quality of data collected during deployment.

### 4.1 Intervention-Aware Advantage Conditioning

Standard advantage-conditioned policy training uses a binarized indicator to distinguish high-quality and low-quality trajectory segments. While effective, this binary view is too coarse in the presence of human takeovers. In particular, intervention trajectories contain several semantically distinct regimes: autonomous progress before failure, the onset of human correction, active recovery under human control, and low-value tail segments after the trajectory has already been rescued. Treating all intervention frames as uniformly positive supervision can therefore dilute the learning signal and obscure which parts of a takeover are actually useful for future policy improvement.

To address this issue, we replace the binary conditioning label with an intervention-aware semantic tag. For each frame, we combine the inferred advantage `A_t`, the intervention indicator `i_t`, the discrepancy between the policy proposal and executed action, and short-horizon temporal context to assign a semantic label

`s_t = g(A_t, i_t, ||a_t^e - a_t^pi||, h_t),`

where `h_t` denotes local trajectory context such as recent intervention history or value trend. In practice, we instantiate `s_t` using a small discrete label set that distinguishes, for example, autonomous-positive, correction-onset, recovery-positive, recovery-tail, and autonomous-negative states. This semantic label is then injected into the task prompt rather than the model architecture, preserving compatibility with text-conditioned robot policies.

Concretely, given an original task description `tau_t`, we construct an intervention-aware conditioned task

`tau_t' = concat(tau_t, Tag(s_t)).`

This design retains the simplicity of prompt-based advantage conditioning while substantially increasing the expressiveness of the supervision signal. Importantly, it also makes ablations clean: the underlying policy architecture remains unchanged, and only the conditioning signal differs. As a result, performance gains can be attributed to improved supervision rather than model scaling or architectural changes.

The intervention-aware relabeling mechanism serves two purposes. First, it provides a more informative training signal for learning which states and trajectory segments should be imitated. Second, it creates a semantic bridge between rollout outcomes and deployment-time intervention events, which later supports both correction distillation and request-for-help prediction. In this sense, semantic relabeling is the front end of the entire framework: it transforms raw rollout logs into structured learning targets that better reflect how humans actually collaborate with the robot.

### 4.2 Counterfactual Human Correction Distillation

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

### 4.3 Query-Efficient Human-in-the-Loop Deployment

Even with improved supervision, continuously requiring a human to monitor deployment is expensive and limits scalability. A practical closed-loop system should therefore learn not only from human intervention, but also when to request it. We formulate this as a deployment-time assistance problem. At each time step, the robot computes a risk score indicating how likely autonomous execution is to become unreliable in the near future. Human assistance is requested only when this score exceeds a threshold, optionally under a fixed intervention budget.

The risk score is computed from deployment-time signals that are already available in the closed-loop pipeline. These include the inferred value or risk-aware value estimate `v_t`, the disagreement between conditioned and unconditioned policy predictions, and recent intervention history. Let `a_t^cond` and `a_t^uncond` denote the actions predicted with and without semantic conditioning. Their discrepancy

`d_t = ||a_t^cond - a_t^uncond||_2`

serves as a measure of action instability or conditional sensitivity. We then define

`r_t = h(-v_t, d_t, bar(i)_{t-k:t-1}, u_t),`

where `u_t` optionally denotes uncertainty and `bar(i)_{t-k:t-1}` summarizes recent intervention history. A help request is triggered when

`q_t = 1[r_t > eta],`

subject to a deployment budget if desired.

This mechanism improves deployment in two ways. First, it reduces the need for constant human attention by concentrating intervention on states that are likely to cause failure. Second, it improves the quality of future data collection by biasing human supervision toward informative failure or near-failure states rather than uniformly monitoring the entire rollout. In other words, the query policy is not just a safety tool; it is also a data curation mechanism for the next round of closed-loop learning.

### 4.4 Closed-Loop Training and Deployment Algorithm

The full CHILO pipeline alternates between deployment, relabeling, training, and redeployment. Starting from a policy `pi_k`, we collect human-in-the-loop rollouts in the real world while recording observations, policy-proposed actions, executed actions, intervention indicators, and episode outcomes. We then run value inference on the collected data to obtain frame-level value and advantage estimates. These signals are combined with intervention annotations to generate intervention-aware semantic tags. The resulting relabeled dataset is used to train the next policy using both the conditioned policy objective and the correction distillation loss. During deployment of `pi_{k+1}`, a learned or calibrated assistance trigger determines when human help should be requested. Newly collected data are merged back into the dataset for the next round.

This procedure can be summarized as

`D_{k+1} = D_k U Collect(pi_k, q_k),`

`S_{k+1} = Relabel(D_{k+1}, V_phi),`

`pi_{k+1} = Train(S_{k+1}).`

Taken together, the proposed framework turns a human takeover trajectory into three aligned supervision signals: a semantic label for conditioning policy training, an action-level correction target for learning recovery behavior, and a deployment-time signal for deciding when human help should be requested. This unified view is what distinguishes CHILO from existing approaches that use interventions either as demonstrations, as risk labels, or as action corrections in isolation. By coupling these signals within a single closed-loop pipeline, CHILO aims to improve not only the policy obtained after one round of training, but also the quality and efficiency of the iterative learning process itself.

---

## 5. Experiments

We evaluate CHILO in a real-world closed-loop human-in-the-loop manipulation setting. Our experiments are designed to answer five questions: (1) whether intervention-aware relabeling improves over standard binary advantage conditioning, (2) whether correction distillation improves recovery behavior, (3) whether learned request-for-help reduces human supervision cost, (4) whether the three components are complementary, and (5) under which scenarios the gains are most pronounced. To this end, we evaluate the method under nominal execution, perturbed initial states, forced near-failure recovery scenarios, and constrained human-budget deployment settings.

### 5.1 Experimental Setup

#### Tasks and platform

We perform experiments on a real dual-arm SO101 platform equipped with three RGB cameras and a human teleoperation interface. Our primary task is `bi_so101_handover_cube`, in which the robot must pick up a cube with the left arm and hand it to the right arm. This task is particularly suitable for evaluating intervention-aware learning because it is long-horizon, requires coordination across both arms, and often exhibits recovery-critical failure modes.

#### Closed-loop pipeline

We follow a closed-loop training protocol. Starting from demonstration data, we train an initial policy and deploy it with human-in-the-loop correction. The resulting rollout data are merged into the training pool, used to train a value function, and relabeled with frame-level value, advantage, and intervention-aware semantic labels. Policies are then trained from these relabeled data and redeployed in the next round. This setup matches the practical training loop used in our system and allows us to measure not only final policy performance but also the quality of the iterative improvement process.

#### Evaluation scenarios

We evaluate the method under four deployment settings. In **nominal rollout**, policies are evaluated from standard initial states without artificial disturbance. In **perturbed-init evaluation**, the task begins from more challenging initial configurations to test robustness. In **forced near-failure evaluation**, the robot is deliberately brought close to states that previously triggered human takeover, and success is measured after recovery. In **fixed-budget deployment**, the amount of human supervision is constrained to evaluate the request-for-help mechanism under limited intervention resources.

### 5.2 Baselines

We compare CHILO against several baselines representing different uses of rollout supervision. **BC** performs standard behavior cloning on the collected dataset without value-based relabeling. **ACP-Base** uses standard binary advantage-conditioned policy training. **ACP-InterventionPositive** assigns all intervention frames to the positive class, testing whether a simple intervention heuristic is sufficient. **RA-BC / SARM** represents reward-aware or stage-aware reweighting baselines already supported in our training stack. For the assistance-trigger experiments, we additionally compare against **Always Monitor**, in which a human continuously supervises deployment, and **Heuristic Query**, which requests assistance based on a fixed hand-designed rule. Finally, we evaluate ablations of our method corresponding to intervention-aware relabeling only, relabeling plus correction distillation, relabeling plus learned query, and the full model.

### 5.3 Metrics

We report three groups of metrics. **Task performance** includes task success rate and average episode length. **Recovery performance** includes recovery success rate and post-intervention success rate, measuring whether the policy can return to successful execution after entering difficult states. **Human-cost metrics** include intervention frame ratio, intervention count per episode, monitoring time, success under fixed human budget, and request-for-help precision and recall. Together, these metrics capture not only how well the robot solves the task, but also how efficiently it uses human supervision during deployment.

### 5.4 Research Questions

#### RQ1: Does Intervention-Aware Relabeling Improve over Binary ACP?

We first evaluate whether intervention-aware relabeling improves policy learning relative to standard binary advantage conditioning. This comparison isolates the contribution of richer semantic supervision while keeping the underlying policy architecture fixed. We compare BC, ACP-Base, ACP-InterventionPositive, and Intervention-Aware ACP under nominal rollout and, when possible, perturbed initial conditions.

Beyond final task performance, we analyze the semantic label distribution and its quality. Specifically, we report how often each label occurs and how each label correlates with frame-level advantage, action-correction magnitude, and episode success. These statistics help determine whether intervention-aware relabeling captures meaningful structure rather than introducing arbitrary label fragmentation.

#### RQ2: Does Correction Distillation Improve Recovery?

We next study whether explicit correction distillation improves recovery behavior. To do so, we compare ACP-Base, Intervention-Aware ACP, and Intervention-Aware ACP with correction distillation in settings where the policy must recover from difficult or previously failure-prone states. In particular, we use perturbed initial states and forced near-failure scenarios to test the ability of each method to return to successful execution after the policy begins to drift.

#### RQ3: Can Learned Request-for-Help Reduce Human Cost?

We then evaluate whether the learned request-for-help mechanism reduces human supervision cost during deployment. We compare Always Monitor, Heuristic Query, and the learned trigger under fixed human-budget settings. The key question is whether the robot can preserve task performance while asking for less human attention, or equivalently achieve better performance under the same monitoring budget.

#### RQ4: Are the Three Components Complementary?

Finally, we evaluate whether the three components of CHILO are complementary. We compare intervention-aware relabeling only, relabeling plus correction distillation, relabeling plus learned query, and the full model. These experiments test whether the framework behaves as a coherent closed-loop system rather than a collection of unrelated heuristics.

#### RQ5: Under Which Scenarios Are the Gains Largest?

To better understand when CHILO is most beneficial, we perform additional analyses across different scenario types, including intervention-heavy trajectories, perturbed starts, and low-budget deployment settings. This analysis is intended to reveal whether the proposed framework is especially useful in recovery-critical regimes, which would be consistent with its design motivation.

---

## 6. Results

### 6.1 Overall Performance

We begin by evaluating overall task performance under nominal rollout and perturbed initial conditions. As shown in Table 1, intervention-aware relabeling consistently improves over standard behavior cloning and binary advantage-conditioned policy training. In particular, our intervention-aware variant achieves higher success while maintaining comparable or better episode efficiency. These gains suggest that the richer semantic labels provide more informative supervision than either uniform imitation or binary ACP.

The gap between Intervention-Aware ACP and the intervention-all-positive baseline is especially important. Simply treating all intervention frames as positive supervision improves over vanilla BC in some cases, but remains inferior to explicitly separating corrective and recovery-related semantics. This result supports our central claim that human takeover trajectories should not be collapsed into a single positive class.

Under perturbed initial states, the advantage of intervention-aware relabeling becomes more pronounced. This suggests that semantic relabeling is particularly helpful when the deployed policy encounters states that differ from the nominal training distribution. Rather than merely improving average performance, the method appears to improve the quality of supervision in precisely those regimes where human intervention is most informative.

### 6.2 Recovery and Correction Results

We next evaluate whether correction distillation improves recovery behavior in difficult states. Table 2 and Figure 3 show that adding correction distillation improves both recovery success rate and post-intervention success, particularly in forced near-failure and perturbed-init evaluations. These results indicate that paired policy-proposed and human-corrected actions provide useful supervision beyond semantic relabeling alone.

The improvement is most evident in states that already caused the deployed policy to drift away from successful execution. In such situations, a standard policy objective may still encourage imitation of the corrected action, but it does not explicitly model how the original policy should have changed its decision. By contrast, correction distillation directly exploits the gap between the proposed and executed actions, making it better suited for learning recovery behavior.

This result is important for the broader closed-loop setting. Human takeovers do not merely provide more data; they provide *structured correction signals*. Our findings suggest that explicitly learning from these proposal-correction pairs helps the policy repair mistakes that would otherwise recur in future deployment rounds.

### 6.3 Human Budget and Query Efficiency

We then turn to the deployment-time assistance mechanism. Table 3 and Figure 4 show that the learned request-for-help trigger achieves a better trade-off between task success and human supervision cost than heuristic or always-monitor baselines. Under fixed supervision budgets, the learned trigger preserves more task performance, while under comparable success levels it requires less monitoring time.

The precision-recall results further suggest that the learned trigger is not merely querying more often. Instead, it appears to concentrate human assistance on states that are both difficult and informative. This is consistent with our design goal: the trigger should not only improve deployment safety, but also improve the quality of the data collected for the next round of training.

These findings highlight an important practical point. In real-world robot deployment, the bottleneck is often not only policy quality, but also the amount of human attention required to sustain iterative learning. By learning when to request help, the system moves closer to a scalable human-in-the-loop training process rather than a fully human-monitored pipeline.

### 6.4 Unified Ablation

Finally, Table 4 evaluates whether the three components of CHILO are complementary. Intervention-aware relabeling alone improves supervision quality and yields a strong performance gain over binary ACP. Adding correction distillation further improves recovery-related metrics, while adding the learned trigger improves human-budget efficiency. The full model achieves the strongest overall trade-off across task success, recovery robustness, and supervision cost.

This ablation is important because it demonstrates that CHILO is not simply a bundle of independent heuristics. Instead, the three components operate at different points in the closed-loop pipeline: semantic relabeling improves how rollout data are interpreted, correction distillation improves how hard states are learned from, and query-efficient deployment improves which states receive human supervision in future rounds. Their gains are therefore additive rather than redundant.

### 6.5 Qualitative Analysis

We additionally provide qualitative rollout analyses to better illustrate how the proposed framework behaves during difficult execution segments. Figure 5 visualizes intervention timing, policy-proposed actions, executed actions, value trends, and request-for-help decisions. These case studies reveal several recurring patterns. First, intervention-aware labels tend to align with meaningful transition points such as takeover onset and successful recovery. Second, policies trained with correction distillation more often return to successful execution after drift. Third, the learned trigger tends to activate near failure-critical states rather than uniformly throughout the trajectory.

Qualitative analysis is particularly useful here because some of the most important differences between methods are temporal and structural rather than scalar. A trajectory in which the robot briefly drifts, requests timely help, and successfully recovers may look only modestly different in aggregate statistics, yet it reflects a substantially more useful closed-loop behavior. These qualitative examples therefore complement the quantitative results by making the intervention dynamics directly visible.

---

## 7. Discussion

Taken together, the experimental results support a simple interpretation: human takeovers are more useful when treated as structured supervision rather than raw corrective demonstrations. Intervention-aware relabeling improves how rollout quality is represented during policy training, correction distillation improves how the policy learns to repair its own mistakes, and query-efficient deployment improves how human effort is allocated during rollout collection. This combination leads not only to a stronger policy, but also to a more effective iterative learning process.

An important implication of these findings is that the value of human intervention in robot learning is not limited to safety or short-term task completion. Human intervention also shapes the future training distribution. By selectively preserving the semantics of corrective segments, explicitly learning from proposal-correction pairs, and requesting help only when necessary, the system converts human supervision into a reusable asset for closed-loop improvement. In this sense, our results suggest that human intervention should be viewed as a first-class training signal in real-world robot deployment.

One of the central motivations of this work is that intervention, correction, and assistance triggering are often studied separately even though they occur in the same rollout. Our results suggest that this separation is artificial in closed-loop robot learning. A single takeover event simultaneously reveals that the policy has entered a difficult state, that a corrective action is needed, and that this state may warrant future assistance requests. Modeling these aspects jointly yields a more coherent and data-efficient learning process than treating them as unrelated problems.

This unified view is especially relevant in real-world robotics, where data collection opportunities are limited and human time is expensive. In such settings, methods that improve only training or only deployment may leave substantial efficiency gains unrealized. CHILO instead improves both how supervision is extracted from collected rollouts and how the next rollouts are collected.

---

## 8. Limitations

Despite the encouraging results, our study has several limitations. First, the framework still relies on human intervention data, and its effectiveness depends on the quality, consistency, and coverage of the collected takeover trajectories. If interventions are sparse, delayed, or highly inconsistent across operators, the semantic relabeling and correction targets may become noisy.

Second, while our experiments focus on real-world closed-loop deployment, they currently cover a limited number of tasks and embodiments. The benefits of intervention-aware relabeling and correction distillation are likely to be strongest in recovery-critical, long-horizon settings, but additional multi-task and cross-embodiment evaluation would be needed to establish broader generality.

Third, the request-for-help mechanism depends on deployment-time risk signals such as value estimates, action disagreement, and intervention history. If these signals are poorly calibrated, the trigger may become overly conservative or overly permissive. Although our lightweight trigger is attractive from a systems perspective, more principled uncertainty modeling may further improve reliability.

Finally, our method is designed to remain compatible with existing text-conditioned robot policies and therefore prioritizes minimal architectural change. This design choice improves modularity and makes ablations cleaner, but it may also limit the extent to which richer structured intervention signals can be exploited compared with more specialized policy architectures.

More broadly, our results should be interpreted as evidence that structured intervention supervision is promising, rather than as a complete solution to human-in-the-loop robot deployment. Future work should study how these ideas scale to larger task sets, multiple operators, and broader robot embodiments.

---

## 9. Future Work

Our work opens several directions for future research. One natural extension is to replace discrete intervention-aware labels with richer structured representations, such as stage-aware or uncertainty-aware semantic tags. Another direction is to use intervention supervision not only for policy improvement but also for data valuation, selectively prioritizing rollout segments that contribute most to future gains. It would also be valuable to study whether the semantics of intervention transfer across embodiments, tasks, or operators, which could help build more general closed-loop learning systems.

From a systems perspective, a particularly promising direction is to unify correction learning and assistance triggering more tightly. For example, a future system could use the same risk signal both to decide when to request help and to predict what type of correction is likely to be needed. This would move closed-loop deployment closer to a collaborative setting in which the robot not only asks for help at the right time, but also learns to anticipate the structure of the help it will receive.

---

## 10. Conclusion

In this paper, we presented CHILO, a unified framework for closed-loop real-world robot learning from human takeovers. Our key premise is that a takeover trajectory contains more than a corrective demonstration: it also reveals semantic information about failure and recovery, action-level evidence of how the policy should change its decision, and deployment-time cues about when human help is needed. We operationalized this view through intervention-aware semantic relabeling, counterfactual correction distillation, and query-efficient human-in-the-loop deployment.

By integrating these components into a single closed-loop pipeline, CHILO improves not only policy learning from collected rollouts but also the quality and efficiency of future rollout collection. This perspective shifts human intervention from a passive safety fallback to an active and reusable supervision source for robot learning. We hope this work helps move real-world robot deployment toward more scalable, data-efficient, and collaborative forms of continual improvement.

---

## Appendix Plan

### Appendix A: Semantic Relabeling Details

- label definitions
- rule table
- threshold selection
- example trajectories

### Appendix B: Additional Experimental Details

- training steps
- rollout budget
- hardware setup
- camera setup
- policy checkpoint details

### Appendix C: Additional Quantitative Results

- full metric tables
- per-scenario results
- per-label statistics

### Appendix D: Additional Qualitative Cases

- rollout timelines
- failure cases
- false-positive / false-negative trigger examples

---

## 当前仍需后续补齐的内容

- 正式参考文献引用与 bibliography
- 真实实验结果数值与表格
- 图 1 到图 5 的正式图片
- appendix 中的 label 规则细节
- 方法名 `CHILO` 是否最终采用

---

## 一句话总结

这份整合版已经把你前面分散的初稿真正合成成一篇连续论文草稿。  
**现在最缺的已经不再是论文结构，而是实验数值、正式图表和最终润色。**
