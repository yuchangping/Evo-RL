import draccus
import pytest
from draccus.utils import ParsingError

from lerobot.scripts.lerobot_record import RecordConfig
from lerobot.scripts.lerobot_teleoperate import TeleoperateConfig


def test_teleoperate_parses_bi_piperx_types():
    args = [
        "--robot.type=bi_piperx_follower",
        "--robot.id=my_bi_piperx_follower",
        "--robot.left_arm_config.port=can0",
        "--robot.right_arm_config.port=can2",
        "--robot.left_arm_config.require_calibration=false",
        "--robot.right_arm_config.require_calibration=false",
        "--teleop.type=bi_piperx_leader",
        "--teleop.id=my_bi_piperx_leader",
        "--teleop.left_arm_config.port=can1",
        "--teleop.right_arm_config.port=can3",
        "--teleop.left_arm_config.require_calibration=false",
        "--teleop.right_arm_config.require_calibration=false",
    ]
    cfg = draccus.parse(config_class=TeleoperateConfig, config_path=None, args=args)
    assert cfg.robot.type == "bi_piperx_follower"
    assert cfg.teleop.type == "bi_piperx_leader"


def test_teleoperate_parses_bi_so_tuning_and_smoothing_args():
    args = [
        "--robot.type=bi_so_follower",
        "--robot.id=my_bi_so_follower",
        "--robot.left_arm_config.port=/dev/left_follower",
        "--robot.right_arm_config.port=/dev/right_follower",
        "--robot.left_arm_config.position_p_coefficient=12",
        "--robot.right_arm_config.position_d_coefficient=40",
        "--robot.left_arm_config.acceleration=80",
        "--robot.right_arm_config.maximum_acceleration=120",
        "--teleop.type=bi_so_leader",
        "--teleop.id=my_bi_so_leader",
        "--teleop.left_arm_config.port=/dev/left_leader",
        "--teleop.right_arm_config.port=/dev/right_leader",
        "--teleop_smoothing_alpha=0.4",
        "--teleop_smooth_gripper=true",
    ]
    cfg = draccus.parse(config_class=TeleoperateConfig, config_path=None, args=args)
    assert cfg.robot.left_arm_config.position_p_coefficient == 12
    assert cfg.robot.right_arm_config.position_d_coefficient == 40
    assert cfg.robot.left_arm_config.acceleration == 80
    assert cfg.robot.right_arm_config.maximum_acceleration == 120
    assert cfg.teleop_smoothing_alpha == 0.4
    assert cfg.teleop_smooth_gripper is True


def test_record_rejects_mixed_bi_piper_pair():
    args = [
        "--robot.type=bi_piper_follower",
        "--robot.id=my_bi_piper_follower",
        "--robot.left_arm_config.port=can0",
        "--robot.right_arm_config.port=can2",
        "--robot.left_arm_config.require_calibration=false",
        "--robot.right_arm_config.require_calibration=false",
        "--teleop.type=bi_piperx_leader",
        "--teleop.id=my_bi_piperx_leader",
        "--teleop.left_arm_config.port=can1",
        "--teleop.right_arm_config.port=can3",
        "--teleop.left_arm_config.require_calibration=false",
        "--teleop.right_arm_config.require_calibration=false",
        "--dataset.repo_id=dummy/dummy",
        "--dataset.single_task=test",
        "--dataset.num_episodes=1",
        "--dataset.episode_time_s=1",
        "--dataset.reset_time_s=1",
        "--dataset.push_to_hub=false",
    ]
    with pytest.raises(ParsingError) as exc_info:
        draccus.parse(config_class=RecordConfig, config_path=None, args=args)
    assert "Couldn't instantiate class RecordConfig" in str(exc_info.value)
    assert exc_info.value.__cause__ is not None
    assert "must be paired" in str(exc_info.value.__cause__)


def test_record_rejects_bimanual_piper_teleop_with_non_bimanual_robot():
    args = [
        "--robot.type=so101_follower",
        "--robot.port=/dev/mock",
        "--teleop.type=bi_piperx_leader",
        "--teleop.id=my_bi_piperx_leader",
        "--teleop.left_arm_config.port=can1",
        "--teleop.right_arm_config.port=can3",
        "--teleop.left_arm_config.require_calibration=false",
        "--teleop.right_arm_config.require_calibration=false",
        "--dataset.repo_id=dummy/dummy",
        "--dataset.single_task=test",
        "--dataset.num_episodes=1",
        "--dataset.episode_time_s=1",
        "--dataset.reset_time_s=1",
        "--dataset.push_to_hub=false",
    ]
    with pytest.raises(ParsingError) as exc_info:
        draccus.parse(config_class=RecordConfig, config_path=None, args=args)
    assert "Couldn't instantiate class RecordConfig" in str(exc_info.value)
    assert exc_info.value.__cause__ is not None
    assert "must be paired" in str(exc_info.value.__cause__)


def test_record_rejects_invalid_teleop_smoothing_alpha():
    args = [
        "--robot.type=so101_follower",
        "--robot.port=/dev/mock",
        "--teleop.type=so101_leader",
        "--teleop.port=/dev/mock_leader",
        "--dataset.repo_id=dummy/dummy",
        "--dataset.single_task=test",
        "--dataset.num_episodes=1",
        "--dataset.episode_time_s=1",
        "--dataset.reset_time_s=1",
        "--dataset.push_to_hub=false",
        "--teleop_smoothing_alpha=0",
    ]
    with pytest.raises(ParsingError) as exc_info:
        draccus.parse(config_class=RecordConfig, config_path=None, args=args)
    assert "Couldn't instantiate class RecordConfig" in str(exc_info.value)
    assert exc_info.value.__cause__ is not None
    assert "teleop_smoothing_alpha" in str(exc_info.value.__cause__)
