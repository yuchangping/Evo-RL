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

from lerobot.teleoperators.so_leader import SOLeaderConfig

from ..config import TeleoperatorConfig


@TeleoperatorConfig.register_subclass("bi_so_leader")
@dataclass
class BiSOLeaderConfig(TeleoperatorConfig):
    """Configuration class for Bi SO Leader teleoperators."""

    left_arm_config: SOLeaderConfig
    right_arm_config: SOLeaderConfig
    # `same_side`: left leader -> left follower, right leader -> right follower.
    # `crossed`: left leader -> right follower, right leader -> left follower.
    arm_mapping: str = "same_side"
    # Flip the left-arm shoulder pan sign so moving the leader left arm outward
    # also moves the follower left arm outward on mirrored hardware layouts.
    invert_left_shoulder_pan: bool = False
    # Flip the left-arm wrist flex sign.
    invert_left_wrist_flex: bool = False
    # Flip the right-arm shoulder pan sign so moving the leader right arm outward
    # also moves the follower right arm outward on mirrored hardware layouts.
    invert_right_shoulder_pan: bool = False
    # Flip the right-arm wrist flex sign.
    invert_right_wrist_flex: bool = False

    def __post_init__(self) -> None:
        if self.arm_mapping not in {"same_side", "crossed"}:
            raise ValueError("`arm_mapping` must be either 'same_side' or 'crossed'.")
