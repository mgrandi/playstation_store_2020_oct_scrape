
import logging
import lzma


logger = logging.getLogger(__name__)

VALKYRIE_API_URL_FORMAT = "https://store.playstation.com/valkyrie-api/{}/{}/999/resolve/{}"
CHIHIRO_API_URL_FORMAT = "https://store.playstation.com/store/api/chihiro/00_09_000/container/{}/{}/999/{}"

def run(parsed_args):


    region_lang = parsed_args.region_lang
    region_country = parsed_args.region_country

    input_file_path = parsed_args.content_ids_file
    output_file_path = parsed_args.output_file

    file_obj = None

    if input_file_path.suffix == ".xz":

        logger.info("reading the file `%s` as a XZ compressed text file", input_file_path)

        file_obj = lzma.open(input_file_path, "rt")

    else:

        logger.info("reading the file `%s` as a text file", input_file_path)

        file_obj = open(input_file_path, "r", encoding="utf-8")


    with open(output_file_path, "w", encoding="utf-8") as f:

        while True:

            content_id = file_obj.readline().strip()

            if not content_id:
                break

            valkyrie_url = VALKYRIE_API_URL_FORMAT.format(region_lang, region_country, content_id)
            chihiro_url = CHIHIRO_API_URL_FORMAT.format(region_country, region_lang, content_id)

            f.write("{}\n".format(valkyrie_url))
            f.write("{}\n".format(chihiro_url))

    file_obj.close()



