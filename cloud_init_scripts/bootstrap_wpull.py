#!/usr/bin/env python3
import argparse
import logging
import sys
import subprocess
import pathlib
import zipfile
import urllib.request
logging.basicConfig(level="INFO")

logger = logging.getLogger()

WPULL_PEX_DOWNLOAD_URL = "http://kramidnarg.com/wpull-2.0.4a0_mgrandi.pex"
PSSTORE_2020_OCT_SCRAPE_PEX_DOWNLOAD_URL = "http://kramidnarg.com/playstation_store_2020_oct_scrape-0.1.pex"
PSSTORE_CONTENT_IDS_DOWNLOAD_URL = "https://github.com/mgrandi/playstation_content_ids/archive/master.zip"
FOLDER_INSIDE_PSSTORECONTENT_IDS_ZIP = "playstation_content_ids-master"

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

    logger.info("starting, with arguments `%s`")

    root_folder = pathlib.Path("~/psstore").expanduser().resolve()
    root_folder.mkdir(exist_ok=True)

    # download wpull
    logger.info("downloading `wpull` PEX")
    wpull_pex_path = root_folder / "wpull.pex"
    download_file(WPULL_PEX_DOWNLOAD_URL, wpull_pex_path)

    # playstation_store_2020_oct_scrape pex
    logger.info("downloading `playstation_store_2020_oct_scrape` PEX")
    psstore_oct_scrape_path = root_folder / "playstation_store_2020_oct_scrape.pex"
    download_file(PSSTORE_2020_OCT_SCRAPE_PEX_DOWNLOAD_URL, psstore_oct_scrape_path)

    # download the zip archive of the master branch of playstation_content_ids git repo
    # the zip file has the folder 'playstation_content_ids-master' inside it, and then the content, so
    # just download and then extract it to the same folder
    logger.info("downloading zip of latest commit to the master branch of the `playstation_content_ids` git repo")
    ps_content_ids_zip_path = root_folder / "playstation_content_ids-master.zip"
    ps_content_ids_extract_path = root_folder
    download_file(PSSTORE_CONTENT_IDS_DOWNLOAD_URL, ps_content_ids_zip_path)
    content_ids_zip_file_obj = zipfile.ZipFile(ps_content_ids_zip_path)
    content_ids_zip_file_obj.extractall(ps_content_ids_extract_path)

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

    # create output folder
    output_folder = root_folder / f"{lang}-{country}-python38_pex"
    output_folder.mkdir(exist_ok=True)

    # create the arguments for generating the wpull url list
    sku_list_path = root_folder / FOLDER_INSIDE_PSSTORECONTENT_IDS_ZIP / "regions" / f"{lang}-{country}.txt.xz"
    wpull_url_list_path = output_folder / f"wpull_urls_{lang}-{country}.txt"

    logger.info("constructed the path to the SKU / content ID list to be `%s`", sku_list_path)

    create_wpull_url_list_arguments = [
        sys.executable,
        psstore_oct_scrape_path,
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
        create_wpull_url_list_result = subprocess.run(create_wpull_url_list_arguments, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error("error generating the wpull url list: Exception: `%s`, output: `%s`, stderr: `%s`",
            e, e.output, e.stderr)
    logger.info("creation of wpull url list successful, result of running command: `%s`", create_wpull_url_list_result)



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

    parsed_args = parser.parse_args()

    try:

        main(parsed_args)

    except Exception as e:
        logger.exception("Something went wrong!")
        sys.exit(1)
