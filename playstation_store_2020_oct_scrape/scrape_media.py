import logging
import pathlib
import subprocess
import sys
import sqlite3

import arrow

logger = logging.getLogger(__name__)

def run(args):
    arg_region_lang = args.region_lang
    arg_region_country = args.region_country
    arg_rsync_url = args.rsync_url
    arg_parent_folder = args.parent_folder
    arg_db_name = args.db_name
    arg_wpull_path = args.wpull_path
    arg_rsync_password_file = args.rsync_password_file


    parent_folder_path = pathlib.Path(arg_parent_folder)

    root_folder = parent_folder_path / f"{arg_region_lang}_{arg_region_country}_media_pex"
    root_folder.mkdir(exist_ok=True)

    wpull_args_file_path = root_folder / f"wpull_args_{arg_region_lang}-{arg_region_country}_with_media.txt"

    cur_date = arrow.utcnow()
    date_str = cur_date.format("YYYY-MM-DD")
    db_path = root_folder / arg_db_name
    output_file_path = root_folder / f"wpull_output_{arg_region_lang}-{arg_region_country}_{date_str}_with_media.log"
    warc_file_path = root_folder / f"wpull_warc_{arg_region_lang}-{arg_region_country}_{date_str}_with_media"
    input_file_path = root_folder / f"wpull_input_{arg_region_lang}-{arg_region_country}_{date_str}_with_media.log"

    logger.info("writing input urls file to `%s`", input_file_path)
    with open(input_file_path, "w", encoding="utf-8") as f:
        f.write("\n")

    # write arguments file
    logger.info("writing input urls file to `%s`", wpull_args_file_path)
    with open(wpull_args_file_path, "w", encoding="utf-8") as f:
        f.write("--database\n")
        f.write(f"{db_path}\n")
        f.write("--output-file\n")
        f.write(f"{output_file_path}\n")
        f.write("--waitretry\n")
        f.write("30\n")
        f.write("--no-robots\n")
        f.write("--warc-file\n")
        f.write(f"{warc_file_path}\n")
        f.write("--warc-max-size\n")
        f.write("5368709000\n")
        f.write("--warc-header\n")
        f.write(f"description:playstation 2020/2021 JSON API scrape for the '{arg_region_lang}-{arg_region_country}' region\n")
        f.write("--warc-header\n")
        f.write(f"date:{date_str}\n")
        f.write("--warc-header\n")
        f.write(f"playstation_store_region:{arg_region_lang}-{arg_region_country}\n")
        f.write("--warc-header\n")
        f.write("playstation_store_scrape_type:media\n")
        f.write("--html-parser\n")
        f.write("libxml2-lxml\n")
        f.write("--warc-tempdir\n")
        f.write(f"{root_folder}\n")
        f.write("--delete-after\n")
        f.write("--very-quiet\n")
        f.write("--warc-append\n")
        f.write("--input-file\n")
        f.write(f"{input_file_path}\n")
        f.write("--recursive\n")
        f.write("--span-hosts\n")

    # rsync database over

    rsync_cmd = [
        "/usr/bin/rsync",
        "--itemize-changes",
        "--recursive",
        "--checksum",
        "--partial",
        "--verbose",
        "--password-file",
        f"{arg_rsync_password_file}",
        arg_rsync_url,
        f"{root_folder / arg_db_name }"]


    logger.info("running rsync cmd: `%s`", rsync_cmd)
    command_result = subprocess.run(rsync_cmd, capture_output=True)
    if command_result.returncode != 0:
        logger.error("failed to run rsync command: completed process obj: `%s`", command_result)
        sys.exit(1)

    logger.info("rsync cmd completed successfully")


    logger.info("editing sqlite3 database at `%s`", db_path)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # update all of the urls we added with the wpull plugin
    # since we didn't have `--recursive` and `--span-hosts` on wpull when we ran just the JSON, they were added
    # to the database as `skipped` and the status_code column is null because wpull never attempted to download it
    # now lets set the status of those to be `todo` so wpull will download the stuff we added, but skip the stuff
    # that wpull tried to download already (aka `status_code` is not null)
    c.execute("update queued_urls set status = 'todo' where status = 'skipped' and status_code is null;")
    conn.commit()
    c.close()
    conn.close()


    # start wpull
    wpull_cmd = [
        sys.executable,
        f"{arg_wpull_path}",
        f"@{wpull_args_file_path}"
    ]


    logger.info("running wpull cmd: `%s`", wpull_cmd)

    command_result2 = subprocess.run(wpull_cmd, capture_output=True)
    if command_result2.returncode != 0:
        logger.error("failed to run wpull command: completed process obj: `%s`", command_result2)
        sys.exit(1)

    logger.info("wpull cmd completed successfully")
