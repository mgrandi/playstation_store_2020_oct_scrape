from __future__ import annotations

import logging
import pprint
import typing
import json
import subprocess
import urllib.parse

import arrow
import requests
import attr
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)



# https://store.playstation.com/en-us/grid/STORE-MSF77008-ALLGAMES/1?PlatformPrivacyWs1=exempt&direction=asc&psappver=19.15.0&scope=sceapp&smcid=psapp%3Alink%20menu%3Astore&sort=release_date
URL_ROOT = "https://store.playstation.com"
URL_FORMAT_TEMPLATE = "{}/de-de/grid/STORE-MSF75508-FULLGAMES/{}".format(URL_ROOT, "{}")
# URL_FORMAT_TEMPLATE = "{}/en-us/grid/STORE-MSF77008-ALLGAMES/{}".format(URL_ROOT, "{}")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0"
GET_PARAMS = {
    "PlatformPrivacyWs1":"exempt",
    "direction":"asc",
    "psappver":"19.15.0",
    "scope":"sceapp",
    "smcid":"psapp:link menu:store",
    "sort":"release_date"
}

HEADERS = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.5",
    "Cache-Control": "no-cache",
    "Cookie": "cookie: akacd_valkyrie-storefront-to-gotham=2177452799~rv=65~id=110c5e7ff3de9d1edff3accaba985101; last_locale=de-DE; s_fid=0DE0FF05F43AB423-361B2AFF495657B2; s_cc=true; s_sq=%5B%5BB%5D%5D; JSESSIONID=8F41E5877F1128181AC08E3AD2BD3A91-n1",
    "Dnt": "1",
    "Host": "store.playstation.com",
    "User-Agent": USER_AGENT,
    "Referer": "https://store.playstation.com/de-de/grid/STORE-MSF75508-ALLGAMES/1?PlatformPrivacyWs1=exempt&direction=asc&psappver=19.15.0&scope=sceapp&smcid=psapp%3Alink%20menu%3Astore&sort=release_date"
  }




session = requests.Session()
session.headers.update(HEADERS)

@attr.s
class GameUrlCollection:
    date_collected:str = attr.ib()
    game_urls:typing.Sequence[PlaystationStoreGameListing] = attr.ib(default=[])
    page_ember_json_dict:str = attr.ib(default={})


@attr.s
class PlaystationStoreGameListingMetadata:
    store_page_number:int = attr.ib()
    store_page_url:str = attr.ib()
    details_1:typing.Optional[str] = attr.ib()
    details_2:typing.Optional[str] = attr.ib()
    details_3:str = attr.ib()
    details_4:str = attr.ib()
    price:str = attr.ib()
    unavailable_reason:str = attr.ib()


@attr.s
class PlaystationStoreGameListing:
    title:str = attr.ib()
    region:str = attr.ib()
    url:str = attr.ib()
    sku:str = attr.ib()
    metadata:PlaystationStoreGameListingMetadata = attr.ib()




def get_tag_by_class_or_raise(tag, tag_name, class_name, url, idx):

    node = tag.find(tag_name, class_name)

    if node:
        return node

    else:
        raise Exception("couldn't find the tag named `{}` with the class `{}` for url `{}` and idx `{}`".format(
            tag_name, class_name, url, idx))


def get_string_or_none(tag):
    '''

    i want actuall None instead of string none if a tag has no text as a child
    '''

    if len(tag.contents) == 1:
        return str(tag.string)
    else:
        return None

def wpull_games_list(parsed_args):

    logger.info("Beginning wpull of urls")

    # rest of the commands are dynamic and are added later
    wpull_command_list_prefix = [
        str(parsed_args.wpull_binary),
        "–no-check-certificate",
        "–no-robots",
        "–page-requisites",
        "–no-parent",
        "–sitemaps",
        "–inet4-only",
        "–timeout",
        "20",
        "–tries ",
        "3",
        "–waitretry ",
        "5",
        "–span-hosts",
        "–retry-connrefused",
        "–retry-dns-error",
        "–delete-after",
        "–warc-append",
        "-U ",
        USER_AGENT,
        "--warc-header ",
        "store.playstation.com 2020-10-25 archive by mgrandi",
        "--concurrent ",
        4]

    url_list = []
    with open(parsed_args.url_list, "r", encoding="utf-8") as f:
        while True:
            x = f.readline()
            if not x:
                break
            else:
                url_list.append(x)

    logger.info("got `%s` urls to download", len(url_list))

    for iter_url in url_list:

        logger.info("on url: `%s`", iter_url)




def get_games_list(parsed_args):

    logger.info("Beginning URL scrape")


    game_url_collection = GameUrlCollection(date_collected=arrow.utcnow().isoformat())

    page_counter = 1
    while True:

        current_url = URL_FORMAT_TEMPLATE.format(page_counter)

        logger.info("on url page index `%s`", page_counter)
        res = session.get(current_url, params=GET_PARAMS)

        if res.status_code != 200:
            logger.error("url `%s` did not return a good status code, it returned `%s`", current_url, res)
            raise Exception("URL `{}` raised status code `{}`".format(current_url, res.status_code))

        soup = BeautifulSoup(res.text, 'html.parser')

        # get current page number from webpage instead of guessing
        # we don't have a index yet so just pass in -1
        page_number_a_tag = get_tag_by_class_or_raise(soup, "a", "paginator-control__page-number--selected", current_url, -1)
        current_page_number_according_to_page = int(page_number_a_tag.string)

        if current_page_number_according_to_page != page_counter:
            logger.info("the current page index is `%s` but the page says its on page `%s`, we have probably reached the end, breaking loop")
            break


        # the list of tags that contain each game listing
        grid_cell_div_tags = soup.select("div.grid-cell")

        logger.debug("got `%s` grid cell div tags", len(grid_cell_div_tags))

        # get the ember JSON that we should have used instead of html scraping but i didn't find it until later, lol
        ember_view_json_str = None
        ember_view_json_script_tag = soup.select("script.ember-view")
        if len(ember_view_json_script_tag) == 1:
            ember_view_json_str = str(ember_view_json_script_tag[0].string)
        else:
            logger.error("couldn't find ember json?")
            raise Exception("couldn't find ember json on url `{}` and idx `{}`".format(current_url, idx) )

        game_url_collection.page_ember_json_dict["page_{}".format(page_counter)] = ember_view_json_str

        iter_count = 0;


        # iterate over each div tag that contains the info for a game
        for idx, iter_grid_cell_div_tag in enumerate(grid_cell_div_tags):

            title = None
            region = None
            url = None

            title_tag = get_tag_by_class_or_raise(iter_grid_cell_div_tag, "div", "grid-cell__title", current_url, idx)
            title = str(title_tag.span.string)


            # Remember that a single tag can have multiple values for its “class” attribute.
            # When you search for a tag that matches a certain CSS class, you’re matching against any of its CSS classes:
            url_tag = get_tag_by_class_or_raise(iter_grid_cell_div_tag, "a", "internal-app-link", current_url, idx)
            url = url_tag["href"]

            full_url = "{}{}".format(URL_ROOT, url)

            # https://store.playstation.com/en-us/product/UP9000-NPUA80001_00-FLOW_BUNDLE_____?scope=sceapp
            parsed_url = urllib.parse.urlparse(full_url)
            sku = parsed_url.path[parsed_url.path.rfind("/") + 1:]


            # TODO FIX
            region = "de-DE"


            # get metadata

            details_1_tag = get_tag_by_class_or_raise(iter_grid_cell_div_tag, "div", "grid-cell__left-detail--detail-1", current_url, idx)
            details_2_tag = get_tag_by_class_or_raise(iter_grid_cell_div_tag, "div", "grid-cell__left-detail--detail-2", current_url, idx)
            details_3_tag = get_tag_by_class_or_raise(iter_grid_cell_div_tag, "div", "grid-cell__left-detail--detail-3", current_url, idx)
            details_4_tag = get_tag_by_class_or_raise(iter_grid_cell_div_tag, "div", "grid-cell__left-detail--detail-4", current_url, idx)

            price_tag = iter_grid_cell_div_tag.find("h3", class_="price-display__price")

            unavail_tag = iter_grid_cell_div_tag.find("div", class_="grid-cell__ineligible-reason")

            meta = PlaystationStoreGameListingMetadata(
                store_page_number=int(page_counter),
                store_page_url=res.url,
                details_1=get_string_or_none(details_1_tag),
                details_2=get_string_or_none(details_2_tag),
                details_3=get_string_or_none(details_3_tag),
                details_4=get_string_or_none(details_4_tag),
                price=str(price_tag.string) if price_tag else None,
                unavailable_reason=str(unavail_tag.string).strip() if unavail_tag else None # seems to have whitespace and stuff
                )


            listing = PlaystationStoreGameListing(
                title=title,
                region=region,
                url=full_url,
                sku=sku,
                metadata=meta
                )


            game_url_collection.game_urls.append(listing)

            logger.debug("created PlaystationStoreGameListing: `%s`", listing)

            iter_count += 1

        logger.info("added `%s` PlaystationStoreGameListing objects", iter_count)


        page_counter += 1



    # import pprint
    # x = pprint.pformat(attr.asdict(game_url_collection))

    # logger.info("final collection: `%s`", x)

    logger.info("got `%s` games", len(game_url_collection.game_urls))

    with open(parsed_args.outfile, "w", encoding="utf-8") as f:

        dict_to_write = attr.asdict(game_url_collection)

        json.dump(dict_to_write, f, indent=4)

    logger.info("output written to `%s`", parsed_args.outfile)









