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

from unittest.mock import MagicMock, patch

from lerobot.robots.bi_so_follower import BiSOFollower, BiSOFollowerConfig
from lerobot.robots.so_follower import SOFollowerConfig


def _make_arm_mock(name: str) -> MagicMock:
    arm = MagicMock(name=name)
    arm.cameras = {}
    arm._motors_ft = {"joint.pos": float}
    arm._cameras_ft = {}
    arm.is_connected = False
    arm.is_calibrated = True
    return arm


def test_bimanual_defaults_left_and_right_id_ranges():
    captured_configs = []

    def _make_arm(config):
        captured_configs.append(config)
        return _make_arm_mock(config.id or "arm")

    with patch(
        "lerobot.robots.bi_so_follower.bi_so_follower.SOFollower",
        side_effect=_make_arm,
    ):
        BiSOFollower(
            BiSOFollowerConfig(
                id="bimanual_follower",
                left_arm_config=SOFollowerConfig(port="/dev/left"),
                right_arm_config=SOFollowerConfig(port="/dev/right"),
            )
        )

    assert [cfg.side for cfg in captured_configs] == ["left", "right"]
