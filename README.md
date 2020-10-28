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

