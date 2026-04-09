# bi_so101_handover_cube_demo 数据检查报告（按详细复现流程）

检查时间：2026-04-09  
检查仓库：`/home/jy/Data/YCP/Evo-RL`  
检查数据：
- 解压目录：`/home/jy/Data/YCP/lerobot_datasets/local/bi_so101_handover_cube_demo`
- 压缩包：`/home/jy/Data/YCP/lerobot_datasets/local/bi_so101_handover_cube_demo.zip`

参考标准：`详细复现流程.md` 中 Step 3.5 的通过标准，以及 Step 4/7/8/9 的训练依赖字段要求。

---

## 1) 压缩包完整性

命令：

```bash
unzip -t /home/jy/Data/YCP/lerobot_datasets/local/bi_so101_handover_cube_demo.zip
```

结果：`No errors detected in compressed data`，压缩包完整。

判定：通过。

---

## 2) 目录结构与文件完整性（LeRobot v3.0）

已检查目录包含：
- `data/chunk-000/file-000..004.parquet`
- `meta/info.json`
- `meta/stats.json`
- `meta/tasks.parquet`
- `meta/episodes/chunk-000/file-000..004.parquet`
- `videos/observation.images.left_wrist/...`
- `videos/observation.images.right_wrist/...`
- `videos/observation.images.right_front/...`

并验证了视频引用一致性（基于 `meta/episodes`）：
- `left_wrist`：引用 6 个文件，实际 6 个，缺失 0，孤儿 0
- `right_wrist`：引用 6 个文件，实际 6 个，缺失 0，孤儿 0
- `right_front`：引用 5 个文件，实际 5 个，缺失 0，孤儿 0

说明：`right_front` 比其他相机少一个分片是“引用与实际一致”的正常结果，不是损坏。

判定：通过。

---

## 3) 元数据与统计一致性

来自 `meta/info.json` 的关键值：
- `codebase_version: v3.0`
- `robot_type: bi_so_follower`
- `total_episodes: 30`
- `total_frames: 57911`
- `fps: 30`
- `total_tasks: 1`
- `action` 维度：14
- `observation.state` 维度：14
- 三路视频分辨率：`480x640x3`

来自 `meta/tasks.parquet`：
- 任务数 1
- 任务文本统一为：  
  `Pick up the cube with the left arm, hand it over to the right arm, and then place it into the box.`

判定：通过。

---

## 4) 官方检查脚本（文档同款）

命令：

```bash
HF_HOME=/tmp/hf_home HF_DATASETS_CACHE=/tmp/hf_datasets_cache \
conda run -n evo-rl lerobot-dataset-report \
  --dataset /home/jy/Data/YCP/lerobot_datasets/local/bi_so101_handover_cube_demo
```

关键输出：
- actual totals: episodes=30, frames=57911
- episode length: mean=64.35s, min=30.83s, max=167.70s
- feature schema 含 `action / observation.state / 3路视频 / task_index / timestamp`

判定：通过（满足 Step 3.5 的“episode 数量、字段、任务统一、长度合理”）。

---

## 5) 深度一致性检查

### 5.1 帧级数据合法性（所有 parquet 帧）

检查项：
- `timestamp` 有限值
- `action` 和 `observation.state` 维度是否恒为 14
- `NaN` 检查
- 每个 episode 的 `frame_index` 是否连续递增
- 每个 episode 的 `timestamp` 是否单调不降

结果：
- `bad_ts=0`
- `bad_dim=0`
- `nan_state=0`
- `nan_action=0`
- `episode_order_violations=0`

判定：通过。

### 5.2 真实解码可读性（训练读数风险检查）

检查方式：
- 用 `LeRobotDataset` 直接加载数据
- 抽样读取首帧、中帧、末帧（含三路视频解码）
- 对 30 个 episode 做首末帧边界解码（共 60 次）

结果：
- 成功加载：`num_episodes=30`, `num_frames=57911`
- 三路视频均成功解码到 `torch.float32`，形状 `(3, 480, 640)`
- 边界解码：`errors=0`

判定：通过。

---

## 6) 按复现流程的训练可用性结论

### 6.1 Step 4（初始 pi05 SFT）是否可用

结论：可用。  
理由：Step 4 对 demo 集的核心要求已满足（30 条、状态动作与图像字段齐全、任务统一、可正常加载）。

### 6.2 Step 7/8/9（Value/ACP）能否只靠这一个 demo 集直接做

结论：不建议，仅靠这一个 demo 集不满足流程目标。  
原因：
- `meta/episodes` 中没有 `episode_success`
- 没有 `complementary_info.collector_policy_id`
- 这两个字段属于 round1 human-in-loop/merge 后才应具备的监督信息

流程建议：
1. 先按文档完成 Step 5（采集 round1，包含成功/失败标注等字段）  
2. 再按 Step 6 merge demo+round1  
3. 再进入 Step 7/8/9（value train / value infer / ACP train）

---

## 7) 最终判定

- 对“初始 SFT 训练数据”标准：通过。  
- 对“完整 RECAP 闭环后续 value/ACP 阶段”标准：当前 demo 单集不充分，需要 round1 + merge 后再继续。

