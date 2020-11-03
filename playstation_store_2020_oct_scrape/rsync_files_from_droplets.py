
import logging
import pathlib
import subprocess
import re

import digitalocean

logger = logging.getLogger(__name__)


def create_rsync_command_list(parsed_args, droplet, destination_folder):

    cmd_list = [
        str(parsed_args.rsync_binary),
        # "--progress",
        "--itemize-changes",
        "--recursive"
        ]

    if parsed_args.remove_source_files:
        cmd_list.append("--remove-source-files")

    cmd_list.extend([
        "{}@{}:{}".format(parsed_args.username, droplet.ip_address, parsed_args.droplet_source_folder),
        "{}".format(destination_folder)
    ])

    return cmd_list



def run(args):


    do_token = args.digital_ocean_token

    name_regex_obj = args.name_regex
    should_dry_run = args.dry_run
    dest_folder_base_apth = args.destination_folder


    # get droplet list

    do_manager = None
    droplet_list = []


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


    # se if we only should list
    if should_dry_run:

        logger.info("Droplets that we would have acted on with the regex `%s`: ", name_regex_obj)

        for iter_droplet in matched_droplets:
            logger.info("-- `%s`", iter_droplet)

        return


    # we are doing it for real
    if args.remove_source_files:
        logger.info("*** We are removing source files! ***")

    for iter_droplet in matched_droplets:

        dest_folder = args.destination_folder / iter_droplet.name
        dest_folder = dest_folder.resolve()

        if not dest_folder.exists():
            logger.info("creating folder `%s`", dest_folder)
            dest_folder.mkdir()

        rsync_cmd = create_rsync_command_list(args, iter_droplet, dest_folder)



        logger.debug("command for droplet `%s` is `%s`", iter_droplet, rsync_cmd)

        command_result = None

        try:

            logger.info("starting rsync command to transfer files from the droplet `%s` to `%s`", iter_droplet.name, dest_folder )
            command_result = subprocess.check_output(rsync_cmd)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("rsync command for droplet `%s` succeeded: `%s`", iter_droplet, command_result)
            else:
                logger.info("rsync command for droplet `%s` succeeded", iter_droplet.name)
        except Exception as e:

            logger.exception("command failed for droplet `%s`, command result: `%s`", iter_droplet, command_result)




