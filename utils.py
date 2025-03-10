import json
from typing import Dict

from zepben.eas.client.eas_client import EasClient

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger()


def get_config_dir(argv):
    return argv[1] if len(argv) > 1 else "."


def get_config(config_dir):
    config = read_json_config(f"{config_dir}/config.json")
    config["feeders"] = list({f for f in config["feeders"]})
    config["forecast_years"] = list({f for f in config["forecast_years"]})
    config["scenarios"] = list({f for f in config["scenarios"]})
    return config


def get_client(config_dir):
    auth_config = read_json_config(f"{config_dir}/auth_config.json")

    return EasClient(
        host=auth_config["eas_server"]["host"],
        port=auth_config["eas_server"]["port"],
        protocol=auth_config["eas_server"]["protocol"],
        access_token=auth_config["eas_server"]["access_token"],
        verify_certificate=auth_config["eas_server"].get("verify_certificate", True),
        ca_filename=auth_config["eas_server"].get("ca_filename")
    )


def read_json_config(config_file_path: str) -> Dict:
    file = open(config_file_path)
    config_dict = json.load(file)
    file.close()
    return config_dict


def print_cancel(result):
    if "data" in result:
        print(f'work_package_id=\n{result["data"]["cancelWorkPackage"]}')
    else:
        if "404" in result["errors"][0]["message"]:
            print("No work package running with provided ID")
        else:
            print("Errors:\n", "\n".join(err["message"] for err in result['errors']))


def print_run(result):
    if "data" in result:
        print(f'work_package_id=\n{result["data"]["runWorkPackage"]}')
    else:
        print("Errors:\n", "\n".join(err["message"] for err in result['errors']))


def print_progress(result):
    logger.info("------------------------------")
    if "data" in result:
        logger.info(f'Progress: \n{str(json.dumps(result["data"]["getWorkPackageProgress"], indent=4))}')
    else:
        logger.error("Errors:\n".join(err["message"] for err in result['errors']))
    logger.info("------------------------------")
