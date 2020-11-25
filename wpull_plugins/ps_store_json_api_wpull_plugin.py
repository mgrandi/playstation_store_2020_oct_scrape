import logging
import json
import enum
import attr

from wpull.application.plugin import WpullPlugin, PluginFunctions, hook, event
from wpull.pipeline.session import ItemSession

import jmespath

logger = logging.getLogger(__name__)


VALKYRIE_URL_PREFIX = "https://store.playstation.com/valkyrie-api/"
CHIHIRO_URL_PREFIX = "https://store.playstation.com/store/api/chihiro/"


class UrlType(enum.Enum):
    VALKYRIE = 1
    CHIHIRO = 2


class PsStoreJsonApiWpullPlugin(WpullPlugin):



    def __debug_logging_tree(self):

        import logging_tree
        print("{}".format( logging_tree.format.build_description(node=None)))



    def activate(self):

        super().activate()

        # use `[]` instead of `[*]` to flatten projections
        # see https://jmespath.org/tutorial.html#flatten-projections
        self.valkyrie_jmespath_expressions = [
            jmespath.compile('''included[].attributes."content-rating".url'''),
            jmespath.compile('''included[].attributes."thumbnail-url-base"'''),
            jmespath.compile('''included[].attributes.parent.thumbnail'''),
            jmespath.compile('''included[].attributes."media-list".preview.url'''),
            jmespath.compile('''included[].attributes."media-list".promo.images[].url'''),
            jmespath.compile('''included[].attributes."media-list".promo.videos[].url'''),
            jmespath.compile('''included[].attributes."media-list".screenshots[].url'''),
            ]

        self.chihiro_jmespath_expressions = [
            jmespath.compile('''content_rating.url'''),
            jmespath.compile('''images[].url'''),
            jmespath.compile('''promomedia[].materials[].urls[].url'''),


        ]

        logger.info("activate()")

    def deactivate(self):
        super().deactivate()

        logger.info("deactivate()")

    @event(PluginFunctions.get_urls)
    def my_get_urls(self, item_session: ItemSession):

        the_url = item_session.request.url

        logger.info("get_urls() for url `%s`", the_url)


        if the_url.startswith(VALKYRIE_URL_PREFIX) or the_url.startswith(CHIHIRO_URL_PREFIX):

            the_type = None
            if the_url.startswith(VALKYRIE_URL_PREFIX):
                the_type = UrlType.VALKYRIE
            elif the_url.startswith(CHIHIRO_URL_PREFIX):
                the_type = UrlType.CHIHIRO
            else:
                raise Exception("unknown url prefix? `%s`", the_url)

            urls = self.process_result(the_type, item_session)

            for iter_url in urls:

                item_session.add_child_url(iter_url)
        else:

            logger.info("url doesn't start with JSON api prefix, not adding any new urls")
            # not one of the main JSON api urls, don't add any new urls



    def process_result(self, url_type:UrlType, item_session:ItemSession):

        json_obj = None
        url = item_session.request.url

        urls_to_add_set = set()

        jmespath_expr_list = None

        if url_type == UrlType.VALKYRIE:
            jmespath_expr_list = self.valkyrie_jmespath_expressions
        elif url_type == UrlType.CHIHIRO:
            jmespath_expr_list = self.chihiro_jmespath_expressions
        else:
            raise Exception("prcoess_result(): unknown url type `{}`".format(url_type))

        try:

            if item_session.response.body.content is None:
                logger.info("`process_result() - %s`: the json body is none?", url_type)
                return set()

            json_obj = json.loads(item_session.response.body.content())

            logger.info("`process_result() - %s`: parsed successfully", url_type)

            for iter_jmespath_expr in jmespath_expr_list:

                result_set = None
                result_obj = iter_jmespath_expr.search(json_obj)

                logger.info("`process_result() - %s`: the expr `%s` found result: `%s`", url_type, iter_jmespath_expr, result_obj)

                # convert into a set if its not
                # it could be a bare string
                if isinstance(result_obj, str):
                    result_set = {result_obj}
                else:
                    # we got a list, convert to a set to deduplicate urls
                    result_set = set(result_obj)


                if result_set:
                    urls_to_add_set.update(result_set)


            logger.info("`process_result() - %s`: urls parsed from url `%s` were: `%s`", url_type, url, urls_to_add_set)

        except Exception as e:

            logger.exception("`process_result() - %s`: Problem decoding the body as JSON for the url `%s`", url_type, url)
            return set()

        return urls_to_add_set


