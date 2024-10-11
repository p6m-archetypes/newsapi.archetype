import boto3
import pandas as pd
from dotenv import load_dotenv
from eventregistry import *

load_dotenv()

class NewsAPIRetrieverWithTopic:
    def __init__(self, inputs):
        self.setup_logging()
        self.load_credentials()
        self.inputs = inputs
        # self.retrieve_articles()
        # self.save_query_parameters('topic')

    def setup_logging(self):
        log_filename = "news_api_topic.log"
        logging.basicConfig(filename=log_filename, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(__name__)

    def load_credentials(self):
        self.API_KEY = os.getenv("API_KEY")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION")
        self.s3_bucket_name = os.getenv("BUCKET_NAME")

    def retrieve_articles(self):
        # with open("topic_input.json", "r") as json_file:
        #     self.inputs = json.load(json_file)

        topic_uri = self.inputs["topic_uri"]
        company_name = self.inputs["company_name"]

        er = EventRegistry(apiKey=self.API_KEY)
        topic = TopicPage(er)
        # Load the topic page
        # topic.loadTopicPageFromER(topic_uri)
        # articles = []
        # self.run_topic_articles(topic, articles, company_name, topic_uri)
        return topic_uri, company_name, topic

    def run_topic_articles(self, topic, articles, company_name, topicuri, s3_topic_key, csv_filename):
        page = 1
        while True:
            # Get articles for the current page
            arts = topic.getArticles(page=page, sortBy="date")
            # Check if there are no more articles on the page
            if not arts['articles']['results']:
                break
            # Append the articles to the list
            articles.extend(arts['articles']['results'])
            # Increment the page number
            page += 1

        # self.save_csv_articles_to_s3(self, articles, company_name, topicuri, s3_topic_key, csv_filename)

    @staticmethod
    def update_lang(lang):
        lang = lang[:2]
        return lang


    def save_articles_to_s3(self, articles, s3_topic_key, filename, filetype):
        s3 = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region,
        )
        num_articles = len(articles)
        df = pd.DataFrame(articles)
        df['lang'] = df.apply(lambda row: self.update_lang(row['lang']), axis=1)

        if filetype == 'csv':
            df.to_csv(filename, index=False)
        elif filetype == 'jsonl':
            df.to_json(filename, orient='records', lines=True)

        s3.upload_file(filename, self.s3_bucket_name, s3_topic_key)
        file_dir = '/'.join(s3_topic_key.split('/')[:-1])
        # s3.upload_file("query_parameters_topic.json", self.s3_bucket_name, file_dir + "/query_parameters_topic.json")

        self.logger.info("Saved articles to {} with count: {}".format(filename, len(df.index)))
        self.logger.info(f"Total number of articles extracted: {num_articles}")
        self.logger.info(f"All articles downloaded and uploaded to S3 at s3://{self.s3_bucket_name}/{s3_topic_key}")
        return self.s3_bucket_name + '/' + s3_topic_key + '/' + filename

    def save_query_parameters(self, type):
        with open(f"query_parameters_{type}.json", "w") as json_file:
            json.dump(self.inputs, json_file, indent=4)
        self.logger.info("Saved query parameters to query_parameters_topic.json")