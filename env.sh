#!/usr/bin/env bash

export DATA_NS=local
export TASK_NAME=bi_so101_handover_cube
export TASK_TEXT="Pick up the cube with the left arm, hand it over to the right arm, and then place it into the box."

export h100training=h100trainingh1

# H100 training server defaults. Override these before `source env.sh` if needed.
export MACHINE_ROLE=${MACHINE_ROLE:-h100_training}
export EVO_RL_DATA_BASE=${EVO_RL_DATA_BASE:-/data2/ycp/lerobot_datasets}
export LOCAL_DATA_ROOT=${LOCAL_DATA_ROOT:-${EVO_RL_DATA_BASE}/local_machine}
export SERVER_DATA_ROOT=${SERVER_DATA_ROOT:-${EVO_RL_DATA_BASE}/h100_server}

export DEMO_REPO_ID=${DATA_NS}/${TASK_NAME}_demo
export ROUND1_REPO_ID=${DATA_NS}/eval_${TASK_NAME}_round1
export MERGED_R1_REPO_ID=${DATA_NS}/${TASK_NAME}_merged_r1

export PI05_SFT_R0_NAME=${TASK_NAME}_pi05_sft_r0
export VALUE_R1_NAME=${TASK_NAME}_value_r1
export PI05_ACP_R1_NAME=${TASK_NAME}_pi05_acp_r1

export ROBOT_ID=bi_follower_arm
export TELEOP_ID=bi_leader_arm

# These hardware paths are only meaningful on the robot-connected machine.
if [[ -d /dev/serial/by-id ]]; then
export PORT_1="/dev/serial/by-id/usb-1a86_USB_Single_Serial_58FA082672-if00"
export PORT_2="/dev/serial/by-id/usb-1a86_USB_Single_Serial_58FA083353-if00"
export PORT_3="/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14029908-if00"
export PORT_4="/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14031881-if00"
else
export PORT_1=""
export PORT_2=""
export PORT_3=""
export PORT_4=""
fi

export RIGHT_FOLLOWER_PORT="${PORT_4}"
export LEFT_FOLLOWER_PORT="${PORT_2}"
export RIGHT_LEADER_PORT="${PORT_3}"
export LEFT_LEADER_PORT="${PORT_1}"

# Teleoperation tuning: smoother and less jittery baseline for SO bimanual control.
export TELEOP_SMOOTHING_ALPHA=0.35
export TELEOP_SMOOTH_GRIPPER=false

export FOLLOWER_ACCELERATION=80
export FOLLOWER_MAX_ACCELERATION=120
export FOLLOWER_POSITION_P=12
export FOLLOWER_POSITION_I=0
export FOLLOWER_POSITION_D=40

export SO_TELEOP_SMOOTHING_ARGS="--teleop_smoothing_alpha=${TELEOP_SMOOTHING_ALPHA} --teleop_smooth_gripper=${TELEOP_SMOOTH_GRIPPER}"
export SO_FOLLOWER_TUNING_ARGS="--robot.left_arm_config.acceleration=${FOLLOWER_ACCELERATION} --robot.left_arm_config.maximum_acceleration=${FOLLOWER_MAX_ACCELERATION} --robot.left_arm_config.position_p_coefficient=${FOLLOWER_POSITION_P} --robot.left_arm_config.position_i_coefficient=${FOLLOWER_POSITION_I} --robot.left_arm_config.position_d_coefficient=${FOLLOWER_POSITION_D} --robot.right_arm_config.acceleration=${FOLLOWER_ACCELERATION} --robot.right_arm_config.maximum_acceleration=${FOLLOWER_MAX_ACCELERATION} --robot.right_arm_config.position_p_coefficient=${FOLLOWER_POSITION_P} --robot.right_arm_config.position_i_coefficient=${FOLLOWER_POSITION_I} --robot.right_arm_config.position_d_coefficient=${FOLLOWER_POSITION_D}"


if [[ -d /dev/v4l/by-path ]]; then
export LEFT_WRIST_CAM="/dev/v4l/by-path/pci-0000:00:14.0-usb-0:9.2:1.0-video-index0"
export RIGHT_WRIST_CAM="/dev/v4l/by-path/pci-0000:00:14.0-usb-0:9.3:1.0-video-index0"
export FRONT_CAM="/dev/v4l/by-path/pci-0000:00:14.0-usb-0:9.1:1.3-video-index0"
else
export LEFT_WRIST_CAM=""
export RIGHT_WRIST_CAM=""
export FRONT_CAM=""
fi



export LEFT_CAM_CFG='{ wrist: {type: opencv, index_or_path: "'"${LEFT_WRIST_CAM}"'", width: 640, height: 480, fps: 30, fourcc: "MJPG"}}'
export FRONT_CAM_CFG='front: {type: opencv, index_or_path: "'"${FRONT_CAM}"'", width: 640, height: 480, fps: 30, fourcc: "MJPG"}'
export RIGHT_CAM_CFG='{ wrist: {type: opencv, index_or_path: "'"${RIGHT_WRIST_CAM}"'", width: 640, height: 480, fps: 30, fourcc: "MJPG"}, '"${FRONT_CAM_CFG}"'}'
