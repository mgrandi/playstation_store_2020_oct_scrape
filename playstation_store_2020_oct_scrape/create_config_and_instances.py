
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

@attr.s
class DropletCreationInfo:
    region_lang = attr.ib()
    region_country = attr.ib()
    machine_name = attr.ib()
    machine_idx = attr.ib()
    droplet = attr.ib()

def run(args):


    SLEEP_TIME_SECONDS_BETWEEN_CREATION = 10

    content_id_folder = args.content_id_files_folder

    digital_ocean_region_list = ["nyc1", "nyc3", "sfo2", "sfo3", "lon1", "tor1"]

    starting_machine_number = args.machine_starting_id

    logger.info("starting at id `%s`", starting_machine_number)

    created_droplets = []

    digital_ocean_auth_token = args.digital_ocean_token

    # get the file listing

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
            args.cloudinit_config_output_folder]

        logger.info("-- running command `%s`", subprocess_args)

        result = subprocess.run(subprocess_args, check=True)

        logger.info("-- process ran successfully: `%s`", result)


        ssh_key_fingerprint_list = ["67:a7:f5:37:54:1c:1d:a2:04:05:3d:89:16:d1:0c:4d"]

        region_choice = random.choice(digital_ocean_region_list)

        size_slug = "s-1vcpu-2gb"

        machine_name ='MINION2-{}-{}-{}'.format(size_slug, region_choice, machine_idx)

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
                ssh_keys=ssh_key_fingerprint_list,
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
