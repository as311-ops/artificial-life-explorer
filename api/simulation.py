import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from main import (
    apply_background_mutation,
    build_neighborhood,
    normalize_cells,
    opcode_token_percent,
    run_epoch_pairs,
    select_pairs,
    shannon_entropy,
)


class Simulation:
    def __init__(
        self,
        seed: int,
        grid_width: int,
        grid_height: int,
        mutation_rate: float,
        num_epochs: int,
        replicator_threshold: float = 5.0,
        tape_size: int = 64,
    ):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.num_epochs = num_epochs
        self.mutation_rate = mutation_rate
        self.replicator_threshold = replicator_threshold
        self.tape_size = tape_size

        self.rng = np.random.default_rng(seed)
        self.programs = self.rng.integers(
            0, 256, size=(grid_width, grid_height, tape_size), dtype=np.uint8
        )

        self.num_programs = grid_width * grid_height
        self.flat_programs = self.programs.reshape(self.num_programs, tape_size)

        neighbors, neighbor_counts = build_neighborhood(grid_width, grid_height)
        self._neighbors = neighbors
        self._neighbor_counts = neighbor_counts

        rows = np.arange(self.num_programs, dtype=np.int32)
        self._valid_rows = rows[neighbor_counts > 0]
        self._valid_neighbor_counts = neighbor_counts[self._valid_rows]
        self._all_rows_valid = self._valid_rows.size == self.num_programs
        self._rows = rows

        self._pairs = np.empty((self.num_programs // 2, 2), dtype=np.int32)
        self._proposals = np.empty(self.num_programs, dtype=np.int32)
        self._taken = np.empty(self.num_programs, dtype=np.uint8)

        self.current_epoch = 0
        self._replicator_epoch: int | None = None
        self._start_time = time.monotonic()

    def step(self) -> dict:
        order = self.rng.permutation(self.num_programs).astype(np.int32, copy=False)

        if self._all_rows_valid:
            choices = self.rng.integers(0, self._neighbor_counts)
            self._proposals[:] = self._neighbors[self._rows, choices]
        else:
            self._proposals.fill(-1)
            choices = self.rng.integers(0, self._valid_neighbor_counts)
            self._proposals[self._valid_rows] = self._neighbors[self._valid_rows, choices]

        pair_count = select_pairs(order, self._proposals, self._pairs, self._taken)
        run_epoch_pairs(self.flat_programs, self._pairs, pair_count)
        apply_background_mutation(self.programs, self.mutation_rate, self.rng)

        opcode_pct = opcode_token_percent(self.programs)
        entropy = shannon_entropy(self.programs)

        if self._replicator_epoch is None and opcode_pct >= self.replicator_threshold:
            self._replicator_epoch = self.current_epoch

        result = {
            "epoch": self.current_epoch,
            "opcode_percent": round(opcode_pct, 4),
            "shannon_entropy": round(entropy, 4),
        }
        self.current_epoch += 1
        return result

    def get_frame_data(self) -> bytes:
        return normalize_cells(self.programs).tobytes()

    def set_mutation_rate(self, rate: float):
        self.mutation_rate = rate

    @property
    def is_complete(self) -> bool:
        return self.current_epoch >= self.num_epochs

    @property
    def replicator_epoch(self) -> int | None:
        return self._replicator_epoch
