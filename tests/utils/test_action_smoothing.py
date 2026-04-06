from lerobot.utils.action_smoothing import ExponentialActionSmoother


def test_action_smoother_applies_ema_to_joint_positions_only():
    smoother = ExponentialActionSmoother(alpha=0.5, smooth_gripper=False)

    first = smoother({"left_shoulder.pos": 10.0, "left_gripper.pos": 80.0})
    second = smoother({"left_shoulder.pos": 20.0, "left_gripper.pos": 20.0})

    assert first["left_shoulder.pos"] == 10.0
    assert first["left_gripper.pos"] == 80.0
    assert second["left_shoulder.pos"] == 15.0
    assert second["left_gripper.pos"] == 20.0


def test_action_smoother_reset_clears_history():
    smoother = ExponentialActionSmoother(alpha=0.25)

    smoother({"joint.pos": 40.0})
    smoother.reset()
    after_reset = smoother({"joint.pos": 0.0})

    assert after_reset["joint.pos"] == 0.0
