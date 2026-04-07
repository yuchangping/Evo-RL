#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

LOCAL_ENV_SH="${LOCAL_ENV_SH:-${REPO_ROOT}/env.sh}"
REMOTE_ENV_SH="${REMOTE_ENV_SH:-/data2/ycp/Evo-RL/env.sh}"

if [[ ! -f "${LOCAL_ENV_SH}" ]]; then
  echo "Local env.sh not found: ${LOCAL_ENV_SH}" >&2
  exit 1
fi

source "${LOCAL_ENV_SH}"

if [[ -z "${H100_USER:-}" || -z "${H100_HOST:-}" ]]; then
  echo "Please set H100_USER and H100_HOST before running this script." >&2
  echo 'Example: H100_USER=neu_lab1 H100_HOST=10.0.0.8 bash scripts/sync_to_h100.sh all' >&2
  exit 1
fi

SYNC_TARGET="${1:-all}"
REMOTE_SSH_TARGET="${H100_USER}@${H100_HOST}"

REMOTE_SERVER_DATA_ROOT="$(
  ssh "${REMOTE_SSH_TARGET}" "bash -lc 'source \"${REMOTE_ENV_SH}\" >/dev/null 2>&1 && printf \"%s\" \"\${SERVER_DATA_ROOT}\"'"
)"

if [[ -z "${REMOTE_SERVER_DATA_ROOT}" ]]; then
  echo "Failed to resolve SERVER_DATA_ROOT on remote host via ${REMOTE_ENV_SH}" >&2
  exit 1
fi

sync_one() {
  local repo_id="$1"
  local src_dir="${LOCAL_DATA_ROOT}/${repo_id}"
  local dst_dir="${REMOTE_SERVER_DATA_ROOT}/${repo_id}"

  if [[ ! -d "${src_dir}" ]]; then
    echo "Local dataset directory does not exist: ${src_dir}" >&2
    exit 1
  fi

  echo "Syncing ${src_dir} -> ${REMOTE_SSH_TARGET}:${dst_dir}"
  ssh "${REMOTE_SSH_TARGET}" "mkdir -p '${dst_dir}'"
  rsync -avh --info=progress2 "${src_dir}/" "${REMOTE_SSH_TARGET}:${dst_dir}/"
}

case "${SYNC_TARGET}" in
  demo)
    sync_one "${DEMO_REPO_ID}"
    ;;
  round1)
    sync_one "${ROUND1_REPO_ID}"
    ;;
  merged_r1)
    sync_one "${MERGED_R1_REPO_ID}"
    ;;
  all)
    sync_one "${DEMO_REPO_ID}"
    sync_one "${ROUND1_REPO_ID}"
    ;;
  *)
    echo "Unsupported target: ${SYNC_TARGET}" >&2
    echo "Usage: bash scripts/sync_to_h100.sh [demo|round1|merged_r1|all]" >&2
    exit 1
    ;;
esac

echo "Done."
