"""
argument parser
"""
import json
import os
from typing import List
from argparse import ArgumentParser

from exceptions import (
    InvalidFileLocationException,
    InvalidConfigException,
)


def parse_file_loc(file_loc) -> List:
    parsed_file_loc_list = []
    if os.path.isdir(file_loc):
        for path in os.listdir(file_loc):
            full_path = os.path.join(file_loc, path)
            if os.path.isfile(full_path):
                parsed_file_loc_list.append(full_path)
        if not parsed_file_loc_list:
            raise InvalidFileLocationException(f"Folder {file_loc} is empty")

    elif os.path.isfile(file_loc):
        parsed_file_loc_list = [file_loc]
    else:
        raise InvalidFileLocationException(
            f"Could not load file(s) {file_loc} " f"for validation"
        )
    return parsed_file_loc_list


def parse_config(config) -> List:
    if os.path.isfile(config):
        with open(config, mode="r") as json_file:
            try:
                parsed_config_dict = json.load(json_file)
            except json.JSONDecodeError as json_decode_err:
                raise InvalidConfigException(
                    f"Could not load config - valid file, "
                    f"JSON decode error: {json_decode_err}"
                )
            except Exception as exc:
                raise InvalidConfigException(
                    f"Could not load config - valid file, " f"general exception: {exc}"
                )
    else:
        raise InvalidConfigException("Could not load config file - not a valid file")    
    return parsed_config_dict


def prepare_args() -> dict:
    """
    function for preparation of the CLI arguments
    :return:
    """
    args = dict()

    parser = ArgumentParser()
    parser.add_argument("-fl", "--filelocation", type=str, required=True)
    parser.add_argument("-cfg", "--configfile", type=str, required=True)
    parsed = parser.parse_args()

    parsed_file_loc = parsed.filelocation
    parsed_config = parsed.configfile
    
    args["file_loc"]: List = parse_file_loc(parsed_file_loc)
    args["config"]: List = parse_config(parsed_config)

    return args
