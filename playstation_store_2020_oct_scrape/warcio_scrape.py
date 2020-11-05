import time
import json
import logging
import random

from warcio.capture_http import capture_http
import requests  # requests must be imported after capture_http
import attr
import arrow

logger = logging.getLogger(__name__)

@attr.s
class ApiEntry:
    sku:str = attr.ib()
    valkyrie_url:str = attr.ib()
    chihiro_url:str = attr.ib()

def do_warcio_scrape(parsed_args):

    TIME_SECONDS_TO_SLEEP_BETWEEN_FAILURES = 5

    KEY_TYPE = "type"
    KEY_INCLUDED = "included"
    KEY_THUMBNAIL_BASE = "thumbnail-url-base"
    KEY_PARENT = "parent"
    KEY_MEDIA_LIST = "media-list"
    KEY_PROMO = "promo"
    KEY_IMAGES = "images"
    KEY_VIDEOS = "videos"
    KEY_SCREENSHOTS = "screenshots"
    KEY_PREVIEW = "preview"
    KEY_URL = "url"
    KEY_THUMBNAIL = "thumbnail"
    KEY_ID = "id"
    KEY_NAME = "name"
    KEY_ATTRIBUTES = "attributes"
    KEY_DEFAULT_SKU = "default-sku-id"

    MAX_RETRIES = 5

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0"

    HEADERS = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache",
        "Dnt": "1",
        "Host": "store.playstation.com",
        "User-Agent": USER_AGENT,
      }

    VALKYRIE_API_URL_FORMAT = "https://store.playstation.com/valkyrie-api/{}/{}/999/resolve/{}"
    CHIHIRO_API_URL_FORMAT = "https://store.playstation.com/store/api/chihiro/00_09_000/container/{}/{}/999/{}"


    api_entry_list = []
    discovered_media_url_list = []

    session = requests.Session()
    session.headers.update(HEADERS)

    start_time = arrow.utcnow()

    with open(parsed_args.sku_list, "r", encoding="utf-8") as file_list_fh:
        while True:
            sku = file_list_fh.readline()
            if not sku:
                break
            else:
                sku_stripped = sku.strip()
                valkyrie_url = VALKYRIE_API_URL_FORMAT.format(parsed_args.region_lang, parsed_args.region_country, sku_stripped)
                chihiro_url = CHIHIRO_API_URL_FORMAT.format(parsed_args.region_country, parsed_args.region_lang, sku_stripped)
                api_entry_list.append(ApiEntry(sku=sku_stripped, valkyrie_url=valkyrie_url, chihiro_url=chihiro_url))

    api_entry_list_size = len(api_entry_list)
    logger.info("have `%s` urls to download", api_entry_list_size)
    logger.info("writing media urls to `%s`", parsed_args.media_files_output_file)


    # the capture_http method probably doesn't take a path objet
    with capture_http(str(parsed_args.warc_output_file), warc_version='1.1'):

        for idx, iter_api_entry in enumerate(api_entry_list):

            # prevent DDOS hopefully...
            # time_to_sleep = random.random()
            # logger.info("[sleeping for `%s`]", time_to_sleep)
            # time.sleep(time_to_sleep)

            iter_discovered_media_list = []

            logger.info("`%s / %s`: url: `%s`", idx, api_entry_list_size, iter_api_entry)


            logger.debug("-- making valkyrie api request")
            # get normal valkyrie response
            success = False
            response = None
            response_json = None
            for i in range(MAX_RETRIES):

                try:

                    response = session.get(iter_api_entry.valkyrie_url)
                    logger.info("-- url `%s` - HTTP `%s`", iter_api_entry.valkyrie_url, response.status_code)

                    response.raise_for_status()
                    success = True
                    response_json = response.json()
                    break

                except Exception as e:
                    logger.error("-- error number `%s` when getting url `%s`: `%s`", i, iter_api_entry, e)
                    time.sleep(TIME_SECONDS_TO_SLEEP_BETWEEN_FAILURES)
                    continue

            if not success:
                logger.error("-- hit `%s` retries when attempting to get URL `%s`, skipping", MAX_RETRIES, iter_api_entry)
                continue

            else:

                # go through the json and get media urls

                included_json_list = response_json[KEY_INCLUDED]

                for iter_included_json_dict in included_json_list:

                    iter_attribute_json_dict = iter_included_json_dict[KEY_ATTRIBUTES]

                    # get the thumbnail, but check to make sure its there, not
                    # all of the attribute dicts have it for some reason, like if there
                    # is a bundle, one will have it, the other won't
                    if KEY_THUMBNAIL_BASE in iter_attribute_json_dict.keys():
                        thumbnail = iter_attribute_json_dict[KEY_THUMBNAIL_BASE]
                        logger.debug("-- found media url (thumbnail): `%s`", thumbnail)
                        iter_discovered_media_list.append(thumbnail)

                    # see if there are other media urls

                    ## look in parent dict

                    if KEY_PARENT in iter_attribute_json_dict.keys() and iter_attribute_json_dict[KEY_PARENT] is not None:
                        parent_json_dict = iter_attribute_json_dict[KEY_PARENT]

                        parent_id = parent_json_dict[KEY_ID]
                        # output parent id just in case

                        thumbnail = parent_json_dict[KEY_THUMBNAIL]

                        logger.debug("-- found media url (parent - thumbnail): `%s`", thumbnail)
                        iter_discovered_media_list.append(thumbnail)

                    # media list stuff

                    if KEY_MEDIA_LIST in iter_attribute_json_dict.keys():

                        media_list_dict = iter_attribute_json_dict[KEY_MEDIA_LIST]

                        for iter_preview_dict in media_list_dict[KEY_PREVIEW]:

                            preview_url = iter_preview_dict[KEY_URL]
                            logger.debug("-- found media url (media list - previews): `%s`", preview_url)
                            iter_discovered_media_list.append(preview_url)

                        for iter_promos_images_dict in media_list_dict[KEY_PROMO][KEY_IMAGES]:

                            image_url = iter_promos_images_dict[KEY_URL]
                            logger.debug("-- found media url (media list - promos - images): `%s`", image_url)
                            iter_discovered_media_list.append(image_url)

                        for iter_promos_videos_dict in media_list_dict[KEY_PROMO][KEY_VIDEOS]:

                            vid_url = iter_promos_videos_dict[KEY_URL]
                            logger.debug("-- found media url (media list - promos - videos): `%s`", vid_url)
                            iter_discovered_media_list.append(vid_url)

                        for iter_screenshot_dict in media_list_dict[KEY_SCREENSHOTS]:

                            ss_url = iter_screenshot_dict[KEY_URL]
                            logger.debug("-- found media url (media list - screenshots): `%s`", ss_url)
                            iter_discovered_media_list.append(ss_url)


            logger.debug("-- making chihiro api request")
            success_two = False
            response_two = None
            response_json_two = None
            for i in range(MAX_RETRIES):

                try:

                    response_two = session.get(iter_api_entry.chihiro_url)
                    logger.info("-- url `%s` - HTTP `%s`", iter_api_entry.chihiro_url, response_two.status_code)

                    response_two.raise_for_status()
                    success_two = True
                    response_json_two = response_two.json()

                    break

                except Exception as e:
                    logger.error("-- error number `%s` when getting url `%s`: `%s`", i, chihiro_url, e)
                    time.sleep(TIME_SECONDS_TO_SLEEP_BETWEEN_FAILURES)
                    continue

            if not success_two:
                logger.error("-- hit `%s` retries when attempting to get URL `%s`, skipping", MAX_RETRIES, chihiro_url)
                continue

            else:

                # get media urls

                # only getting these for now, as they are higher resolution then the ones that the valkyrie api returns

                image_dict_list = response_json_two[KEY_IMAGES]

                for iter_image_dict in image_dict_list:

                    image_type = iter_image_dict[KEY_TYPE]
                    image_url = iter_image_dict[KEY_URL]
                    logger.debug("-- found media url (chihiro images): `%s` of type `%s`", image_url, image_type)
                    iter_discovered_media_list.append(image_url)

            num_media_this_run = len(iter_discovered_media_list)
            logger.debug("-- discovered `%s` media urls for this URL", num_media_this_run)
            discovered_media_url_list.extend(iter_discovered_media_list)
            logger.debug("-- discovered media list now has a size of `%s`", len(discovered_media_url_list))

            # write out the new media discovered this iteration in case we crash
            with open(parsed_args.media_files_output_file, "a", encoding="utf-8", newline="\n") as f:

                for iter_media_url in iter_discovered_media_list:
                    f.write("{}\n".format(iter_media_url))

    end_time = arrow.utcnow()

    elapsed_time = end_time - start_time

    logger.info("start time: `%s`, end time: `%s`, elapsed time: `%s`", start_time, end_time, elapsed_time)
    logger.info("discovered `%s` media urls", len(discovered_media_url_list))



