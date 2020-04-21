import asyncio
import websockets
import json
from config import config
import logging

logging.basicConfig(level=logging.INFO)


# TODO: properly shard and share connection state
connection_pool = []


async def handle_websocket(websocket, path):
    global connection_pool
    logging.info("doThings: invoked")
    connection_pool.append(websocket)
    async for message in websocket:
        logging.info(message)
        for client_ws in connection_pool:
            is_open = client_ws.state == websockets.protocol.State.OPEN
            # TODO: remove it from the pool if is_open is false
            if is_open and client_ws != websocket:
                await client_ws.send(message)
        #await websocket.send(json.dumps(result))


def main():
    logging.info("Starting WS on port %d" % config.MY_WS_PORT)
    wsserver = websockets.serve(handle_websocket,
        "0.0.0.0", config.MY_WS_PORT)
    asyncio.get_event_loop().run_until_complete(wsserver)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()
