
import logging
import pathlib
import subprocess
import re

import digitalocean

logger = logging.getLogger(__name__)


def create_rsync_command_list(parsed_args, droplet, destination_folder):
    '''
    constructs the rsync command line list that we will pass to `subprocess.run()`

    @param parsed_args - the `argaparse.Namespace` object we get from argparse
    @param droplet - the `digitalocean.Droplet` object we rsyncing from
    @param destination_folder - a `pathlib.Path` object of where we should put the files
    @return a list of arguments to pass to `subprocess.run()`
    '''

    # common rsync arguments
    cmd_list = [
        str(parsed_args.rsync_binary),
        # "--progress",
        "--itemize-changes",
        "--recursive",
        "--checksum",
        "--partial"
        ]

    # if we are removing source files
    if parsed_args.remove_source_files:
        cmd_list.append("--remove-source-files")

    # add any filters
    if parsed_args.rsync_filters_list:
        for iter_filter_str in parsed_args.rsync_filters_list:
            filter_arg_list = ["--filter", iter_filter_str]
            cmd_list.extend(filter_arg_list)

    cmd_list.extend([
        "{}@{}:{}".format(parsed_args.username, droplet.ip_address, parsed_args.droplet_source_folder),
        "{}".format(destination_folder)
    ])

    return cmd_list



def run(args):

    do_manager = None
    droplet_list = []

    do_token = args.digital_ocean_token
    name_regex_obj = args.name_regex
    should_dry_run = args.dry_run
    dest_folder_base_path = args.destination_folder

    # get droplet list
    try:
        do_manager = digitalocean.Manager(token=do_token)

        logger.info("Querying for the list of Digital Ocean droplets...")
        droplet_list = do_manager.get_all_droplets()

        logger.info("Found `%s` total droplets", len(droplet_list))

    except Exception as e:

        logger.exception("Failed to get the droplet list!")
        raise e


    # now figure out what droplets we should act on
    matched_droplets = []

    for iter_droplet in droplet_list:

        name = iter_droplet.name

        search_res = name_regex_obj.search(name)

        logger.debug("regex `%s` search result against droplet `%s` 's name: `%s`",
            name_regex_obj, iter_droplet, search_res)

        if search_res:
            logger.debug("droplet `%s` matched")
            matched_droplets.append(iter_droplet)

    logger.info("`%s` droplets matched our regex", len(matched_droplets))

    for iter_droplet in matched_droplets:

        dest_folder = dest_folder_base_path / iter_droplet.name
        dest_folder = dest_folder.resolve()

        if not dest_folder.exists():
            if not should_dry_run:
                logger.info("attempting to create folder `%s`", dest_folder)
                dest_folder.mkdir(exist_ok=True)
            else:
                logger.info("DRY RUN: would have attempted to create the folder `%s`", dest_folder)

        rsync_cmd = create_rsync_command_list(args, iter_droplet, dest_folder)

        logger.debug("command for droplet `%s` is `%s`", iter_droplet, rsync_cmd)

        command_result = None

        # list the droplet and what rsync command we would have ran if this is a dry run, and then continue the loop
        # and not actually execute the command
        if should_dry_run:
            logger.info("DRY RUN: Would have acted on droplet `%s` with the command `%s`", iter_droplet, rsync_cmd)
            continue

        # we are doing it for real, NOT a dry run
        if args.remove_source_files:
            logger.info("*** We are removing source files! ***")

        try:

            logger.info("starting rsync command to transfer files from the droplet `%s` to `%s`", iter_droplet.name, dest_folder )
            command_result = subprocess.check_output(rsync_cmd)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("rsync command for droplet `%s` succeeded: `%s`", iter_droplet, command_result)
            else:
                logger.info("rsync command for droplet `%s` succeeded", iter_droplet.name)

        except Exception as e:

            logger.exception("command failed for droplet `%s`, command result: `%s`", iter_droplet, command_result)




