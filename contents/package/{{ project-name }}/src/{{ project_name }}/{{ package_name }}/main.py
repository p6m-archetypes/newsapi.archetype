from eventregistry import *
from dotenv import load_dotenv
from concept_run import NewsAPIRetrieverWithConcept as concept_driver
from topic_run import NewsAPIRetrieverWithTopic as topic_driver
from shared_lib_driver.driver_lib.p6m.data.utils.md5.MD5Generator import MD5Source

logger = logging.getLogger()


class Constants:
    DRIVER_NAME = "newsapi"  # must match postgres database lookup table
    APPLICATION_NAME = DRIVER_NAME
    s3_CONCEPT_KEY = 'p6m/public/raw/newsapi/{}/{}/{}'
    s3_TOPIC_KEY = 'p6m/public/raw/newsapi/{}/topics/{}/{}/{}/{}'


class NewsAPI:
    def __init__(self):
        self.logger = None
        self.root_logger = logging.getLogger()

    def load_env_vars(self):
        try:
            load_dotenv('.env')
            newsapi_args = json.loads(os.getenv('NEWSAPI_ARGS'))
            module_type = newsapi_args['module_type']
            query_params = newsapi_args['run_params']

            return module_type, query_params

        except Exception as e:
            logger.info(" Error loading env file, expecting MODULE_TYPE and RUN_PARAMS")

    def run(self):
        self.root_logger.setLevel(logging.INFO)

        # NOTE  sample payload
        """
        
         {  
            "module_type": "concept_run", 
            "run_params": ""
        }
        module_name: notifies that news_api is the module that we're running it for.
        module_type: can be either of the values: 'concept_run' or 'topic_run'
        params: the query parameters for the type of module selected
        """

        logging.info(">> Loading env variables... ")
        module_type, run_params = self.load_env_vars()
        logging.info(f"Initial env vars as: module_type:: {module_type}, run_params::{run_params}")

        inputs = json.loads(run_params.replace("'", '"'))

        if module_type == "":
            self.root_logger.info(f"missing module_type - {module_type}")
            return

        if module_type == 'concept_run':
            # concept_driver
            news_api_retriever = concept_driver(inputs)
            epoch_timestamp = int(time.time())
            json_file = f'newsapi_{epoch_timestamp}.jsonl'
            json_filename = news_api_retriever.save_articles_to_json(news_api_retriever.articles, json_file)
            # Pass the input JSON and delimiter to the MD5Generator
            concept_json = news_api_retriever.inputs["query"]
            md5_generator = MD5Source(input_json=concept_json, keys_to_exclude=None, delimiter='|')
            concept_query_id = MD5Source.generate_md5_hash(md5_generator)
            s3_concept_key = Constants.s3_CONCEPT_KEY.format(news_api_retriever.concept,
                                                             concept_query_id, news_api_retriever.epoch_timestamp)
            s3_file = news_api_retriever.upload_to_s3(json_filename, s3_concept_key)

            self.root_logger.info(f">> Checksum = {md5_generator.query_id} completed..")
            self.root_logger.info(f"\n===============Completed=================\n")

        elif module_type == 'topic_run':
            news_api_topic_obj = topic_driver(inputs)
            epoch_timestamp = int(time.time())
            json_filename = f'newsapi_{epoch_timestamp}.jsonl'
            topic_uri, company_name, topic = news_api_topic_obj.retrieve_articles()
            # Load the topic page
            topic.loadTopicPageFromER(topic_uri)
            articles = []
            md5_generator = MD5Source(input_json=inputs, keys_to_exclude=None, delimiter='|')
            topic_query_id = MD5Source.generate_md5_hash(md5_generator)
            s3_topic_key = Constants.s3_TOPIC_KEY.format(company_name, topic_uri,
                                                         topic_query_id, epoch_timestamp, json_filename)
            news_api_topic_obj.run_topic_articles(topic, articles, company_name, topic_uri, s3_topic_key, json_filename)
            s3_topic_file = news_api_topic_obj.save_articles_to_s3(articles, s3_topic_key, json_filename, 'jsonl')
            news_api_topic_obj.save_query_parameters('topic')

            self.root_logger.info(f"Checksum = {md5_generator.query_id} completed..")
            self.root_logger.info(f"\n===============Completed=================\n")


if __name__ == '__main__':
    newsapi_obj = NewsAPI()
    newsapi_obj.run()
    logger.info(" Completed the run for NewsAPI module.")
