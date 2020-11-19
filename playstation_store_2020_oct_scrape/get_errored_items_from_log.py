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

    total_items_count = 0
    errored_item_list = []
    valkyrie_failed = False
    chihiro_failed = False
    current_api_entry = None
    logger.info("Opening log file: `%s`", parsed_args.source_log)
    with open(parsed_args.source_log, "r", encoding="utf-8") as source_log_fh:
        for line in source_log_fh:
            if line != "\n":

                if item_start_regex_obj.search(line) or log_end_regex_obj.search(line):
                    total_items_count += 1
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

    logger.info("found `%s` failed items out of %s total items for a failure rate of %s%%", len(errored_item_list), total_items_count, len(errored_item_list)/total_items_count*100)

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
    if parsed_args.only_valkyrie_failures:
        logger.info("Writing only items with valkyrie failures and no chihiro failures")
    if parsed_args.only_chihiro_failures:
        logger.info("Writing only items with chihiro failures and no valkyrie failures")

    # Prepare the output based on the provided switches
    if parsed_args.output_as_URLs:
        if parsed_args.only_dual_failures:
            print_item_list = [x for item in errored_item_list for x in (item.api.valkyrie_url, item.api.chihiro_url)
                               if item.valkyrie_failed and item.chihiro_failed]
        elif parsed_args.only_valkyrie_failures:
            print_item_list = [item.api.valkyrie_url for item in errored_item_list
                               if item.valkyrie_failed and not item.chihiro_failed]
        elif parsed_args.only_chihiro_failures:
            print_item_list = [item.api.chihiro_url for item in errored_item_list
                               if not item.valkyrie_failed and item.chihiro_failed]
        else:
            print_item_list = [x for item in errored_item_list for x in (item.api.valkyrie_url, item.api.chihiro_url)]
    else:
        if parsed_args.only_dual_failures:
            print_item_list = [item.api.sku for item in errored_item_list
                               if item.valkyrie_failed and item.chihiro_failed]
        elif parsed_args.only_valkyrie_failures:
            print_item_list = [item.api.sku for item in errored_item_list
                               if item.valkyrie_failed and not item.chihiro_failed]
        elif parsed_args.only_chihiro_failures:
            print_item_list = [item.api.sku for item in errored_item_list
                               if not item.valkyrie_failed and item.chihiro_failed]
        else:
            print_item_list = [item.api.sku for item in errored_item_list]


    with open(parsed_args.error_item_output_file, "w", encoding="utf-8", newline="\n") as f:
        for item in print_item_list:
            f.write("{}\n".format(item))
