import asyncio
import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .simulation import Simulation
from .protocol import (
    config_message,
    error_message,
    frame_binary,
    metrics_message,
    parse_client_message,
    replicator_message,
    status_message,
)

np.seterr(over="ignore", under="ignore")

app = FastAPI(title="Artificial Life Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from web/out/ if it exists
_static_dir = Path(__file__).resolve().parent.parent / "web" / "out"
if _static_dir.is_dir():
    app.mount("/app", StaticFiles(directory=str(_static_dir), html=True), name="static")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    sim: Simulation | None = None
    running_event = asyncio.Event()
    stop_event = asyncio.Event()
    sim_task: asyncio.Task | None = None
    replicator_sent = False

    async def run_simulation():
        nonlocal replicator_sent
        assert sim is not None

        await ws.send_text(status_message("warming_up"))

        # Run first epoch to trigger Numba JIT warmup
        first_metrics = await asyncio.to_thread(sim.step)
        await ws.send_text(metrics_message(**first_metrics))
        if sim.replicator_epoch is not None and not replicator_sent:
            await ws.send_text(replicator_message(sim.replicator_epoch))
            replicator_sent = True
        frame_data = await asyncio.to_thread(sim.get_frame_data)
        await ws.send_bytes(frame_binary(first_metrics["epoch"], frame_data))

        await ws.send_text(status_message("running"))

        while not sim.is_complete:
            if stop_event.is_set():
                return

            if not running_event.is_set():
                await ws.send_text(status_message("paused"))
                await running_event.wait()
                if stop_event.is_set():
                    return
                await ws.send_text(status_message("running"))

            metrics = await asyncio.to_thread(sim.step)

            if sim.replicator_epoch is not None and not replicator_sent:
                await ws.send_text(replicator_message(sim.replicator_epoch))
                replicator_sent = True

            epoch = metrics["epoch"]
            if epoch % 10 == 0 or sim.is_complete:
                await ws.send_text(metrics_message(**metrics))

            if epoch % 20 == 0 or sim.is_complete:
                frame_data = await asyncio.to_thread(sim.get_frame_data)
                await ws.send_bytes(frame_binary(epoch, frame_data))

            await asyncio.sleep(0)

        await ws.send_text(status_message("completed"))

    try:
        while True:
            data = await ws.receive_text()
            msg = parse_client_message(data)
            msg_type = msg.get("type")

            if msg_type == "start":
                # Stop any existing simulation
                if sim_task is not None and not sim_task.done():
                    stop_event.set()
                    running_event.set()
                    await sim_task

                stop_event.clear()
                running_event.set()
                replicator_sent = False

                params = msg.get("params", {})
                try:
                    sim = Simulation(
                        seed=params.get("seed", 1),
                        grid_width=params.get("grid_width", 240),
                        grid_height=params.get("grid_height", 135),
                        mutation_rate=params.get("mutation_rate", 0.024 / 100.0),
                        num_epochs=params.get("num_epochs", 7500),
                        replicator_threshold=params.get("replicator_threshold", 5.0),
                    )
                except Exception as e:
                    await ws.send_text(error_message(str(e)))
                    continue

                await ws.send_text(config_message(
                    sim.grid_width, sim.grid_height, sim.num_epochs
                ))
                sim_task = asyncio.create_task(run_simulation())

            elif msg_type == "pause":
                running_event.clear()

            elif msg_type == "resume":
                running_event.set()

            elif msg_type == "stop":
                if sim_task is not None and not sim_task.done():
                    stop_event.set()
                    running_event.set()
                    await sim_task
                await ws.send_text(status_message("stopped"))

            elif msg_type == "step":
                if sim is not None and not sim.is_complete:
                    count = msg.get("count", 1)
                    for _ in range(count):
                        if sim.is_complete:
                            break
                        metrics = await asyncio.to_thread(sim.step)
                        await ws.send_text(metrics_message(**metrics))
                        if sim.replicator_epoch is not None and not replicator_sent:
                            await ws.send_text(replicator_message(sim.replicator_epoch))
                            replicator_sent = True
                    frame_data = await asyncio.to_thread(sim.get_frame_data)
                    await ws.send_bytes(frame_binary(metrics["epoch"], frame_data))
                    if sim.is_complete:
                        await ws.send_text(status_message("completed"))

            elif msg_type == "set_mutation_rate":
                if sim is not None:
                    sim.set_mutation_rate(msg.get("value", sim.mutation_rate))

            else:
                await ws.send_text(error_message(f"unknown message type: {msg_type}"))

    except WebSocketDisconnect:
        if sim_task is not None and not sim_task.done():
            stop_event.set()
            running_event.set()
            sim_task.cancel()
    except Exception as e:
        if sim_task is not None and not sim_task.done():
            stop_event.set()
            running_event.set()
            sim_task.cancel()
        try:
            await ws.send_text(error_message(str(e)))
        except Exception:
            pass
