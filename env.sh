#!/usr/bin/env bash

export DATA_NS=local
export TASK_NAME=bi_so101_handover_cube
export TASK_TEXT="Pick up the cube with the left arm and hand it to the right arm."

export one_yaocao=one_yaocao1
export one_yaocao=one_yaocao1

export LOCAL_DATA_ROOT=/home/jy/Data/YCP/lerobot_datasets
export SERVER_DATA_ROOT=/home/jy/Data/a100_lerobot_datasets

export DEMO_REPO_ID=${DATA_NS}/${TASK_NAME}_demo
export ROUND1_REPO_ID=${DATA_NS}/eval_${TASK_NAME}_round1
export MERGED_R1_REPO_ID=${DATA_NS}/${TASK_NAME}_merged_r1

export PI05_SFT_R0_NAME=${TASK_NAME}_pi05_sft_r0
export VALUE_R1_NAME=${TASK_NAME}_value_r1
export PI05_ACP_R1_NAME=${TASK_NAME}_pi05_acp_r1

export ROBOT_ID=bi_so101_follower
export TELEOP_ID=bi_so101_leader

export PORT_1="/dev/serial/by-id/usb-1a86_USB_Single_Serial_58FA082672-if00"
export PORT_2="/dev/serial/by-id/usb-1a86_USB_Single_Serial_58FA083353-if00"
export PORT_3="/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14029908-if00"
export PORT_4="/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14031881-if00"

export RIGHT_FOLLOWER_PORT="${PORT_4}"
export LEFT_FOLLOWER_PORT="${PORT_2}"
export RIGHT_LEADER_PORT="${PORT_3}"
export LEFT_LEADER_PORT="${PORT_1}"


export LEFT_WRIST_CAM="/dev/v4l/by-path/请替换左腕相机"
export RIGHT_WRIST_CAM="/dev/v4l/by-path/请替换右腕相机"
export FRONT_CAM="/dev/v4l/by-path/请替换前视相机"

export LEFT_CAM_CFG='{ wrist: {type: opencv, index_or_path: "'"${LEFT_WRIST_CAM}"'", width: 640, height: 480, fps: 30, fourcc: "MJPG"}}'
export RIGHT_CAM_CFG='{ wrist: {type: opencv, index_or_path: "'"${RIGHT_WRIST_CAM}"'", width: 640, height: 480, fps: 30, fourcc: "MJPG"}, front: {type: opencv, index_or_path: "'"${FRONT_CAM}"'", width: 640, height: 480, fps: 30, fourcc: "MJPG"}}'
