import asyncio
import json
import socket
from typing import Set

import websockets

from app.config.schema import SharedState


async def handler(websocket, path, shared: SharedState, clients: Set):
    clients.add(websocket)
    try:
        # Send initial params
        await websocket.send(json.dumps({"type": "params", "data": shared.params}))
        async for message in websocket:
            try:
                data = json.loads(message)
            except Exception:
                continue
            msg_type = data.get("type")
            if msg_type == "slider":
                key = data.get("id")
                value = data.get("value")
                if key is not None:
                    shared.set_param(key, value)
            elif msg_type == "trigger":
                action = data.get("action")
                if action == "record":
                    shared.record_request = True
            # Broadcast updated params to all
            for c in list(clients):
                if c.open:
                    await c.send(json.dumps({"type": "params", "data": shared.params}))
    finally:
        clients.discard(websocket)


def run_websocket_server(shared: SharedState):
    host = shared.config.get("network", {}).get("host", "0.0.0.0")
    port = int(shared.config.get("network", {}).get("ws_port", 8765))
    clients: Set = set()

    async def _main():
        async with websockets.serve(lambda ws, p: handler(ws, p, shared, clients), host, port):
            print(f"WebSocket server listening on ws://{socket.gethostbyname(socket.gethostname())}:{port}")
            await asyncio.Future()  # run forever

    asyncio.run(_main())
