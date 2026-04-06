# RQ1 Relabeling 与标签统计实施方案

> 时间基准：2026-04-02  
> 关联文档：`实验计划表.md`、`Evo-RL论文大纲版.md`、`Evo-RL论文初稿版_Introduction_Method.md`  
> 重要约束：**本文件只整理实现方案，不改任何代码文件。**  
> 目标：把 `RQ1: Intervention-aware relabeling 是否优于原始二值 ACP` 需要的 relabeling 和标签统计，整理成一份可以直接照着实施的文档。

---

## 0. 这份文档解决什么问题

你现在已经有：

- `value train`
- `value infer`
- `advantage`
- `acp indicator`
- `policy_action`
- `is_intervention`
- `episode_success`

但对于 `RQ1` 来说，还缺两件真正能支撑实验的东西：

1. **Intervention-aware semantic relabeling**
2. **标签质量统计输出**

也就是说，我们现在不是再讨论“要不要做”，而是把下面这件事定义清楚：

**如何在不改变现有整体主链的前提下，把 `lerobot_value_infer.py` 从“只写回 value / advantage / binary indicator”升级成“还能写回 semantic label，并自动产出标签统计摘要”的流程。**

---

## 1. RQ1 的论文目标，翻译成工程目标是什么

在论文里，`RQ1` 的表述是：

**Intervention-aware relabeling 是否优于原始二值 ACP？**

把它翻译成工程目标，就是下面 4 件事：

1. 在 `value infer` 阶段额外生成一个新的逐帧语义标签字段
2. 这个标签字段必须使用你已有的 intervention / action gap / advantage 信息
3. 这个标签字段必须被写回原始数据集，和 `value / advantage / indicator` 一样稳定可复用
4. 推理结束后自动输出统计结果，用于论文里的 `FIG-2` 和 `K12`

所以 RQ1 的最低落地标准，不是“脑子里想到了 4 类标签”，而是：

- 数据集里真的有了新字段
- 输出目录里真的有了标签统计文件
- 你真的能拿这些统计去画图、做表、写论文

---

## 2. 当前代码里最适合改哪

按照你仓库现在的结构，**最合理的改动入口就是 `src/lerobot/scripts/lerobot_value_infer.py`**。

原因：

- 现在 `value infer` 已经负责：
  - 算 `predicted value`
  - 算 `advantages`
  - 二值化 `indicator`
  - 写回 parquet
- 也就是说，它天然就是“标签后处理中心”
- 如果 RQ1 从这里接入，风险最低

当前最相关的文件应该是：

- [src/lerobot/scripts/lerobot_value_infer.py](/home/jy/Data/YCP/Evo-RL/src/lerobot/scripts/lerobot_value_infer.py)
- [src/lerobot/configs/value.py](/home/jy/Data/YCP/Evo-RL/src/lerobot/configs/value.py)
- [src/lerobot/scripts/value_infer_viz.py](/home/jy/Data/YCP/Evo-RL/src/lerobot/scripts/value_infer_viz.py)
- [实验计划表.md](/home/jy/Data/YCP/Evo-RL/实验计划表.md)

其中最重要的事实是：

- 现在已经有 `_compute_n_step_advantages(...)`
- 现在已经有 `_binarize_advantages(...)`
- 现在已经有 `_write_columns_in_place(...)`

所以 RQ1 不需要另开一条脚本链，而应该在这条链上加一个新分支：

```text
predicted value
    ->
advantage
    ->
binary indicator
    ->
semantic relabel
    ->
label stats
    ->
write back to dataset
```

---

## 3. 建议新增的字段

为了尽量不破坏当前主链，我建议 RQ1 新增下面两个产物：

### 3.1 新的逐帧字段

建议新增：

```text
complementary_info.acp_semantic_label
```

类型建议：

- `int64`

原因：

- 和当前 `acp_indicator` 的写回方式一致
- 便于训练时作为条件标签或后续 hook 使用
- 便于 parquet 写回，不需要先扩展字符串类型处理逻辑

### 3.2 新的统计文件

建议新增：

```text
outputs/value_infer/<RUN>/value/semantic_label_stats.json
```

这个文件不写回数据集，而是写到输出目录里。

原因：

- 标签统计本质上是一次推理 run 的产物
- 不一定要作为 dataset feature 永久保存
- JSON 很适合后续做论文图表和复盘

---

## 4. 建议采用的语义标签定义

为了让故事清晰，同时保持实现复杂度可控，我建议 `RQ1` 第一版只用 **5 类标签**。

| 标签 ID | 标签名 | 含义 |
| --- | --- | --- |
| `0` | `autonomous_negative` | 非 intervention 帧，且属于低质量 / 负标签帧 |
| `1` | `autonomous_positive` | 非 intervention 帧，且属于高质量 / 正标签帧 |
| `2` | `correction_onset` | intervention 段开始时的接管帧 |
| `3` | `recovery_positive` | intervention 段中真正起恢复作用的高价值帧 |
| `4` | `recovery_tail` | intervention 段中价值较低、偏尾部的恢复帧 |

这 5 类的好处是：

- 语义非常直观
- 足够覆盖 `RQ1` 的论文叙事
- 不会因为标签过多导致样本过稀

不建议第一版就加太多类，比如：

- `release`
- `pre_failure`
- `near_miss`
- `post_recovery_negative`

这些更适合作为第二版消融，不适合一上来就塞进主文。

---

## 5. RQ1 第一版 relabeling 规则

下面给出一版足够稳、又能体现论文新意的规则。

### 5.1 输入信号

建议使用以下输入：

- `advantage`
- `binary indicator`
- `is_intervention`
- `action`
- `complementary_info.policy_action`
- 局部 intervention 状态上下文

对应你当前代码里已有字段：

- `action`
- `complementary_info.policy_action`
- `complementary_info.is_intervention`
- `complementary_info.advantage_*`
- `complementary_info.acp_indicator_*`

### 5.2 派生量

先计算：

```text
delta_t = ||action_t - policy_action_t||_2
```

它表示：

- 当前这一帧，人类对 policy 纠正了多大

再计算：

- 当前 intervention 段的开始位置
- 当前帧是否处于 intervention 段中
- 当前帧是否是 intervention onset

### 5.3 具体规则

#### 规则 A：非 intervention 帧

如果：

```text
is_intervention = 0
```

则：

- `indicator = 1` -> `autonomous_positive`
- `indicator = 0` -> `autonomous_negative`

#### 规则 B：intervention onset

如果：

```text
当前帧 is_intervention = 1
且前一帧不是同一段 intervention
```

则：

- 直接标成 `correction_onset`

#### 规则 C：intervention 中间帧

如果：

```text
当前帧在 intervention 段内部
且不是 onset
```

则：

- 如果 `indicator = 1`，标成 `recovery_positive`
- 否则如果 `delta_t` 高于 intervention 帧内部的某个分位阈值，也标成 `recovery_positive`
- 否则标成 `recovery_tail`

### 5.4 为什么这套规则合理

因为它同时用到了三种信息：

1. **quality**：来自 `advantage / indicator`
2. **human correction strength**：来自 `action - policy_action`
3. **intervention semantics**：来自接管开始 / 中间 / 结束结构

这正好对应论文里要讲的三点：

- 原始 ACP 太粗
- 接管不是全部 positive
- 真正有学习价值的是接管中的关键恢复片段

---

## 6. RQ1 应该怎么改文件

这里先强调一遍：**下面是改动方案，不是已经改好的代码。**

### 6.1 [src/lerobot/configs/value.py](/home/jy/Data/YCP/Evo-RL/src/lerobot/configs/value.py)

建议新增一组 semantic relabel 配置，例如：

```text
acp.semantic.enable
acp.semantic.label_field
acp.semantic.action_field
acp.semantic.policy_action_field
acp.semantic.delta_quantile
acp.semantic.stats_output_filename
```

建议默认值：

```text
acp.semantic.enable = false
acp.semantic.label_field = complementary_info.acp_semantic_label
acp.semantic.action_field = action
acp.semantic.policy_action_field = complementary_info.policy_action
acp.semantic.delta_quantile = 0.75
acp.semantic.stats_output_filename = semantic_label_stats.json
```

### 6.2 [src/lerobot/scripts/lerobot_value_infer.py](/home/jy/Data/YCP/Evo-RL/src/lerobot/scripts/lerobot_value_infer.py)

建议新增这些 helper：

```text
_compute_action_gap_norms(...)
_compute_intervention_onset_mask(...)
_compute_semantic_labels(...)
_compute_semantic_label_stats(...)
_write_semantic_label_stats_json(...)
```

然后在当前逻辑里接入：

```text
predicted_values
    ->
advantages
    ->
binary indicators
    ->
semantic_labels
    ->
columns[...] = semantic_labels
    ->
stats_json
```

### 6.3 [src/lerobot/scripts/value_infer_viz.py](/home/jy/Data/YCP/Evo-RL/src/lerobot/scripts/value_infer_viz.py)

第一版不是必须改。

如果后面你要做主文 `FIG-2` 的可视化增强，再考虑补：

- 不同 semantic label 的颜色条
- intervention onset 标记
- recovery tail 标记

### 6.4 [src/lerobot/rl/acp_hook.py](/home/jy/Data/YCP/Evo-RL/src/lerobot/rl/acp_hook.py)

**RQ1 第一阶段先不改。**

因为现在先要做的是：

- label 生成
- label 统计

等标签分布验证合理后，再决定怎么把 semantic label 真正接入训练。

换句话说，当前阶段的目标是：

**先把标签做对，再把标签用进去。**

---

## 7. 推荐的伪代码

下面给出一版非常接近真实实现的伪代码。

```python
# Step 1: existing outputs
advantages = compute_advantages(...)
indicators = binarize_advantages(...)

# Step 2: action gap
delta = l2_norm(action - policy_action)

# Step 3: intervention segmentation
onset = compute_intervention_onset_mask(intervention, episode_index, frame_index)

# Step 4: choose threshold inside intervention frames
delta_threshold = quantile(delta[intervention == 1], q=0.75)

# Step 5: semantic relabel
labels = zeros_like(indicators)
for t in range(num_frames):
    if intervention[t] == 0:
        labels[t] = autonomous_positive if indicators[t] == 1 else autonomous_negative
    else:
        if onset[t]:
            labels[t] = correction_onset
        else:
            if indicators[t] == 1 or delta[t] >= delta_threshold:
                labels[t] = recovery_positive
            else:
                labels[t] = recovery_tail

# Step 6: write back
columns["complementary_info.acp_semantic_label"] = labels

# Step 7: stats
stats = summarize_by_label(
    labels=labels,
    advantages=advantages,
    values=predicted_values,
    delta=delta,
    intervention=intervention,
    episode_success=episode_success,
)
write_json(stats)
```

---

## 8. 应该输出哪些统计

为了让 `RQ1` 真正能用在论文里，我建议统计至少分成三层。

### 8.1 Overall label distribution

输出：

- 每个 label 的 count
- 每个 label 的 ratio

例如：

```json
{
  "autonomous_negative": {"count": 1234, "ratio": 0.31},
  "autonomous_positive": {"count": 1456, "ratio": 0.36},
  "correction_onset": {"count": 120, "ratio": 0.03},
  "recovery_positive": {"count": 698, "ratio": 0.17},
  "recovery_tail": {"count": 512, "ratio": 0.13}
}
```

### 8.2 Label quality summary

建议每个 label 再统计：

- mean advantage
- mean predicted value
- mean action gap
- success-episode ratio
- intervention ratio

这部分就是论文里的 `K12` 基础。

### 8.3 Per-task label stats

如果后面你有多个 task，这一层非常重要。

即便当前你主要只有一个 `bi_so101_handover_cube`，也建议现在就把格式设计好。

建议输出：

- 每个 task 内各标签 count / ratio

这样未来扩任务时不会返工。

---

## 9. JSON 统计文件建议格式

建议 `semantic_label_stats.json` 至少包含下面这些键：

```json
{
  "dataset_repo_id": "...",
  "label_field": "complementary_info.acp_semantic_label",
  "label_id_to_name": {
    "0": "autonomous_negative",
    "1": "autonomous_positive",
    "2": "correction_onset",
    "3": "recovery_positive",
    "4": "recovery_tail"
  },
  "frame_count": 0,
  "intervention_frame_count": 0,
  "delta_quantile": 0.75,
  "delta_threshold": 0.0,
  "overall": {},
  "per_task": {}
}
```

这里最关键的是两个字段：

- `delta_quantile`
- `delta_threshold`

因为你论文里一定会被问：

**recovery_positive 和 recovery_tail 到底怎么分的？**

只要这个 JSON 里有阈值记录，后面复盘和论文写作都会轻松很多。

---

## 10. 这个统计如何对应论文图表

### 10.1 对应 `FIG-2`

建议 `FIG-2` 做成两部分：

1. semantic label distribution 柱状图
2. 不同 label 的 `mean advantage / mean delta gap / success ratio`

### 10.2 对应 `TBL-1`

`TBL-1` 是 RQ1 的主结果表，里面应该放：

- BC
- 原始 ACP
- intervention-positive ACP
- intervention-aware ACP

而这份统计文件的作用是支撑：

- 为什么 semantic relabeling 合理
- 为什么它不是拍脑袋的 heuristic

### 10.3 对应 Appendix

附录建议额外放：

- 每个 label 的示意轨迹截图
- label 数量分布
- label 与 intervention 段位置的关系

---

## 11. RQ1 最低可交付物

如果你要判断“RQ1 有没有真正做出来”，我建议最低标准是下面这些：

### 必须有

- [ ] 数据集新增 `complementary_info.acp_semantic_label`
- [ ] 输出目录新增 `semantic_label_stats.json`
- [ ] 标签数量分布可读
- [ ] 每个标签的 mean advantage / mean delta gap / success ratio 可读

### 最好有

- [ ] 每个 task 的标签分布
- [ ] 标签和 intervention onset 的关系统计
- [ ] 一张可视化图草稿

### 当前阶段不要求

- [ ] 先不要求已经接进训练
- [ ] 先不要求 prompt hook 已支持多标签
- [ ] 先不要求线上部署 query 逻辑已经改

这是因为当前目标只是 `RQ1`，不要把整个方法一次做太大。

---

## 12. 你现在就可以怎么用这份文档

如果你下一步准备真正开始实现，我建议顺序是：

1. 先照本文件第 6 节改配置和 `value_infer`
2. 先把 `semantic_label_stats.json` 跑出来
3. 对照本文件第 8 节检查统计是否合理
4. 再决定要不要进入训练侧接入

如果你继续保持“只新增文档、不改代码”的方式推进，那这份文档本身已经可以直接作为：

- RQ1 的实施说明
- 论文方法附注
- 代码改动 TODO 清单

---

## 13. 一句话总结

RQ1 真正需要的不是“一个更花哨的标签名”，而是：

**把现有 `value infer -> indicator write-back` 链路升级成 `semantic relabel -> stats output -> dataset write-back` 链路，并且让每个标签为什么成立、分布如何、质量怎样，都能在输出文件里被看到。**
