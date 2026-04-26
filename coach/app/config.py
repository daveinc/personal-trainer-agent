import json
import os


def load():
    try:
        with open("/data/options.json") as f:
            options = json.load(f)
        for key, value in options.items():
            os.environ.setdefault(key.upper(), str(value))
    except (FileNotFoundError, json.JSONDecodeError):
        pass
