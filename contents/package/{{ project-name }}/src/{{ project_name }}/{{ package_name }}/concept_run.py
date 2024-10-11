import boto3
import pandas as pd
from dotenv import load_dotenv
from eventregistry import *

load_dotenv()


class NewsAPIRetrieverWithConcept:
    def __init__(self, inputs):
        self.setup_logging()
        self.load_credentials()
        self.inputs = inputs
        self.retrieve_articles()
        self.save_query_parameters('concept')
        self.epoch_timestamp = int(time.time())

    def setup_logging(self):
        log_filename = "news_api_concept.log"
        logging.basicConfig(filename=log_filename, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(__name__)

    def load_credentials(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION")
        self.s3_bucket_name = os.getenv("BUCKET_NAME")

    def retrieve_articles(self):
        # with open("concept_input.json", "r") as json_file:
        #     self.inputs = json.load(json_file)

        self.concept = self.inputs["concept"]
        query = self.inputs["query"]
        max_items = self.inputs["maxItems"]
        er = EventRegistry(apiKey=os.getenv("API_KEY"))
        q = QueryArticlesIter.initWithComplexQuery(query)
        articles = []
        if max_items is None:
            self.logger.info("Processing all articles since maxItems settings is not provided")
            max_items = q.count(er)

        # change maxItems to get the number of results that you want
        for article in q.execQuery(er, maxItems=max_items):
            # update language code to 2 chars
            article['lang'] = article['lang'][0:2]
            articles.append(article)

        self.logger.info("Number of results: %d" % q.count(er))
        self.articles = articles

        if isinstance(self.concept, list):
            self.concept = "_".join(self.concept)
        self.concept = self.concept.replace(' ', '_')

    @staticmethod
    def update_lang(lang):
        lang = lang[:2]
        return lang

    def save_articles_to_csv(self, articles):
        epoch_timestamp = int(time.time())
        df = pd.DataFrame(articles)
        csv_filename = f'newsapi_{epoch_timestamp}.csv'
        df.to_csv(csv_filename, index=False)
        self.logger.info("Saved articles to {} with count: {}".format(csv_filename, len(df.index)))
        return csv_filename

    def save_articles_to_json(self, articles, json_filename):
        df = pd.DataFrame(articles)
        df['lang'] = df.apply(lambda row: self.update_lang(row['lang']), axis=1)
        df.to_json(json_filename, orient='records', lines=True)
        self.logger.info("Saved articles to {} with count: {}".format(json_filename, len(df.index)))
        return json_filename

    def upload_to_s3(self, filename, s3_key):
        s3 = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region,
        )
        try:
            s3.upload_file(filename, self.s3_bucket_name, s3_key + '/' + filename)
            # s3.upload_file("query_parameters_concept.json", self.s3_bucket_name, s3_key + '/' +
            #                "query_parameters_concept.json")

            self.logger.info(f"Uploaded {filename} and query_parameters.json to S3 bucket: s3://{self.s3_bucket_name}/{s3_key}")
            return self.s3_bucket_name + '/' + s3_key + '/' + filename
        except Exception as e:
            self.logger.error(f"Failed to upload files to S3: {str(e)}")


    def save_query_parameters(self, type):
        with open(f"query_parameters_{type}.json", "w") as json_file:
            json.dump(self.inputs, json_file, indent=4)
        self.logger.info("Saved query parameters to query_parameters_topic.json")