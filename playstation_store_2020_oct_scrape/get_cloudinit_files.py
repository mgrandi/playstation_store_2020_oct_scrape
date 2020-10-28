
import logging

logger = logging.getLogger(__name__)

# https://store.playstation.com/en-us/product/UP3252-PCSE01475_00-JANDUSOFT0000001?smcid=psapp
URL_BASE = "https://store.playstation.com/{}-{}/product/{}?smcid=psapp"

REJECT_REGEX = r"(^https?://ajax\.googleapis\.com.*|^https?://store\.playstation\.com/fonts/.*|^https?://social\.playstation\.com.*|^https?://static\.playstation\.com.*|^https?://fonts\.gstatic\.com.*|^https?://store\.playstation\.com\/assets\/sharedNav\/1.5.7\/assets\/fonts\/.*|^https?://store\.playstation\.com\/assets\/.*)"
ARGUMENTS_BASE = \
'''#!/bin/bash
cd /home/mgrandi/psstore
./wget-at \
--user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0" \
--page-requisites \
--no-verbose \
--input-file=/home/mgrandi/psstore/wget_at-url_list_{}-{}.txt \
--output-file=/home/mgrandi/psstore/wget-at_output.log \
--no-cookies \
--content-on-error \
--content-on-redirect \
--truncate-output \
--no-check-certificate \
--output-document=/home/mgrandi/psstore/wget.tmp \
-e "robots=off" \
--rotate-dns \
--no-parent \
--timeout=30 \
--tries inf \
--waitretry=10 \
--warc-file=/home/mgrandi/psstore/ps_store_2020_oct_scrape_{}-{} \
--warc-header="operator: mgrandi" \
--warc-header="description: playstation store en-US scrape 2020-10-27" \
--warc-dedup-url-agnostic \
--warc-max-size=5368709120 \
--reject-regex "{}" \
--truncate-output
'''


# rather than using a dictionary + a yaml parser lets use string formatting! whoo
CLOUD_INIT_YAML_BASE = \
'''#cloud-config
users:
  - default
  - name: mgrandi
    groups: admin
    shell: /bin/bash
    sudo: ['ALL=(ALL) NOPASSWD:ALL']
    ssh-authorized-keys:
      - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPcmMkSxD3/0fupXUdUXl4eQn+2WYB/fxoJHIpn5A4Wa snowyegret-s-1vcpu-1gb-sfo3-01_ed25519
chpasswd:
  list: |
    mgrandi:ilikegravy
  expire: False
package_update: True
package_upgrade: True

packages:
  - python3
  - python3-pip
  - python3-venv
  - python3-wheel
  - lua50
  - git-core
  - libgnutls28-dev
  - lua5.1
  - liblua5.1-0
  - liblua5.1-0-dev
  - screen
  - bzip2
  - zlib1g-dev
  - flex
  - autoconf
  - autopoint
  - texinfo
  - gperf
  - lua-socket
  - rsync
  - automake
  - pkg-config
  - python3-dev
  - build-essential
  - zstd
  - libzstd-dev
  - libzstd1

byobu_by_default: enable

write_files:
  - path: /var/lib/cloud/scripts/per-once/start_scrape.sh
    owner: mgrandi:mgrandi
    permissions: "777"
    content: |
      #!/bin/bash
      mkdir /home/mgrandi/psstore/
      cd /home/mgrandi/psstore/
      curl -o "wget_at-url_list_{}-{}.txt" "http://161.35.231.94/wget_at-url_list_{}-{}.txt"
      curl -o "wget_at_args_{}-{}.sh" "http://161.35.231.94/wget_at_args_{}-{}.sh"
      curl -o "wget-at" "http://161.35.231.94/wget-at"
      chmod +x wget-at
      chmod +x wget_at_args_{}-{}.sh
      chown -R mgrandi:mgrandi /home/mgrandi/psstore
      runuser -l mgrandi -c "/bin/bash /home/mgrandi/psstore/wget_at_args_{}-{}.sh &"

'''


def get_yaml_file_string(region_lang, region_country):

    output = CLOUD_INIT_YAML_BASE.format(
        region_lang,
        region_country,
        region_lang,
        region_country,
        region_lang,
        region_country,
        region_lang,
        region_country,
        region_lang,
        region_country,
        region_lang,
        region_country)

    return output

def get_cloudinit_files(args):

    lang_code = args.region_lang
    country_code = args.region_country

    wget_at_url_list_filepath = args.output_folder / "wget_at-url_list_{}-{}.txt".format(lang_code, country_code)
    cloud_init_yaml_filepath = args.output_folder / "cloud_init_{}-{}.yaml".format(lang_code, country_code)
    args_file_filepath = args.output_folder / "wget_at_args_{}-{}.sh".format(lang_code, country_code)

    # write the url list for wget-at
    sku_list = []
    with open(args.sku_list, "r", encoding="utf-8") as f:

        while True:
            iter_sku = f.readline()

            if not iter_sku:
                break
            else:
                sku_list.append(iter_sku.strip())

    # set newline or else when read on linux it freaks out
    with open(wget_at_url_list_filepath, "w", encoding="utf-8", newline="\n") as f:

        for iter_sku in sku_list:

            f.write(URL_BASE.format(lang_code, country_code, iter_sku) + "\n")


    logger.info("url list written to `%s`", wget_at_url_list_filepath)


    # write the arguments file
    # set newline or else when read on linux it freaks out
    with open(args_file_filepath, "w", encoding="utf-8", newline="\n") as f:

        output = ARGUMENTS_BASE.format(lang_code, country_code, lang_code, country_code, REJECT_REGEX)

        f.write(output)

    logger.info("args file written to `%s`", args_file_filepath)


    # write the YAML cloud init file
    # set newline or else when read on linux it freaks out
    with open(cloud_init_yaml_filepath, "w", encoding="utf-8", newline="\n") as f:

        yaml_output = get_yaml_file_string(lang_code, country_code)

        f.write(yaml_output)

    logger.info("cloud init YAML file written to `%s`", cloud_init_yaml_filepath)





