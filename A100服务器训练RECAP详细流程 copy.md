# A100服务器训练RECAP详细流程

## 1. 文档目的

这份文档的目标不是只讲概念，而是把这套 `Evo-RL / RECAP 风格闭环` 按照“真的上手跑”的方式完整梳理一遍。

默认按下面这套实际配置来写：

- 机器人：`SO101`
- 策略模型：`pi05`
- 训练服务器：`单卡 A100 80GB`
- 机器人侧机器：本地控制机
- 数据同步方式：`本地机落盘 + 手动上传到 A100 服务器`

本文档会覆盖：

1. 整体流程到底是什么
2. 本地机和 A100 服务器分别做什么
3. 从采集第一批 demo，到训练初始 policy
4. 从 human-in-loop 收集 round1，到训练 value
5. 从 value infer 打标签，到 ACP policy 训练
6. 如何部署新策略并进入下一轮
7. 每一步结束后，怎么判断自己能不能进入下一步
8. 常见坑、常见误区、常见报错思路

如果后面你要逐步问问题，我们就以这份文档为主线。

---

## 2. 先建立全局图

这套代码的核心不是“在线 actor-learner 式强化学习”，而是一个 **迭代式 offline RL / RECAP 风格闭环**：

```text
人工示范 / 人在环采集
        |
        v
得到当前轮数据集
        |
        v
训练 value model
        |
        v
对每一帧做 value inference
        |
        v
计算 advantage，并二值化成 ACP indicator
        |
        v
用 indicator 给 task text 注入 positive / negative tag
        |
        v
训练下一版 policy
        |
        v
部署新 policy 到机器人
        |
        v
继续收下一轮数据
```

这条链路里最重要的 4 个命令行入口是：

- `lerobot-human-inloop-record`
- `lerobot-value-train`
- `lerobot-value-infer`
- `lerobot-train`

你可以把它理解成：

- `record`：收集数据
- `value-train`：训练“好坏评估器”
- `value-infer`：给数据集逐帧打分、打标签
- `train`：用标签继续训练 policy

---

## 3. 机器分工

这一步一定要先想清楚，不然后面很容易把流程跑乱。

### 3.1 本地机器人机负责什么

本地机负责：

- 机械臂和相机联调
- 纯人工 demo 采集
- human-in-loop 策略部署
- 人工 takeover 纠错
- 成功 / 失败标注

本地机不建议承担正式训练任务。

### 3.2 A100 服务器负责什么

A100 服务器负责：

- 初始 `pi05` SFT
- `value` 模型训练
- `value` 推理并写回数据集
- ACP policy 训练

### 3.3 为什么要这样分工

因为：

- 机器人、串口、相机、leader/follower 都在本地机上
- 训练最吃显存和算力，应该交给 A100
- 最稳的工作方式是：
  - 本地机把数据集直接写到本地磁盘
  - 用 `rsync` / `scp` 把数据目录上传到 A100
  - A100 直接从本地目录训练
  - 训练出的 policy 再从 A100 拷回本地机部署

这样做的好处是：

- 不依赖 Hugging Face Hub 存储数据
- 数据同步过程更可控
- 对内网实验环境更友好

---

## 4. 你在开始前需要准备什么

## 4.1 本地机准备

至少确认下面这些东西是通的：

- SO101 follower 能正常被识别
- SO101 leader 能正常被识别
- 相机能正常出图
- 你知道每个串口和相机路径
- 你已经能激活仓库环境

环境按仓库里的要求：

```bash
conda activate lerobot
```

如果你的环境不是这个名字，再按仓库指令切换。

## 4.2 A100 服务器准备

A100 服务器要确认：

- CUDA 正常
- 能拉 Hugging Face 模型
- 能运行 `lerobot-train`
- 能运行 `lerobot-value-train`
- 能运行 `lerobot-value-infer`

注意：这里说的“能拉 Hugging Face 模型”，主要是指：

- `lerobot/pi05_base`
- `google/siglip-so400m-patch14-384`
- `google/gemma-3-270m`

也就是**模型权重来源**仍然可能在 Hugging Face 上。

但你的**数据集本身**可以完全不走 Hugging Face Hub。

如果服务器是共享环境，还要按仓库说明设置：

```bash
export HF_HOME=/llm_jzm/cache/huggingface/
export HF_TOKEN=<SHARED_HF_TOKEN>
export HF_ENDPOINT=https://hf-mirror.com
export WANDB_API_KEY=<SHARED_WANDB_API_KEY>
wandb login --relogin "$WANDB_API_KEY"
```

如果你是自己机器上的专用环境，就不需要强行套共享配置。

## 4.3 建议统一命名

后面所有数据集 ID、目录、run 名都建议统一，不然后面 round1、round2 很容易混乱。

在这套“本地机落盘 + 上传服务器”的工作流里，我建议你先约定下面这些变量：

```bash
export DATA_NS=local
export TASK_NAME=so101_cube_pick
export TASK_TEXT="Pick up the cube and place it into the target area"

export LOCAL_DATA_ROOT=/path/to/local_machine/lerobot_datasets
export SERVER_DATA_ROOT=/path/to/a100/lerobot_datasets
```

推荐继续把每个数据集和模型名也固定下来：

```bash
export DEMO_REPO_ID=${DATA_NS}/${TASK_NAME}_demo
export ROUND1_REPO_ID=${DATA_NS}/eval_${TASK_NAME}_round1
export MERGED_R1_REPO_ID=${DATA_NS}/${TASK_NAME}_merged_r1

export PI05_SFT_R0_NAME=${TASK_NAME}_pi05_sft_r0
export VALUE_R1_NAME=${TASK_NAME}_value_r1
export PI05_ACP_R1_NAME=${TASK_NAME}_pi05_acp_r1
```

这里有两个关键点：

1. `repo_id` 仍然建议保留成带 `/` 的形式
   - 例如 `local/so101_cube_pick_demo`
   - 因为仓库里很多工具默认按这种格式工作

2. 带 policy 的 human-in-loop 数据集建议加 `eval_` 前缀
   - 例如 `local/eval_so101_cube_pick_round1`
   - 因为当前 `lerobot-human-inloop-record` 内部会检查这个命名约束

后面命名建议按这个规范：

- 初始 demo 数据集 ID：`${DEMO_REPO_ID}`            纯人工示范
- round1 数据集 ID：`${ROUND1_REPO_ID}`             
- merge 后数据集 ID：`${MERGED_R1_REPO_ID}`
- 初始 policy 目录名：`${PI05_SFT_R0_NAME}`
- value 模型目录名：`${VALUE_R1_NAME}`
- ACP policy 目录名：`${PI05_ACP_R1_NAME}`

本地机和服务器上的目录建议都按 `root/repo_id` 存：

- demo 本地目录：`${LOCAL_DATA_ROOT}/${DEMO_REPO_ID}`
- round1 本地目录：`${LOCAL_DATA_ROOT}/${ROUND1_REPO_ID}`
- demo 服务器目录：`${SERVER_DATA_ROOT}/${DEMO_REPO_ID}`
- round1 服务器目录：`${SERVER_DATA_ROOT}/${ROUND1_REPO_ID}`

### 4.5 正式开始前，先执行一次变量初始化

是的，建议你在**第一阶段采 demo 之前**，先把这一组变量统一 `export` 一次。

原因很简单：

- 后面所有命令都会反复用到这些名字
- 如果不先定义，像 `${DEMO_REPO_ID}` 这种变量不会自动存在
- 先统一好变量，可以避免手写路径和数据集名时出错

推荐你在本地机和 A100 服务器各自终端里，都先执行一遍。

你可以直接用这个模板：

```bash
export DATA_NS=local
export TASK_NAME=so101_cube_pick
export TASK_TEXT="Pick up the cube and place it into the target area"

export LOCAL_DATA_ROOT=/path/to/local_machine/lerobot_datasets
export SERVER_DATA_ROOT=/path/to/a100/lerobot_datasets

export DEMO_REPO_ID=${DATA_NS}/${TASK_NAME}_demo
export ROUND1_REPO_ID=${DATA_NS}/eval_${TASK_NAME}_round1
export MERGED_R1_REPO_ID=${DATA_NS}/${TASK_NAME}_merged_r1

export PI05_SFT_R0_NAME=${TASK_NAME}_pi05_sft_r0
export VALUE_R1_NAME=${TASK_NAME}_value_r1
export PI05_ACP_R1_NAME=${TASK_NAME}_pi05_acp_r1
```

执行完以后，建议立刻检查一下：

```bash
echo $DEMO_REPO_ID
echo $ROUND1_REPO_ID
echo $LOCAL_DATA_ROOT
echo $SERVER_DATA_ROOT
```

你应该能看到类似：

```text
local/so101_cube_pick_demo
local/eval_so101_cube_pick_round1
/path/to/local_machine/lerobot_datasets
/path/to/a100/lerobot_datasets
```

如果你不想每次重新输入，可以把这段放进：

- 本地机的 `~/.bashrc`
- A100 服务器的 `~/.bashrc`

或者单独存成一个 `env.sh`，每次先执行：

```bash
source env.sh
```

后面第 7 阶段开始出现的 `${DEMO_REPO_ID}`、`${ROUND1_REPO_ID}`、`${PI05_SFT_R0_NAME}` 这些变量，默认都建立在这一步已经执行过的前提上。

### 4.6 推荐直接准备一个 `env.sh`

如果你准备多次跑这个流程，我更建议你直接准备一个单独的环境变量脚本。

例如可以在项目目录里放一个：

```bash
#!/usr/bin/env bash

export DATA_NS=local
export TASK_NAME=so101_cube_pick
export TASK_TEXT="Pick up the cube and place it into the target area"

export LOCAL_DATA_ROOT=/path/to/local_machine/lerobot_datasets
export SERVER_DATA_ROOT=/path/to/a100/lerobot_datasets

export DEMO_REPO_ID=${DATA_NS}/${TASK_NAME}_demo
export ROUND1_REPO_ID=${DATA_NS}/eval_${TASK_NAME}_round1
export MERGED_R1_REPO_ID=${DATA_NS}/${TASK_NAME}_merged_r1

export PI05_SFT_R0_NAME=${TASK_NAME}_pi05_sft_r0
export VALUE_R1_NAME=${TASK_NAME}_value_r1
export PI05_ACP_R1_NAME=${TASK_NAME}_pi05_acp_r1
```

后面每次开新终端，只要先执行：

```bash
source env.sh
```

然后可以马上检查：

```bash
echo $DEMO_REPO_ID
echo $ROUND1_REPO_ID
echo $PI05_SFT_R0_NAME
```

这样后面文档里所有像：

- `${DEMO_REPO_ID}`
- `${ROUND1_REPO_ID}`
- `${MERGED_R1_REPO_ID}`
- `${PI05_SFT_R0_NAME}`

这些变量都会自动可用。


## 5. 先记住 A100 80GB 上的推荐 batch

仓库 README 给的是模板值，但真正第一次跑，建议按“保守可落地”的配置来。

### 5.1 我建议你第一次先这样设

- 初始 `pi05` SFT：`batch_size=8`
- ACP `pi05` 训练：`batch_size=8`
- `value-train`：`batch_size=64`
- `value-infer`：`runtime.batch_size=128`

### 5.2 如果显存仍然紧张

按这个顺序改：

1. 先降 `batch_size`
2. 确保 `--policy.gradient_checkpointing=true`
3. 确保 `--policy.dtype=bfloat16`
4. 先把 `--policy.compile_model=false`
5. 如果只是先求闭环跑通，加 `--policy.train_expert_only=true`

### 5.3 为什么不直接照 README 的 `32`

因为 README 给的是“单 GPU 模板”，不是“你第一次上手最稳配置”。

对于 `pi05 + A100 80GB`，理论上可以比 `8` 更大，但第一次跑流程时，更重要的是：

- 先稳定跑通
- 先搞清楚数据是不是对的
- 先避免在训练第一步就被 OOM 或数据异常卡住

所以第一次先从保守值开始，后面再放大。

---

## 6. 第零阶段：先做本地硬件联调

这一步不是可选项。

如果机械臂、相机、leader/follower 还没稳定，后面所有训练结果都没有意义。

### 6.1 目标

确认：

- follower 可以正常执行动作
- leader 可以正常 teleop
- 图像采集正常
- 显示正常
- 没有明显串口掉线或相机掉帧

### 6.2 推荐动作

先用 `lerobot-teleoperate` 做最小联调。

单臂 SO101 的命令会因你的硬件接线略有差异，这里给你一个结构模板：

```bash
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/<SO101_FOLLOWER_PORT> \
  --robot.id=my_so101_follower \
  --robot.cameras='{ front: {type: opencv, index_or_path: "/dev/v4l/by-path/<FRONT_CAM>", width: 640, height: 480, fps: 30}}' \
  --teleop.type=so101_leader \
  --teleop.port=/dev/serial/by-id/<SO101_LEADER_PORT> \
  --teleop.id=my_so101_leader \
  --display_data=true
```

如果你是双臂 SO101，要改成 README 里的 `bi_so_follower` / `bi_so_leader` 结构。

### 6.3 通过标准

满足下面这些再继续：

- 你能稳定 teleop 完成一个完整任务动作
- 相机画面稳定
- follower 没有乱跳、抽搐、明显延迟
- reset 操作是可控的

### 6.4 如果这一步不过

先不要采数据。

优先排查：

- 串口路径是不是错了
- 相机路径是不是错了
- SO101 校准是否正常
- 机械臂回中位是否正常
- 帧率太高导致采图异常

---

## 7. 第一阶段：采集第一批纯人工 demo

这一批数据的作用是：

- 给 policy 一个最初的行为克隆起点
- 让第一版 policy 至少“能做出接近任务的动作”

这一步先不要带 policy，不要急着上 human-in-loop。

### 7.1 目标

采集一批高质量纯人工示范。

建议：

- 最少：`20` 条
- 更稳：`30-50` 条

### 7.2 推荐命令

```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/<SO101_FOLLOWER_PORT> \
  --robot.id=my_so101_follower \
  --robot.cameras='{ front: {type: opencv, index_or_path: "/dev/v4l/by-path/<FRONT_CAM>", width: 640, height: 480, fps: 30}}' \
  --teleop.type=so101_leader \
  --teleop.port=/dev/serial/by-id/<SO101_LEADER_PORT> \
  --teleop.id=my_so101_leader \
  --dataset.repo_id=${DEMO_REPO_ID} \
  --dataset.root=${LOCAL_DATA_ROOT}/${DEMO_REPO_ID} \
  --dataset.single_task="${TASK_TEXT}" \
  --dataset.num_episodes=30 \
  --dataset.episode_time_s=60 \
  --dataset.reset_time_s=30 \
  --dataset.push_to_hub=false \
  --display_data=true
```

### 7.3 这一阶段要特别注意什么

- `task` 文本要固定，不要来回改写
- 尽量保证每条 demo 的风格一致
- 成功轨迹优先，不要收太多明显失败样本
- 如果任务本身比较长，宁愿少量高质量，也不要大量拖泥带水

### 7.4 如果中断了怎么办

如果你只是继续往同一个 demo 数据集里补采，可以用：

```bash
--resume=true
```

但注意：

- `resume=true` 是 **往已有同一个数据集追加**
- `dataset.num_episodes` 表示 **本次额外新增多少条**
- 不是让你重新指定“总共要有多少条”

### 7.5 采完后必须做的检查

```bash
lerobot-dataset-report --dataset ${LOCAL_DATA_ROOT}/${DEMO_REPO_ID}
```

你至少要检查：

- episode 数量是不是对的
- 平均长度是不是合理
- task 列是不是只有你定义的那一句
- 图像、状态、动作字段有没有缺失

如果第一批 demo 自己都说不清楚质量，那先别训练。

---

## 8. 第二阶段：A100 上训练初始 pi05 policy

这一步的目标不是“直接得到最终能部署的策略”，而是得到一个足够能动、能上机 rollout 的起始 policy。

### 8.1 训练目标

在 demo 数据上做一轮标准 offline policy 训练。

这一轮：

- 不开 ACP
- 不依赖 value
- 相当于初始 SFT / 行为克隆

### 8.2 推荐命令

先把 demo 数据从本地机传到 A100，例如：

```bash
rsync -av ${LOCAL_DATA_ROOT}/${DEMO_REPO_ID}/ <A100_USER>@<A100_HOST>:${SERVER_DATA_ROOT}/${DEMO_REPO_ID}/
```

然后在 A100 服务器上跑：

```bash
lerobot-train \
  --dataset.repo_id=${DEMO_REPO_ID} \
  --dataset.root=${SERVER_DATA_ROOT}/${DEMO_REPO_ID} \
  --policy.type=pi05 \
  --policy.pretrained_path=lerobot/pi05_base \
  --policy.device=cuda \
  --policy.dtype=bfloat16 \
  --policy.gradient_checkpointing=true \
  --policy.compile_model=false \
  --policy.freeze_vision_encoder=false \
  --policy.train_expert_only=false \
  --batch_size=8 \
  --steps=10000 \
  --acp.enable=false \
  --output_dir=outputs/train/${TASK_NAME}_sft_r0 \
  --job_name=${TASK_NAME}_sft_r0 \
  --wandb.enable=true \
  --policy.push_to_hub=false
```

### 8.3 第一轮为什么先这样设

这几个参数很关键：

- `--policy.dtype=bfloat16`
  - 节省显存
- `--policy.gradient_checkpointing=true`
  - 减少显存峰值
- `--policy.compile_model=false`
  - 第一次排查问题更稳
- `--batch_size=8`
  - 对第一次跑最友好

### 8.4 如果 OOM

优先这样改：

```bash
--batch_size=4
```

如果你只是先想把流程打通，也可以加：

```bash
--policy.train_expert_only=true
```

这样通常会更稳。

### 8.5 什么时候算这一步成功

不是只看 loss 下降。

更重要的是：

- 训练能完整跑完
- 没有数据字段缺失报错
- policy 成功保存
- 成功写到本地输出目录

### 8.6 产物是什么

你会得到第一版 policy：

- A100 本地目录：`outputs/train/${PI05_SFT_R0_NAME}`

部署前通常还要把 policy 从 A100 拷回本地机，例如：

```bash
rsync -av <A100_USER>@<A100_HOST>:/path/to/Evo-RL/outputs/train/${PI05_SFT_R0_NAME}/checkpoints/last/pretrained_model/ \
  /path/to/local_machine/policies/${PI05_SFT_R0_NAME}/
```

后面本地部署就会用这个 policy。

---

## 9. 第三阶段：本地机做第一轮 human-in-loop rollout

这一步是 RECAP 闭环真正开始的地方。

你不再只靠纯人工演示，而是：

- 让 policy 先跑
- 人在必要时 takeover
- 用成功 / 失败标签告诉系统这一条 episode 的结果

### 9.1 这个命令和普通 `record` 的区别

`lerobot-human-inloop-record` 会自动做这些事：

- 如果有 policy，就启用 intervention 状态机
- 自动开启 episode outcome 标注
- 默认把未显式标注的 episode 视作 `failure`
- 记录 `complementary_info.policy_action`
- 记录 `complementary_info.is_intervention`
- 记录 `complementary_info.state`
- 记录 `complementary_info.collector_policy_id`

这也是为什么后续 value 和 ACP 能接上。

### 9.2 热键一定要记住

- `i`：进入 / 退出人工接管
- `s`：标记成功并结束当前 episode
- `f`：标记失败并结束当前 episode
- `Right Arrow`：提前结束当前循环
- `Left Arrow`：提前结束并重录当前 episode
- `Esc`：结束整个录制会话

### 9.3 推荐命令

这一步在本地机上跑。

注意：如果你是新建 `round1` 数据集，**不要加 `--resume=true`**。

```bash
lerobot-human-inloop-record \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/<SO101_FOLLOWER_PORT> \
  --robot.id=my_so101_follower \
  --robot.cameras='{ front: {type: opencv, index_or_path: "/dev/v4l/by-path/<FRONT_CAM>", width: 640, height: 480, fps: 30}}' \
  --teleop.type=so101_leader \
  --teleop.port=/dev/serial/by-id/<SO101_LEADER_PORT> \
  --teleop.id=my_so101_leader \
  --dataset.repo_id=${ROUND1_REPO_ID} \
  --dataset.root=${LOCAL_DATA_ROOT}/${ROUND1_REPO_ID} \
  --dataset.single_task="${TASK_TEXT}" \
  --dataset.num_episodes=20 \
  --dataset.episode_time_s=60 \
  --dataset.reset_time_s=30 \
  --dataset.push_to_hub=false \
  --display_data=true \
  --policy.path=/path/to/local_machine/policies/${PI05_SFT_R0_NAME}
```

### 9.4 这一轮 rollout 应该怎么做

推荐策略：

- 先让 policy 自己做
- 明显要失败时再 intervention
- intervention 尽量是“纠正关键动作”，不是全程替它做完
- 每条 episode 认真按 `s` 或 `f`

### 9.5 为什么不要一直强行把任务拖到成功

因为 value 后面要从这些 episode 学：

- 什么状态接近成功
- 什么状态明显走偏
- 哪些帧应该被看成正样本

如果你每条都用人硬拖成成功，value 学到的分布会很怪。

### 9.6 这一步结束后怎么检查

```bash
lerobot-dataset-report --dataset ${LOCAL_DATA_ROOT}/${ROUND1_REPO_ID}
```

你要重点看：

- 成功 / 失败数量是不是合理
- intervention 比例是否合理
- episode 数量是不是对的
- schema 里是否包含：
  - `complementary_info.policy_action`
  - `complementary_info.is_intervention`
  - `complementary_info.state`
  - `complementary_info.collector_policy_id`

如果这些字段没有，就不要进入下一步。

---

## 10. 第四阶段：合并数据集

如果你把 demo 和 round1 分成两个数据集，通常先合并，再训练 value。

### 10.1 为什么要 merge

因为 value 训练通常希望看到：

- 初始 demo
- 当前 policy rollout
- intervention 修正
- success / failure 标签

如果把这些数据碎在多个 repo 里，后面训练和统计都更麻烦。

### 10.2 推荐命令

在 A100 服务器上执行：

```bash
rsync -av ${LOCAL_DATA_ROOT}/${ROUND1_REPO_ID}/ <A100_USER>@<A100_HOST>:${SERVER_DATA_ROOT}/${ROUND1_REPO_ID}/

lerobot-edit-dataset \
  --repo_id=${MERGED_R1_REPO_ID} \
  --root=${SERVER_DATA_ROOT} \
  --operation.type=merge \
  --operation.repo_ids="['${DEMO_REPO_ID}','${ROUND1_REPO_ID}']"
```

### 10.3 merge 后检查

```bash
lerobot-dataset-report --dataset ${SERVER_DATA_ROOT}/${MERGED_R1_REPO_ID}
```

确认：

- 总 episode 数是 demo + round1
- task 仍然统一
- intervention 字段还在
- episode_success 还在

---

## 11. 第五阶段：A100 上训练 value model

这一步是 RECAP 的第一条关键支线。

### 11.1 这一步在做什么

它不是训练 policy。

它是在训练一个 value model，让模型学会：

- 某一帧状态距离成功还有多远
- 某条轨迹整体偏好不好
- 哪些帧是更值得模仿的

当前仓库这条线默认是：

- `--value.type=pistar06`

### 11.2 推荐命令

```bash
lerobot-value-train \
  --dataset.repo_id=${MERGED_R1_REPO_ID} \
  --dataset.root=${SERVER_DATA_ROOT}/${MERGED_R1_REPO_ID} \
  --value.type=pistar06 \
  --value.dtype=bfloat16 \
  --batch_size=64 \
  --output_dir=outputs/value_train/${TASK_NAME}_r1 \
  --job_name=${TASK_NAME}_value_r1 \
  --wandb.enable=true \
  --value.push_to_hub=false
```

### 11.3 A100 上推荐 batch

先用：

```bash
--batch_size=64
```

如果报显存问题，就改成：

```bash
--batch_size=32
```

### 11.4 这一步结束后你应该得到什么

得到一个 value checkpoint，用于下一步 `value infer`。

本地路径通常在：

```text
outputs/value_train/${TASK_NAME}_r1
```

### 11.5 这一步常见误区

- 误以为 value 是最终控制策略
- 误以为 value-train 后就能直接部署

都不是。

它的作用是给数据打分，而不是直接控制机械臂。

---

## 12. 第六阶段：A100 上做 value inference，写回 advantage / indicator

这是 RECAP 最核心的一步。

### 12.1 这一步在做什么

`lerobot-value-infer` 会：

1. 对每一帧预测 `value`
2. 结合 episode 成功 / 失败信息，计算 advantage
3. 按任务内部分位数做阈值切分
4. 把 advantage 二值化为 `0/1` 的 indicator
5. 把这些列直接写回原始数据集

### 12.2 这一步写回哪些列

建议你显式加 tag，避免后面多轮覆盖。

例如 round1：

- `complementary_info.value_r1`
- `complementary_info.advantage_r1`
- `complementary_info.acp_indicator_r1`

### 12.3 推荐命令

```bash
lerobot-value-infer \
  --dataset.repo_id=${MERGED_R1_REPO_ID} \
  --dataset.root=${SERVER_DATA_ROOT}/${MERGED_R1_REPO_ID} \
  --inference.checkpoint_path=outputs/value_train/${TASK_NAME}_r1 \
  --runtime.device=cuda \
  --runtime.batch_size=128 \
  --acp.enable=true \
  --acp.n_step=50 \
  --acp.positive_ratio=0.3 \
  --acp.value_field=complementary_info.value_r1 \
  --acp.advantage_field=complementary_info.advantage_r1 \
  --acp.indicator_field=complementary_info.acp_indicator_r1 \
  --output_dir=outputs/value_infer/${TASK_NAME}_r1 \
  --job_name=${TASK_NAME}_infer_r1
```

### 12.4 这些参数怎么理解

- `--runtime.batch_size=128`
  - A100 上先这么试，通常够用
- `--acp.n_step=50`
  - n-step advantage 计算跨度
- `--acp.positive_ratio=0.3`
  - 每个 task 内大约取 top 30% 作为 positive

### 12.5 一个很关键的实现细节

如果数据集里有 intervention 字段，仓库默认会在二值化时考虑：

- `complementary_info.is_intervention`

并且默认配置里：

- `force_intervention_positive=true`

也就是说， intervention 帧会被强制偏向正样本。

这和 RECAP 里“人纠正过的动作更值得学”的直觉是一致的。

### 12.6 这一步跑完后要检查什么

先再跑一遍：

```bash
lerobot-dataset-report --dataset ${SERVER_DATA_ROOT}/${MERGED_R1_REPO_ID}
```

再确认数据集 schema 里出现了：

- `complementary_info.value_r1`
- `complementary_info.advantage_r1`
- `complementary_info.acp_indicator_r1`

如果 indicator 列没有成功写进去，下一步 ACP 训练一定会失败。

---

## 13. 第七阶段：A100 上做第一轮 ACP policy 训练

这一步是“把 value 产出的标签真的用到 policy 上”的地方。

### 13.1 这一步在做什么

这里并不是直接做 policy gradient。

这套代码的做法是：

- 在 batch 里读取 `acp_indicator`
- 根据 indicator 把 task 文本改成：
  - `Advantage: positive`
  - 或 `Advantage: negative`
- 再用带标签的 task 去做 policy 训练

所以本质上是：

- `文本条件化 + 行为建模`
- 而不是直接 PPO 那种在线 RL

### 13.2 推荐命令

```bash
lerobot-train \
  --dataset.repo_id=${MERGED_R1_REPO_ID} \
  --dataset.root=${SERVER_DATA_ROOT}/${MERGED_R1_REPO_ID} \
  --policy.type=pi05 \
  --policy.pretrained_path=outputs/train/${PI05_SFT_R0_NAME}/checkpoints/last/pretrained_model \
  --policy.device=cuda \
  --policy.dtype=bfloat16 \
  --policy.gradient_checkpointing=true \
  --policy.compile_model=false \
  --policy.freeze_vision_encoder=false \
  --policy.train_expert_only=false \
  --batch_size=8 \
  --steps=30000 \
  --acp.enable=true \
  --acp.indicator_field=complementary_info.acp_indicator_r1 \
  --acp.indicator_dropout_prob=0.3 \
  --output_dir=outputs/train/${TASK_NAME}_acp_r1 \
  --job_name=${TASK_NAME}_acp_r1 \
  --wandb.enable=true \
  --policy.push_to_hub=false
```

### 13.3 为什么 indicator dropout 设 0.3

这个参数控制 task tag 的 dropout。

设成 `0.3` 的作用是：

- 模型既学会 tagged condition
- 也不完全丢掉原始 task condition

第一次建议先用 README 的默认思路，不要乱改。

### 13.4 这一步常见报错点

最常见的是：

- `acp.indicator_field` 在数据集里不存在
- indicator 不是 `0/1` 二值列
- `policy.pretrained_path` 指错了

所以在跑之前一定先确认：

- `complementary_info.acp_indicator_r1` 已经真实写回数据集

### 13.5 什么时候算这一步完成

你应该得到：

- 本地输出：`outputs/train/${TASK_NAME}_acp_r1`

这就是第一版 RECAP 改进后的 policy。

---

## 14. 第八阶段：本地机部署第一版 ACP policy

现在你终于拿到第一版“经过 RECAP 闭环更新”的策略了。

### 14.1 部署目标

验证两件事：

1. 比最初 `sft_r0` 更好
2. 可以进入下一轮数据采集

### 14.2 推荐命令

如果你要继续进入 round2，就直接再跑一轮 human-in-loop：

```bash
lerobot-human-inloop-record \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/<SO101_FOLLOWER_PORT> \
  --robot.id=my_so101_follower \
  --robot.cameras='{ front: {type: opencv, index_or_path: "/dev/v4l/by-path/<FRONT_CAM>", width: 640, height: 480, fps: 30}}' \
  --teleop.type=so101_leader \
  --teleop.port=/dev/serial/by-id/<SO101_LEADER_PORT> \
  --teleop.id=my_so101_leader \
  --dataset.repo_id=${DATA_NS}/eval_${TASK_NAME}_round2 \
  --dataset.root=${LOCAL_DATA_ROOT}/${DATA_NS}/eval_${TASK_NAME}_round2 \
  --dataset.single_task="${TASK_TEXT}" \
  --dataset.num_episodes=20 \
  --dataset.episode_time_s=60 \
  --dataset.reset_time_s=30 \
  --dataset.push_to_hub=false \
  --display_data=true \
  --policy.path=/path/to/local_machine/policies/${PI05_ACP_R1_NAME}
```

### 14.3 什么时候用 `--resume=true`

只在下面这种情况用：

- 你继续往同一个 `round2` 数据集里追加录制

不要在“新建 round2 数据集”时一上来就加 `resume=true`。

### 14.4 如果想尝试 ACP inference

仓库还支持在部署阶段直接做 ACP inference。

也就是部署时让 policy 走：

- positive-tagged task
- 甚至 conditional / unconditional 的 CFG 组合

命令层面可以尝试：

```bash
--acp_inference.enable=true
--acp_inference.use_cfg=true
--acp_inference.cfg_beta=1.0
```

但建议：

- 第一次闭环先不要开
- 先把“标准流程”跑稳
- 后面再单独做 ablation

### 14.5 如何判断“部署成功”

不要只看它会不会动。

更重要的是：

- 成功率比 `sft_r0` 更高
- intervention 次数下降
- 动作更顺
- 同一任务重复执行更稳定

如果这些都没改善，通常不是“继续堆轮次”就能解决，而要回头看：

- demo 质量
- round1 质量
- success/failure 标注是否认真
- intervention 是否过度

---

## 15. 从 round2 开始，后面每一轮都怎么重复

从第二轮开始，你的主循环就固定了：

### 15.1 本地机

1. 用最新 policy 跑 `lerobot-human-inloop-record`
2. 采一轮新的数据集，比如 `round2`

### 15.2 A100 服务器

1. merge 历史数据和新一轮数据
2. 跑 `lerobot-value-train`
3. 跑 `lerobot-value-infer`
4. 跑 ACP `lerobot-train`

### 15.3 再回本地机

1. 拉取新 policy
2. 部署
3. 继续下一轮

可以把它记成这个循环：

```text
roundN collect
  -> merge
  -> value-train
  -> value-infer
  -> acp-train
  -> deploy
  -> roundN+1 collect
```

---

## 16. 最推荐的第一轮落地策略

如果你现在就是要开始跑，我建议不要一上来搞复杂版本。

直接按这个顺序：

1. 本地机联调 SO101
2. 采 `30` 条纯 demo
3. A100 训 `pi05_sft_r0`
4. 本地机做 `20` 条 round1 human-in-loop
5. A100 merge 数据
6. A100 训 value
7. A100 做 value infer
8. A100 训 `pi05_acp_r1`
9. 本地机部署 `pi05_acp_r1`

第一次只要把这 9 步完整跑通，你对整个项目就已经有了真正的控制感。

---

## 16.1 把 round1 真正跑通的一条“最细执行版”

如果你现在已经有了：

- `${LOCAL_DATA_ROOT}/${DEMO_REPO_ID}`
- `${LOCAL_DATA_ROOT}/${ROUND1_REPO_ID}`
- `/path/to/local_machine/policies/${PI05_SFT_R0_NAME}`

那么 A100 上最推荐的执行顺序就是下面这条链，不要跳步：

```bash
# 1) 先检查 round1 数据是不是完整
lerobot-dataset-report --dataset ${LOCAL_DATA_ROOT}/${ROUND1_REPO_ID}

# 2) 把 demo / round1 上传到 A100
rsync -av ${LOCAL_DATA_ROOT}/${DEMO_REPO_ID}/ <A100_USER>@<A100_HOST>:${SERVER_DATA_ROOT}/${DEMO_REPO_ID}/
rsync -av ${LOCAL_DATA_ROOT}/${ROUND1_REPO_ID}/ <A100_USER>@<A100_HOST>:${SERVER_DATA_ROOT}/${ROUND1_REPO_ID}/

# 3) merge demo + round1
lerobot-edit-dataset \
  --repo_id=${MERGED_R1_REPO_ID} \
  --root=${SERVER_DATA_ROOT} \
  --operation.type=merge \
  --operation.repo_ids="['${DEMO_REPO_ID}','${ROUND1_REPO_ID}']"

# 4) 再检查 merge 后字段
lerobot-dataset-report --dataset ${SERVER_DATA_ROOT}/${MERGED_R1_REPO_ID}

# 5) 训练 value
lerobot-value-train \
  --dataset.repo_id=${MERGED_R1_REPO_ID} \
  --dataset.root=${SERVER_DATA_ROOT}/${MERGED_R1_REPO_ID} \
  --value.type=pistar06 \
  --value.dtype=bfloat16 \
  --targets.success_field=episode_success \
  --targets.default_success=failure \
  --targets.c_fail_coef=1.0 \
  --batch_size=64 \
  --steps=8000 \
  --output_dir=outputs/value_train/${TASK_NAME}_r1 \
  --job_name=${TASK_NAME}_value_r1 \
  --wandb.enable=true \
  --value.push_to_hub=false

# 6) 对 merge 后数据集写回 value / advantage / indicator
lerobot-value-infer \
  --dataset.repo_id=${MERGED_R1_REPO_ID} \
  --dataset.root=${SERVER_DATA_ROOT}/${MERGED_R1_REPO_ID} \
  --inference.checkpoint_path=outputs/value_train/${TASK_NAME}_r1 \
  --inference.checkpoint_ref=last \
  --runtime.device=cuda \
  --runtime.batch_size=128 \
  --acp.enable=true \
  --acp.n_step=50 \
  --acp.positive_ratio=0.3 \
  --acp.c_fail_coef=1.0 \
  --acp.value_field=complementary_info.value_r1 \
  --acp.advantage_field=complementary_info.advantage_r1 \
  --acp.indicator_field=complementary_info.acp_indicator_r1 \
  --output_dir=outputs/value_infer/${TASK_NAME}_r1 \
  --job_name=${TASK_NAME}_infer_r1

# 7) 检查 indicator 是否真的写回成功
lerobot-dataset-report --dataset ${SERVER_DATA_ROOT}/${MERGED_R1_REPO_ID}

# 8) 用 indicator 训练 ACP policy
lerobot-train \
  --dataset.repo_id=${MERGED_R1_REPO_ID} \
  --dataset.root=${SERVER_DATA_ROOT}/${MERGED_R1_REPO_ID} \
  --policy.type=pi05 \
  --policy.pretrained_path=outputs/train/${PI05_SFT_R0_NAME}/checkpoints/last/pretrained_model \
  --policy.device=cuda \
  --policy.dtype=bfloat16 \
  --policy.gradient_checkpointing=true \
  --policy.compile_model=false \
  --policy.freeze_vision_encoder=false \
  --policy.train_expert_only=false \
  --batch_size=8 \
  --steps=30000 \
  --acp.enable=true \
  --acp.indicator_field=complementary_info.acp_indicator_r1 \
  --acp.indicator_dropout_prob=0.3 \
  --output_dir=outputs/train/${TASK_NAME}_acp_r1 \
  --job_name=${TASK_NAME}_acp_r1 \
  --wandb.enable=true \
  --policy.push_to_hub=false
```

如果你第一次只想把闭环跑通，就老老实实按这 8 步来，不要一开始就同时改模型、改数据命名、改 batch、改 inference 策略。

### 16.2 每一步之间到底在验证什么

你可以把上面这 8 步理解成 3 个检查门：

1. 数据门
   - `round1` 必须真的带有 `episode_success`
   - 最好带有 `complementary_info.is_intervention`
   - merge 后 schema 不能丢字段

2. value 门
   - `lerobot-value-train` 结束后要有可读 checkpoint
   - `lerobot-value-infer` 结束后数据集里要出现新列

3. policy 门
   - `acp_indicator` 必须已经是数据集里的真实列
   - 它必须是 `0/1` 二值，而不是浮点数或别的字符串标签

如果这 3 个门里任何一个没过，不要硬往后跑。

### 16.3 value-train 这一步代码里真正学的目标是什么

这一点原理上很重要，因为很多人会误以为 value 是直接学“成功率分类”。

这里实际不是简单二分类，而是先按 episode 构造一个连续的 `value target`：

- 成功轨迹：
  - 越接近结束帧，target 越高
- 失败轨迹：
  - 同样考虑“离结束还有多远”
  - 但会额外减去一个 failure penalty

代码里对应的是一种归一化 return-to-go 形式：

```text
remaining_steps = episode_length - frame_index - 1
g = - remaining_steps
if episode is failure:
    g = g - c_fail
g_norm = g / (task_max_length + c_fail)
```

其中：

- `task_max_length` 是这个 task 下最长 episode 的长度
- `c_fail = task_max_length * c_fail_coef`
- 默认推荐 `c_fail_coef=1.0`

所以你可以把它理解成：

- 成功轨迹后段的帧 value target 更高
- 失败轨迹整体会被往更差的区间压

这也是为什么：

- `episode_success` 标注不能乱写
- 失败 episode 不应该被你全都硬修成成功

### 16.4 value-infer 不是只做“预测 value”，它还顺手完成了 ACP 打标

`lerobot-value-infer` 在这套仓库里做了 4 件事：

1. 用训练好的 value model 给每一帧预测 `value`
2. 用数据集里的 episode 成功/失败信息重新构造 dense reward
3. 算 `n-step advantage`
4. 在每个 task 内按分位数把 advantage 切成 `0/1` indicator

关键点有两个：

- `positive_ratio=0.3`
  - 不是全局 top 30%
  - 而是每个 task 内各自取 top 30%

- `force_intervention_positive=true`
  - 如果数据集中存在 `complementary_info.is_intervention`
  - intervention 帧会被强制设成 positive

这意味着：

- 人工纠正过的关键帧会更容易进入正样本
- 但前提是你的 intervention 真的只在关键时刻用，而不是整条轨迹全程接管

### 16.5 ACP policy train 到底是怎么“用上 advantage”的

这一步非常容易被误解成“用 advantage 给 loss 加权”。

这套实现当前不是这么做的。

它真正做的是：

1. 从 batch 里读取 `complementary_info.acp_indicator_r1`
2. 如果值是 `1`，就把 task 改写成：

```text
原始任务文本
Advantage: positive
```

3. 如果值是 `0`，就改成：

```text
原始任务文本
Advantage: negative
```

4. 再用这个带 tag 的 task 文本去训练 `pi05`

所以本质上是：

- 用 `positive/negative` prompt tag 条件化行为建模
- 而不是直接做 PPO 或 AWR 那种 advantage-weighted 更新

这也是为什么文档里一直强调：

- 你的 policy 必须支持 task/text 输入
- `acp.indicator_field` 必须真的是可读的二值列

### 16.6 什么时候要先 patch 旧数据集 schema

如果你的老数据集是在更早版本录的，merge 时可能会缺少 human-in-loop 相关列。

这时候你会在 merge 前后发现这些字段不全：

- `complementary_info.policy_action`
- `complementary_info.is_intervention`
- `complementary_info.state`

这不是小问题，因为后面的 RECAP 流程默认假设这些列存在。

如果你确定是旧数据集 schema 不兼容，可以先跑：

```bash
lerobot-patch-hil-dataset-schema \
  --repo_id=${DEMO_REPO_ID} \
  --root=${SERVER_DATA_ROOT} \
  --output_repo_id=${DATA_NS}/${TASK_NAME}_demo_hil_schema_patched
```

或者对另一个旧 round 数据集也做同样处理，然后再 merge。

只有在你确认“是旧 schema 导致 merge/字段兼容性问题”时才需要这一步。新采的数据通常不用补。

### 16.7 推荐你在 A100 上额外保留的两个输出目录

除了模型本身，我建议你每一轮都保留：

- `outputs/value_train/${TASK_NAME}_r1`
- `outputs/value_infer/${TASK_NAME}_r1`

原因很简单：

- `value_train` 目录里有训练配置和 checkpoint
- `value_infer` 目录里有这次打标过程的日志

后面如果你发现：

- indicator 比例异常
- 某轮 policy 反而变差
- 你怀疑 value model 用错了 checkpoint

这些目录就是你最快回溯问题的地方。

---

## 17. 每一步的“通过条件”清单

## 17.1 联调通过

- 机械臂可控
- 相机稳定
- teleop 正常

## 17.2 demo 采集通过

- 数据集 episode 数正确
- task 文本统一
- 轨迹质量可接受

## 17.3 初始 SFT 通过

- 训练完整结束
- 模型成功保存
- 能被本地机加载部署

## 17.4 round1 采集通过

- `episode_success` 有意义
- intervention 字段存在
- `policy_action` 字段存在

## 17.5 value-train 通过

- 有可用 checkpoint
- 无字段缺失报错

## 17.6 value-infer 通过

- 数据集中新增 value / advantage / indicator 列

## 17.7 ACP policy train 通过

- indicator 被成功读取
- 训练正常结束
- 新 policy 可部署

## 17.8 部署通过

- 成功率比上一版更好
- intervention 下降
- 行为更稳

---

## 18. 最容易踩的坑

## 18.1 新数据集误加 `--resume=true`

这是最常见的。

记住：

- 新 round 数据集：一般不要加
- 往已有同名数据集继续追加：才加

## 18.2 task 文本不统一

如果你一会儿写中文、一会儿写英文、一会儿改描述，后面 task 统计和 ACP 条件都会变乱。

第一次就固定一句。

## 18.3 human-in-loop 时全程人工完成

如果 policy 还没开始发挥作用，你采到的就又只是另一批 demo，不是 RECAP 风格数据。

## 18.4 round1 结束后没做 dataset-report

不检查字段就直接进 value-train，后面容易在更晚的步骤才爆雷。

## 18.5 indicator 没写回成功就开始 ACP 训练

这会直接在训练时报错，或者更糟的是你以为它在用 ACP，实际上根本没接上。

## 18.6 一上来就追论文满配

最好的策略不是“直接冲最大 batch、最长训练、最复杂部署”，而是：

- 先跑通
- 再变强

---

## 19. 推荐你实际执行时的记录方式

每一轮至少记录这些内容：

- 当前 policy 名称
- 当前数据集名称
- 采集了多少条 episode
- success / failure 比例
- intervention 大概多少
- value-train 用的参数
- value-infer 用的字段名
- ACP train 用的 indicator 字段名
- 当前部署时的主观表现

因为这个项目一旦迭代 2 到 3 轮，如果没有清晰记录，很快就会分不清：

- 哪一版模型更好
- 哪个数据集对应哪一轮
- 哪个 indicator 字段来自哪一次 value infer

---

## 20. 最后给你的操作建议

如果你准备正式开始，我建议你就按下面这条最短路径走：

1. 先固定 `TASK_NAME` 和 `TASK_TEXT`
2. 本地机联调 SO101
3. 采 30 条 demo
4. A100 训第一版 `pi05_sft_r0`
5. 本地机采 20 条 `round1`
6. A100 跑 `value-train -> value-infer -> acp-train`
7. 本地机部署 `pi05_acp_r1`

只要这条链通了，后面的问题就不再是“我完全不知道这项目在干什么”，而是更具体的：

- 这一步参数要不要改
- 这一轮数据够不够
- indicator 打得好不好
- intervention 策略该怎么优化

这时候我们再逐段讨论，就会非常高效。

---

## 21. 如果你要真正理解 RECAP，代码从哪里开始看

前面 1 到 20 章讲的是“怎么跑”。

这一章讲的是“怎么读代码”。

建议你不要一上来就从 `src/` 顶层随便翻。这个仓库是基于 LeRobot 扩展出来的，目录很多，如果没有顺序，很容易看一堆通用训练代码，却没抓住 RECAP 自己真正新增的部分。

最好的读法是：

1. 先看 README，确认主流程
2. 再看 4 个命令行入口脚本
3. 再看 ACP 相关代码
4. 再看 value 相关代码
5. 最后再看 `pi05` policy 本体和工厂装配逻辑

你可以把 RECAP 代码理解成两层：

- 第一层：**流程层**
  - 采数据
  - 训 value
  - 打标签
  - 训 policy
- 第二层：**实现层**
  - 数据集里具体写了哪些字段
  - advantage 怎么算
  - positive / negative tag 怎么注入 task text
  - policy 是怎么加载和训练的

---

## 22. 先看哪几个文件，最省力

如果你的目标是“先把这项目大体看懂”，我建议先只看下面 10 个文件。

### 22.1 第一优先级：先建立闭环感

1. `README.md`
2. `src/lerobot/scripts/lerobot_human_inloop_record.py`
3. `src/lerobot/scripts/recording_loop.py`
4. `src/lerobot/scripts/lerobot_value_train.py`
5. `src/lerobot/scripts/lerobot_value_infer.py`
6. `src/lerobot/scripts/lerobot_train.py`
7. `src/lerobot/rl/acp_hook.py`
8. `src/lerobot/rl/acp_tags.py`
9. `src/lerobot/values/pistar06/modeling_pistar06.py`
10. `src/lerobot/scripts/recording_hil.py`

只看完这 10 个文件，你就已经能回答下面这些关键问题：

- RECAP 的数据是怎么收的
- intervention 是怎么记录的
- success / failure 是怎么记录的
- value 是怎么训练的
- advantage 和 indicator 是怎么来的
- ACP 是怎么变成文本条件的
- 部署时 policy 是怎么跑的

---

## 23. 第一遍阅读顺序

这一部分很重要。

下面是我最推荐的第一遍阅读顺序。

### 23.1 第一步：先看 `README.md`

这一份不是为了看细节，而是为了先建立“项目流程脑图”。

你重点看这几个章节：

- Data Collection
- Value Function Training
- Value Inference
- Policy Training
- Closed-loop Rollout and Next Round

你看 README 的目标只有一个：

- 先确认项目作者想让你按什么顺序用这套系统

不要在这一阶段纠结实现细节。

### 23.2 第二步：看 `lerobot_human_inloop_record.py`

这个文件回答的问题是：

- human-in-loop 录制命令到底做了哪些额外事情

你重点看这些点：

- 是否要求 teleop
- 是否自动开启 intervention state machine
- 是否自动开启 episode success / failure 标注
- 是否自动启用 `collector_policy_id`
- policy 存在时是否会保存 failure reset pose

你会看到这个脚本实际上是对通用 `record` 的一层包装，把 RECAP 需要的录制行为都提前打开了。

### 23.3 第三步：看 `recording_loop.py`

这个文件非常关键。

因为真正每一步录进数据集的内容，是在这里决定的。

你重点看：

- policy 和 teleop 是怎么切换的
- intervention state machine 是怎么工作的
- `is_intervention` 在什么情况下写成 1
- `policy_action` 在什么地方写进 frame
- `collector_policy_id` 在什么地方写进 frame
- episode 什么时候结束

你可以把这个文件理解成：

- “RECAP 的采集现场到底发生了什么”

### 23.4 第四步：看 `lerobot_value_train.py`

这个文件回答的问题是：

- value 模型训练流程是怎么搭起来的

你重点看：

- dataset 是怎么创建的
- value policy 是怎么创建的
- raw-batch hook 是怎么接进训练流程的
- resume、checkpoint、wandb 是怎么接的

它本身不是最核心算法文件，但它把训练主线串起来了。

### 23.5 第五步：看 `modeling_pistar06.py`

这是 value 路线的核心实现文件。

你重点看：

- value target 是怎么构造的
- success / failure 如何影响 target
- 剩余步数如何归一化
- `c_fail_coef` 怎么影响失败轨迹
- `predict_value` 怎么暴露给 `value-infer`
- `build_training_raw_batch_hook` 怎么把训练 target 接进去

如果你想理解“为什么 value 能从 success / failure 学到有用东西”，这个文件必须看。

### 23.6 第六步：看 `lerobot_value_infer.py`

这个文件是 RECAP 里最关键的“桥”。

因为它把：

- value model 输出
- episode success / failure
- intervention 信息

转成了：

- value
- advantage
- indicator

你重点看：

- `_build_episode_info`
- `_compute_n_step_advantages`
- `_compute_task_thresholds`
- `_binarize_advantages`
- `_write_columns_in_place`

这几个函数几乎就是整套“从 value 到 ACP 标签”的核心。

### 23.7 第七步：看 `acp_tags.py` 和 `acp_hook.py`

这两个文件很短，但特别重要。

它们回答的问题是：

- positive / negative 到底是怎么进 policy 的

你会发现这里没有直接修改网络结构，也没有额外加一个 complicated controller。

它做的事情更直接：

- 从 batch 里读 indicator
- 判断这一条样本是 positive 还是 negative
- 把 task 文本改成带标签的版本

这一步看懂以后，你就会明白：

- 这套代码为什么更像“带条件标签的行为建模”
- 而不是传统意义上直接用 RL loss 更新 policy

### 23.8 第八步：看 `lerobot_train.py`

你重点不是看整个 LeRobot 训练器的所有细节，而是看：

- ACP raw batch hook 是什么时候接入的
- dataset、policy、optimizer 是怎么创建的
- 指标和 checkpoint 是怎么保存的

这一步的目标是：

- 看懂 ACP 最终是如何进入标准 policy 训练流程的

### 23.9 第九步：看 `recording_hil.py`

这个文件回答的问题是：

- 部署时 policy prediction 是怎么做的
- ACP inference 是怎么在部署侧生效的

你重点看：

- `ACPInferenceConfig`
- `_predict_policy_action_with_acp_inference`
- `conditional_task = build_acp_tagged_task(task, is_positive=True)`
- CFG 推理分支

这一步会帮你区分两件事：

- 训练阶段的 ACP
- 部署阶段的 ACP inference

它们是相关的，但不是一回事。

---

## 24. 第二遍应该看哪些代码

如果第一遍看完后，你已经知道主流程了，第二遍再看下面这些文件会更有价值。

### 24.1 policy 装配层

建议看：

- `src/lerobot/policies/factory.py`
- `src/lerobot/configs/train.py`

这两个文件帮助你理解：

- `--policy.type=pi05` 是怎么实例化出来的
- `--policy.pretrained_path` 是怎么加载的
- `--acp.indicator_field` 是怎么进配置的

### 24.2 pi05 本体

建议看：

- `src/lerobot/policies/pi05/configuration_pi05.py`
- `src/lerobot/policies/pi05/modeling_pi05.py`
- `src/lerobot/policies/pi05/processor_pi05.py`

这一层的作用不是专门理解 RECAP，而是理解：

- 这套 RECAP 最终到底在训练什么 policy

你重点看：

- `pi05` 的输入输出是什么
- task text 是怎么被 processor 和 model 使用的
- gradient checkpointing、compile、train_expert_only 是怎么生效的

### 24.3 dataset 工具层

建议看：

- `src/lerobot/scripts/lerobot_dataset_report.py`
- `src/lerobot/scripts/lerobot_edit_dataset.py`

这两个文件帮助你理解：

- merge 是怎么做的
- report 统计了哪些质量指标
- intervention 和 success ratio 是怎么被统计出来的

---

## 25. 如果你只想最短路径理解 RECAP，最少看哪些文件

如果你时间有限，只看这 6 个就够形成骨架理解：

1. `README.md`
2. `src/lerobot/scripts/lerobot_human_inloop_record.py`
3. `src/lerobot/scripts/recording_loop.py`
4. `src/lerobot/scripts/lerobot_value_infer.py`
5. `src/lerobot/rl/acp_hook.py`
6. `src/lerobot/scripts/lerobot_train.py`

为什么是这 6 个：

- `README` 让你知道流程
- `human_inloop_record + recording_loop` 让你知道数据怎么来
- `value_infer` 让你知道标签怎么来
- `acp_hook` 让你知道标签怎么进 policy
- `train.py` 让你知道最终训练怎么落地

如果你只看这 6 个，虽然还没有完全吃透 value target 细节，但已经能把 RECAP 主线串起来。

---

## 26. 每个关键文件分别负责什么

下面这张“职责表”适合你后面查阅。

### 26.1 录制与部署

- `src/lerobot/scripts/lerobot_human_inloop_record.py`
  - human-in-loop 录制入口
  - 打开 success/failure 标注
  - 打开 intervention
  - 配置 failure reset

- `src/lerobot/scripts/lerobot_record.py`
  - 通用录制脚本
  - 定义录制配置、键位、dataset feature

- `src/lerobot/scripts/recording_loop.py`
  - 实际逐帧录制主循环
  - 决定 frame 里写哪些字段

- `src/lerobot/scripts/recording_hil.py`
  - human-in-loop 部署侧推理
  - ACP inference 和 CFG inference

### 26.2 value 路线

- `src/lerobot/scripts/lerobot_value_train.py`
  - value 训练入口

- `src/lerobot/values/pistar06/modeling_pistar06.py`
  - value 核心实现
  - value target 构造
  - predict_value
  - raw-batch hook

- `src/lerobot/scripts/lerobot_value_infer.py`
  - value 推理
  - advantage 计算
  - indicator 二值化
  - 写回数据集列

### 26.3 ACP 路线

- `src/lerobot/rl/acp_tags.py`
  - 生成 `Advantage: positive/negative` task 文本

- `src/lerobot/rl/acp_hook.py`
  - 从 batch 读取 indicator
  - 把 indicator 转成 task 标签

### 26.4 policy 训练路线

- `src/lerobot/scripts/lerobot_train.py`
  - policy 训练入口
  - ACP hook 接入点

- `src/lerobot/policies/factory.py`
  - policy / processor 工厂

- `src/lerobot/policies/pi05/modeling_pi05.py`
  - `pi05` 模型本体

- `src/lerobot/policies/pi05/processor_pi05.py`
  - `pi05` 输入输出处理

---

## 27. 你读代码时最应该问自己的问题

建议你不要只是“看代码走没走通”，而是带着问题看。

第一组问题，关于数据：

- 这一帧最终写进数据集的字段有哪些
- 哪些字段是 RECAP 特有新增的
- success / failure 是 episode 级还是 frame 级
- intervention 是 frame 级还是 episode 级

第二组问题，关于 value：

- value target 到底是怎么来的
- success / failure 如何影响 target
- 为什么要用剩余步数归一化
- advantage 为什么要按 task 内分位数阈值化

第三组问题，关于 ACP：

- indicator 是在哪里读出来的
- positive / negative 是怎么改写 task text 的
- policy 到底有没有“显式看到”这个标签

第四组问题，关于部署：

- 本地 rollout 时执行的是 human action 还是 policy action
- intervention 时数据里记下的 action 是什么
- `policy_action` 和 `action` 的区别是什么

你只要带着这些问题去看，理解速度会快很多。

---

## 28. 我最推荐的阅读姿势

真正看这套代码时，我建议你采用下面这个顺序：

### 28.1 第一轮阅读

目标：

- 只抓主线
- 不抠模型细节

顺序：

1. `README.md`
2. `lerobot_human_inloop_record.py`
3. `recording_loop.py`
4. `lerobot_value_infer.py`
5. `acp_hook.py`
6. `lerobot_train.py`

### 28.2 第二轮阅读

目标：

- 搞懂 RECAP 算法实现

顺序：

1. `modeling_pistar06.py`
2. `lerobot_value_train.py`
3. `acp_tags.py`
4. `recording_hil.py`

### 28.3 第三轮阅读

目标：

- 搞懂具体 policy 是怎么工作的

顺序：

1. `factory.py`
2. `configuration_pi05.py`
3. `processor_pi05.py`
4. `modeling_pi05.py`

---

## 29. 一句话总结“RECAP 代码最该看哪一块”

如果只用一句话总结：

**先看“数据怎么被采下来”，再看“标签怎么被打出来”，最后看“标签怎么进入 policy 训练”。**

对应到文件就是：

1. `lerobot_human_inloop_record.py + recording_loop.py`
2. `lerobot_value_infer.py + modeling_pistar06.py`
3. `acp_hook.py + acp_tags.py + lerobot_train.py`

这三块看懂了，你对这套 RECAP 代码的理解就已经不是“会跑命令”，而是真正知道它在做什么了。
