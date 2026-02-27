# ================================
# IoT Multi-Protocol Sender Script
# Allows protocol selection from CMD
# ================================

import argparse
import datetime
import json
import random
import shlex
import socket
import subprocess
import time

import numpy as np
import requests


# List of available communication methods
METHODS = [
    "HTTP_TUTORIAL_GET",
    "HTTP_TUTORIAL_POST",
    "HTTP_SERVER_POST",
    "HTTP_SERVER_SEND_CURL",
    "UDP_SERVER_SEND",
    "TCP_SERVER_SEND",
]


def call_curl(cmd: str) -> bytes:
    """
    Executes a curl command using subprocess.
    Returns server response.
    """
    args = shlex.split(cmd)
    process = subprocess.Popen(
        args,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = process.communicate()

    # Raise error if curl failed
    if process.returncode != 0:
        raise RuntimeError(
            f"curl failed ({process.returncode}): {stderr.decode(errors='ignore')}"
        )

    return stdout


def build_payload(ID: int, Name: str) -> dict:
    """
    Generates a random IoT sensor payload.
    """
    return {
        "ID": ID,
        "Name": Name,
        "v1": random.uniform(0, 100),
        "v2": float(np.round(random.uniform(0, 100), 0)),
        "v3": random.uniform(0, 100),
        "v4": random.uniform(0, 3.3),
        "timestamp": datetime.datetime.now().timestamp(),
        "notification_category": 1,
    }


def parse_args():
    """
    Parses command-line arguments.
    Allows selecting protocol from CMD.
    """
    parser = argparse.ArgumentParser(
        description="IoT sender script (select protocol from CMD)"
    )

    parser.add_argument(
        "--method",
        choices=METHODS,
        default="HTTP_SERVER_SEND_CURL",
        help="Select communication method"
    )

    parser.add_argument("--id", type=int, default=1,
                        help="Starting device ID")

    parser.add_argument("--name", default="home",
                        help="Device/site name")

    parser.add_argument("--host", default="127.0.0.1",
                        help="Server host for TCP/UDP")

    parser.add_argument("--port", type=int, default=60000,
                        help="Server port for TCP/UDP")

    parser.add_argument("--url",
                        default="http://127.0.0.1:1880/setlevel",
                        help="HTTP server URL")

    parser.add_argument("--period", type=float, default=0.5,
                        help="Delay between transmissions (seconds)")

    return parser.parse_args()


def main():
    """
    Main program logic.
    Selects protocol and continuously sends data.
    """
    args = parse_args()

    METHOD = args.method
    ID = args.id
    Name = args.name

    print(f"Running method: {METHOD}")

    # ------------------------------
    # HTTP GET (httpbin tutorial)
    # ------------------------------
    if METHOD == "HTTP_TUTORIAL_GET":
        while True:
            payload = build_payload(ID, Name)
            response = requests.get(
                "https://httpbin.org/get", params=payload
            )
            print("Status:", response.status_code)
            print("Response:", response.text)
            time.sleep(args.period)
            ID += 1

    # ------------------------------
    # HTTP POST (httpbin tutorial)
    # ------------------------------
    elif METHOD == "HTTP_TUTORIAL_POST":
        while True:
            payload = build_payload(ID, Name)
            response = requests.post(
                "https://httpbin.org/post", data=payload
            )
            print("Status:", response.status_code)
            print("Response:", response.text)
            time.sleep(args.period)
            ID += 1

    # ------------------------------
    # HTTP POST to Node-RED server
    # ------------------------------
    elif METHOD == "HTTP_SERVER_POST":
        while True:
            payload = build_payload(ID, Name)
            response = requests.post(args.url, data=payload)
            print("Status:", response.status_code)
            print("Response:", response.text)
            time.sleep(args.period)
            ID += 1

    # ------------------------------
    # HTTP POST using curl command
    # ------------------------------
    elif METHOD == "HTTP_SERVER_SEND_CURL":
        while True:
            payload = build_payload(ID, Name)
            data_json = json.dumps(payload)

            cmd = (
                f'curl -iX POST -H "Content-Type: application/json" '
                f'-d {shlex.quote(data_json)} {shlex.quote(args.url)}'
            )

            print("Executing:", cmd)
            result = call_curl(cmd)
            print(result.decode(errors="ignore"))

            time.sleep(args.period)
            ID += 1

    # ------------------------------
    # UDP Communication
    # ------------------------------
    elif METHOD == "UDP_SERVER_SEND":
        while True:
            payload = build_payload(ID, Name)
            data = json.dumps(payload).encode("utf-8")

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(data, (args.host, args.port))

            print("UDP packet sent")
            time.sleep(args.period)
            ID += 1

    # ------------------------------
    # TCP Communication
    # ------------------------------
    elif METHOD == "TCP_SERVER_SEND":
        while True:
            payload = build_payload(ID, Name)
            data = json.dumps(payload).encode("utf-8")

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((args.host, args.port))
                s.sendall(data)
                response = s.recv(2048)

            print("Server response:", response.decode(errors="ignore"))
            time.sleep(args.period)
            ID += 1


# Run program
if __name__ == "__main__":
    main()

"""
python send.py --method UDP_SERVER_SEND --host 127.0.0.1 --port 60000 --period 0.5
python send.py --method TCP_SERVER_SEND --host 127.0.0.1 --port 60000 --period 0.5
python send.py --method HTTP_SERVER_POST --url http://127.0.0.1:1880/setlevel --period 1
"""