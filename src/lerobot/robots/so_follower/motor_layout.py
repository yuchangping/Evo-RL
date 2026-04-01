#!/usr/bin/env python

# Copyright 2026 The HuggingFace Inc. team. All rights reserved.
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

SO_ARM_MOTOR_NAMES: tuple[str, ...] = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "forearm_roll",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)

SO_ARM_LEFT_IDS: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7)
SO_ARM_RIGHT_IDS: tuple[int, ...] = (8, 9, 10, 11, 12, 13, 14)
SO_ARM_FULL_TURN_MOTORS: tuple[str, ...] = ("forearm_roll", "wrist_roll")


def resolve_so_arm_side(side: str | None, device_id: str | None) -> str:
    if side is not None:
        normalized_side = side.lower()
        if normalized_side not in {"left", "right"}:
            raise ValueError("`side` must be either 'left', 'right', or omitted.")
        return normalized_side

    if device_id is not None:
        lowered_id = device_id.lower()
        if "right" in lowered_id:
            return "right"
        if "left" in lowered_id:
            return "left"

    return "left"


def get_so_arm_motor_ids(side: str | None, device_id: str | None = None) -> dict[str, int]:
    resolved_side = resolve_so_arm_side(side, device_id)
    default_ids = SO_ARM_LEFT_IDS if resolved_side == "left" else SO_ARM_RIGHT_IDS
    return dict(zip(SO_ARM_MOTOR_NAMES, default_ids))
