import logging
import json

from wpull.application.plugin import WpullPlugin, PluginFunctions, hook, event
from wpull.pipeline.session import ItemSession

import jmespath

logger = logging.getLogger(__name__)


VALKYRIE_URL_PREFIX = "https://store.playstation.com/valkyrie-api/"
CHIHIRO_URL_PREFIX = "https://store.playstation.com/store/api/chihiro/"



class PsStoreJsonApiWpullPlugin(WpullPlugin):





    def __debug_logging_tree(self):

        import logging_tree
        print("{}".format( logging_tree.format.build_description(node=None)))



    def activate(self):

        super().activate()

        self.valkyrie_jmespath_expressions = [
            jmespath.compile('''included[*].attributes."content-rating".url'''),
            jmespath.compile('''included[*].attributes."thumbnail-url-base"'''),
            jmespath.compile('''included[*].attributes.parent.thumbnail'''),
            jmespath.compile('''included[*].attributes."media-list".preview[*].url[]'''),
            jmespath.compile('''included[*].attributes."media-list".promo.images[*].url[]'''),
            jmespath.compile('''included[*].attributes."media-list".promo.videos[*].url[]'''),
            jmespath.compile('''included[*].attributes."media-list".screenshots[*].url[]'''),


            ]

        logger.info("activate()")

    def deactivate(self):
        super().deactivate()

        logger.info("deactivate()")

    @event(PluginFunctions.get_urls)
    def my_get_urls(self, item_session: ItemSession):

        the_url = item_session.request.url

        logger.info("get_urls() for url `%s`", the_url)


        if the_url.startswith(VALKYRIE_URL_PREFIX):

            valkyrie_urls = self.process_valkyrie_result(item_session)

            for iter_url in valkyrie_urls:

                item_session.add_child_url(iter_url)


        elif the_url.startswith(CHIHIRO_URL_PREFIX):

            self.process_chihiro_result(item_session)

        else:

            logger.info("url doesn't start with JSON api prefix, not adding any new urls")
            # not one of the main JSON api urls, don't add any new urls



    def process_chihiro_result(self, item_session:ItemSession):

        pass

    def process_valkyrie_result(self, item_session:ItemSession):

        json_obj = None
        url = item_session.request.url

        urls_to_add_set = set()

        try:

            if item_session.response.body.content is None:
                logger.info("the json body is none?")
                return set()

            json_obj = json.loads(item_session.response.body.content())

            logger.info("parsed successfully")

            for iter_jmespath_expr in self.valkyrie_jmespath_expressions:

                result_list = iter_jmespath_expr.search(json_obj)

                logger.info("the expr `%s` found result: `%s`", iter_jmespath_expr, result_list)

                # deduplicate urls
                result_set = set(result_list)


                if result_set:
                    urls_to_add_set.update(result_set)


            logger.info("urls parsed from url `%s` were: `%s`", url, urls_to_add_set)

        except Exception as e:

            logger.exception("Problem decoding the body as JSON for the url `%s`", url)
            return set()

        return urls_to_add_set


