from __future__ import annotations
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
    machine_idx:str = attr.ib()
    droplet:digitalocean.Droplet = attr.ib()
    droplet_arguments:DropletCreationArgs= attr.ib()

@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class DropletCreationArgs:
    '''
    basically a carbon copy of the arguments we pass to
    `digitalocean.Droplet`, but since the __str__ of the Droplet
    class is lacking, we basically have this attr class, and then
    we pass the arguments to the actual `digitalocean.Droplet` class
    '''
    token:str = attr.ib(repr=False)
    name:str = attr.ib()
    region:str = attr.ib()
    image:str = attr.ib()
    size_slug:str = attr.ib()
    backups:bool = attr.ib()
    ipv6:bool = attr.ib()
    monitoring:bool = attr.ib()
    ssh_keys:typing.Sequence[str] = attr.ib()
    user_data:str = attr.ib(repr=False)
    tags:typing.Sequence[str] = attr.ib()