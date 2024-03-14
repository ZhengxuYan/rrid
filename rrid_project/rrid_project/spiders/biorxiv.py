import scrapy
import json
import csv
import logging
from datetime import datetime
from datetime import timedelta

class BiorxivSpider(scrapy.Spider):
    name = 'biorxiv'
    allowed_domains = ['api.biorxiv.org']
    # get today's date in the format YYYY-MM-DD
    today = datetime.now().date().isoformat()
    # get the date 1 month ago in the format YYYY-MM-DD
    three_month_ago = (datetime.now() - timedelta(days=90)).date().isoformat()

    def __init__(self, server='biorxiv', start_date=three_month_ago, end_date=today, *args, **kwargs):
        super(BiorxivSpider, self).__init__(*args, **kwargs)
        self.logger.setLevel(logging.DEBUG)
        self.server = server
        # join the start and end date with a / to form the date range
        self.interval = f'{start_date}/{end_date}'
        self.cursor = 0
        self.file = open(f'results/{server}_results.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['Link/DOI', 'Publication Date', 'Title', 'Authors', 'Abstract'])

    def start_requests(self):
        url = f'https://api.biorxiv.org/pubs/{self.server}/{self.interval}/{self.cursor}'
        yield scrapy.Request(url=url, method='GET', callback=self.parse)
    
    def parse(self, response):
        data = json.loads(response.text)
        # self.logger.debug(json.dumps(data, indent=2))
        articles = data.get('collection', [])

        for article in articles:
            # biorxiv has closed their epidemiology category!!!
            # article_category = article.get('preprint_category').lower()
            # self.logger.info(f'Article category: {article_category}')
            # if article_category != 'epidemiology':
            #     continue  # Skip articles not in the specified category

            authors = article.get('preprint_authors', [])
            # Convert the list directly to a string representation
            authors_str = str([authors])
            
            # Remove or replace new line characters in abstract and title
            abstract = article.get('preprint_abstract', '').replace('\n', ' ').lower()
            title = article.get('preprint_title', '').replace('\n', ' ').lower()

            if article.get('preprint_doi') and article.get('preprint_title'):
                # filter base on category
                # make doi into a link
                doi = "https://doi.org/" + article.get('preprint_doi')
                self.writer.writerow([
                    doi,
                    article.get('published_date', ''),
                    title,
                    authors_str,
                    abstract
                ])
        
        # Handling pagination
        messages = data.get('messages', [])
        # self.logger.debug(json.dumps(messages, indent=2))
        if messages:
            message = messages[0]
            count = message.get('count', 0)
            next_cursor = message.get('cursor', None)
            # self.logger.info(f'Next cursor: {next_cursor}')

            if next_cursor is not None:
                self.cursor = int(next_cursor) + count  # Ensure cursor is updated based on API response
                next_url = f'https://api.biorxiv.org/pubs/{self.server}/{self.interval}/{self.cursor}'
                yield scrapy.Request(url=next_url, callback=self.parse)

    def close_spider(self, spider):
        self.file.close()
