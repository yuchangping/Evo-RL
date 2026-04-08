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

import pytest

from lerobot.teleoperators.bi_so_leader import BiSOLeader, BiSOLeaderConfig
from lerobot.teleoperators.so_leader import SOLeaderConfig
from lerobot.utils.errors import DeviceNotConnectedError


def _make_arm_mock(name: str) -> MagicMock:
    arm = MagicMock(name=name)
    arm.is_connected = False
    arm.is_calibrated = True
    arm.action_features = {"joint.pos": float}

    def _connect(*_args, **_kwargs):
        arm.is_connected = True

    def _disconnect():
        arm.is_connected = False

    arm.connect.side_effect = _connect
    arm.disconnect.side_effect = _disconnect
    arm.get_action.return_value = {"joint.pos": 0.0}
    return arm


@pytest.fixture
def bi_leader():
    left_arm = _make_arm_mock("left_arm")
    right_arm = _make_arm_mock("right_arm")

    with patch(
        "lerobot.teleoperators.bi_so_leader.bi_so_leader.SOLeader",
        side_effect=[left_arm, right_arm],
    ):
        teleop = BiSOLeader(
            BiSOLeaderConfig(
                left_arm_config=SOLeaderConfig(port="/dev/left"),
                right_arm_config=SOLeaderConfig(port="/dev/right"),
            )
        )
        yield teleop, left_arm, right_arm


def test_set_manual_control_requires_connection(bi_leader):
    teleop, _, _ = bi_leader

    with pytest.raises(DeviceNotConnectedError):
        teleop.set_manual_control(True)


def test_set_manual_control_forwards_to_both_arms(bi_leader):
    teleop, left_arm, right_arm = bi_leader
    teleop.connect()

    teleop.set_manual_control(True)
    teleop.set_manual_control(False)

    left_arm.set_manual_control.assert_any_call(True)
    left_arm.set_manual_control.assert_any_call(False)
    right_arm.set_manual_control.assert_any_call(True)
    right_arm.set_manual_control.assert_any_call(False)


def test_bimanual_defaults_left_and_right_id_ranges():
    captured_configs = []

    def _make_arm(config):
        captured_configs.append(config)
        return _make_arm_mock(config.id or "arm")

    with patch(
        "lerobot.teleoperators.bi_so_leader.bi_so_leader.SOLeader",
        side_effect=_make_arm,
    ):
        BiSOLeader(
            BiSOLeaderConfig(
                id="bimanual_leader",
                left_arm_config=SOLeaderConfig(port="/dev/left"),
                right_arm_config=SOLeaderConfig(port="/dev/right"),
            )
        )

    assert [cfg.side for cfg in captured_configs] == ["left", "right"]


def test_crossed_arm_mapping_swaps_output_prefixes_and_feedback_routes(bi_leader):
    left_arm = _make_arm_mock("left_arm")
    right_arm = _make_arm_mock("right_arm")

    with patch(
        "lerobot.teleoperators.bi_so_leader.bi_so_leader.SOLeader",
        side_effect=[left_arm, right_arm],
    ):
        teleop = BiSOLeader(
            BiSOLeaderConfig(
                left_arm_config=SOLeaderConfig(port="/dev/left"),
                right_arm_config=SOLeaderConfig(port="/dev/right"),
                arm_mapping="crossed",
            )
        )

    teleop.connect()

    left_arm.get_action.return_value = {"joint.pos": 1.0}
    right_arm.get_action.return_value = {"joint.pos": 2.0}

    assert teleop.get_action() == {
        "right_joint.pos": 1.0,
        "left_joint.pos": 2.0,
    }

    teleop.send_feedback(
        {
            "left_joint.pos": 10.0,
            "right_joint.pos": 20.0,
        }
    )

    left_arm.send_feedback.assert_called_with({"joint.pos": 20.0})
    right_arm.send_feedback.assert_called_with({"joint.pos": 10.0})


def test_invert_right_shoulder_pan_flips_right_arm_only():
    left_arm = _make_arm_mock("left_arm")
    right_arm = _make_arm_mock("right_arm")

    with patch(
        "lerobot.teleoperators.bi_so_leader.bi_so_leader.SOLeader",
        side_effect=[left_arm, right_arm],
    ):
        teleop = BiSOLeader(
            BiSOLeaderConfig(
                left_arm_config=SOLeaderConfig(port="/dev/left"),
                right_arm_config=SOLeaderConfig(port="/dev/right"),
                invert_right_shoulder_pan=True,
            )
        )

    teleop.connect()
    left_arm.get_action.return_value = {"shoulder_pan.pos": 12.0, "joint.pos": 1.0}
    right_arm.get_action.return_value = {"shoulder_pan.pos": 30.0, "joint.pos": 2.0}

    assert teleop.get_action() == {
        "left_shoulder_pan.pos": 12.0,
        "left_joint.pos": 1.0,
        "right_shoulder_pan.pos": -30.0,
        "right_joint.pos": 2.0,
    }

    teleop.send_feedback(
        {
            "left_shoulder_pan.pos": 5.0,
            "right_shoulder_pan.pos": 8.0,
        }
    )

    left_arm.send_feedback.assert_called_with({"shoulder_pan.pos": 5.0})
    right_arm.send_feedback.assert_called_with({"shoulder_pan.pos": -8.0})


def test_invert_left_and_right_shoulder_pan_flips_both_sides():
    left_arm = _make_arm_mock("left_arm")
    right_arm = _make_arm_mock("right_arm")

    with patch(
        "lerobot.teleoperators.bi_so_leader.bi_so_leader.SOLeader",
        side_effect=[left_arm, right_arm],
    ):
        teleop = BiSOLeader(
            BiSOLeaderConfig(
                left_arm_config=SOLeaderConfig(port="/dev/left"),
                right_arm_config=SOLeaderConfig(port="/dev/right"),
                invert_left_shoulder_pan=True,
                invert_right_shoulder_pan=True,
            )
        )

    teleop.connect()
    left_arm.get_action.return_value = {"shoulder_pan.pos": 12.0}
    right_arm.get_action.return_value = {"shoulder_pan.pos": 30.0}

    assert teleop.get_action() == {
        "left_shoulder_pan.pos": -12.0,
        "right_shoulder_pan.pos": -30.0,
    }

    teleop.send_feedback(
        {
            "left_shoulder_pan.pos": 5.0,
            "right_shoulder_pan.pos": 8.0,
        }
    )

    left_arm.send_feedback.assert_called_with({"shoulder_pan.pos": -5.0})
    right_arm.send_feedback.assert_called_with({"shoulder_pan.pos": -8.0})


def test_invert_left_and_right_wrist_flex_flips_both_sides():
    left_arm = _make_arm_mock("left_arm")
    right_arm = _make_arm_mock("right_arm")

    with patch(
        "lerobot.teleoperators.bi_so_leader.bi_so_leader.SOLeader",
        side_effect=[left_arm, right_arm],
    ):
        teleop = BiSOLeader(
            BiSOLeaderConfig(
                left_arm_config=SOLeaderConfig(port="/dev/left"),
                right_arm_config=SOLeaderConfig(port="/dev/right"),
                invert_left_wrist_flex=True,
                invert_right_wrist_flex=True,
            )
        )

    teleop.connect()
    left_arm.get_action.return_value = {"wrist_flex.pos": 12.0}
    right_arm.get_action.return_value = {"wrist_flex.pos": 30.0}

    assert teleop.get_action() == {
        "left_wrist_flex.pos": -12.0,
        "right_wrist_flex.pos": -30.0,
    }

    teleop.send_feedback(
        {
            "left_wrist_flex.pos": 5.0,
            "right_wrist_flex.pos": 8.0,
        }
    )

    left_arm.send_feedback.assert_called_with({"wrist_flex.pos": -5.0})
    right_arm.send_feedback.assert_called_with({"wrist_flex.pos": -8.0})


def test_invert_left_and_right_wrist_roll_flips_both_sides():
    left_arm = _make_arm_mock("left_arm")
    right_arm = _make_arm_mock("right_arm")

    with patch(
        "lerobot.teleoperators.bi_so_leader.bi_so_leader.SOLeader",
        side_effect=[left_arm, right_arm],
    ):
        teleop = BiSOLeader(
            BiSOLeaderConfig(
                left_arm_config=SOLeaderConfig(port="/dev/left"),
                right_arm_config=SOLeaderConfig(port="/dev/right"),
                invert_left_wrist_roll=True,
                invert_right_wrist_roll=True,
            )
        )

    teleop.connect()
    left_arm.get_action.return_value = {"wrist_roll.pos": 12.0}
    right_arm.get_action.return_value = {"wrist_roll.pos": 30.0}

    assert teleop.get_action() == {
        "left_wrist_roll.pos": -12.0,
        "right_wrist_roll.pos": -30.0,
    }

    teleop.send_feedback(
        {
            "left_wrist_roll.pos": 5.0,
            "right_wrist_roll.pos": 8.0,
        }
    )

    left_arm.send_feedback.assert_called_with({"wrist_roll.pos": -5.0})
    right_arm.send_feedback.assert_called_with({"wrist_roll.pos": -8.0})
