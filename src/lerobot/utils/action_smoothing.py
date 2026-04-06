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

from dataclasses import dataclass, field
from numbers import Real
from typing import Any

@dataclass
class ExponentialActionSmoother:
    """Applies a simple EMA to teleop actions to reduce joint jitter."""

    alpha: float = 1.0
    smooth_gripper: bool = False
    _previous_action: dict[str, float] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if not (0.0 < self.alpha <= 1.0):
            raise ValueError("`alpha` must be in the range (0, 1].")

    def reset(self) -> None:
        self._previous_action.clear()

    def _should_smooth(self, key: str, value: Any) -> bool:
        if isinstance(value, bool) or not isinstance(value, Real):
            return False
        if not self.smooth_gripper and "gripper" in key:
            return False
        return True

    def __call__(self, action: dict[str, Any]) -> dict[str, Any]:
        if self.alpha >= 1.0:
            return action

        smoothed_action: dict[str, Any] = {}
        next_previous_action: dict[str, float] = {}

        for key, value in action.items():
            if not self._should_smooth(key, value):
                smoothed_action[key] = value
                continue

            current_value = float(value)
            previous_value = self._previous_action.get(key)
            if previous_value is None:
                smoothed_value = current_value
            else:
                smoothed_value = self.alpha * current_value + (1.0 - self.alpha) * previous_value

            smoothed_action[key] = smoothed_value
            next_previous_action[key] = smoothed_value

        self._previous_action = next_previous_action
        return smoothed_action
