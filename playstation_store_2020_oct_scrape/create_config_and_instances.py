
import logging
import pathlib
import subprocess
import sys
import random
import pprint
import time

import digitalocean
import attr

from playstation_store_2020_oct_scrape import get_cloudinit_files

logger = logging.getLogger(__name__)

SLEEP_TIME_SECONDS_BETWEEN_CREATION = 10

DIGITAL_OCEAN_REGION_LIST = ["nyc1", "nyc3", "sfo2", "sfo3", "lon1", "tor1"]

@attr.s
class DropletCreationInfo:
    region_lang = attr.ib()
    region_country = attr.ib()
    machine_name = attr.ib()
    machine_idx = attr.ib()
    droplet = attr.ib()

def run(args):

    ssh_key_fingerprints_list = args.ssh_key_fingerprints
    machine_name_prefix = args.machine_name_prefix
    content_id_folder = args.content_id_files_folder
    starting_machine_number = args.machine_starting_id
    digital_ocean_auth_token = args.digital_ocean_token
    cloud_init_output_folder = args.cloudinit_config_output_folder
    is_dry_run = args.dry_run


    logger.info("starting at id `%s`", starting_machine_number)

    created_droplets = []

    # get the file listing
    # TODO: MARK FIX make this take arguments instead of looking in a folder
    for machine_idx, iter_content_id_file in enumerate(content_id_folder.glob("*.txt"), start=starting_machine_number):

        logger.info("found file `%s`", iter_content_id_file)

        stem = iter_content_id_file.stem

        s = stem.split("-")
        lang = s[0]
        country = s[1]

        logger.info("-- lang: `%s`, country: `%s`", lang, country)

        # get the yaml
        cloudinit_yaml_str = get_cloudinit_files.get_yaml_file_string(lang, country)


        # call basically ourselves to generate the rest of the files

        subprocess_args = [sys.executable,
            "cli.py",
            "get_cloudinit_files",
            "--sku-list",
            iter_content_id_file.resolve(),
            "--region-lang",
            lang,
            "--region-country",
            country,
            "--output-folder",
            cloud_init_output_folder]

        logger.info("-- running command `%s`", subprocess_args)

        result = subprocess.run(subprocess_args, check=True)

        logger.info("-- process ran successfully: `%s`", result)

        region_choice = random.choice(DIGITAL_OCEAN_REGION_LIST)

        size_slug = "s-1vcpu-2gb"

        machine_name ='MINION2-{}-{}-{}'.format(size_slug, region_choice, machine_idx)

        if is_dry_run:

            logger.info("DRY RUN: Would have created a droplet with the name `%s`, region: `%s`, size: `%s`",
                machine_name, region_choice, size_slug)
        else:
            try:
                droplet = digitalocean.Droplet(
                    token=digital_ocean_auth_token,
                    name=machine_name,
                    region=region_choice,
                    image='ubuntu-20-04-x64', # Ubuntu 20.04 x64
                    size_slug='s-1vcpu-2gb',  # 2GB RAM, 1 vCPU
                    backups=False,
                    ipv6=True,
                    monitoring=False,
                    ssh_keys=ssh_key_fingerprints_list,
                    user_data=cloudinit_yaml_str)

                logger.info("about to create the droplet `%s`, but sleeping for `%s` seconds first. ctrl+c if you don't want this",
                    droplet, SLEEP_TIME_SECONDS_BETWEEN_CREATION)
                time.sleep(SLEEP_TIME_SECONDS_BETWEEN_CREATION)

                droplet.create()

                logger.info("-- droplet created: `%s`", droplet)

                info = DropletCreationInfo(
                    region_lang=lang,
                    region_country=country,
                    machine_name=machine_name,
                    machine_idx=machine_idx,
                    droplet=droplet,)

                created_droplets.append(info)

            except Exception as e:

                logger.exception("failed to create droplet with idx `%s`, region `%s`, size slug `%s` and name `%s`",
                    machine_idx, region_choice, size_slug, machine_name)

                continue

    logger.info("created droplets: \n%s", pprint.pformat(created_droplets))
