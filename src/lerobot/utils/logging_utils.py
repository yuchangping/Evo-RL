#!/usr/bin/env python

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import math
import time
from collections.abc import Callable
from numbers import Real
from typing import Any

import torch

from lerobot.utils.utils import format_big_number


class AverageMeter:
    """
    Computes and stores the average and current value
    Adapted from https://github.com/pytorch/examples/blob/main/imagenet/main.py
    """

    def __init__(self, name: str, fmt: str = ":f"):
        self.name = name
        self.fmt = fmt
        self.reset()

    def reset(self) -> None:
        self.val = 0.0
        self.avg = 0.0
        self.sum = 0.0
        self.count = 0.0

    def update(self, val: float, n: int = 1) -> None:
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count

    def __str__(self):
        fmtstr = "{name}:{avg" + self.fmt + "}"
        return fmtstr.format(**self.__dict__)


_HUMAN_METRIC_LABELS = {
    "loss": "损失",
    "grad_norm": "梯度范数",
    "lr": "学习率",
    "update_s": "参数更新时间",
    "dataloading_s": "数据加载时间",
    "avg_sum_reward": "平均累计奖励",
    "pc_success": "成功率",
    "eval_s": "评估耗时",
    "loss_per_dim": "各动作维损失",
    "total_loss": "总损失",
    "sparse_stage_loss": "稀疏阶段损失",
    "sparse_subtask_loss": "稀疏子任务损失",
    "dense_stage_loss": "稠密阶段损失",
    "dense_subtask_loss": "稠密子任务损失",
    "rabc_mean_weight": "RA-BC 平均权重",
    "rabc_num_zero_weight": "RA-BC 零权重样本数",
    "rabc_num_full_weight": "RA-BC 满权重样本数",
    "rabc_delta_mean": "RA-BC delta 均值",
    "rabc_delta_std": "RA-BC delta 标准差",
    "rabc_num_frames": "RA-BC 统计帧数",
    "samples_per_s": "每秒样本数",
    "steps_per_s": "每秒训练步数",
    "gpu_memory_allocated_gb": "GPU 已分配显存",
    "gpu_memory_reserved_gb": "GPU 已保留显存",
    "gpu_max_memory_allocated_gb": "GPU 峰值已分配显存",
    "gpu_max_memory_reserved_gb": "GPU 峰值已保留显存",
}


def humanize_metric_label(metric_key: str, fallback: str | None = None) -> str:
    return _HUMAN_METRIC_LABELS.get(metric_key, fallback or metric_key)


def is_scalar_metric(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def is_numeric_list_metric(value: Any) -> bool:
    return isinstance(value, (list, tuple)) and len(value) > 0 and all(
        is_scalar_metric(item) for item in value
    )


def format_metric_number(value: Any) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)

    numeric_value = float(value)
    if math.isnan(numeric_value) or math.isinf(numeric_value):
        return str(numeric_value)
    if numeric_value != 0 and abs(numeric_value) < 1e-4:
        return f"{numeric_value:.3e}"
    if abs(numeric_value) >= 1000:
        return f"{numeric_value:.3e}"
    return f"{numeric_value:.4f}".rstrip("0").rstrip(".")


def metric_unit_suffix(metric_key: str) -> str:
    if metric_key.endswith("_gb"):
        return " GB"
    if metric_key.endswith("_s") and not metric_key.endswith("_per_s"):
        return " 秒"
    return ""


def infer_meter_format(metric_key: str, metric_value: Any) -> str:
    if isinstance(metric_value, int) and not isinstance(metric_value, bool):
        return ":.0f"
    if metric_key == "lr" or metric_key.endswith("_lr"):
        return ":0.1e"
    return ":.3f"


def format_metrics_section(title: str, metrics: dict[str, Any] | None) -> str:
    if not metrics:
        return ""

    lines = [title]
    for metric_key, metric_value in metrics.items():
        if metric_value is None:
            continue

        label = humanize_metric_label(metric_key, metric_key)
        suffix = metric_unit_suffix(metric_key)

        if is_scalar_metric(metric_value):
            lines.append(f"  {label}: {format_metric_number(metric_value)}{suffix}")
            continue

        if is_numeric_list_metric(metric_value):
            lines.append(f"  {label}:")
            formatted_values = [format_metric_number(item) for item in metric_value]
            for i in range(0, len(formatted_values), 8):
                lines.append(f"    {' '.join(formatted_values[i : i + 8])}{suffix}")
            continue

        if isinstance(metric_value, str):
            lines.append(f"  {label}: {metric_value}")
            continue

        lines.append(f"  {label}: {metric_value}")

    if len(lines) == 1:
        return ""
    return "\n".join(lines)


def attach_output_metrics_to_tracker(
    train_tracker: "MetricsTracker", output_dict: dict[str, Any] | None
) -> dict[str, Any]:
    display_only_metrics: dict[str, Any] = {}
    if not output_dict:
        return display_only_metrics

    for metric_key, metric_value in output_dict.items():
        if metric_key in train_tracker.metrics:
            continue
        if is_scalar_metric(metric_value):
            if metric_key not in train_tracker.metrics:
                train_tracker.metrics[metric_key] = AverageMeter(
                    metric_key, infer_meter_format(metric_key, metric_value)
                )
            train_tracker.metrics[metric_key].update(float(metric_value))
        else:
            display_only_metrics[metric_key] = metric_value

    return display_only_metrics


def collect_runtime_metrics(
    train_tracker: "MetricsTracker", device: torch.device, effective_batch_size: int
) -> dict[str, float]:
    runtime_metrics: dict[str, float] = {}
    tracker_dict = train_tracker.to_dict()
    iteration_s = tracker_dict.get("iteration_s")
    if is_scalar_metric(iteration_s) and float(iteration_s) > 0:
        runtime_metrics["samples_per_s"] = effective_batch_size / float(iteration_s)
        runtime_metrics["steps_per_s"] = 1.0 / float(iteration_s)

    if device.type == "cuda" and torch.cuda.is_available():
        device_index = device.index if device.index is not None else torch.cuda.current_device()
        gib = 1024**3
        runtime_metrics["gpu_memory_allocated_gb"] = torch.cuda.memory_allocated(device_index) / gib
        runtime_metrics["gpu_memory_reserved_gb"] = torch.cuda.memory_reserved(device_index) / gib
        runtime_metrics["gpu_max_memory_allocated_gb"] = torch.cuda.max_memory_allocated(device_index) / gib
        runtime_metrics["gpu_max_memory_reserved_gb"] = torch.cuda.max_memory_reserved(device_index) / gib

    return runtime_metrics


def split_runtime_metrics(metrics: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    regular_metrics: dict[str, Any] = {}
    detailed_metrics: dict[str, Any] = {}
    if not metrics:
        return regular_metrics, detailed_metrics

    for metric_key, metric_value in metrics.items():
        if metric_key.endswith("_gb"):
            detailed_metrics[metric_key] = metric_value
        else:
            regular_metrics[metric_key] = metric_value

    return regular_metrics, detailed_metrics


def should_log_detailed_metrics(step: int, total_steps: int | None, log_freq: int, every_n_logs: int = 5) -> bool:
    if log_freq <= 0:
        return False
    detailed_interval = max(log_freq, log_freq * every_n_logs)
    if total_steps is not None and step >= total_steps:
        return True
    return step % detailed_interval == 0


class MetricsTracker:
    """
    A helper class to track and log metrics over time.

    Usage pattern:

    ```python
    # initialize, potentially with non-zero initial step (e.g. if resuming run)
    metrics = {"loss": AverageMeter("loss", ":.3f")}
    train_metrics = MetricsTracker(cfg, dataset, metrics, initial_step=step)

    # update metrics derived from step (samples, episodes, epochs) at each training step
    train_metrics.step()

    # update various metrics
    loss = policy.forward(batch)
    train_metrics.loss = loss

    # display current metrics
    logging.info(train_metrics)

    # export for wandb
    wandb.log(train_metrics.to_dict())

    # reset averages after logging
    train_metrics.reset_averages()
    ```
    """

    __keys__ = [
        "_batch_size",
        "_num_frames",
        "_avg_samples_per_ep",
        "_total_steps",
        "_start_time",
        "metrics",
        "steps",
        "samples",
        "episodes",
        "epochs",
        "accelerator",
    ]

    def __init__(
        self,
        batch_size: int,
        num_frames: int,
        num_episodes: int,
        metrics: dict[str, AverageMeter],
        initial_step: int = 0,
        total_steps: int | None = None,
        accelerator: Callable | None = None,
    ):
        self.__dict__.update(dict.fromkeys(self.__keys__))
        self._batch_size = batch_size
        self._num_frames = num_frames
        self._avg_samples_per_ep = num_frames / num_episodes
        self._total_steps = total_steps
        self._start_time = time.perf_counter()
        self.metrics = metrics

        self.steps = initial_step
        # A sample is an (observation,action) pair, where observation and action
        # can be on multiple timestamps. In a batch, we have `batch_size` number of samples.
        self.samples = self.steps * self._batch_size
        self.episodes = self.samples / self._avg_samples_per_ep
        self.epochs = self.samples / self._num_frames
        self.accelerator = accelerator

    @staticmethod
    def _format_duration(seconds: float) -> str:
        seconds = max(0, int(round(seconds)))
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def _format_metric_value(meter: AverageMeter) -> str:
        return format(meter.avg, meter.fmt[1:])

    @staticmethod
    def _human_metric_label(metric_key: str, meter: AverageMeter) -> str:
        return humanize_metric_label(metric_key, meter.name)

    def __getattr__(self, name: str) -> int | dict[str, AverageMeter] | AverageMeter | Any:
        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self.metrics:
            return self.metrics[name]
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__dict__:
            super().__setattr__(name, value)
        elif name in self.metrics:
            self.metrics[name].update(value)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def step(self) -> None:
        """
        Updates metrics that depend on 'step' for one step.
        """
        self.steps += 1
        self.samples += self._batch_size * (self.accelerator.num_processes if self.accelerator else 1)
        self.episodes = self.samples / self._avg_samples_per_ep
        self.epochs = self.samples / self._num_frames

    def __str__(self) -> str:
        elapsed_s = time.perf_counter() - self._start_time
        current_iteration_s = None
        avg_iteration_s = None
        if "update_s" in self.metrics and "dataloading_s" in self.metrics:
            current_iteration_s = self.metrics["update_s"].val + self.metrics["dataloading_s"].val
            avg_iteration_s = self.metrics["update_s"].avg + self.metrics["dataloading_s"].avg

        display_lines = [
            "训练状态",
            f"  当前步数: {self.steps}",
        ]
        if self._total_steps:
            display_lines.append(f"  当前进度: {100 * self.steps / self._total_steps:.1f}%")
        if current_iteration_s is not None:
            display_lines.append(f"  当前单步耗时: {current_iteration_s:.3f} 秒")
        if avg_iteration_s is not None:
            display_lines.append(f"  平均单步耗时: {avg_iteration_s:.3f} 秒")
        display_lines.append(f"  已运行时间: {self._format_duration(elapsed_s)}")
        if self._total_steps and avg_iteration_s is not None:
            remaining_steps = max(0, self._total_steps - self.steps)
            estimated_total_s = self._total_steps * avg_iteration_s
            display_lines.append(f"  预计总耗时: {self._format_duration(estimated_total_s)}")
            display_lines.append(
                f"  预计剩余时间: {self._format_duration(remaining_steps * avg_iteration_s)}"
            )
        return "\n".join(display_lines)

    def format_detailed_metrics(self) -> str:
        detail_lines = [
            "详细训练指标",
            f"  已处理样本: {format_big_number(self.samples)}",
            f"  已覆盖回合: {format_big_number(self.episodes)}",
            f"  数据轮次: {self.epochs:.2f}",
        ]
        for metric_key, meter in self.metrics.items():
            label = self._human_metric_label(metric_key, meter)
            value = self._format_metric_value(meter)
            suffix = " 秒" if metric_key.endswith("_s") else ""
            detail_lines.append(f"  {label}: {value}{suffix}")
        return "\n".join(detail_lines)

    def to_dict(self, use_avg: bool = True) -> dict[str, int | float]:
        """
        Returns the current metric values (or averages if `use_avg=True`) as a dict.
        """
        metrics_dict = {
            "steps": self.steps,
            "samples": self.samples,
            "episodes": self.episodes,
            "epochs": self.epochs,
            "elapsed_s": time.perf_counter() - self._start_time,
            **{k: m.avg if use_avg else m.val for k, m in self.metrics.items()},
        }
        if "update_s" in self.metrics and "dataloading_s" in self.metrics:
            current_iteration_s = self.metrics["update_s"].val + self.metrics["dataloading_s"].val
            avg_iteration_s = self.metrics["update_s"].avg + self.metrics["dataloading_s"].avg
            metrics_dict["current_iteration_s"] = current_iteration_s
            metrics_dict["iteration_s"] = avg_iteration_s
            if self._total_steps:
                metrics_dict["remaining_s"] = max(0, self._total_steps - self.steps) * avg_iteration_s
                metrics_dict["estimated_total_s"] = self._total_steps * avg_iteration_s
        if self._total_steps:
            metrics_dict["progress_pct"] = 100 * self.steps / self._total_steps
        return metrics_dict

    def reset_averages(self) -> None:
        """Resets average meters."""
        for m in self.metrics.values():
            m.reset()
