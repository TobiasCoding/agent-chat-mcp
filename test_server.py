#!/usr/bin/env python3
"""End-to-end regression test for the agent-chat stdio MCP server."""
import json
import os
import subprocess
import sys
import tempfile
import concurrent.futures
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    with tempfile.TemporaryDirectory(prefix="agent-chat-test-") as directory:
        env = os.environ | {"AGENT_CHAT_DB": str(Path(directory) / "messages.sqlite3")}
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "post_message", "arguments": {"room": "release", "author": "alice", "message": "hello", "recipients": ["bob"], "metadata": {"priority": "high"}}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "post_message", "arguments": {"room": "release", "author": "bob", "message": "ack"}}},
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "list_messages", "arguments": {"room": "release", "after_id": 1}}},
            {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "list_rooms", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "list_messages", "arguments": {"room": "release", "limit": -1}}},
        ]
        process = subprocess.run(
            [str(ROOT / "run.sh")], input="".join(json.dumps(request) + "\n" for request in requests),
            text=True, capture_output=True, env=env, check=True,
        )
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    assert len(responses) == 7, responses
    assert responses[0]["result"]["serverInfo"]["name"] == "agent-chat"
    assert {tool["name"] for tool in responses[1]["result"]["tools"]} == {"post_message", "list_messages", "list_rooms"}
    assert responses[2]["result"]["structuredContent"]["id"] == 1
    assert responses[3]["result"]["structuredContent"]["id"] == 2
    assert responses[4]["result"]["structuredContent"]["messages"][0]["author"] == "bob"
    assert responses[5]["result"]["structuredContent"]["rooms"][0]["message_count"] == 2
    assert responses[6]["result"]["isError"] is True
    concurrency_db = Path(directory) / "concurrency.sqlite3"

    def post_concurrently(number):
        request = {"jsonrpc": "2.0", "id": number, "method": "tools/call", "params": {"name": "post_message", "arguments": {"room": "concurrency", "author": f"client-{number}", "message": "ok"}}}
        concurrent_env = env | {"AGENT_CHAT_DB": str(concurrency_db)}
        completed = subprocess.run([str(ROOT / "run.sh")], input=json.dumps(request) + "\n", text=True, capture_output=True, env=concurrent_env, check=True)
        response = json.loads(completed.stdout)
        assert not response["result"].get("isError"), response
        return response["result"]["structuredContent"]["id"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        ids = list(executor.map(post_concurrently, range(1, 25)))
    assert len(set(ids)) == 24
    print("PASS: stdio lifecycle, discovery, persistence, cursor, rooms, input validation")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
