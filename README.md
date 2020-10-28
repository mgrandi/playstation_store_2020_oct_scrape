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

## warcio scrape example:

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


## cloud init files example

```plaintext


$ python cli.py get_cloudinit_files --sku-list "C:\Users\mgrandi\Desktop\ps_store\laststand\finished_regions_sourcefiles\es-es.txt" --region-lang "es" --region-country "es" --output-folder "C:\Users\mgrandi\Desktop\ps_store\laststand\cloudinit_files"

2020-10-27T20:46:17.400896-07:00 MainThread playstation_store_2020_oct_scrape.get_cloudinit_files INFO    : url list written to `C:\Users\mgrandi\Desktop\ps_store\laststand\cloudinit_files\wget_at-url_list_es-es.txt`
2020-10-27T20:46:17.405381-07:00 MainThread playstation_store_2020_oct_scrape.get_cloudinit_files INFO    : args file written to `C:\Users\mgrandi\Desktop\ps_store\laststand\cloudinit_files\wget_at_args_es-es.sh`

```

## going from json list to url list


two parts, first part (individual game urls)

```plaintext

jq -r ".game_urls[].url" C:\Users\mark\Desktop\ps_store_outfile_5.txt > url_list.txt

```

second part (get the urls that have the game listings)

```plaintext

jq -r "[.game_urls[].metadata.store_page_url] | unique | .[]" C:\Users\mark\Desktop\ps_store_outfile_5.txt > url_list2.txt

```

