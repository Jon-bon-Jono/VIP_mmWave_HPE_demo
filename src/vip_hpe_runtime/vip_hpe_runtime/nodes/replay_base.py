"""Shared replay-node utilities."""

from __future__ import annotations

from pathlib import Path

from vip_hpe_runtime.replay.living_lab import LivingLabSubjectReplay


class ReplayCursor:
    """Simple frame cursor with loop/end-index support."""

    def __init__(self, replay: LivingLabSubjectReplay, start_index: int, end_index: int, loop: bool):
        self.replay = replay
        self.start_index = int(start_index)
        self.end_index = int(end_index) if int(end_index) >= 0 else len(replay)
        self.end_index = min(self.end_index, len(replay))
        self.loop = bool(loop)
        self.current_index = self.start_index
        if self.start_index < 0 or self.start_index >= len(replay):
            raise ValueError(f'start_index {self.start_index} is outside replay length {len(replay)}')
        if self.end_index <= self.start_index:
            raise ValueError(f'end_index {self.end_index} must be greater than start_index {self.start_index}')

    def next_frame(self):
        if self.current_index >= self.end_index:
            if not self.loop:
                return None
            self.current_index = self.start_index
        frame = self.replay[self.current_index]
        self.current_index += 1
        return frame


def load_replay_or_raise(pickle_path: str, gtrack_filtering: bool = True, fps_fallback: float = 10.0) -> LivingLabSubjectReplay:
    path = Path(pickle_path).expanduser()
    if not pickle_path:
        raise ValueError('pickle_path parameter is empty')
    return LivingLabSubjectReplay(path, gtrack_filtering=gtrack_filtering, fps_fallback=fps_fallback)
