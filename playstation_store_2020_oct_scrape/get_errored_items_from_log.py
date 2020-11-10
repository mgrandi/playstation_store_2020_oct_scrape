import time
import logging
import attr
import re
from playstation_store_2020_oct_scrape.warcio_scrape import ApiEntry

logger = logging.getLogger(__name__)

@attr.s
class ErrorItem:
    api:ApiEntry = attr.ib()
    valkyrie_failed:bool = attr.ib()
    chihiro_failed:bool = attr.ib()

def run(parsed_args):
    item_start_regex_obj = re.compile(r"warcio_scrape INFO    \: \`[0-9]+ \/ [0-9]+\`")
    item_sku_regex_obj = re.compile(r"sku='([0-9a-zA-Z\-\_]+)'")
    item_valkyrie_regex_obj = re.compile(r"valkyrie_url='([0-9a-zA-Z\-\_\:\/\.]+)'")
    item_chihiro_regex_obj = re.compile(r"chihiro_url='([0-9a-zA-Z\-\_\:\/\.]+)'")
    item_skipped_regex_obj = re.compile(r"hit `[0-9]+` retries")
    old_valkyrie_skipped_regex_obj = re.compile(r"ApiEntry")
    new_valkyrie_skipped_regex_obj = re.compile(r"URL `https:\/\/store\.playstation\.com\/valkyrie-api")
    chihiro_skipped_regex_obj = re.compile(r"URL `https:\/\/store\.playstation\.com\/store\/api\/chihiro")
    log_end_regex_obj = re.compile(r": start time: `")

    errored_item_list = []
    valkyrie_failed = False
    chihiro_failed = False
    current_api_entry = None
    logger.info("Opening log file: `%s`", parsed_args.source_log)
    with open(parsed_args.source_log, "r", encoding="utf-8") as source_log_fh:
        for line in source_log_fh:
            if line != "\n":

                if item_start_regex_obj.search(line) or log_end_regex_obj.search(line):
                    # Previous item has now ended, so store
                    # results if necessary
                    if current_api_entry is not None and (valkyrie_failed or chihiro_failed):
                        sku_list = [x.api.sku for x in errored_item_list]
                        # Only add unique entries
                        if current_api_entry.sku not in sku_list:
                            errored_item_list.append(ErrorItem(current_api_entry, valkyrie_failed, chihiro_failed))

                    if log_end_regex_obj.search(line):
                        break

                    # Setup for the next item
                    valkyrie_failed = False
                    chihiro_failed = False
                    sku = item_sku_regex_obj.search(line).group(1)
                    valkyrie_url = item_valkyrie_regex_obj.search(line).group(1)
                    chihiro_url = item_chihiro_regex_obj.search(line).group(1)
                    current_api_entry = ApiEntry(sku=sku,valkyrie_url=valkyrie_url, chihiro_url=chihiro_url)

                if item_skipped_regex_obj.search(line):
                    if old_valkyrie_skipped_regex_obj.search(line) or new_valkyrie_skipped_regex_obj.search(line):
                        valkyrie_failed = True

                    if chihiro_skipped_regex_obj.search(line):
                        chihiro_failed = True

    logger.info("found `%s` failed items", len(errored_item_list))

    errored_valkyrie_list = [x.api for x in errored_item_list if x.valkyrie_failed and not x.chihiro_failed]
    errored_chihiro_list = [x.api for x in errored_item_list if x.chihiro_failed and not x.valkyrie_failed]
    errored_both_list = [x.api for x in errored_item_list if x.valkyrie_failed and x.chihiro_failed]

    logger.info("-- `%s` have failed valkyrie links only", len(errored_valkyrie_list))
    logger.info("-- `%s` have failed chihiro links only", len(errored_chihiro_list))
    logger.info("-- `%s` have both failed valkyrie and chihiro links", len(errored_both_list))

    logger.info("Writing to %s", parsed_args.error_item_output_file)
    if parsed_args.output_as_URLs:
        logger.info("Writing out URLs instead of IDs")
    if parsed_args.only_dual_failures:
        logger.info("Writing only items with dual failures")

    if parsed_args.output_as_URLs:
        with open(parsed_args.error_item_output_file, "w", encoding="utf-8", newline="\n") as f:
            for item in errored_item_list:
                if parsed_args.only_dual_failures:
                    if item.valkyrie_failed and item.chihiro_failed:
                        f.write("{}\n".format(item.api.valkyrie_url))
                        f.write("{}\n".format(item.api.chihiro_url))
                else:
                    if item.valkyrie_failed:
                        f.write("{}\n".format(item.api.valkyrie_url))
                    if item.chihiro_failed:
                        f.write("{}\n".format(item.api.chihiro_url))
    else:
        with open(parsed_args.error_item_output_file, "w", encoding="utf-8", newline="\n") as f:
            for item in errored_item_list:
                if parsed_args.only_dual_failures:
                    if item.valkyrie_failed and item.chihiro_failed:
                        f.write("{}\n".format(item.api.sku))
                else:
                    f.write("{}\n".format(item.api.sku))
