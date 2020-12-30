import typing

import attr
import language_tags.Tag
import digitalocean

@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class CloudInitYamlArgs:
    language_tag:language_tags.Tag.Tag = attr.ib()
    ssh_key_fingerprints:typing.Sequence[str] = attr.ib()
    main_account_username:str = attr.ib()
    main_account_password:str = attr.ib()
    download_url:str = attr.ib()

@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class DropletCreationInfo:
    language_tag:language_tags.Tag.Tag = attr.ib()
    machine_name:str = attr.ib()
    machine_idx:str = attr.ib()
    droplet:digitalocean.Droplet = attr.ib()