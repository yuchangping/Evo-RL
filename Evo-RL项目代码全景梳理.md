# Evo-RL 项目代码全景梳理

## 0. 文档范围

这份文档基于你当前本地工作区 `/home/jy/Data/YCP/Evo-RL` 整理，目标不是简单“列目录”，而是帮助你真正读懂这份仓库：

- 这份仓库的上游远端是 `https://github.com/MINT-SJTU/Evo-RL.git`。
- 本地 `origin` 指向 `https://github.com/yuchangping/Evo-RL.git`，说明这是在上游基础上的个人工作副本。
- 当前工作区是干净的，没有未提交修改。
- 项目包名仍然是 `lerobot`，版本号是 `0.4.4`，说明 **Evo-RL 是在 LeRobot 之上做真实机器人 RL 扩展，而不是完全另起炉灶的新框架**。

一句话概括：

`Evo-RL = LeRobot 的数据采集/策略训练/机器人控制骨架 + 面向真实机器人闭环强化学习的 value model、ACP、人在回路采集、双臂/AgileX PiPER 支持。`

---

## 1. 这个项目到底在做什么

从 `README.md` 可以把 Evo-RL 的主业务闭环概括成 7 步：

1. 安装环境。
2. 配置真实机器人硬件和相机。
3. 采集初始数据集。
4. 训练 value function。
5. 用 value model 给数据集回写 value / advantage / ACP indicator。
6. 训练策略模型。
7. 用策略上机 rollout，在人在回路模式下继续采集下一轮数据，再回到第 4 步。

这条闭环在代码里的对应关系非常清晰：

```text
README
  -> lerobot-teleoperate / lerobot-record / lerobot-human-inloop-record
  -> lerobot-value-train
  -> lerobot-value-infer
  -> lerobot-train
  -> 再次 lerobot-human-inloop-record
```

如果你只想抓住这个仓库最核心的“增量价值”，那重点不是所有 policy family，而是下面这几块：

- `src/lerobot/scripts/lerobot_value_train.py`
- `src/lerobot/scripts/lerobot_value_infer.py`
- `src/lerobot/scripts/lerobot_human_inloop_record.py`
- `src/lerobot/scripts/recording_loop.py`
- `src/lerobot/scripts/recording_hil.py`
- `src/lerobot/values/pistar06/`
- `src/lerobot/rl/`
- `src/lerobot/rl/acp_hook.py`
- `src/lerobot/rl/acp_tags.py`
- `src/lerobot/policies/sarm/compute_rabc_weights.py`

---

## 2. 仓库统计

### 2.1 顶层统计

下面的统计不包含 `.git` 元数据，聚焦仓库中真正需要阅读和维护的文件。

| 区域 | 文件数 | 说明 |
| --- | ---: | --- |
| 根目录普通文件 | 16 | 安装、构建、说明、你本地的复现笔记 |
| `src` | 352 | 核心源码 |
| `tests` | 129 | 测试 |
| `docs` | 60 | 文档源文件 |
| `examples` | 37 | 使用示例 |
| `website` | 14 | 项目官网静态文件 |
| `benchmarks` | 2 | benchmark |
| `docker` | 2 | Dockerfile |

### 2.2 核心源码 `src/lerobot` 统计

`src/lerobot` 是最重要的区域，约 11 万行代码。按模块拆分如下：

| 模块 | 文件数 | 近似代码行数 | 作用 |
| --- | ---: | ---: | --- |
| `policies` | 85 | 35303 | 各类策略模型及其 processor |
| `datasets` | 18 | 9667 | 数据集格式、统计、视频、写盘、流式读取 |
| `scripts` | 24 | 8351 | 全部 CLI 入口 |
| `robots` | 52 | 7195 | 真实机器人设备实现 |
| `teleoperators` | 54 | 6911 | 主手/遥操作设备实现 |
| `processor` | 17 | 6170 | 统一的数据处理流水线 |
| `rl` | 14 | 4849 | 在线 RL / actor-learner / ACP |
| `motors` | 13 | 4078 | 电机总线和底层驱动 |
| `utils` | 18 | 3061 | 公共工具 |
| `cameras` | 17 | 2657 | 相机实现 |
| `envs` | 7 | 1939 | 仿真环境封装 |
| `async_inference` | 5 | 1496 | 异步推理客户端/服务端 |
| `configs` | 8 | 1259 | 配置系统 |
| `data_processing` | 3 | 1228 | SARM 标注相关数据处理 |
| `values` | 5 | 1217 | value model（当前主要是 Pi\*0.6） |
| `transport` | 4 | 771 | gRPC / protobuf 传输层 |
| `optim` | 4 | 558 | 优化器和 scheduler 工厂 |
| `model` | 1 | 132 | 通用运动学 |
| `(root)` | 2 | 223 | 包入口和版本号 |
| `templates` | 1 | 91 | model card 模板 |

### 2.3 测试与文档体量

- `tests` 约 4.5 万行，说明这个项目非常依赖测试来守住兼容性。
- `docs/source` 59 个文件，说明官方文档是重要阅读辅助，不只是“摆设”。

---

## 3. 根目录文件梳理

### 3.1 根目录文件

| 文件 | 作用 |
| --- | --- |
| `.codex` | 本地工具产生的占位文件，不属于项目逻辑 |
| `.dockerignore` | Docker 构建忽略规则 |
| `.gitattributes` | Git/LFS 等属性配置 |
| `.gitignore` | Git 忽略规则 |
| `.pre-commit-config.yaml` | pre-commit 代码检查配置 |
| `A100服务器训练RECAP详细流程 copy.md` | 你本地的训练流程笔记，不属于上游核心代码 |
| `CODE_OF_CONDUCT.md` | 社区行为规范 |
| `CONTRIBUTING.md` | 贡献说明 |
| `LICENSE` | Apache-2.0 许可证 |
| `MANIFEST.in` | 打包清单 |
| `Makefile` | 常用开发命令，尤其是端到端测试命令 |
| `README.md` | 项目总说明，Evo-RL 主流程在这里定义 |
| `SECURITY.md` | 安全策略 |
| `docs-requirements.txt` | 构建文档需要的依赖 |
| `env.sh` | 本地环境脚本 |
| `pyproject.toml` | 依赖、extra、CLI script 的总入口 |
| `requirements-macos.txt` | macOS 依赖锁定 |
| `requirements-ubuntu.txt` | Ubuntu 依赖锁定 |
| `requirements.in` | 依赖源文件 |
| `setup.py` | 读取 `pyproject.toml` + `README.md` 做安装打包 |
| `详细复现流程.md` | 你本地的复现笔记，不属于上游核心代码 |

### 3.2 顶层目录

| 目录 | 作用 |
| --- | --- |
| `src` | 核心源码 |
| `tests` | 测试 |
| `examples` | 使用示例 |
| `docs` | 文档源文件 |
| `website` | 官网静态站点 |
| `benchmarks` | benchmark |
| `docker` | Docker 镜像构建 |
| `.github` | CI / workflow / issue template |

### 3.3 最值得先读的根文件

如果你只看 6 个根文件，建议顺序如下：

1. `README.md`
2. `pyproject.toml`
3. `Makefile`
4. `setup.py`
5. `详细复现流程.md`
6. `A100服务器训练RECAP详细流程 copy.md`

其中：

- `README.md` 负责定义“项目要做什么”。
- `pyproject.toml` 负责定义“代码怎么被安装和调用”。
- `Makefile` 负责定义“开发者平时怎么测试它”。

---

## 4. 这个仓库的主架构

### 4.1 最高层结构

你可以把整个仓库理解成 6 层：

1. **CLI 层**：用户通过 `lerobot-*` 命令进入系统。
2. **配置层**：`draccus + parser.wrap()` 把命令行解析成 dataclass config。
3. **工厂层**：`make_policy`、`make_dataset`、`make_robot_from_config`、`make_teleoperator_from_config`。
4. **处理流水线层**：`processor/pipeline.py` 把 observation / action / batch 做统一转换。
5. **执行层**：policy、value model、robot、teleoperator、dataset、env。
6. **Evo-RL 增量层**：value inference、ACP、人在回路、actor-learner 在线 RL。

### 4.2 最核心的数据流

```text
CLI
  -> Config dataclass
  -> parser.wrap()
  -> make_dataset / make_policy / make_robot / make_teleoperator
  -> processor pipeline
  -> 训练 / 推理 / 采集 / 回放 / 在线 RL
  -> 写回 dataset / checkpoint / visualization
```

### 4.3 为什么说它“本质上还是 LeRobot”

证据很明确：

- `pyproject.toml` 中包名还是 `lerobot`。
- CLI 仍然以 `lerobot-*` 为命名规范。
- 训练、评估、采集、回放的主脚本命名全部延续 LeRobot。
- 大量 policy family、dataset 格式、processor 机制、robot/teleop 抽象类都来自 LeRobot 体系。

Evo-RL 的价值不是推翻这些，而是在其上增加：

- `value train / value infer`
- `human-in-the-loop record`
- `ACP advantage-conditioned prompt`
- `RA-BC`
- `actor / learner` 在线 RL 链路
- SO101 / PiPER / 双臂等真实机器人流程打通

---

## 5. 关键执行链路

## 5.1 数据采集链路

主入口：

- `src/lerobot/scripts/lerobot_record.py`
- `src/lerobot/scripts/lerobot_human_inloop_record.py`
- `src/lerobot/scripts/recording_loop.py`
- `src/lerobot/scripts/recording_hil.py`

简化后的执行过程：

```text
RecordConfig
  -> make_robot_from_config()
  -> make_teleoperator_from_config()
  -> make_default_processors()
  -> LeRobotDataset.create() 或 LeRobotDataset(...)
  -> make_policy() + make_pre_post_processors()（如果是 policy 驱动）
  -> record_loop()
  -> 逐帧写入 observation/action/complementary_info
```

这条链路里最重要的不是“录数据”三个字，而是 **数据结构在何处被定义、何处被处理、何处被回写**：

- 数据字段的初始 schema 在 `lerobot_record.py` 里拼出来。
- 单步控制逻辑在 `recording_loop.py`。
- 人工接管、ACP inference、policy 同步到主手在 `recording_hil.py`。

## 5.2 策略训练链路

主入口：

- `src/lerobot/scripts/lerobot_train.py`

简化链路：

```text
TrainPipelineConfig.validate()
  -> make_dataset()
  -> make_policy()
  -> make_pre_post_processors()
  -> make_optimizer_and_scheduler()
  -> dataloader
  -> update_policy()
  -> save_checkpoint()
  -> eval_policy_all()
```

Evo-RL 在这条链路上加了两个明显增量：

- ACP：通过 `rl/acp_hook.py` 改写 task prompt。
- RA-BC：训练时允许按 reward/progress 对样本加权。

## 5.3 Value 训练与回写链路

主入口：

- `src/lerobot/scripts/lerobot_value_train.py`
- `src/lerobot/scripts/lerobot_value_infer.py`
- `src/lerobot/values/pistar06/`

简化链路：

```text
当前数据集
  -> value_train 训练 Pistar06
  -> value_infer 跑全量数据推理
  -> 计算 value / dense reward / n-step advantage / ACP indicator
  -> 直接写回 dataset parquet 列
```

这一块是 Evo-RL 相比 LeRobot 最关键的新增功能之一。

## 5.4 在线 RL 链路

主入口：

- `src/lerobot/rl/actor.py`
- `src/lerobot/rl/learner.py`
- `src/lerobot/rl/learner_service.py`
- `src/lerobot/transport/`

简化链路：

```text
Actor 连接真实机器人环境
  -> rollout + 收集 transition
  -> gRPC 发给 Learner
  -> Learner 更新 policy / replay buffer
  -> Learner 再把参数发回 Actor
```

这块更偏在线强化学习/HILSerl，不是 README 那条 value->policy 的主闭环唯一部分，但属于 Evo-RL 的强化学习支线能力。

---

## 6. `src/lerobot` 源码全模块梳理

## 6.1 `configs/`：配置系统

文件清单：

```text
default.py
eval.py
parser.py
policies.py
train.py
types.py
value.py
value_train.py
```

阅读重点：

- `parser.py`
  负责 CLI 解析增强，最重要的是 `wrap()`。
  它除了调用 `draccus.parse()`，还支持 `--policy.path`、`--value.path`、插件自动加载。
- `policies.py`
  定义 `PreTrainedConfig`，所有 policy/value config 都从这里继承。
- `train.py`
  定义离线策略训练配置 `TrainPipelineConfig`，并在 `validate()` 里补齐 optimizer / scheduler / resume 逻辑。
- `value_train.py`
  定义 value 训练配置，目前强绑定 `pistar06`。
- `value.py`
  定义 value inference 配置，决定要回写哪些列到数据集里。

一条非常重要的认识：

`parser.py + configs/*.py` 是整仓库的“参数入口总线”。如果你不先读懂这里，后面很多脚本会觉得“参数是从天上掉下来的”。

## 6.2 `scripts/`：所有 CLI 入口

文件清单：

```text
lerobot_calibrate.py
lerobot_dataset_report.py
lerobot_dataset_viz.py
lerobot_edit_dataset.py
lerobot_eval.py
lerobot_find_cameras.py
lerobot_find_joint_limits.py
lerobot_find_port.py
lerobot_human_inloop_record.py
lerobot_imgtransform_viz.py
lerobot_info.py
lerobot_patch_hil_dataset_schema.py
lerobot_record.py
lerobot_replay.py
lerobot_setup_can.py
lerobot_setup_motors.py
lerobot_teleoperate.py
lerobot_train.py
lerobot_train_tokenizer.py
lerobot_value_infer.py
lerobot_value_train.py
recording_hil.py
recording_loop.py
value_infer_viz.py
```

这些脚本可以分成 6 类：

- 设备与联调：`lerobot_teleoperate.py`、`lerobot_calibrate.py`、`lerobot_find_port.py`、`lerobot_find_cameras.py`、`lerobot_setup_motors.py`、`lerobot_setup_can.py`
- 数据采集与回放：`lerobot_record.py`、`lerobot_human_inloop_record.py`、`lerobot_replay.py`
- 数据集治理：`lerobot_dataset_report.py`、`lerobot_dataset_viz.py`、`lerobot_edit_dataset.py`、`lerobot_patch_hil_dataset_schema.py`
- 策略训练与评估：`lerobot_train.py`、`lerobot_eval.py`
- Value 支线：`lerobot_value_train.py`、`lerobot_value_infer.py`、`value_infer_viz.py`
- 内部循环核心：`recording_loop.py`、`recording_hil.py`

如果只能看 5 个脚本，建议看：

1. `lerobot_record.py`
2. `recording_loop.py`
3. `lerobot_train.py`
4. `lerobot_value_train.py`
5. `lerobot_value_infer.py`

## 6.3 `datasets/`：数据集格式与磁盘 IO

主要文件：

```text
aggregate.py
backward_compatibility.py
card_template.md
compute_stats.py
dataset_tools.py
factory.py
image_writer.py
lerobot_dataset.py
online_buffer.py
pipeline_features.py
push_dataset_to_hub/utils.py
sampler.py
streaming_dataset.py
transforms.py
utils.py
v30/augment_dataset_quantile_stats.py
v30/convert_dataset_v21_to_v30.py
video_utils.py
```

其中最关键的是：

- `lerobot_dataset.py`
  数据集核心类，负责 metadata、episode、frame、video、stats 的读写。
- `factory.py`
  按训练配置构造数据集，处理 `delta_timestamps` 和 streaming。
- `pipeline_features.py`
  把 processor pipeline 的 feature 变换结果映射回 dataset feature schema。
- `image_writer.py` 和 `video_utils.py`
  负责采集时的图片/视频写盘和编码。
- `dataset_tools.py`
  数据集维护工具，很大，也很常用。

这部分是整个仓库的“数据底盘”，离线训练、value inference、回放、数据可视化都依赖它。

## 6.4 `processor/`：统一处理流水线

文件清单：

```text
__init__.py
batch_processor.py
converters.py
core.py
delta_action_processor.py
device_processor.py
env_processor.py
factory.py
gym_action_processor.py
hil_processor.py
migrate_policy_normalization.py
normalize_processor.py
observation_processor.py
pipeline.py
policy_robot_bridge.py
rename_processor.py
tokenizer_processor.py
```

理解这个模块的关键一句话：

**processor 不是“几个小工具函数”，而是整个仓库统一 observation / action / batch / transition 变换语义的骨架。**

最关键文件：

- `pipeline.py`
  定义 `ProcessorStepRegistry`、`ProcessorStep`、`DataProcessorPipeline`。
- `converters.py`
  负责 dict、transition、batch 之间互转。
- `normalize_processor.py`
  负责规范化。
- `rename_processor.py`
  负责多相机/多臂命名映射。
- `device_processor.py`
  负责张量设备迁移。
- `policy_robot_bridge.py`
  把 policy 的 action 和 robot 的 action 语义连接起来。

如果你发现“为什么同一个 observation 在不同脚本里名字不一样”，答案通常就在 `processor`。

## 6.5 `policies/`：策略模型家族

结构可以分成两层：

### 6.5.1 共用骨架

- `factory.py`
- `pretrained.py`
- `utils.py`

其中：

- `factory.py` 决定创建哪一种 policy 类，以及对应的 pre/post processor。
- `pretrained.py` 是所有策略模型的统一父类接口。

### 6.5.2 各策略 family

| family | 主要文件 | 说明 |
| --- | --- | --- |
| `act` | `configuration_act.py` / `modeling_act.py` / `processor_act.py` | ACT 模型 |
| `diffusion` | `configuration_diffusion.py` / `modeling_diffusion.py` / `processor_diffusion.py` | Diffusion Policy |
| `pi0` | `configuration_pi0.py` / `modeling_pi0.py` / `processor_pi0.py` | Pi0 |
| `pi05` | `configuration_pi05.py` / `modeling_pi05.py` / `processor_pi05.py` | Pi0.5 |
| `pi0_fast` | `configuration_pi0_fast.py` / `modeling_pi0_fast.py` / `processor_pi0_fast.py` | 轻量快速版 Pi0 |
| `smolvla` | `configuration_smolvla.py` / `modeling_smolvla.py` / `processor_smolvla.py` | SmolVLA |
| `vqbet` | `configuration_vqbet.py` / `modeling_vqbet.py` / `processor_vqbet.py` / `vqbet_utils.py` | VQBeT |
| `tdmpc` | `configuration_tdmpc.py` / `modeling_tdmpc.py` / `processor_tdmpc.py` | TDMPC |
| `sac` | `configuration_sac.py` / `modeling_sac.py` / `processor_sac.py` | 在线 RL 的 SAC |
| `sarm` | `configuration_sarm.py` / `modeling_sarm.py` / `processor_sarm.py` / `compute_rabc_weights.py` / `sarm_utils.py` | Reward model / RA-BC |
| `groot` | `configuration_groot.py` / `modeling_groot.py` / `processor_groot.py` / `groot_n1.py` / `utils.py` | GROOT VLA |
| `wall_x` | `configuration_wall_x.py` / `modeling_wall_x.py` / `processor_wall_x.py` / `utils.py` / `constant.py` | Wall-X |
| `xvla` | `configuration_xvla.py` / `configuration_florence2.py` / `modeling_xvla.py` / `modeling_florence2.py` / `processor_xvla.py` / `soft_transformer.py` / `action_hub.py` / `utils.py` | XVLA |
| `rtc` | `configuration_rtc.py` / `modeling_rtc.py` / `action_queue.py` / `latency_tracker.py` / `debug_tracker.py` / `debug_visualizer.py` | 实时控制相关 |

结论：

- `policies/` 是全仓最大模块。
- 但如果你想先读懂 **Evo-RL 主流程**，不要一开始就淹没在所有 policy family 里。
- 先读 `factory.py`，再读你当前训练命令真正使用的 policy family。

## 6.6 `values/`：当前 value model 栈

文件清单：

```text
__init__.py
pistar06/__init__.py
pistar06/configuration_pistar06.py
pistar06/modeling_pistar06.py
pistar06/processor_pistar06.py
```

这块就是 Evo-RL 现在的 value 支线核心。

理解要点：

- 当前 `value_train` 只支持 `pistar06`。
- `configuration_pistar06.py` 定义了 SigLIP + Gemma 融合模型的配置。
- `modeling_pistar06.py` 定义了分布式 value head 和目标构造逻辑。
- `processor_pistar06.py` 定义了 value model 需要的输入处理方式。

## 6.7 `rl/`：在线 RL 与 ACP

文件清单：

```text
acp_dataset_stats.py
acp_hook.py
acp_tags.py
actor.py
buffer.py
crop_dataset_roi.py
eval_policy.py
gym_manipulator.py
joint_observations_processor.py
learner.py
learner_service.py
process.py
queue.py
wandb_utils.py
```

可分成两类：

- 在线 RL：`actor.py`、`learner.py`、`buffer.py`、`learner_service.py`
- ACP 支撑：`acp_hook.py`、`acp_tags.py`、`acp_dataset_stats.py`

这里的关键认识是：

- `ACP` 并不是独立模型，而是“根据 advantage 给 task prompt 打标签”的机制。
- `actor/learner` 又是另一条支线，偏 HILSerl 风格的在线 RL。

## 6.8 `robots/`：机器人本体

核心骨架文件：

- `config.py`
- `robot.py`
- `utils.py`

支持的主要机器人/跟随臂子包：

```text
bi_openarm_follower
bi_piper_follower
bi_so_follower
earthrover_mini_plus
hope_jr
koch_follower
lekiwi
omx_follower
openarm_follower
piper_follower
reachy2
so_follower
unitree_g1
```

这部分的阅读方法不是“把每个机器人都读一遍”，而是：

1. 先读 `robot.py` 抽象接口。
2. 再读 `utils.py` 的 `make_robot_from_config()` 看类型分发。
3. 最后只读你当前要用的机器人子包。

### 关于 PiPER 资源文件的特别说明

`README.md` 明确要求 PiPER 用户执行 `git lfs pull` 拉取：

- `src/lerobot/assets/piper_description/**`
- `src/lerobot/assets/piper_x_description/**`

当前本地工作区里 `assets` 目录存在，但没有检出具体资源文件，因此：

- 代码结构是完整的。
- 但某些 PiPER 相关运行时资源可能还没有真正落地到磁盘。

## 6.9 `teleoperators/`：主手/遥操作设备

核心骨架文件：

- `config.py`
- `teleoperator.py`
- `utils.py`

支持的主要 teleoperator 子包：

```text
bi_openarm_leader
bi_piper_leader
bi_so_leader
gamepad
homunculus
keyboard
koch_leader
omx_leader
openarm_leader
phone
piper_leader
reachy2_teleoperator
so_leader
unitree_g1
```

这部分和 `robots/` 是镜像结构：

- `teleoperator.py` 定义抽象接口。
- `utils.py` 里的 `make_teleoperator_from_config()` 做实例化分发。
- 各子包各自实现 `get_action()` / `send_feedback()` / `connect()` 等。

## 6.10 `cameras/`、`motors/`、`envs/`、`async_inference/`、`transport/`、`utils/`

### `cameras/`

主要支持：

- `opencv`
- `realsense`
- `reachy2_camera`
- `zmq`

重要文件：

- `camera.py`
- `configs.py`
- `utils.py`

### `motors/`

主要支持：

- `dynamixel`
- `feetech`
- `damiao`

关键文件：

- `motors_bus.py`
- `encoding_utils.py`
- `calibration_gui.py`

### `envs/`

主要文件：

```text
__init__.py
configs.py
factory.py
libero.py
metaworld.py
metaworld_config.json
utils.py
```

这块主要为训练/评估的仿真环境服务。

### `async_inference/`

文件清单：

```text
configs.py
constants.py
helpers.py
policy_server.py
robot_client.py
```

用于异步推理部署。

### `transport/`

文件清单：

```text
services.proto
services_pb2.py
services_pb2_grpc.py
utils.py
```

这块是在线 RL 的通信底座。

### `utils/`

工具文件清单：

```text
constants.py
control_utils.py
decorators.py
errors.py
hub.py
import_utils.py
io_utils.py
logging_utils.py
piper_sdk.py
rabc.py
random_utils.py
recording_annotations.py
robot_utils.py
rotation.py
train_utils.py
transition.py
utils.py
visualization_utils.py
```

最常用的几个：

- `constants.py`
- `import_utils.py`
- `train_utils.py`
- `recording_annotations.py`
- `control_utils.py`
- `visualization_utils.py`

---

## 7. 关键代码部分精读

下面这些文件，是我认为“真正把这个仓库读懂”的核心节点。

### 7.1 `src/lerobot/configs/parser.py`

为什么重要：

- 这是所有 CLI 脚本的共同入口增强器。
- `wrap()` 不只是 parse config。
- 它还做了三件关键事：
  1. 解析 `--policy.path` / `--value.path` 这类“从已有 checkpoint/hub 读配置”的参数。
  2. 自动加载插件。
  3. 过滤路径相关参数，避免和 `draccus` 的 choice/type 解析冲突。

你在读所有 `@parser.wrap()` 的脚本时，都应该默认脑中带着这层预处理。

### 7.2 `src/lerobot/configs/train.py`

为什么重要：

- `TrainPipelineConfig.validate()` 会决定训练是从头开始、从 checkpoint 恢复，还是从 pretrained policy 启动。
- optimizer/scheduler 默认值不是散落在脚本里，而是在这里和 policy preset 联动出来。
- ACP、RA-BC、rename_map 也是在这里挂进训练配置树的。

读懂这一个文件，基本就能看懂训练命令行参数是如何流入训练主循环的。

### 7.3 `src/lerobot/policies/factory.py`

为什么重要：

- `get_policy_class()` 做策略类动态分发。
- `make_pre_post_processors()` 根据 policy type 选择不同 processor 组合。
- `make_policy()` 决定是从 dataset meta 推断 feature，还是从 env 推断 feature。

这就是“策略世界”的总工厂。

### 7.4 `src/lerobot/datasets/factory.py`

为什么重要：

- 它把 `TrainPipelineConfig` 翻译成具体 dataset 对象。
- 这里会解析 `delta_timestamps`。
- 这里决定是普通 `LeRobotDataset` 还是 `StreamingLeRobotDataset`。

所以它不是“一个简单的 new Dataset”，而是训练数据语义的入口。

### 7.5 `src/lerobot/datasets/lerobot_dataset.py`

为什么重要：

- 这是整个仓库的数据底层。
- metadata、tasks、episodes、stats、video path、parquet path、写盘、版本兼容，都在这里。
- 很多“我这个字段为什么在数据集中存在/不存在”的答案，也在这里。

如果你只看一个 dataset 文件，就看它。

### 7.6 `src/lerobot/processor/pipeline.py`

为什么重要：

- 它定义了 processor 的核心抽象。
- 仓库里 observation/action/batch 的各种变换，几乎都靠它统一起来。
- 如果没有它，`record`、`train`、`eval`、`value infer` 会各写一套数据变换代码，维护成本会非常高。

你可以把它理解成“统一的中间表示变换框架”。

### 7.7 `src/lerobot/scripts/lerobot_record.py`

为什么重要：

- 这里把 robot、teleop、dataset、policy、processor 全部连起来。
- 它先聚合 dataset feature schema，再创建数据集，再连接硬件，再进入 `record_loop()`。
- `human-in-loop` 能不能跑起来，本质上也是从这个脚本分流出去的。

如果你只想搞懂真实机器人数据是怎么采进来的，这个文件必须精读。

### 7.8 `src/lerobot/scripts/recording_loop.py`

为什么重要：

- 这是单步控制循环的核心。
- 一次循环里会发生：
  1. `robot.get_observation()`
  2. `robot_observation_processor`
  3. policy 或 teleop 产生动作
  4. `robot_action_processor`
  5. `robot.send_action()`
  6. 写 dataset frame

这个文件最像“真实执行引擎”。

### 7.9 `src/lerobot/scripts/recording_hil.py`

为什么重要：

- 它把 `policy`、`teleop`、`intervention`、`ACP inference` 串起来。
- `PolicySyncDualArmExecutor` 负责把 policy action 同步到 follower 和 teleop arm。
- `_predict_policy_action_with_acp_inference()` 实现 ACP 条件/无条件推理与 CFG 风格融合。

这是 Evo-RL 人在回路采集最重要的增量文件之一。

### 7.10 `src/lerobot/scripts/lerobot_train.py`

为什么重要：

- 离线策略训练总入口。
- `update_policy()` 是最核心的单步训练逻辑。
- ACP raw-batch hook、RA-BC sample weighting、evaluation、checkpointing 都在这里汇总。

它像是“把一切训练用零件组装起来的调度器”。

### 7.11 `src/lerobot/values/pistar06/modeling_pistar06.py`

为什么重要：

- 这是当前 value 模型的实现核心。
- 它把 vision encoder 和 language model 融合，再输出 distributional value bins。
- `compute_normalized_value_targets()` 则定义了怎样从 episode 成败和剩余步数生成训练目标。

这是你理解 Evo-RL value 支线的第一文件。

### 7.12 `src/lerobot/scripts/lerobot_value_infer.py`

为什么重要：

- 它会把训练好的 value model 用在整个数据集上。
- 它不只是推理 value，还会计算：
  - dense rewards
  - n-step advantages
  - ACP indicator
- 最关键的是：**它会把这些列直接回写到 dataset parquet**。

从“算法结果”到“数据集字段”的桥，就是这里。

### 7.13 `src/lerobot/rl/acp_hook.py` 与 `src/lerobot/rl/acp_tags.py`

为什么重要：

- `acp_tags.py` 定义 advantage tag 文本格式。
- `acp_hook.py` 在训练时把 `task` 文本改写成带正/负 advantage 标签的 prompt。

这部分代码很小，但概念很关键：

**ACP 的本质不是改模型结构，而是改输入 prompt。**

### 7.14 `src/lerobot/rl/actor.py` 与 `src/lerobot/rl/learner.py`

为什么重要：

- 这是在线 RL 的 actor-learner 分布式实现。
- `actor.py` 负责连真实环境、收集 transition、发给 learner。
- `learner.py` 负责 replay buffer、参数更新、参数回传。

如果你未来要扩展到更强的在线真实机器人 RL，这两份文件必须吃透。

---

## 8. README 与代码的映射关系

| README 阶段 | 主要 CLI | 关键源码 |
| --- | --- | --- |
| Installation | `pip install -e .` | `pyproject.toml`, `setup.py` |
| Hardware Setup | `lerobot-teleoperate` | `scripts/lerobot_teleoperate.py`, `robots/`, `teleoperators/`, `cameras/`, `motors/` |
| Data Collection | `lerobot-record`, `lerobot-human-inloop-record` | `scripts/lerobot_record.py`, `scripts/recording_loop.py`, `scripts/recording_hil.py` |
| Value Function Training | `lerobot-value-train` | `scripts/lerobot_value_train.py`, `values/pistar06/` |
| Value Inference | `lerobot-value-infer` | `scripts/lerobot_value_infer.py`, `configs/value.py` |
| Policy Training | `lerobot-train` | `scripts/lerobot_train.py`, `configs/train.py`, `policies/factory.py` |
| Closed-loop Rollout | `lerobot-human-inloop-record` | `scripts/lerobot_human_inloop_record.py`, `scripts/recording_hil.py` |

---

## 9. 示例、测试、文档分别能帮你做什么

## 9.1 `examples/`

文件数 37，按主题分成以下目录：

```text
backward_compatibility
dataset
lekiwi
phone_to_so100
port_datasets
rtc
so100_to_so100_EE
training
tutorial
unitree_g1
```

最值得先看的示例：

- `examples/training/train_policy.py`
- `examples/training/train_with_streaming.py`
- `examples/so100_to_so100_EE/record.py`
- `examples/so100_to_so100_EE/teleoperate.py`
- `examples/rtc/eval_with_real_robot.py`
- `examples/tutorial/*`

如果你是第一次看这个仓库，示例的作用不是学“原理”，而是帮你快速知道某类功能到底怎么调用。

## 9.2 `tests/`

`tests` 不是边角料，反而很适合拿来反向理解模块职责。

按子域分布如下：

```text
(root) 7
artifacts 3
async_inference 4
cameras 3
configs 1
datasets 14
envs 1
fixtures 5
mocks 6
motors 4
optim 2
policies 24
processor 20
rl 4
robots 3
scripts 3
teleoperators 3
training 5
transport 1
utils 10
value 6
```

如果你想快速验证自己是否读懂某块代码，推荐直接对照这些测试：

- 读 dataset：看 `tests/datasets/`
- 读 processor：看 `tests/processor/`
- 读 value 支线：看 `tests/value/`
- 读 ACP：看 `tests/training/test_acp_*`
- 读在线 RL：看 `tests/rl/`

## 9.3 `docs/`

`docs/source` 下有 59 个文档源文件，覆盖：

- 安装
- 各硬件平台
- 各 policy family
- processor 机制
- env hub
- dataset v3
- HILSerl / async / peft / multi-gpu

如果你读源码读到一半发现“概念已经模糊了”，很适合回头翻 `docs/source/*.mdx`。

## 9.4 `website/`

这里是官网静态资源：

- `index.html`
- `app.js`
- `styles.css`
- `assets/images/*`
- `assets/videos/*`

它不是训练逻辑，但能帮助你从产品视角理解项目如何对外讲述自己。

---

## 10. 建议阅读顺序

如果你的目标是“详细读懂整个 Evo-RL 仓库”，我建议按下面顺序读：

1. `README.md`
   先建立业务闭环，不然源码会显得零散。
2. `pyproject.toml`
   先搞清楚有哪些 CLI 命令。
3. `src/lerobot/configs/parser.py`
   先搞清楚参数是怎么进系统的。
4. `src/lerobot/configs/train.py`、`value_train.py`、`value.py`
   建立训练/推理配置树。
5. `src/lerobot/scripts/lerobot_record.py`
   看真实机器人数据是怎么组织的。
6. `src/lerobot/scripts/recording_loop.py`
   看单步控制循环。
7. `src/lerobot/datasets/lerobot_dataset.py`
   看数据集底层。
8. `src/lerobot/processor/pipeline.py`
   看统一处理流水线。
9. `src/lerobot/policies/factory.py`
   看策略工厂。
10. 你实际会用的 policy family
   比如 `pi0` / `pi05` / `sac` / `smolvla`。
11. `src/lerobot/values/pistar06/`
   看 value 模型和目标构造。
12. `src/lerobot/scripts/lerobot_value_infer.py`
   看 value 如何回写成 dataset 字段。
13. `src/lerobot/scripts/lerobot_human_inloop_record.py`
   看闭环 rollout 的采集策略。
14. `src/lerobot/scripts/recording_hil.py`
   看 intervention、teleop mirror、ACP inference。
15. `src/lerobot/rl/`
   最后再看在线 RL 支线。

---

## 11. 如果你只想最快抓住核心，先打开这 12 个文件

| 优先级 | 文件 | 理由 |
| --- | --- | --- |
| 1 | `README.md` | 先建立业务闭环 |
| 2 | `pyproject.toml` | 先知道命令入口 |
| 3 | `src/lerobot/configs/parser.py` | 先知道 CLI 如何变成 config |
| 4 | `src/lerobot/scripts/lerobot_record.py` | 真实机器人采集总入口 |
| 5 | `src/lerobot/scripts/recording_loop.py` | 单步控制核心 |
| 6 | `src/lerobot/datasets/lerobot_dataset.py` | 数据集底层 |
| 7 | `src/lerobot/processor/pipeline.py` | 统一 processor 框架 |
| 8 | `src/lerobot/policies/factory.py` | policy 工厂和 processor 工厂 |
| 9 | `src/lerobot/scripts/lerobot_train.py` | 离线策略训练主入口 |
| 10 | `src/lerobot/values/pistar06/modeling_pistar06.py` | 当前 value model 核心 |
| 11 | `src/lerobot/scripts/lerobot_value_infer.py` | value/advantage/indicator 回写入口 |
| 12 | `src/lerobot/scripts/recording_hil.py` | 人在回路和 ACP inference 核心 |

---

## 12. 这份仓库里，哪些部分最像“Evo-RL 自己的东西”

如果站在“和原始 LeRobot 区分”的角度看，最具 Evo-RL 特征的是：

- `README.md` 中定义的 value->policy->closed-loop 真实机器人 RL 工作流
- `src/lerobot/scripts/lerobot_value_train.py`
- `src/lerobot/scripts/lerobot_value_infer.py`
- `src/lerobot/values/pistar06/`
- `src/lerobot/scripts/lerobot_human_inloop_record.py`
- `src/lerobot/scripts/recording_hil.py`
- `src/lerobot/rl/acp_hook.py`
- `src/lerobot/rl/acp_tags.py`
- `src/lerobot/policies/sarm/compute_rabc_weights.py`
- `src/lerobot/scripts/lerobot_dataset_report.py`

如果你的目标是“读懂 Evo-RL 自身创新”，建议优先读这些，而不是平均分配精力给所有 policy family。

---

## 13. 最后的阅读建议

读这个仓库最容易犯的错，是一开始就钻进某个大模型实现文件，例如：

- `modeling_pi0.py`
- `modeling_wall_x.py`
- `modeling_florence2.py`

这样会很快丢失全局。

更好的办法是：

1. 先读流程脚本。
2. 再读配置和工厂。
3. 再读 dataset 与 processor。
4. 最后才读具体 model。

因为这个项目的复杂度，更多来自 **系统装配**，而不只是某一个神经网络文件本身。

---

## 14. 一句话总结

如果把这个项目压缩成一句话：

**Evo-RL 是一个建立在 LeRobot 之上的真实机器人强化学习工程系统，它把硬件控制、数据采集、value 打标、prompt 条件化策略训练和人在回路闭环迭代，串成了一条可以复现的工程流水线。**
