
import logging

import attr
import ruamel.yaml
import io
import pathlib

logger = logging.getLogger(__name__)



def get_yaml_file_string_from_dict(input_dict:dict) -> str:

    yaml_string_io = io.StringIO()

    # get the 'handle' to the YAML parser/dumper, it seems like this
    # is basically like a handle in the C sense, it doesn't really handle any
    # state itself but i just give it instances to the stuff i'm dumping
    # you need `rt` (round trip) to make it preserve comments
    yaml_handle = ruamel.yaml.YAML(typ="rt")

    comment_mark = ruamel.yaml.error.CommentMark(column=0)
    cloud_config_comment_token  = ruamel.yaml.tokens.CommentToken("#cloud-config\n", comment_mark, None)

    # basically a regular dictionary that we will add to , that supports comments
    yaml_dictionary = ruamel.yaml.comments.CommentedMap(input_dict)

    # add the comment
    # we can't call the handly method on `ruamel.yaml.comments.CommentedMap`: `yaml_set_start_comment()` because it
    # adds a space between the `#` and the rest of the comment, and we need it to be WITHOUT a space, see the examples
    # for cloudinit: https://cloudinit.readthedocs.io/en/latest/topics/examples.html
    # so we have to hack together some thing to add a comment without a space
    # see https://sourceforge.net/p/ruamel-yaml/tickets/371/
    yaml_dictionary._yaml_get_pre_comment().append(cloud_config_comment_token)

    # then write the commented map with the comment to the StringIO
    yaml_handle.dump(yaml_dictionary, yaml_string_io)

    return yaml_string_io.getvalue()

def get_yaml_dictionary(args):

    # you provide the string 'default' , then define other users in the following dictionaries
    # see https://cloudinit.readthedocs.io/en/latest/topics/modules.html#users-and-groups
    users_list = [
        "default",
        {
            'name': args.main_account_username,
            'groups': 'admin',
            'shell': '/bin/bash',
            'sudo': ['ALL=(ALL) NOPASSWD:ALL'],
            'ssh-authorized-keys': args.ssh_key_fingerprints
        },
    ]

    # see https://cloudinit.readthedocs.io/en/latest/topics/modules.html#set-passwords
    chpasswd_dict = {
        "list": [f"{args.main_account_username}{args.main_account_password}"],
        "expire": False
    }

    packages_list = [
        'python3',
        'python3-pip',
        'python3-venv',
        'python3-wheel',
        'lua50',
        'git-core',
        'libgnutls28-dev',
        'lua5.1',
        'liblua5.1-0',
        'liblua5.1-0-dev',
        'screen',
        'bzip2',
        'zlib1g-dev',
        'flex',
        'autoconf',
        'autopoint',
        'texinfo',
        'gperf',
        'lua-socket',
        'rsync',
        'automake',
        'pkg-config',
        'python3-dev',
        'build-essential',
        'zstd',
        'libzstd-dev',
        'libzstd1'
    ]

    # this file is: `playstation_store_2020_oct_scrape/playstation_store_2020_oct_scrape/get_cloudinit_files.py
    # file we want is `playstation_store_2020_oct_scrape/cloud_init_scripts/script_inside_cloudinit_yaml.py`

    per_once_script_contents_path = pathlib.Path(__file__).parent / "../cloud_init_scripts/script_inside_cloudinit_yaml.py".resolve()
    logger.info("loading yaml content template from `%s`", per_once_script_contents_path)

    per_once_script_contents = None
    with open(per_once_script_contents_path, "r", encoding="utf-8") as f:
        per_once_script_contents = f.read()


    write_files_dict = {
        "path": "/var/lib/cloud/scripts/per-once/wpull_per_once_bootstrap.sh",
        "owner": f"{args.main_account_username}:{args.main_account_username}",
        "permissions": "777",
        "content": per_once_script_contents

    }

    top_level_dict = {
        "users": users_list,
        "chpasswd": chpasswd_dict,
        "package_update": True,
        "package_upgrade": True,
        "packages": packages_list,
        "byobu_by_default": "enable",
        "write_files": write_files_dict
    }


def get_cloudinit_files(args):

    lang_code = args.region_lang
    country_code = args.region_country

    wget_at_url_list_filepath = args.output_folder / "wget_at-url_list_{}-{}.txt".format(lang_code, country_code)
    cloud_init_yaml_filepath = args.output_folder / "cloud_init_{}-{}.yaml".format(lang_code, country_code)
    args_file_filepath = args.output_folder / "wget_at_args_{}-{}.sh".format(lang_code, country_code)

    # write the url list for wget-at
    # sku_list = []
    # with open(args.sku_list, "r", encoding="utf-8") as f:

    #     while True:
    #         iter_sku = f.readline()

    #         if not iter_sku:
    #             break
    #         else:
    #             sku_list.append(iter_sku.strip())

    # # set newline or else when read on linux it freaks out
    # with open(wget_at_url_list_filepath, "w", encoding="utf-8", newline="\n") as f:

    #     for iter_sku in sku_list:

    #         f.write(URL_BASE.format(lang_code, country_code, iter_sku) + "\n")


    # logger.info("url list written to `%s`", wget_at_url_list_filepath)


    # # write the arguments file
    # # set newline or else when read on linux it freaks out
    # with open(args_file_filepath, "w", encoding="utf-8", newline="\n") as f:

    #     output = ARGUMENTS_BASE.format(lang_code, country_code, lang_code, country_code, REJECT_REGEX)

    #     f.write(output)

    # logger.info("args file written to `%s`", args_file_filepath)


    # write the YAML cloud init file
    # set newline or else when read on linux it freaks out
    with open(cloud_init_yaml_filepath, "w", encoding="utf-8", newline="\n") as f:

        yaml_output = get_yaml_file_string_from_dict(get_yaml_dictionary(args))

        f.write(yaml_output)

    logger.info("cloud init YAML file written to `%s`", cloud_init_yaml_filepath)





