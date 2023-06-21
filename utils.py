import json
from typing import Dict

from zepben.eas.client.eas_client import EasClient


def get_feeders():
    with open("feeders.txt", "r") as f:
        return list({word.strip() for word in f})


def get_client():
    auth_config = read_json_config("auth_config.json")
    return EasClient(
        host=auth_config["eas_server"]["host"],
        port=auth_config["eas_server"]["port"],
        protocol=auth_config["eas_server"]["protocol"],
        client_id=auth_config["eas_server"].get("client_id"),
        username=auth_config["eas_server"].get("username"),
        password=auth_config["eas_server"].get("password"),
        client_secret=auth_config["eas_server"].get("client_secret"),
        verify_certificate=auth_config["eas_server"].get("verify_certificate", True),
        ca_filename=auth_config["eas_server"].get("ca_filename")
    )


def read_json_config(config_file_path: str) -> Dict:
    file = open(config_file_path)
    config_dict = json.load(file)
    file.close()
    return config_dict
