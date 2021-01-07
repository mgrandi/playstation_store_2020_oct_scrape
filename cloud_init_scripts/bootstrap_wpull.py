#!/usr/bin/env python3
import argparse
import logging
import sys
import subprocess
import pathlib
import zipfile
import urllib.request
import datetime
import typing

logger = logging.getLogger("bootstrap_wpull.py")

WPULL_PEX_DOWNLOAD_URL = "http://kramidnarg.com/wpull-2.0.4a1_mgrandi.pex"
PSSTORE_2020_OCT_SCRAPE_PEX_DOWNLOAD_URL = "http://kramidnarg.com/playstation_store_2020_oct_scrape-0.1.pex"
PSSTORE_CONTENT_IDS_DOWNLOAD_URL = "https://github.com/mgrandi/playstation_content_ids/archive/master.zip"
FOLDER_INSIDE_PSSTORECONTENT_IDS_ZIP = "playstation_content_ids-master"
PSSTORE_2020_OCT_SCRAPE_PEX_DEPS_FOLDER_PREFIX = "playstation_store_2020_oct_scrape"
ROOT_FOLDER_PATH_STR = "~/psstore"
# see wpull\build\lib\wpull\errors.py:ExitStatus
#
# Attributes:
#
# generic_error (1): An unclassified serious or fatal error occurred.
# parser_error (2): A local document or configuration file could not
#     be parsed.
# file_io_error (3): A problem with reading/writing a file occurred.
# network_failure (4): A problem with the network occurred such as a DNS
#     resolver error or a connection was refused.
# ssl_verification_error (5): A server's SSL/TLS certificate was invalid.
# authentication_failure (6): A problem with a username or password.
# protocol_error (7): A problem with communicating with a server
#     occurred.
# server_error (8): The server had problems fulfilling our requests.
ACCEPTABLE_STATUS_CODES_NORMAL = [0]
ACCEPTABLE_STATUS_CODES_WPULL = [0, 4, 5, 8]

def check_completedprocess_for_acceptable_statuscodes(
    completed_process_obj:subprocess.CompletedProcess,
    acceptable_status_codes:typing.Sequence[int]):
    ''' sees if a `subprocess.CompletedProcess` object has an acceptable status code
    if not, we call subprocess.CompletedProcess.check_returncode() which will throw an exception

    @param completed_process_obj - the subprocess.CompletedProcess object to check
    @param acceptable_status_codes - the list of integers of acceptable status codes
    @throws `subprocess.CalledProcessError` if the status code is not in the acceptable list
    '''

    logger.debug("checking return code: acceptable: `%s`, CompletedProcess return code: `%s`",
        completed_process_obj.returncode, acceptable_status_codes)

    # throw an exception if the status code is not in our acceptble list
    # this assumes that 0 is always a valid status code, since `check_returncode()` won't
    # throw an exception if the status code is 0
    if not completed_process_obj.returncode in acceptable_status_codes:
        completed_process_obj.check_returncode()




def download_file(url, path):
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

    logger.info("####################################")
    logger.info("starting, with arguments `%s`", args)

    root_folder = pathlib.Path(ROOT_FOLDER_PATH_STR).expanduser().resolve()
    root_folder.mkdir(exist_ok=True)
    temp_dir = root_folder / "temp"
    temp_dir.mkdir(exist_ok=True)

    # normalize the region / country names, namely because the playstation store
    # says it supports stuff like `zh-hans-cn` but in URLs , its `zh-cn`
    # however we only need the 'normalized' ones for generating the url list
    country = args.region_country
    lang = args.region_lang
    normalized_country = country
    normalized_lang = lang
    if normalized_lang.startswith("zh"):
        normalized_lang = "zh"
        logger.info("normalizing the language tag `%s` to `%s`", lang, normalized_lang)

    # download wpull
    logger.info("downloading `wpull` PEX")
    wpull_pex_path = root_folder / "wpull.pex"
    download_file(WPULL_PEX_DOWNLOAD_URL, wpull_pex_path)

    # playstation_store_2020_oct_scrape pex
    logger.info("downloading `playstation_store_2020_oct_scrape` PEX")
    psstore_oct_scrape_pex_path = root_folder / "playstation_store_2020_oct_scrape.pex"
    download_file(PSSTORE_2020_OCT_SCRAPE_PEX_DOWNLOAD_URL, psstore_oct_scrape_pex_path)

    # download the zip archive of the master branch of playstation_content_ids git repo
    # the zip file has the folder 'playstation_content_ids-master' inside it, and then the content, so
    # just download and then extract it to the same folder
    logger.info("downloading zip of latest commit to the master branch of the `playstation_content_ids` git repo")
    ps_content_ids_zip_path = root_folder / "playstation_content_ids-master.zip"
    ps_content_ids_extract_path = root_folder
    download_file(PSSTORE_CONTENT_IDS_DOWNLOAD_URL, ps_content_ids_zip_path)
    content_ids_zip_file_obj = zipfile.ZipFile(ps_content_ids_zip_path)
    content_ids_zip_file_obj.extractall(ps_content_ids_extract_path)



    # create output folder
    output_folder = root_folder / f"{lang}-{country}_python38_pex"
    output_folder.mkdir(exist_ok=True)

    # create the arguments for generating the wpull url list
    sku_list_path = root_folder / FOLDER_INSIDE_PSSTORECONTENT_IDS_ZIP / "regions" / f"{lang}-{country}.txt.xz"
    wpull_url_list_path = output_folder / f"wpull_urls_{lang}-{country}.txt"

    logger.info("constructed the path to the SKU / content ID list to be `%s`", sku_list_path)

    create_wpull_url_list_arguments = [
        sys.executable,
        psstore_oct_scrape_pex_path,
        "generate_wpull_urls_from_content_ids",
        "--content-ids-file",
        sku_list_path,
        "--output-file",
        wpull_url_list_path,
        "--region-lang",
        normalized_lang,
        "--region-country",
        normalized_country ]

    logger.info("full arguments for generating the wpull url list: `%s`", create_wpull_url_list_arguments)

    try:
        # don't use `check=True` cause we need to check the status codes , and subprocess.run() doesn't have a built in
        # mechanism to do that
        create_wpull_url_list_result = subprocess.run(create_wpull_url_list_arguments, capture_output=True)
        check_completedprocess_for_acceptable_statuscodes(create_wpull_url_list_result, ACCEPTABLE_STATUS_CODES_NORMAL)
    except subprocess.CalledProcessError as e:
        logger.error("error generating the wpull url list: Exception: `%s`, output: `%s`, stderr: `%s`",
            e, e.output, e.stderr)
    logger.info("creation of wpull url list successful, output of running command: \n\n`%s`", create_wpull_url_list_result.stdout.decode("utf-8"))

    # now generate the arguments file and run wpull

    current_date = datetime.date.today()
    cur_date_str = current_date.strftime("%Y-%m-%d")
    lang_and_cur_date_str = f"{lang}-{country}_{cur_date_str}"
    wpull_plugin_path = root_folder / "wpull_plugin.py"
    wpull_arguments_list_file_path = output_folder / f"wpull_argument_list_{lang_and_cur_date_str}.txt"
    wpull_database_path = output_folder / f"wpull_database_{lang_and_cur_date_str}.sqlite3"
    wpull_output_log_path = output_folder / f"wpull_output_{lang_and_cur_date_str}.log"
    # don't add .warc or any other extension, wpull will add them
    wpull_warc_file_output_path = output_folder / f"psstore_json_{lang_and_cur_date_str}"


    # a pex is just a zip file, so to avoid having to download the source code or something, just open the pex
    # as a zip file and extract the script
    # however since the version number might be different later, lets iterate the children of this folder and find the
    # folder, and then create the rest of the path dynamically
    logger.info("finding wpull plugin in the pex file: `%s`", psstore_oct_scrape_pex_path)

    # get the zipfile.Path for the `.deps` folder
    psstore_oct_scrape_inside_pex_zip_deps_folder_path = zipfile.Path(psstore_oct_scrape_pex_path) / ".deps"
    if not psstore_oct_scrape_inside_pex_zip_deps_folder_path.exists():
        raise Exception("Couldn't find the .deps folder inside the pex zip: `%s`", psstore_oct_scrape_inside_pex_zip_deps_folder_path)

    # search the children of the .deps folder to find the `playstation_store_2020_oct_scrape` folder
    found_psstore_oct_scrape_deps_path = None
    for iter_zip_path in psstore_oct_scrape_inside_pex_zip_deps_folder_path.iterdir():
        tmp_name = iter_zip_path.name
        logger.debug("checking to see if the iter name `%s` starts with `%s`", tmp_name, PSSTORE_2020_OCT_SCRAPE_PEX_DEPS_FOLDER_PREFIX)

        if tmp_name.startswith(PSSTORE_2020_OCT_SCRAPE_PEX_DEPS_FOLDER_PREFIX):
            found_psstore_oct_scrape_deps_path = iter_zip_path
            logger.debug("found wpull plugin folder: `%s`", found_psstore_oct_scrape_deps_path)

    # see if we found it, if not, exit out early
    if not found_psstore_oct_scrape_deps_path:
        raise Exception("couldn't find the `playstation_store_2020_oct_scrape*` folder in the `%s` zip file",
            psstore_oct_scrape_inside_pex_zip_deps_folder_path)

    # get the zipfile.Path of the actual wpull plguin
    wpull_plugin_path_inside_pex_zip = found_psstore_oct_scrape_deps_path / "wpull_plugins" / "ps_store_json_api_wpull_plugin.py"
    if not wpull_plugin_path_inside_pex_zip.exists():
        raise Exception("couldn't find the wpull plguin python script inside the pex zip: `%s`", wpull_plugin_path_inside_pex_zip)

    # then get the wpull plugin and extract it
    logger.info("writing the wpull plugin from `%s` to `%s`", wpull_plugin_path_inside_pex_zip, wpull_plugin_path)
    with open(wpull_plugin_path, "w", encoding="utf-8") as f:
        text_to_write = wpull_plugin_path_inside_pex_zip.read_text(encoding="utf-8")
        f.write(text_to_write)

    wpull_argument_list_to_write_to_file = [
        "--database",
        str(wpull_database_path),
        "--output-file",
        str(wpull_output_log_path),
        "--waitretry",
        "30",
        "--no-robots",
        "--warc-file",
        str(wpull_warc_file_output_path),
        "--warc-max-size",
        "5368709000", # 5 GiB
        "--warc-header",
        f"description:playstation 2020/2021 JSON API scrape for the '{lang}-{country}' region",
        "--warc-header",
        f"date:{cur_date_str}",
        "--warc-header",
        f"playstation_store_region:{lang}-{country}",
        "--warc-header",
        "playstation_store_scrape_type:json",
        "--input-file",
        str(wpull_url_list_path),
        "--plugin-script",
        str(wpull_plugin_path),
        "--html-parser",
        "libxml2-lxml",
        "--warc-tempdir",
        str(temp_dir),
        "--delete-after",
        "--warc-append",
        "--very-quiet" ]

    # now write the wpull argument list to a file
    logger.info("writing wpull arguments file to `%s`", wpull_arguments_list_file_path)

    with open(wpull_arguments_list_file_path, "w", encoding="utf-8") as f:
        for iter_argument_line in wpull_argument_list_to_write_to_file:
            f.write(iter_argument_line)
            f.write("\n")

    # now finally, run wpull

    wpull_argument_list = [
        sys.executable,
        str(wpull_pex_path),
        f"@{wpull_arguments_list_file_path}"
    ]


    try:
        # don't use `check=True` cause we need to check the status codes , and subprocess.run() doesn't have a built in
        # mechanism to do that
        wpull_result = subprocess.run(wpull_argument_list, capture_output=True)
        check_completedprocess_for_acceptable_statuscodes(wpull_result, ACCEPTABLE_STATUS_CODES_WPULL)
    except subprocess.CalledProcessError as e:
        logger.error("error running wpull: Exception: `%s`, output: `%s`, stderr: `%s`",
            e, e.output, e.stderr)
        raise e

    logger.info("wpull command completed successfully , output of running command: \n\n`%s`", wpull_result.stdout.decode("utf-8"))


    logger.info("####################################")



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="script to run wpull")

    # these need to be kept in sync with the arguments that the `script_inside_cloudinit_yaml.py` script calls
    parser.add_argument("--region-lang",
        dest="region_lang",
        required=True,
        help="the first part of a region code, aka the `en` in `en-US`")
    parser.add_argument("--region-country",
        dest="region_country",
        required=True,
        help="the second part of a region code, aka the `us` in `en-US`")
    parser.add_argument("--verbose", action="store_true", help="increase logger verbosity")

    parsed_args = parser.parse_args()

    # set up logging stuff
    logging.captureWarnings(True) # capture warnings with the logging infrastructure
    root_logger = logging.getLogger()
    logging_formatter = logging.Formatter("%(asctime)s %(threadName)-10s %(name)-20s %(levelname)-8s: %(message)s")

    parsed_args = parser.parse_args()

    #############
    # duplicated code, the main() method also needs the 'output' folder so we create a reference to it
    # in that method too
    country = parsed_args.region_country
    lang = parsed_args.region_lang
    # create output folder
    root_folder = pathlib.Path(ROOT_FOLDER_PATH_STR).expanduser().resolve()
    output_folder = root_folder / f"{lang}-{country}_python38_pex"
    output_folder.mkdir(exist_ok=True)
    #############

    log_path = output_folder / f"bootstrap_wpull - {parsed_args.region_lang}-{parsed_args.region_country} - output.log"

    # file handler
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(logging_formatter)
    root_logger.addHandler(file_handler)

    # stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging_formatter)
    root_logger.addHandler(stdout_handler)


    # set logging level based on arguments
    if parsed_args.verbose:
        root_logger.setLevel("DEBUG")
    else:
        root_logger.setLevel("INFO")

    try:

        main(parsed_args)

    except Exception as e:
        logger.exception("Something went wrong!")
        sys.exit(1)
