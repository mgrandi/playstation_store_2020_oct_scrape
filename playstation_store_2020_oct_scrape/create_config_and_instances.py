
import logging
import pathlib
import subprocess
import sys
import random
import pprint
import time
import arrow

import digitalocean
import attr
import language_tags.Tag

from playstation_store_2020_oct_scrape import get_cloudinit_files
from playstation_store_2020_oct_scrape import model

logger = logging.getLogger(__name__)

SLEEP_TIME_SECONDS_BETWEEN_CREATION = 20

DIGITAL_OCEAN_REGION_LIST = ["nyc1", "nyc3", "sfo2", "sfo3", "lon1", "tor1"]



def run(args):

    language_tag_list = args.language_tag
    machine_name_prefix = args.machine_name_prefix
    starting_machine_number = args.machine_starting_id
    digital_ocean_auth_token = args.digital_ocean_token
    cloud_init_output_folder = args.output_folder
    is_dry_run = args.dry_run
    ssh_key_fingerprints_list = args.ssh_key_fingerprints
    droplet_tag_list = args.tag


    logger.info("starting at id `%s`", starting_machine_number)

    created_droplets = []

    # get the file listing
    # TODO: MARK FIX make this take arguments instead of looking in a folder
    for machine_idx, iter_language_tag in enumerate(language_tag_list, start=starting_machine_number):

        logger.info("on machine_idx: `%s`, language tag: `%s`", machine_idx, iter_language_tag)

        # get the yaml
        cloudinit_yaml_args = model.CloudInitYamlArgs(
            language_tag=iter_language_tag,
            ssh_key_fingerprints=ssh_key_fingerprints_list,
            main_account_username= args.main_account_username,
            main_account_password=args.main_account_password,
            download_url=args.bootstrap_script_download_url)

        logger.debug("getting cloud-init yaml string with args: `%s`", cloudinit_yaml_args)

        cloudinit_yaml_str = get_cloudinit_files.get_yaml_dictionary(cloudinit_yaml_args)

        logger.debug("yaml string: \n%s", cloudinit_yaml_str)

        region_choice = random.choice(DIGITAL_OCEAN_REGION_LIST)

        size_slug = "s-1vcpu-2gb"

        machine_name ='{}-{}-{}-{}'.format(machine_name_prefix, size_slug, region_choice, machine_idx)

        # write out the yaml to the output folder as a record
        output_yaml_path = cloud_init_output_folder / f"{arrow.utcnow().timestamp}_cloud-init_{'DRY-RUN' if is_dry_run else 'LIVE'}_{machine_name}.yaml"

        logger.info("writing cloud-init yaml output for droplet `%s` to `%s`", machine_name, output_yaml_path)

        with open(output_yaml_path, "w", encoding="utf-8") as f:
            f.write(cloudinit_yaml_str)

        if is_dry_run:

            logger.info("DRY RUN: Would have created a droplet with the name `%s`, region: `%s`, size: `%s`",
                machine_name, region_choice, size_slug)
        else:
            try:

                logger.info("LIVE RUN")
                # to get the image slug names, run this:
                # `doctl compute image list-distribution --public`
                # to get the size_slug names, run this:
                # `doctl compute size list`
                droplet_args = model.DropletCreationArgs(
                    token=digital_ocean_auth_token,
                    name=machine_name,
                    region=region_choice,
                    image='ubuntu-20-10-x64', # Ubuntu 20.10 x64
                    size_slug='s-1vcpu-1gb',  # 1GB RAM, 1 vCPU
                    backups=False,
                    ipv6=True,
                    monitoring=False,
                    ssh_keys=ssh_key_fingerprints_list,
                    user_data=cloudinit_yaml_str,
                    tags=droplet_tag_list)

                logger.info("about to create the droplet `%s`, but sleeping for `%s` seconds first. ctrl+c if you don't want this",
                    droplet_args, SLEEP_TIME_SECONDS_BETWEEN_CREATION)
                time.sleep(SLEEP_TIME_SECONDS_BETWEEN_CREATION)

                # convert the DropletCreationArgs to a dict, and then pass it as kwargs to
                # `digitalocean.Droplet`
                droplet = digitalocean.Droplet(**attr.asdict(droplet_args))

                droplet.create()

                logger.info("-- droplet created: `%s`", droplet)

                info = model.DropletCreationInfo(
                    language_tag=iter_language_tag,
                    machine_idx=machine_idx,
                    droplet=droplet,
                    droplet_arguments=droplet_args)

                created_droplets.append(info)

            except Exception as e:

                logger.exception("failed to create droplet with idx `%s`, region `%s`, size slug `%s` and name `%s`",
                    machine_idx, region_choice, size_slug, machine_name)

                continue

    logger.info("created droplets: \n%s", pprint.pformat(created_droplets))
