#!/usr/bin/env bash

export DATA_NS=local
export TASK_NAME=bi_so101_handover_cube
export TASK_TEXT="Pick up the cube with the left arm, hand it over to the right arm, and then place it into the box."


export startcaiji=startcaiji1

export LOCAL_DATA_ROOT=/home/jy/Data/YCP/lerobot_datasets
export SERVER_DATA_ROOT=/home/jy/Data/a100_lerobot_datasets

export DEMO_REPO_ID=${DATA_NS}/${TASK_NAME}_demo
export ROUND1_REPO_ID=${DATA_NS}/eval_${TASK_NAME}_round1
export MERGED_R1_REPO_ID=${DATA_NS}/${TASK_NAME}_merged_r1

export PI05_SFT_R0_NAME=${TASK_NAME}_pi05_sft_r0
export VALUE_R1_NAME=${TASK_NAME}_value_r1
export PI05_ACP_R1_NAME=${TASK_NAME}_pi05_acp_r1

export ROBOT_ID=bi_follower_arm
export TELEOP_ID=bi_leader_arm

export PORT_1="/dev/serial/by-id/usb-1a86_USB_Single_Serial_58FA082672-if00"
export PORT_2="/dev/serial/by-id/usb-1a86_USB_Single_Serial_58FA083353-if00"
export PORT_3="/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14029908-if00"
export PORT_4="/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14031881-if00"

export RIGHT_FOLLOWER_PORT="${PORT_4}"
export LEFT_FOLLOWER_PORT="${PORT_2}"
export RIGHT_LEADER_PORT="${PORT_3}"
export LEFT_LEADER_PORT="${PORT_1}"

# Teleoperation tuning: smoother and less jittery baseline for SO bimanual control.
export TELEOP_SMOOTHING_ALPHA=0.35
export TELEOP_SMOOTH_GRIPPER=false
export SO_TELEOP_ARM_MAPPING="same_side"
export SO_TELEOP_INVERT_LEFT_SHOULDER_PAN=true
export SO_TELEOP_INVERT_LEFT_WRIST_FLEX=true
export SO_TELEOP_INVERT_LEFT_WRIST_ROLL=true
# Right leader shoulder pan inversion:
# when the right leader arm swings outward, the right follower arm also swings outward.
export SO_TELEOP_INVERT_RIGHT_SHOULDER_PAN=true
export SO_TELEOP_INVERT_RIGHT_WRIST_FLEX=true
export SO_TELEOP_INVERT_RIGHT_WRIST_ROLL=true

export FOLLOWER_ACCELERATION=80
export FOLLOWER_MAX_ACCELERATION=120
export FOLLOWER_POSITION_P=12
export FOLLOWER_POSITION_I=0
export FOLLOWER_POSITION_D=40

export SO_TELEOP_SMOOTHING_ARGS="--teleop_smoothing_alpha=${TELEOP_SMOOTHING_ALPHA} --teleop_smooth_gripper=${TELEOP_SMOOTH_GRIPPER}"
export SO_TELEOP_LAYOUT_ARGS="--teleop.arm_mapping=${SO_TELEOP_ARM_MAPPING}"
export SO_TELEOP_DIRECTION_ARGS="--teleop.invert_left_shoulder_pan=${SO_TELEOP_INVERT_LEFT_SHOULDER_PAN} --teleop.invert_left_wrist_flex=${SO_TELEOP_INVERT_LEFT_WRIST_FLEX} --teleop.invert_left_wrist_roll=${SO_TELEOP_INVERT_LEFT_WRIST_ROLL} --teleop.invert_right_shoulder_pan=${SO_TELEOP_INVERT_RIGHT_SHOULDER_PAN} --teleop.invert_right_wrist_flex=${SO_TELEOP_INVERT_RIGHT_WRIST_FLEX} --teleop.invert_right_wrist_roll=${SO_TELEOP_INVERT_RIGHT_WRIST_ROLL}"
export SO_TELEOP_ARGS="${SO_TELEOP_SMOOTHING_ARGS} ${SO_TELEOP_LAYOUT_ARGS} ${SO_TELEOP_DIRECTION_ARGS}"
export SO_FOLLOWER_TUNING_ARGS="--robot.left_arm_config.acceleration=${FOLLOWER_ACCELERATION} --robot.left_arm_config.maximum_acceleration=${FOLLOWER_MAX_ACCELERATION} --robot.left_arm_config.position_p_coefficient=${FOLLOWER_POSITION_P} --robot.left_arm_config.position_i_coefficient=${FOLLOWER_POSITION_I} --robot.left_arm_config.position_d_coefficient=${FOLLOWER_POSITION_D} --robot.right_arm_config.acceleration=${FOLLOWER_ACCELERATION} --robot.right_arm_config.maximum_acceleration=${FOLLOWER_MAX_ACCELERATION} --robot.right_arm_config.position_p_coefficient=${FOLLOWER_POSITION_P} --robot.right_arm_config.position_i_coefficient=${FOLLOWER_POSITION_I} --robot.right_arm_config.position_d_coefficient=${FOLLOWER_POSITION_D}"


export LEFT_WRIST_CAM="/dev/v4l/by-path/pci-0000:00:14.0-usb-0:9.2:1.3-video-index0"
export RIGHT_WRIST_CAM="/dev/v4l/by-path/pci-0000:00:14.0-usb-0:9.3:1.0-video-index0"
export FRONT_CAM="/dev/v4l/by-path/pci-0000:00:14.0-usb-0:9.1:1.3-video-index0"


export LEFT_CAM_CFG='{ wrist: {type: opencv, index_or_path: "'"${LEFT_WRIST_CAM}"'", width: 640, height: 480, fps: 30, fourcc: "MJPG"}}'
export FRONT_CAM_CFG='front: {type: opencv, index_or_path: "'"${FRONT_CAM}"'", width: 640, height: 480, fps: 30, fourcc: "MJPG"}'
export RIGHT_CAM_CFG='{ wrist: {type: opencv, index_or_path: "'"${RIGHT_WRIST_CAM}"'", width: 640, height: 480, fps: 30, fourcc: "MJPG"}, '"${FRONT_CAM_CFG}"'}'


show_demo_count() {
  local dataset_dir="${LOCAL_DATA_ROOT}/${DEMO_REPO_ID}"
  local info_json="${dataset_dir}/meta/info.json"
  local current=0

  if [ -f "$info_json" ]; then
    current=$(python - "$info_json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    print(int(json.load(f).get("total_episodes", 0)))
PY
)
  fi

  echo "${DEMO_REPO_ID}: ${current} episodes"
}


record_to_total() {
  local target_total="$1"
  local dataset_dir="${LOCAL_DATA_ROOT}/${DEMO_REPO_ID}"
  local info_json="${dataset_dir}/meta/info.json"
  local current=0

  if [ -z "$target_total" ]; then
    echo "Usage: record_to_total <target_total>"
    return 1
  fi

  if ! [[ "$target_total" =~ ^[0-9]+$ ]]; then
    echo "target_total must be a non-negative integer"
    return 1
  fi

  if [ -f "$info_json" ]; then
    current=$(python - "$info_json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    print(int(json.load(f).get("total_episodes", 0)))
PY
)
  fi

  local remaining=$((target_total - current))

  if [ "$remaining" -le 0 ]; then
    echo "Current dataset already has ${current} episodes, meeting or exceeding target ${target_total}."
    return 0
  fi

  mkdir -p "$dataset_dir"
  echo "Current dataset has ${current} episodes. Recording ${remaining} more to reach ${target_total} total."

  lerobot-record \
    --robot.type=bi_so_follower \
    --robot.left_arm_config.port="${LEFT_FOLLOWER_PORT}" \
    --robot.right_arm_config.port="${RIGHT_FOLLOWER_PORT}" \
    --robot.id="${ROBOT_ID}" \
    --robot.left_arm_config.cameras="${LEFT_CAM_CFG}" \
    --robot.right_arm_config.cameras="${RIGHT_CAM_CFG}" \
    --teleop.type=bi_so_leader \
    --teleop.left_arm_config.port="${LEFT_LEADER_PORT}" \
    --teleop.right_arm_config.port="${RIGHT_LEADER_PORT}" \
    --teleop.left_arm_config.gripper_input_min=0 \
    --teleop.left_arm_config.gripper_input_max=40 \
    --teleop.right_arm_config.gripper_input_min=0 \
    --teleop.right_arm_config.gripper_input_max=40 \
    --teleop.id="${TELEOP_ID}" \
    --dataset.repo_id="${DEMO_REPO_ID}" \
    --dataset.root="${dataset_dir}" \
    --dataset.single_task="${TASK_TEXT}" \
    --dataset.num_episodes="${remaining}" \
    --dataset.episode_time_s=0 \
    --dataset.reset_time_s=0 \
    --dataset.push_to_hub=false \
    --display_data=true \
    --resume=true \
    ${SO_TELEOP_ARGS} \
    ${SO_FOLLOWER_TUNING_ARGS}
}
