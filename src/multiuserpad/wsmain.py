import asyncio
import websockets
import json
from config import config
import logging

from editorstate import apply_doc_edit, get_document_state
from runtime import executor


logging.basicConfig(level=logging.INFO)
RECORD_OUTPUT_FILE = "/tmp/records.json"


# TODO: properly shard and share connection state
connection_pool = []
all_actions = []


async def send_all(message, ws_to_avoid=None):
    for client_ws in connection_pool:
        is_open = client_ws.state == websockets.protocol.State.OPEN
        # TODO: remove it from the pool if is_open is false
        if is_open and client_ws is not None and client_ws != ws_to_avoid:
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


def marshal_load_response():
    replay_log = all_actions
    # TODO: remove / generalize test code:
    #replay_log = json.load(open("data/typed-c-main-2.json"))
    return json.dumps({
        "action": "load",
        "enabled": config.ENABLE_REPLAY,
        "body": get_document_state()})


def marshal_execution_response():
    stdout, stderr = executor(get_document_state())

    # TODO: generalize iostream handling past stderr/stdout
    return json.dumps({
        "action": "execute",
        "enabled": config.ENABLE_REPLAY,
        "stdout": stdout,
        "stderr": stderr})


async def handle_websocket(websocket, path):
    global connection_pool
    logging.info("handle_websocket: invoked")
    connection_pool.append(websocket)
    # ws message actions to be sent to everyone else
    actions_for_all_else = ["outputcontrol", "output", "selection"]
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
                    await send_all(raw_message, websocket)
                elif message["action"] == "replay":
                    await websocket.send(get_all_replay())
                elif message["action"] == "load":
                    await websocket.send(marshal_load_response())
                elif message["action"] == "execute":
                    execution_response = marshal_execution_response()
                    await send_all(execution_response)
                elif message["action"] in actions_for_all_else:
                    await send_all(raw_message, websocket)
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
