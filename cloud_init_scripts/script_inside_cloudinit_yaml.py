#!/usr/bin/env python3
import argparse
import logging
import sys
import subprocess
import pathlib
import urllib.request
logger = logging.getLogger("script_inside_cloudinit_yaml.py")
# the string contents get replaced by the script that generates the cloud-init yaml
REGION_LANG = "___REGION_LANG___"
REGION_COUNTRY = "___REGION_COUNTRY___"
DOWNLOAD_URL = "___DOWNLOAD_URL___"
RSYNC_URL = "__RSYNC_URL__"
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
    try:
        subprocess_result = subprocess.run(python_run_bootstrap_args, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error("error calling the python script we downloaded. Exception: `%s`, output: `%s`, stderr: `%s`",
            e, e.output, e.stderr)
        raise e
    # `output` only exists on CalledProcessError ? lol, you have to use `stdout`
    logger.info("---------------------------")
    logger.info("subprocess completed successfully: \n\n`%s`", subprocess_result.stdout.decode("utf-8"))
    logger.info("---------------------------")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="cloudinit script that bootstraps everything else")
    parsed_args = parser.parse_args()
    # setup logging stuff
    root_logger = logging.getLogger()
    logging_formatter = logging.Formatter("%(asctime)s %(threadName)-10s %(name)-20s %(levelname)-8s: %(message)s")
    root_logger.setLevel("INFO")
    # this folder should match what bootstrap_wpull creates
    # create output folder
    root_folder = pathlib.Path("~/psstore").expanduser().resolve()
    root_folder.mkdir(exist_ok=True)
    output_folder = root_folder / f"{REGION_LANG}-{REGION_COUNTRY}_python38_pex"
    output_folder.mkdir(exist_ok=True)
    log_path = output_folder / f"script_inside_cloudinit_yaml - {REGION_LANG}-{REGION_COUNTRY} - output.log"
    # file handler
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(logging_formatter)
    root_logger.addHandler(file_handler)
    # stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging_formatter)
    root_logger.addHandler(stdout_handler)
    try:
        main(parsed_args)
    except Exception as e:
        logger.exception("Something went wrong!")
        sys.exit(1)
