#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
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

from dataclasses import dataclass
from typing import TypeAlias

from ..config import TeleoperatorConfig


@dataclass
class SOLeaderConfig:
    """Base configuration class for SO Leader teleoperators."""

    # Port to connect to the arm
    port: str

    # Arm side used to choose the expected servo ID range.
    # If omitted, it is inferred from `id` when possible and otherwise defaults to `left`.
    side: str | None = None

    # Whether to use degrees for angles
    use_degrees: bool = False

    # Remap the leader gripper's normalized input range to the full 0-100 teleop output range.
    # This is useful when the leader gripper has a longer physical stroke than the follower.
    # For example, setting min=0 and max=40 means only the first 40% of leader travel spans
    # the full follower open/close range.
    gripper_input_min: float = 0.0
    gripper_input_max: float = 100.0


@TeleoperatorConfig.register_subclass("so101_leader")
@TeleoperatorConfig.register_subclass("so100_leader")
@dataclass
class SOLeaderTeleopConfig(TeleoperatorConfig, SOLeaderConfig):
    pass


SO100LeaderConfig: TypeAlias = SOLeaderTeleopConfig
SO101LeaderConfig: TypeAlias = SOLeaderTeleopConfig
