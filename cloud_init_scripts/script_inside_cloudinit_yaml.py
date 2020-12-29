#!/usr/bin/env python3
import argparse
import logging
import sys
import subprocess
import pathlib
import urllib.request
logging.basicConfig(level="INFO")
logger = logging.getLogger()
def download_script(url, path):
    logger.info("downloading `%s` to `%s`", url, path)
    response = urllib.request.urlopen(url)
    CHUNK = 16 * 1024
    with open(path, 'wb') as f:
        while True:
            chunk = response.read(CHUNK)
            if not chunk:
                break
            f.write(chunk)
    logger.info("download complete")
def main(args):
    # the string contents get replaced by the script that generates the cloud-init yaml
    REGION_LANG = "___REGION_LANG___"
    REGION_COUNTRY = "___REGION_COUNTRY___"
    DOWNLOAD_URL = "___DOWNLOAD_URL___"
    root_folder = pathlib.Path("~/psstore").expanduser().resolve()
    root_folder.mkdir(exist_ok=True)
    bootstrap_script_path = root_folder / "bootstrap_wpull.py"
    # download the script
    logger.info("downloading script")
    download_script(DOWNLOAD_URL, bootstrap_script_path)
    python_exe_path_str = sys.executable
    if not sys.executable:
        raise Exception("can't find python exe that executed this script?? it was `%s`".format(python_exe_path_str))
    python_run_bootstrap_args = [
        python_exe_path_str,
        bootstrap_script_path,
        "--region-lang",
        REGION_LANG,
        "--region-country",
        REGION_COUNTRY]
    # run the script that we downloaded
    logger.info("running python subprocess with args: `%s`", python_run_bootstrap_args)
    subprocess_result = subprocess.run(python_run_bootstrap_args, capture_output=True, check=True)
    logger.info("subprocess completely successfully: `%s`", subprocess_result)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="cloudinit script that bootstraps everything else")
    parsed_args = parser.parse_args()
    try:
        main(parsed_args)
    except Exception as e:
        logger.exception("Something went wrong!")
        sys.exit(1)
