# playstation_store_2020_oct_scrape


## setup

```plaintext

# probably run this individual command as administrator as it should be installed globally
pip3 install poetry

cd playstation_store_2020_oct_scrape

# these should be a file that gets setup by python, for me its located in
# `C:\Python39\Scripts\poetry.exe`, and requires `C:\Python39\Scripts` to be in the PATH
poetry shell

poetry install

# etc
python3 cli.py --help
python3 cli.py @args.txt

```

## usage

```plaintext
$ python cli.py --help
usage: cli.py [-h] [--log-to-file-path LOG_TO_FILE_PATH] [--verbose] [--no-stdout]
              {scrape_urls,wpull_urls,warcio_scrape,get_cloudinit_files,create_config_and_instances,rsync_files_from_droplets}
              ...

scrape the playstation games site

positional arguments:
  {scrape_urls,wpull_urls,warcio_scrape,get_cloudinit_files,create_config_and_instances,rsync_files_from_droplets}
                        sub-command help
    scrape_urls         Scrape URLs to JSON
    wpull_urls          download URLs with wpull
    warcio_scrape       download urls via warcio
    get_cloudinit_files
                        get files for cloudinit
    create_config_and_instances
                        given a list of content-id files , create the config and then create DO instances
    rsync_files_from_droplets
                        for every droplet specified, rsync files over to a local folder

optional arguments:
  -h, --help            show this help message and exit
  --log-to-file-path LOG_TO_FILE_PATH
                        log to the specified file
  --verbose             Increase logging verbosity
  --no-stdout           if true, will not log to stdout
```

## scrape_urls

don't use :)

## create_config_and_instances

don't use yet :)

## wpull_urls

don't use :)

## rsync_files_from_droplets
```plaintext

$ python cli.py rsync_files_from_droplets --help
usage: cli.py rsync_files_from_droplets [-h] --username USERNAME --rsync-binary RSYNC_BINARY --digital-ocean-token
                                        DIGITAL_OCEAN_TOKEN --name-regex NAME_REGEX [--dry-run]
                                        --droplet-source-folder DROPLET_SOURCE_FOLDER
                                        [--destination-folder DESTINATION_FOLDER]

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME   the username to log into the drolets
  --rsync-binary RSYNC_BINARY
                        path to the rsync binary
  --digital-ocean-token DIGITAL_OCEAN_TOKEN
                        the token to login to the DO API
  --name-regex NAME_REGEX
                        regex for the names to match
  --dry-run             if true, only list what droplets we would rsync files over from
  --droplet-source-folder DROPLET_SOURCE_FOLDER
                        the folder on the droplet that we are downloading files from
  --destination-folder DESTINATION_FOLDER
                        where to tell rsync to store the files in, a folder will be created per droplet name
```

### example


#### dry run

to test your `--name-regex`

```plaintext
$ python cli.py rsync_files_from_droplets --username "mgrandi" --digital-ocean-token "TOKEN_GOES_HERE" --rsync-binary "/usr/bin/rsync" --name-regex "^SCRAPERMINION.*$" --droplet-source-folder "/home/mgrandi/psstore/playstation_content_ids/scripts" --destination-folder "/home/mark/
tmp" --dry-run

2020-11-03T02:58:13.651710-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : have `6` total droplets
2020-11-03T02:58:13.660307-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : Droplets that we would have acted on with the regex `re.compile('^SCRAPERMINION.*$')`:
2020-11-03T02:58:13.662217-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : -- `<Droplet: 214183113 SCRAPERMINION-s-1vcpu-1gb-tor1-01>`
2020-11-03T02:58:13.663647-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : -- `<Droplet: 214922151 SCRAPERMINION-s-1vcpu-1gb-tor1-02>`
2020-11-03T02:58:13.667813-08:00 MainThread root                 INFO    : Done!

```

#### actual run

```plaintext

$ tree /home/mark/tmp
/home/mark/tmp

0 directories, 0 files



$ python cli.py rsync_files_from_droplets --username "mgrandi" --digital-ocean-token "TOKEN_GOES_HERE" --rsync-binary "/usr/bin/rsync" --name-regex "^SCRAPERMINION.*$" --droplet-source-folder "/home/mgrandi/tmp" --destination-folder "/home/mark/tmp"

2020-11-03T03:25:21.977305-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : Querying for the list of Digital Ocean droplets...
2020-11-03T03:25:22.824925-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : Found `6` total droplets
2020-11-03T03:25:22.827014-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : creating folder `/home/mark/tmp/SCRAPERMINION-s-1vcpu-1gb-tor1-01`
2020-11-03T03:25:22.829485-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : starting rsync command to transfer files from the droplet `SCRAPERMINION-s-1vcpu-1gb-tor1-01` to `/home/mark/tmp/SCRAPERMINION-s-1vcpu-1gb-tor1-01`
2020-11-03T03:25:26.584630-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : rsync command for droplet `SCRAPERMINION-s-1vcpu-1gb-tor1-01` succeeded
2020-11-03T03:25:26.586911-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : creating folder `/home/mark/tmp/SCRAPERMINION-s-1vcpu-1gb-tor1-02`
2020-11-03T03:25:26.588115-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : starting rsync command to transfer files from the droplet `SCRAPERMINION-s-1vcpu-1gb-tor1-02` to `/home/mark/tmp/SCRAPERMINION-s-1vcpu-1gb-tor1-02`
2020-11-03T03:25:29.868707-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : rsync command for droplet `SCRAPERMINION-s-1vcpu-1gb-tor1-02` succeeded
2020-11-03T03:25:29.875419-08:00 MainThread root                 INFO    : Done!



mark@Alcidae:~$ tree /home/mark/tmp
/home/mark/tmp
├── SCRAPERMINION-s-1vcpu-1gb-tor1-01
│   └── tmp
│       └── test.txt
└── SCRAPERMINION-s-1vcpu-1gb-tor1-02
    └── tmp
        └── test.txt

4 directories, 2 files
```

### actual run - removing source files

```plaintext

$ python cli.py rsync_files_from_droplets --username "mgrandi" --digital-ocean-token "TOKEN_GOES_HERE" --rsync-binary "/usr/bin/rsync" --name-regex "^SCRAPERMINION.*$" --droplet-source-folder "/home/mgrandi/tmp" --destination-folder "/home/mark/tmp" --remove-source-files

2020-11-03T03:28:05.705601-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : Querying for the list of Digital Ocean droplets...
2020-11-03T03:28:06.873919-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : Found `6` total droplets
2020-11-03T03:28:06.875979-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : *** We are removing source files! ***
2020-11-03T03:28:06.877725-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : starting rsync command to transfer files from the droplet `SCRAPERMINION-s-1vcpu-1gb-tor1-01` to `/home/mark/tmp/SCRAPERMINION-s-1vcpu-1gb-tor1-01`
2020-11-03T03:28:10.728561-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : rsync command for droplet `/SCRAPERMINION-s-1vcpu-1gb-tor1-01` succeeded
2020-11-03T03:28:10.731581-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : starting rsync command to transfer files from the droplet `SCRAPERMINION-s-1vcpu-1gb-tor1-02` to `/home/mark/tmp/SCRAPERMINION-s-1vcpu-1gb-tor1-02`
2020-11-03T03:28:13.937568-08:00 MainThread playstation_store_2020_oct_scrape.rsync_files_from_droplets INFO    : rsync command for droplet `SCRAPERMINION-s-1vcpu-1gb-tor1-02` succeeded
2020-11-03T03:28:13.947158-08:00 MainThread root                 INFO    : Done!

```

## warcio_scrape

```plaintext
$ python cli.py warcio_scrape --help
usage: cli.py warcio_scrape [-h] --sku-list SKU_LIST --region-lang REGION_LANG --region-country REGION_COUNTRY
                            [--warc-output-file WARC_OUTPUT_FILE]
                            [--media-files-output-file MEDIA_FILES_OUTPUT_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --sku-list SKU_LIST   the list of skus to download
  --region-lang REGION_LANG
                        the first part of a region code, aka the `en` in `en-US`
  --region-country REGION_COUNTRY
                        the second part of a region code, aka the `us` in `en-US`
  --warc-output-file WARC_OUTPUT_FILE
                        where to save the warc file, include 'warc.gz' in this name please
  --media-files-output-file MEDIA_FILES_OUTPUT_FILE
                        where to save the list of media urls we discovered
```

### example:

command line:

```plaintext

python3 cli.py @args.txt
```

args file:

```plaintext
--log-to-file-path
/home/mgrandi/at/ps_store_data_2/regions/es-ES/ps_store_oct2020_scrape_es-ES.log
warcio_scrape
--sku-list
/home/mgrandi/at/ps_store_data_2/regions/es-ES/es-es.txt
--region-lang
es
--region-country
es
--warc-output-file
/home/mgrandi/at/ps_store_data_2/regions/es-ES/ps_store_oct2020_scrape_es-ES_try1.warc.gz
--media-files-output-file
/home/mgrandi/at/ps_store_data_2/regions/es-ES/ps_store_oct2020_scrape_es-ES_try1_mediafiles.txt

```

this will spit out several files:

```plaintext
mgrandi@ubuntu-s-1vcpu-1gb-nyc1-07:~/psstore/ja-jp$ ls -lah
total 32M
drwxrwxr-x 2 mgrandi mgrandi 4.0K Oct 28 13:11 .
drwxrwxr-x 5 mgrandi mgrandi 4.0K Oct 28 12:22 ..
-rw-rw-r-- 1 mgrandi mgrandi  375 Oct 28 12:34 args_ja-JP.txt
-rw-rw-r-- 1 mgrandi mgrandi 2.0M Oct 28 12:23 ja-jp.txt
-rw-rw-r-- 1 mgrandi mgrandi 3.1M Oct 28 13:47 ps_store_oct2020_scrape_ja-JP.log
-rw-rw-r-- 1 mgrandi mgrandi  27M Oct 28 13:47 ps_store_oct2020_scrape_ja_JP_try1.warc.gz
```

When done, you should have these files in the output folder somewhere (maybe not the `args` or the content id filelist):

```

mgrandi@ubuntu-s-1vcpu-1gb-nyc1-07:~/psstore/es-es$ ls -lah
total 891M
drwxrwxr-x 2 mgrandi mgrandi 4.0K Oct 28 12:23 .
drwxrwxr-x 5 mgrandi mgrandi 4.0K Oct 28 12:22 ..
-rw-rw-r-- 1 mgrandi mgrandi  351 Oct 27 14:29 args_es-ES.txt
-rw-rw-r-- 1 mgrandi mgrandi 1.9M Oct 27 14:28 es-es.txt
-rw-rw-r-- 1 mgrandi mgrandi 326M Oct 28 07:06 ps_store_oct2020_scrape_es-ES.log
-rw-rw-r-- 1 mgrandi mgrandi 462M Oct 28 07:06 ps_store_oct2020_scrape_es-ES_try1.warc.gz
-rw-rw-r-- 1 mgrandi mgrandi 103M Oct 28 07:06 ps_store_oct2020_scrape_es-ES_try1_mediafiles.txt

```

save all of them, you can compress the .log file to save space, but the .warc.gz and the mediafiles.txt are the main output of this script


## get_cloudinit_files

```plaintext
$ python cli.py get_cloudinit_files --help
usage: cli.py get_cloudinit_files [-h] --sku-list SKU_LIST --region-lang REGION_LANG --region-country
                                  REGION_COUNTRY --output-folder OUTPUT_FOLDER

optional arguments:
  -h, --help            show this help message and exit
  --sku-list SKU_LIST   newline delimited list of skus
  --region-lang REGION_LANG
                        the first part of a region code, aka the `en` in `en-US`
  --region-country REGION_COUNTRY
                        the second part of a region code, aka the `us` in `en-US`
  --output-folder OUTPUT_FOLDER
                        where to store the resulting files

```

### example

```plaintext


$ python cli.py get_cloudinit_files --sku-list "C:\Users\mgrandi\Desktop\ps_store\laststand\finished_regions_sourcefiles\es-es.txt" --region-lang "es" --region-country "es" --output-folder "C:\Users\mgrandi\Desktop\ps_store\laststand\cloudinit_files"

2020-10-27T20:46:17.400896-07:00 MainThread playstation_store_2020_oct_scrape.get_cloudinit_files INFO    : url list written to `C:\Users\mgrandi\Desktop\ps_store\laststand\cloudinit_files\wget_at-url_list_es-es.txt`
2020-10-27T20:46:17.405381-07:00 MainThread playstation_store_2020_oct_scrape.get_cloudinit_files INFO    : args file written to `C:\Users\mgrandi\Desktop\ps_store\laststand\cloudinit_files\wget_at_args_es-es.sh`

```

## get_errored_items_from_log

Given a warcio scrape log file, outputs the IDs that failed to download.

```plaintext
$ python cli.py get_errored_items_from_log --help
usage: cli.py get_errored_items_from_log [-h] --source-log SOURCE_LOG --output-file ERROR_ITEM_OUTPUT_FILE [--output-as-URLs] [--only-dual-failures]

optional arguments:
  -h, --help            show this help message and exit
  --source-log SOURCE_LOG
                        path to the warcio scrape log that you want to extract from
  --output-file ERROR_ITEM_OUTPUT_FILE
                        newline-delmited output will be written to this file
  --output-as-URLs      if set, output the exact URLs that failed instead of the associated IDs
  --only-dual-failures  if set, only output the items that failed for both chihiro and valkyrie

```

### example:

command line:

```plaintext

python3 cli.py @args.txt
```

args file:

```plaintext
--log-to-file-path
err_parse.log
get_errored_items_from_log
--source-log
ps_store_oct2020_scrape_ja-jp_try1.log
--output-file
ja-jp_err.txt
```

this will give you a file `ja-jp_err.txt` that has the content-IDs that failed to completely download.
You can feed this text file back into warcio_scrape to retry.

The log output will also give you some info about what was found.
```plaintext
2020-11-10T18:44:18.883655+09:00 MainThread playstation_store_2020_oct_scrape.get_errored_items_from_log INFO    : Opening log file: `/home/mgrandi/playstation_store_2020_oct_scrape/ps_store_oct2020_scrape_ja-jp_update.log`
2020-11-10T18:44:19.483894+09:00 MainThread playstation_store_2020_oct_scrape.get_errored_items_from_log INFO    : found `57` failed items
2020-11-10T18:44:19.484870+09:00 MainThread playstation_store_2020_oct_scrape.get_errored_items_from_log INFO    : -- `14` have failed valkyrie links only
2020-11-10T18:44:19.485846+09:00 MainThread playstation_store_2020_oct_scrape.get_errored_items_from_log INFO    : -- `43` have failed chihiro links only
2020-11-10T18:44:19.485846+09:00 MainThread playstation_store_2020_oct_scrape.get_errored_items_from_log INFO    : -- `0` have both failed valkyrie and chihiro links
2020-11-10T18:44:19.486822+09:00 MainThread playstation_store_2020_oct_scrape.get_errored_items_from_log INFO    : Writing to /home/mgrandi/playstation_store_2020_oct_scrape/err.txt
2020-11-10T18:44:19.489778+09:00 MainThread root                 INFO    : Done!
```

## other misc commands

### going from json list to url list


two parts, first part (individual game urls)

```plaintext

jq -r ".game_urls[].url" C:\Users\mark\Desktop\ps_store_outfile_5.txt > url_list.txt

```

second part (get the urls that have the game listings)

```plaintext

jq -r "[.game_urls[].metadata.store_page_url] | unique | .[]" C:\Users\mark\Desktop\ps_store_outfile_5.txt > url_list2.txt

```

