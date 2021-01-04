import logging

import attr
import ruamel.yaml
import io
import pathlib
import gzip

logger = logging.getLogger(__name__)

from playstation_store_2020_oct_scrape import model

REPLACEMENT_STR_LANGUAGE = "___REGION_LANG___"
REPLACEMENT_STR_COUNTRY = "___REGION_COUNTRY___"
REPLACEMENT_STR_DOWNLOAD_URL = "___DOWNLOAD_URL___"

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

    # TODO: maybe write the input_dict or some other identifying info to the end of line comment of the yaml
    # so we can tell which yaml goes to which instance without decompressing the gzip script and looking at the
    # variables

    # then write the commented map with the comment to the StringIO
    yaml_handle.dump(yaml_dictionary, yaml_string_io)

    return yaml_string_io.getvalue()

def get_yaml_dictionary(args:model.CloudInitYamlArgs):

    logger.debug("creating yaml dictionary from CloudInitYamlArgs: `%s`", args)

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

    per_once_script_contents_path = pathlib.Path(__file__).parent.joinpath("..", "cloud_init_scripts", "script_inside_cloudinit_yaml.py").resolve()
    logger.debug("loading yaml content template from `%s`", per_once_script_contents_path)

    per_once_script_contents = None
    with open(per_once_script_contents_path, "r", encoding="utf-8") as f:
        per_once_script_contents = f.read()

    # now replace the values in the script that we will be embedding in the cloud-init YAML

    logger.debug("replacing marker values with their real values")
    # NOTE: I call it 'country' when the library calls its 'region', whoops
    # NOTE: also: you have to convert it to  string, `language_tags.Tag.Tag.region` for example returns a
    # `language_tags.Subtag.Subtag` unless you convert it
    tmp_country = str(args.language_tag.region).lower()
    tmp_lang = str(args.language_tag.language).lower()
    per_once_script_contents = per_once_script_contents.replace(REPLACEMENT_STR_COUNTRY, tmp_country)
    per_once_script_contents = per_once_script_contents.replace(REPLACEMENT_STR_LANGUAGE, tmp_lang)
    per_once_script_contents = per_once_script_contents.replace(REPLACEMENT_STR_DOWNLOAD_URL, args.download_url)


    # in order to make this easier to test, lets compress the contents with gzip
    # can either do `gzip.compress()` or use the `gzip.GzipFile` with a fileobj on a io.BytesIO
    # but according to the examples, we should use a gzip file rather than a raw zlib compressed
    # stream i guess
    # see https://cloudinit.readthedocs.io/en/latest/topics/modules.html#write-files
    logger.debug("compressing contents of python script")
    per_once_script_compressed = gzip.compress(per_once_script_contents.encode("utf-8"))

    # FIXME: apparently i cannot set the owner of the file to be any users I am creating
    # as when `write_files` runs, it runs before users are created? lol
    # so for now I am setting the owner/group to be `root`
    # see https://bugs.launchpad.net/cloud-init/+bug/1486113
    write_files_dict = {
        "path": "/var/lib/cloud/scripts/per-once/wpull_per_once_bootstrap.py",
        "owner": "root:root",
        "permissions": "0777",
        "encoding": "gzip",
        "content": per_once_script_compressed
    }

    write_files_list = [write_files_dict]

    top_level_dict = {
        "users": users_list,
        "chpasswd": chpasswd_dict,
        "package_update": True,
        "package_upgrade": True,
        "packages": packages_list,
        "byobu_by_default": "enable",
        "write_files": write_files_list
    }

    final_yaml_str =  get_yaml_file_string_from_dict(top_level_dict)
    logger.debug("final yaml document string created")
    return final_yaml_str
