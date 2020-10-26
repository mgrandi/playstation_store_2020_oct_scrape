# playstation_store_2020_oct_scrape

## going from json list to url list


two parts, first part (individual game urls)

```plaintext

jq -r ".game_urls[].url" C:\Users\mark\Desktop\ps_store_outfile_5.txt > url_list.txt

```

second part (get the urls that have the game listings)

```plaintext

jq -r "[.game_urls[].metadata.store_page_url] | unique | .[]" C:\Users\mark\Desktop\ps_store_outfile_5.txt > url_list2.txt

```