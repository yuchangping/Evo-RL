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

import logging
from functools import cached_property

from lerobot.teleoperators.so_leader import SOLeaderTeleopConfig
from lerobot.utils.decorators import check_if_already_connected, check_if_not_connected

from ..so_leader import SOLeader
from ..teleoperator import Teleoperator
from .config_bi_so_leader import BiSOLeaderConfig

logger = logging.getLogger(__name__)


class BiSOLeader(Teleoperator):
    """
    [Bimanual SO Leader Arms](https://github.com/TheRobotStudio/SO-ARM100) designed by TheRobotStudio
    """

    config_class = BiSOLeaderConfig
    name = "bi_so_leader"

    def __init__(self, config: BiSOLeaderConfig):
        super().__init__(config)
        self.config = config

        left_arm_config = SOLeaderTeleopConfig(
            id=f"{config.id}_left" if config.id else None,
            calibration_dir=config.calibration_dir,
            port=config.left_arm_config.port,
            side=config.left_arm_config.side or "left",
            use_degrees=config.left_arm_config.use_degrees,
            gripper_input_min=config.left_arm_config.gripper_input_min,
            gripper_input_max=config.left_arm_config.gripper_input_max,
        )

        right_arm_config = SOLeaderTeleopConfig(
            id=f"{config.id}_right" if config.id else None,
            calibration_dir=config.calibration_dir,
            port=config.right_arm_config.port,
            side=config.right_arm_config.side or "right",
            use_degrees=config.right_arm_config.use_degrees,
            gripper_input_min=config.right_arm_config.gripper_input_min,
            gripper_input_max=config.right_arm_config.gripper_input_max,
        )

        self.left_arm = SOLeader(left_arm_config)
        self.right_arm = SOLeader(right_arm_config)

    def _maybe_invert_physical_arm_action(self, arm_side: str, action: dict[str, float]) -> dict[str, float]:
        adjusted_action = dict(action)
        should_invert_shoulder_pan = (
            (arm_side == "left" and self.config.invert_left_shoulder_pan)
            or (arm_side == "right" and self.config.invert_right_shoulder_pan)
        )
        should_invert_wrist_flex = (
            (arm_side == "left" and self.config.invert_left_wrist_flex)
            or (arm_side == "right" and self.config.invert_right_wrist_flex)
        )
        should_invert_wrist_roll = (
            (arm_side == "left" and self.config.invert_left_wrist_roll)
            or (arm_side == "right" and self.config.invert_right_wrist_roll)
        )
        if should_invert_shoulder_pan and "shoulder_pan.pos" in adjusted_action:
            adjusted_action["shoulder_pan.pos"] = -adjusted_action["shoulder_pan.pos"]
        if should_invert_wrist_flex and "wrist_flex.pos" in adjusted_action:
            adjusted_action["wrist_flex.pos"] = -adjusted_action["wrist_flex.pos"]
        if should_invert_wrist_roll and "wrist_roll.pos" in adjusted_action:
            adjusted_action["wrist_roll.pos"] = -adjusted_action["wrist_roll.pos"]
        return adjusted_action

    def _maybe_invert_physical_arm_feedback(self, arm_side: str, feedback: dict[str, float]) -> dict[str, float]:
        adjusted_feedback = dict(feedback)
        should_invert_shoulder_pan = (
            (arm_side == "left" and self.config.invert_left_shoulder_pan)
            or (arm_side == "right" and self.config.invert_right_shoulder_pan)
        )
        should_invert_wrist_flex = (
            (arm_side == "left" and self.config.invert_left_wrist_flex)
            or (arm_side == "right" and self.config.invert_right_wrist_flex)
        )
        should_invert_wrist_roll = (
            (arm_side == "left" and self.config.invert_left_wrist_roll)
            or (arm_side == "right" and self.config.invert_right_wrist_roll)
        )
        if should_invert_shoulder_pan and "shoulder_pan.pos" in adjusted_feedback:
            adjusted_feedback["shoulder_pan.pos"] = -adjusted_feedback["shoulder_pan.pos"]
        if should_invert_wrist_flex and "wrist_flex.pos" in adjusted_feedback:
            adjusted_feedback["wrist_flex.pos"] = -adjusted_feedback["wrist_flex.pos"]
        if should_invert_wrist_roll and "wrist_roll.pos" in adjusted_feedback:
            adjusted_feedback["wrist_roll.pos"] = -adjusted_feedback["wrist_roll.pos"]
        return adjusted_feedback

    def _output_prefix_for_arm(self, arm_side: str) -> str:
        if self.config.arm_mapping == "crossed":
            return "right" if arm_side == "left" else "left"
        return arm_side

    def _arm_side_for_output_prefix(self, output_prefix: str) -> str:
        if self.config.arm_mapping == "crossed":
            return "right" if output_prefix == "left" else "left"
        return output_prefix

    @cached_property
    def action_features(self) -> dict[str, type]:
        left_arm_features = self.left_arm.action_features
        right_arm_features = self.right_arm.action_features

        return {
            **{f"{self._output_prefix_for_arm('left')}_{k}": v for k, v in left_arm_features.items()},
            **{f"{self._output_prefix_for_arm('right')}_{k}": v for k, v in right_arm_features.items()},
        }

    @cached_property
    def feedback_features(self) -> dict[str, type]:
        return {}

    @property
    def is_connected(self) -> bool:
        return self.left_arm.is_connected and self.right_arm.is_connected

    @check_if_already_connected
    def connect(self, calibrate: bool = True) -> None:
        self.left_arm.connect(calibrate)
        self.right_arm.connect(calibrate)

    @property
    def is_calibrated(self) -> bool:
        return self.left_arm.is_calibrated and self.right_arm.is_calibrated

    def calibrate(self) -> None:
        self.left_arm.calibrate()
        self.right_arm.calibrate()

    def configure(self) -> None:
        self.left_arm.configure()
        self.right_arm.configure()

    def setup_motors(self) -> None:
        self.left_arm.setup_motors()
        self.right_arm.setup_motors()

    @check_if_not_connected
    def set_manual_control(self, enabled: bool) -> None:
        self.left_arm.set_manual_control(enabled)
        self.right_arm.set_manual_control(enabled)

    @check_if_not_connected
    def get_action(self) -> dict[str, float]:
        action_dict = {}

        # Map the physical leader arm to the configured output side.
        left_action = self._maybe_invert_physical_arm_action("left", self.left_arm.get_action())
        left_prefix = self._output_prefix_for_arm("left")
        action_dict.update({f"{left_prefix}_{key}": value for key, value in left_action.items()})

        right_action = self._maybe_invert_physical_arm_action("right", self.right_arm.get_action())
        right_prefix = self._output_prefix_for_arm("right")
        action_dict.update({f"{right_prefix}_{key}": value for key, value in right_action.items()})

        return action_dict

    @check_if_not_connected
    def send_feedback(self, feedback: dict[str, float]) -> None:
        feedback_by_arm = {"left": {}, "right": {}}
        for prefix in ("left", "right"):
            arm_side = self._arm_side_for_output_prefix(prefix)
            feedback_by_arm[arm_side].update(
                {
                    key.removeprefix(f"{prefix}_"): value
                    for key, value in feedback.items()
                    if key.startswith(f"{prefix}_")
                }
            )

        self.left_arm.send_feedback(self._maybe_invert_physical_arm_feedback("left", feedback_by_arm["left"]))
        self.right_arm.send_feedback(self._maybe_invert_physical_arm_feedback("right", feedback_by_arm["right"]))

    @check_if_not_connected
    def disconnect(self) -> None:
        self.left_arm.disconnect()
        self.right_arm.disconnect()
