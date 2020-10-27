# playstation_store_2020_oct_scrape


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

## going from json list to url list


two parts, first part (individual game urls)

```plaintext

jq -r ".game_urls[].url" C:\Users\mark\Desktop\ps_store_outfile_5.txt > url_list.txt

```

second part (get the urls that have the game listings)

```plaintext

jq -r "[.game_urls[].metadata.store_page_url] | unique | .[]" C:\Users\mark\Desktop\ps_store_outfile_5.txt > url_list2.txt

```

