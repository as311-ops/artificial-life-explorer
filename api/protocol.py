import json
import struct

# --- Client -> Server message parsing ---

def parse_client_message(raw: str) -> dict:
    return json.loads(raw)


# --- Server -> Client text messages ---

def metrics_message(epoch: int, opcode_percent: float, shannon_entropy: float) -> str:
    return json.dumps({
        "type": "metrics",
        "epoch": epoch,
        "opcode_percent": opcode_percent,
        "shannon_entropy": shannon_entropy,
    })


def status_message(state: str) -> str:
    return json.dumps({"type": "status", "state": state})


def replicator_message(epoch: int) -> str:
    return json.dumps({"type": "replicator", "epoch": epoch})


def error_message(message: str) -> str:
    return json.dumps({"type": "error", "message": message})


def config_message(grid_width: int, grid_height: int, num_epochs: int) -> str:
    return json.dumps({
        "type": "config",
        "grid_width": grid_width,
        "grid_height": grid_height,
        "num_epochs": num_epochs,
    })


# --- Server -> Client binary frame ---

def frame_binary(epoch: int, cell_data: bytes) -> bytes:
    return struct.pack(">I", epoch) + cell_data
