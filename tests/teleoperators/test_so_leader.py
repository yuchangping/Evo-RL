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

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from lerobot.teleoperators.so_leader import SO100Leader, SO100LeaderConfig


def _make_bus_mock() -> MagicMock:
    bus = MagicMock(name="FeetechBusMock")
    bus.is_connected = False

    def _connect():
        bus.is_connected = True

    def _disconnect():
        bus.is_connected = False

    @contextmanager
    def _dummy_cm():
        yield

    bus.connect.side_effect = _connect
    bus.disconnect.side_effect = _disconnect
    bus.torque_disabled.side_effect = _dummy_cm
    return bus


@pytest.fixture
def leader():
    teleop = _make_leader(SO100LeaderConfig(port="/dev/null"))
    yield teleop
    if teleop.is_connected:
        teleop.disconnect()


def _make_leader(config: SO100LeaderConfig) -> SO100Leader:
    bus_mock = _make_bus_mock()

    def _bus_side_effect(*_args, **kwargs):
        bus_mock.motors = kwargs["motors"]
        motors_order: list[str] = list(bus_mock.motors)
        bus_mock.sync_read.return_value = {motor: idx for idx, motor in enumerate(motors_order, 1)}
        bus_mock.sync_write.return_value = None
        bus_mock.write.return_value = None
        bus_mock.disable_torque.return_value = None
        bus_mock.is_calibrated = True
        return bus_mock

    with (
        patch(
            "lerobot.teleoperators.so_leader.so_leader.FeetechMotorsBus",
            side_effect=_bus_side_effect,
        ),
        patch.object(SO100Leader, "configure", lambda self: None),
    ):
        return SO100Leader(config)


def test_connect_disconnect(leader):
    assert not leader.is_connected
    leader.connect()
    assert leader.is_connected
    leader.disconnect()
    assert not leader.is_connected


def test_get_action(leader):
    leader.connect()
    action = leader.get_action()
    expected_keys = {f"{m}.pos" for m in leader.bus.motors}
    assert set(action.keys()) == expected_keys


def test_send_feedback(leader):
    leader.connect()
    feedback = {f"{m}.pos": i * 10 for i, m in enumerate(leader.bus.motors, 1)}
    leader.send_feedback(feedback)

    goal_pos = {m: (i + 1) * 10 for i, m in enumerate(leader.bus.motors)}
    leader.bus.sync_write.assert_called_once_with("Goal_Position", goal_pos)


def test_default_single_arm_uses_left_id_range():
    leader = _make_leader(SO100LeaderConfig(port="/dev/null"))
    assert [motor.id for motor in leader.bus.motors.values()] == [1, 2, 3, 4, 5, 6, 7]


def test_right_single_arm_infers_right_id_range_from_teleop_id():
    leader = _make_leader(SO100LeaderConfig(port="/dev/null", id="right_leader_arm"))
    assert [motor.id for motor in leader.bus.motors.values()] == [8, 9, 10, 11, 12, 13, 14]


def test_gripper_input_range_is_remapped_to_full_output():
    leader = _make_leader(
        SO100LeaderConfig(
            port="/dev/null",
            gripper_input_min=0.0,
            gripper_input_max=40.0,
        )
    )
    leader.connect()
    leader.bus.sync_read.return_value = {
        "shoulder_pan": 1.0,
        "shoulder_lift": 2.0,
        "elbow_flex": 3.0,
        "forearm_roll": 4.0,
        "wrist_flex": 5.0,
        "wrist_roll": 6.0,
        "gripper": 20.0,
    }

    action = leader.get_action()

    assert action["gripper.pos"] == 50.0
