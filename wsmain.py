import asyncio
import websockets
import json
from config import config
import logging

logging.basicConfig(level=logging.INFO)


# TODO: properly shard and share connection state
connection_pool = []
all_actions = []

async def send_all_but_ws(message, ws_to_avoid):
    for client_ws in connection_pool:
        is_open = client_ws.state == websockets.protocol.State.OPEN
        # TODO: remove it from the pool if is_open is false
        if is_open and client_ws != ws_to_avoid:
            await client_ws.send(message)


def add_replay(message):
    if config.ENABLE_REPLAY == True:
        all_actions.append(message)


def get_all_replay():
    return json.dumps({
        "action": "replay",
        "enabled": config.ENABLE_REPLAY,
        "body": all_actions})


async def handle_websocket(websocket, path):
    global connection_pool
    logging.info("handle_websocket: invoked")
    connection_pool.append(websocket)
    async for raw_message in websocket:
        # should be edit messages from clients
        try:
            message = json.loads(raw_message)
            logging.info(message)
            if "action" in message:
                if message["action"] == "edit":
                    add_replay(raw_message)
                    # TODO: use real connection ids instead of comparing to ws
                    await send_all_but_ws(raw_message, websocket)
                elif message["action"] == "replay":
                    await websocket.send(get_all_replay())
        except json.decoder.JSONDecodeError:
            logging.info("message failed json parse")


def main():
    logging.info("Starting WS on port %d" % config.MY_WS_PORT)
    wsserver = websockets.serve(handle_websocket,
        "0.0.0.0", config.MY_WS_PORT)
    asyncio.get_event_loop().run_until_complete(wsserver)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()
