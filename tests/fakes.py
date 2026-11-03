"""A stand-in for the YAM rig: three named cameras whose pixels encode the frame number."""

from __future__ import annotations

from typing import Any

import numpy as np
from inspect_robots import (
    Action,
    ActionSemantics,
    Box,
    CameraSpec,
    EmbodimentInfo,
    Observation,
    ObservationSpace,
    Scene,
    StepResult,
)

SIZE = 6


def frame_image(t: int, camera: str) -> np.ndarray[Any, Any]:
    """The image camera ``camera`` shows at frame ``t`` (distinct per frame and camera)."""
    offset = {"top_cam": 0, "left_cam": 1, "right_cam": 2}.get(camera, 3)
    return np.full((SIZE, SIZE, 3), (t * 4 + offset) % 256, dtype=np.uint8)


class ThreeCameraRig:
    """Moves nothing; reports three cameras and optionally claims success after ``done_after``."""

    def __init__(
        self,
        *,
        cameras: tuple[str, ...] = ("top_cam", "left_cam", "right_cam"),
        done_after: int | None = None,
    ) -> None:
        self.cameras = cameras
        self.done_after = done_after
        self.t = 0
        self.info = EmbodimentInfo(
            name="three_camera_rig",
            action_space=Box(
                shape=(2,), semantics=ActionSemantics(control_mode="eef_delta_pos", frame="world")
            ),
            observation_space=ObservationSpace(
                cameras=tuple(
                    CameraSpec(name=c, height=SIZE, width=SIZE, channels=3) for c in cameras
                ),
            ),
            control_hz=10.0,
            is_simulated=True,
            capabilities=frozenset(),
        )

    def reset(self, scene: Scene, *, seed: int | None = None) -> Observation:
        self.t = 0
        return self._observe()

    def step(self, action: Action) -> StepResult:
        self.t += 1
        done = self.done_after is not None and self.t >= self.done_after
        return StepResult(
            observation=self._observe(),
            reward=0.0,
            terminated=done,
            termination_reason="success" if done else None,
            truncated=False,
            info={},
        )

    def close(self) -> None:
        return None

    def _observe(self) -> Observation:
        return Observation(
            images={c: frame_image(self.t, c) for c in self.cameras},
            state={"t": np.array([self.t], dtype=np.float64)},
        )
