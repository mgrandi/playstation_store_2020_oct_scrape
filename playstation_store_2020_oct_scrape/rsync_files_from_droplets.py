
import logging
import pathlib
import subprocess
import re

import digitalocean

logger = logging.getLogger(__name__)



def native_windows_path_to_cygnative_path(path):


    cygdrive_parts = ["/cygdrive"]

    for idx, iter_part in enumerate(path.parts):
        if idx == 0:
            drive_letter = iter_part[0]
            cygdrive_parts.append(drive_letter)
            continue
        cygdrive_parts.append(iter_part)

    return "/".join(cygdrive_parts)


def create_rsync_command_list(parsed_args, droplet):
    # .\rsync --progress -args -e="..\..\cygnative1.2\cygnative plink" mgrandi@159.203.45.139:"/home/mgrandi/psstore/en-ca.txt" /cygdrive/c/Users/auror/Desktop/ps_store/laststand/tmp

    dest_folder = parsed_args.destination_folder / droplet.name

    # dest_folder = native_windows_path_to_cygnative_path(dest_folder)

    cmd_list = [
        str(parsed_args.rsync_binary),
        # "--progress",
        "--itemize-changes",
        "--recursive",
        "--remove-source-files",
        # "--rsh",
        # "{} {}".format(parsed_args.cygnative_binary, parsed_args.plink_binary),
        "{}@{}:{}".format(parsed_args.username, droplet.ip_address, parsed_args.droplet_source_folder),
        "{}".format(dest_folder)
    ]

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

        droplet_list = do_manager.get_all_droplets()

        logger.info("have `%s` total droplets", len(droplet_list))

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


    for iter_droplet in matched_droplets:

        rsync_cmd = create_rsync_command_list(args, iter_droplet)

        logger.info("command for droplet `%s` is `%s`", iter_droplet, rsync_cmd)

        command_result = None

        try:

            command_result = subprocess.check_output(rsync_cmd)

            logger.info("command for droplet `%s` succeeded: `%s`", iter_droplet, command_result)
        except Exception as e:

            logger.exception("command failed for droplet `%s`, command result: `%s`", iter_droplet, command_result)




