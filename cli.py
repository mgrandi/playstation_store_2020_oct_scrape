#!/usr/bin/env python3

# library imports
import argparse
import logging
import sys
import pathlib
import re

# third party imports
from warcio.capture_http import capture_http
import requests  # requests must be imported after capture_http
import arrow
import attr
import logging_tree

# self imports
from playstation_store_2020_oct_scrape import scrape
from playstation_store_2020_oct_scrape import warcio_scrape
from playstation_store_2020_oct_scrape import get_cloudinit_files
from playstation_store_2020_oct_scrape import create_config_and_instances
from playstation_store_2020_oct_scrape import rsync_files_from_droplets
from playstation_store_2020_oct_scrape import get_errored_items_from_log
from playstation_store_2020_oct_scrape import generate_wpull_urls_from_content_ids


class ArrowLoggingFormatter(logging.Formatter):
    ''' logging.Formatter subclass that uses arrow, that formats the timestamp
    to the local timezone (but its in ISO format)
    '''

    def formatTime(self, record, datefmt=None):
        return arrow.get("{}".format(record.created), "X").to("local").isoformat()


def isValidNewFileLocation(filePath):
    ''' see if the file path given to us by argparse is a file
    @param filePath - the filepath we get from argparse
    @return the filepath as a pathlib.Path() if it is a file, else we raise a ArgumentTypeError'''

    path_maybe = pathlib.Path(filePath)
    path_resolved = None

    # try and resolve the path
    try:
        path_resolved = path_maybe.resolve(strict=False).expanduser()

    except Exception as e:
        raise argparse.ArgumentTypeError("Failed to parse `{}` as a path: `{}`".format(filePath, e))

    if not path_resolved.parent.exists():
        raise argparse.ArgumentTypeError("The parent directory of  `{}` doesn't exist!".format(path_resolved))

    return path_resolved


def isRegexType(regex_str):
    '''
    see if the given string is a valid regex
    @param regex_str - the regex string we get from argparse
    @return the compiled regex object if its valid else we raise an ArgumentTypeError

    '''

    obj = None

    try:

        obj = re.compile(regex_str)
    except Exception as e:

        raise argparse.ArgumentTypeError("Failed to compile the string `{}` as a regex: `{}`".format(regex_str, e))

    return obj


def isFileType(strict=True):
    def _isFileType(filePath):
        ''' see if the file path given to us by argparse is a file
        @param filePath - the filepath we get from argparse
        @return the filepath as a pathlib.Path() if it is a file, else we raise a ArgumentTypeError'''

        path_maybe = pathlib.Path(filePath)
        path_resolved = None

        # try and resolve the path
        try:
            path_resolved = path_maybe.resolve(strict=strict).expanduser()

        except Exception as e:
            raise argparse.ArgumentTypeError("Failed to parse `{}` as a path: `{}`".format(filePath, e))

        # double check to see if its a file
        if strict:
            if not path_resolved.is_file():
                raise argparse.ArgumentTypeError("The path `{}` is not a file!".format(path_resolved))

        return path_resolved
    return _isFileType

def isDirectoryType(filePath):
    ''' see if the file path given to us by argparse is a directory
    @param filePath - the filepath we get from argparse
    @return the filepath as a pathlib.Path() if it is a directory, else we raise a ArgumentTypeError'''

    path_maybe = pathlib.Path(filePath)
    path_resolved = None

    # try and resolve the path
    try:
        path_resolved = path_maybe.resolve(strict=True).expanduser()

    except Exception as e:
        raise argparse.ArgumentTypeError("Failed to parse `{}` as a path: `{}`".format(filePath, e))

    # double check to see if its a file
    if not path_resolved.is_dir():
        raise argparse.ArgumentTypeError("The path `{}` is not a file!".format(path_resolved))

    return path_resolved

if __name__ == "__main__":
    # if we are being run as a real program

    parser = argparse.ArgumentParser(
        description="scrape the playstation games site",
        epilog="Copyright 2020-10-24 - Mark Grandi",
        fromfile_prefix_chars='@')

    parser.add_argument("--log-to-file-path", dest="log_to_file_path", type=isFileType(False), help="log to the specified file")
    parser.add_argument("--verbose", action="store_true", help="Increase logging verbosity")
    parser.add_argument("--no-stdout", dest="no_stdout", action="store_true", help="if true, will not log to stdout" )


    subparsers = parser.add_subparsers(help="sub-command help" )

    scrape_urls_parser = subparsers.add_parser("scrape_urls", help="Scrape URLs to JSON")
    scrape_urls_parser.add_argument('--outfile', dest="outfile", required=True, type=isValidNewFileLocation, help="where to save the JSON file containing the URLs")
    scrape_urls_parser.set_defaults(func_to_run=scrape.get_games_list)


    wpull_parser = subparsers.add_parser("wpull_urls", help="download URLs with wpull")
    wpull_parser.add_argument("--url-list", dest="url_list", required=True, type=isFileType(), help="the list of urls to download")
    wpull_parser.add_argument("--wpull-binary", dest="wpull_binary", required=True, type=isFileType(), help="the path to wpull")
    wpull_parser.add_argument("--warc-output-folder", dest="warc_output_folder", required=True, type=isDirectoryType, help="where to store the resulting WARCs")
    wpull_parser.set_defaults(func_to_run=scrape.wpull_games_list)


    warcio_parser = subparsers.add_parser("warcio_scrape", help="download urls via warcio")
    warcio_parser.add_argument("--sku-list", dest="sku_list", required=True, type=isFileType(), help="the list of skus to download")
    warcio_parser.add_argument("--region-lang", dest="region_lang", required=True, help="the first part of a region code, aka the `en` in `en-US`")
    warcio_parser.add_argument("--region-country", dest="region_country", required=True, help="the second part of a region code, aka the `us` in `en-US`")
    warcio_parser.add_argument("--warc-output-file", dest="warc_output_file", type=isFileType(False),
        help="where to save the warc file, include 'warc.gz' in this name please")
    warcio_parser.add_argument("--media-files-output-file", dest="media_files_output_file", type=isFileType(False),
        help="where to save the list of media urls we discovered")
    warcio_parser.set_defaults(func_to_run=warcio_scrape.do_warcio_scrape)



    cloudinit_parser = subparsers.add_parser("get_cloudinit_files", help="get files for cloudinit")
    cloudinit_parser.add_argument("--sku-list", dest="sku_list", required=True, help="newline delimited list of skus")
    cloudinit_parser.add_argument("--region-lang", dest="region_lang", required=True, help="the first part of a region code, aka the `en` in `en-US`")
    cloudinit_parser.add_argument("--region-country", dest="region_country", required=True, help="the second part of a region code, aka the `us` in `en-US`")
    cloudinit_parser.add_argument("--output-folder", dest="output_folder", required=True, type=isDirectoryType, help="where to store the resulting files")
    cloudinit_parser.set_defaults(func_to_run=get_cloudinit_files.get_cloudinit_files)


    create_config_and_instances_parser = subparsers.add_parser("create_config_and_instances", help="given a list of content-id files , create the config and then create DO instances")
    create_config_and_instances_parser.add_argument("--digital-ocean-token", dest="digital_ocean_token", required=True,  help="the token to login to the DO API")
    create_config_and_instances_parser.add_argument("--content-id-files-folder", dest="content_id_files_folder", required=True, type=isDirectoryType,
        help="the folder of the `en-us.txt` like files that have the list of content ids")
    create_config_and_instances_parser.add_argument("--cloudinit-config-output-folder", dest="cloudinit_config_output_folder",
        required=True, type=isDirectoryType, help="where to store the generated cloudinit config")
    create_config_and_instances_parser.add_argument("--machine-starting-id", dest="machine_starting_id",
        required=True, type=int, help="the starting number for naming the droplets sequentially")
    create_config_and_instances_parser.add_argument("--machine-name-prefix", dest="machine_name_prefix",
        required=True, help="the prefix added to the name of each droplet we end up creating")
    create_config_and_instances_parser.add_argument("--machine-username", dest="machine_username",
        required=True, help="the username of the main user account")
    create_config_and_instances.add_argument("--machine-password", dest="machine_password",
        required=True, help="the password of the main user account")
    create_config_and_instances_parser.add_argument("--ssh-key-fingerprint", dest="ssh_key_fingerprints", action="extend",
        required=True, help="the ssh key fingerprint to use to bootstrap the digital ocean droplet, can be provided multiple times")
    create_config_and_instances_parser.set_defaults(func_to_run=create_config_and_instances.run)


    rsync_files_parser = subparsers.add_parser("rsync_files_from_droplets", help="for every droplet specified, rsync files over to a local folder")
    rsync_files_parser.add_argument("--username", required=True, help="the username to log into the drolets")
    rsync_files_parser.add_argument("--rsync-binary", dest="rsync_binary", required=True, type=isFileType(True), help="path to the rsync binary")
    rsync_files_parser.add_argument("--digital-ocean-token", dest="digital_ocean_token", required=True,  help="the token to login to the DO API")
    rsync_files_parser.add_argument("--name-regex", dest="name_regex", required=True, type=isRegexType, help="regex for the names to match")
    rsync_files_parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="if true, only list what droplets we would rsync files over from")
    rsync_files_parser.add_argument("--droplet-source-folder", dest="droplet_source_folder", required=True, help="the folder on the droplet that we are downloading files from")
    rsync_files_parser.add_argument("--destination-folder", dest="destination_folder", type=isDirectoryType, help="where to tell rsync to store the files in, a folder will be created per droplet name")
    rsync_files_parser.add_argument("--remove-source-files", dest="remove_source_files", action="store_true",
        help="if set, will instruct rsync to remove the files after transfer (but leave folders, see the rsync docs for `--remove-source-files`")

    rsync_files_parser.set_defaults(func_to_run=rsync_files_from_droplets.run)

    log_reader_parser = subparsers.add_parser("get_errored_items_from_log", help="Given a warcio scrape log file, output the IDs that failed to download")
    log_reader_parser.add_argument("--source-log", dest="source_log", required=True, type=isFileType(), help="path to the warcio scrape log that you want to extract from")
    log_reader_parser.add_argument("--output-file", dest="error_item_output_file", required=True, type=isFileType(False), help="newline-delmited output will be written to this file")
    log_reader_parser.add_argument("--output-as-URLs", dest="output_as_URLs", action="store_true", help="if set, output the exact URLs that failed instead of the associated IDs")
    log_reader_parser_group = log_reader_parser.add_mutually_exclusive_group()
    log_reader_parser_group.add_argument("--only-dual-failures", dest="only_dual_failures", action="store_true", help="if set, only output the items that failed for both chihiro and valkyrie")
    log_reader_parser_group.add_argument("--only-valkyrie-failures", dest="only_valkyrie_failures", action="store_true",
                                   help="if set, only output the items that failed for valkyrie and not chihiro")
    log_reader_parser_group.add_argument("--only-chihiro-failures", dest="only_chihiro_failures", action="store_true",
                                   help="if set, only output the items that failed for chihiro and not valkyrie")
    log_reader_parser.set_defaults(func_to_run=get_errored_items_from_log.run)


    wpull_urls_parser = subparsers.add_parser("generate_wpull_urls_from_content_ids", help="generate urls for wpull given a list of content ids")
    wpull_urls_parser.add_argument("--content-ids-file", dest="content_ids_file", required=True, type=isFileType(), help="the file of content ids")
    wpull_urls_parser.add_argument("--output-file", dest="output_file",  required=True, type=isFileType(False), help="where to store the output")
    wpull_urls_parser.add_argument("--region-lang", dest="region_lang", required=True, help="the first part of a region code, aka the `en` in `en-US`")
    wpull_urls_parser.add_argument("--region-country", dest="region_country", required=True, help="the second part of a region code, aka the `us` in `en-US`")
    wpull_urls_parser.set_defaults(func_to_run=generate_wpull_urls_from_content_ids.run)

    try:

        # set up logging stuff
        logging.captureWarnings(True) # capture warnings with the logging infrastructure
        root_logger = logging.getLogger()
        logging_formatter = ArrowLoggingFormatter("%(asctime)s %(threadName)-10s %(name)-20s %(levelname)-8s: %(message)s")

        parsed_args = parser.parse_args()

        if parsed_args.log_to_file_path:

            file_handler = logging.FileHandler(parsed_args.log_to_file_path, encoding="utf-8")
            file_handler.setFormatter(logging_formatter)
            root_logger.addHandler(file_handler)

        if not parsed_args.no_stdout:
            logging_handler = logging.StreamHandler(sys.stdout)
            logging_handler.setFormatter(logging_formatter)
            root_logger.addHandler(logging_handler)


        # set logging level based on arguments
        if parsed_args.verbose:
            root_logger.setLevel("DEBUG")
        else:
            root_logger.setLevel("INFO")


        root_logger.debug("Parsed arguments: %s", parsed_args)
        root_logger.debug("Logger hierarchy:\n%s", logging_tree.format.build_description(node=None))


        # run the function associated with each sub command
        if "func_to_run" in parsed_args:

            parsed_args.func_to_run(parsed_args)

        else:
            root_logger.info("no subcommand specified!")
            parser.print_help()
            sys.exit(0)

        root_logger.info("Done!")
    except Exception as e:
        root_logger.exception("Something went wrong!")
        sys.exit(1)