import asyncio
import websockets
import json
from config import config
import logging
from editorstate import apply_doc_edit

logging.basicConfig(level=logging.INFO)


RECORD_OUTPUT_FILE = "/tmp/records.json"

# TODO: properly shard and share connection state
connection_pool = []
all_actions = []


async def send_all_but_ws(message, ws_to_avoid):
    for client_ws in connection_pool:
        is_open = client_ws.state == websockets.protocol.State.OPEN
        # TODO: remove it from the pool if is_open is false
        if is_open and client_ws != ws_to_avoid:
            await client_ws.send(message)


def get_edit_contents(message):
    result = None
    try:
        parsed = json.loads(message)
        if "contents" in parsed:
            result = parsed["contents"]
    except json.decoder.JSONDecodeError:
        pass
    return result


def add_replay(message):
    if config.ENABLE_REPLAY == True:
        all_actions.append(message)
        parsed = get_edit_contents(message)
        if parsed is not None:
            try:
                apply_doc_edit(parsed)
            except Exception as e:
                # TODO: don't catch Exception
                print("Caught Exception from apply_doc_edit")
                print(e)


def get_all_replay():
    replay_log = all_actions
    # TODO: remove / generalize test code:
    #replay_log = json.load(open("data/typed-c-main-2.json"))
    return json.dumps({
        "action": "replay",
        "enabled": config.ENABLE_REPLAY,
        "body": replay_log})


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
                    # TODO: add client_id
                    add_replay(raw_message)
                    # TODO: use real connection ids instead of comparing to ws
                    await send_all_but_ws(raw_message, websocket)
                elif message["action"] == "replay":
                    await websocket.send(get_all_replay())
                elif message["action"] == "dump":
                    json.dump(all_actions, open(RECORD_OUTPUT_FILE, "w"))
                    logging.info("dumped in %s" % RECORD_OUTPUT_FILE)
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
