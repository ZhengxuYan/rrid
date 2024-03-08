import scrapy
import json
import csv
import logging
from datetime import datetime
from datetime import timedelta

class ChemrxivSpider(scrapy.Spider):
    name = 'chemrxiv'
    allowed_domains = ['chemrxiv.org']
    # get today's date in the format YYYY-MM-DD
    today = datetime.now().date().isoformat()
    # get the date 1 month ago in the format YYYY-MM-DD
    one_month_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
    print(one_month_ago)

    def __init__(self, server='chemrxiv', start_date=one_month_ago, end_date=today, *args, **kwargs):
        super(ChemrxivSpider, self).__init__(*args, **kwargs)
        self.logger.setLevel(logging.DEBUG)
        self.server = server
        # join the start and end date with a / to form the date range
        self.limit = 50
        self.skip = 0
        self.searchDateFrom = start_date
        self.searchDateTo = end_date
        self.file = open(f'results/{server}_results.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['Link/DOI', 'Publication Date', 'Title', 'Authors', 'Abstract']) # Add aug data

    def start_requests(self):
        url = f'https://chemrxiv.org/engage/chemrxiv/public-api/v1/items?limit={self.limit}&searchDateFrom={self.searchDateFrom}&searchDateTo={self.searchDateTo}'
        yield scrapy.Request(url=url, method='GET', callback=self.parse)

    def parse(self, response):
        data = json.loads(response.text)
        # self.logger.debug(json.dumps(data, indent=2))
        itemHits = data.get('itemHits')
        if itemHits:
            for item in itemHits:
                article = item.get('item')
                # self.logger.info(f'Article: {article}')
                authors = article.get('authors')
                # self.logger.info(f'Authors: {authors}')
                # parse aurthor.firstName and author.lastName and join them with a space
                authors_str = ' '.join([f"{author.get('firstName')} {author.get('lastName')}" for author in authors])
                
                # Remove or replace new line characters in abstract and title
                abstract = article.get('abstract', '').replace('\n', ' ').lower()
                title = article.get('title', '').replace('\n', ' ').lower()

                # date only needs year-month-day
                date = article.get('date')

                if article.get('doi') and article.get('title'):
                    # filter base on category
                    # make doi into a link
                    doi = "https://doi.org/" + article.get('doi')
                    self.writer.writerow([
                        doi,
                        article.get('publishedDate', ''),
                        title,
                        authors_str,
                        abstract
                    ])
        
        # Handling pagination
        self.skip += self.limit
        if self.skip < data.get('totalCount'):
            next_url = f'https://chemrxiv.org/engage/chemrxiv/public-api/v1/items?limit={self.limit}&searchDateFrom={self.searchDateFrom}&searchDateTo={self.searchDateTo}&skip={self.skip}'
            yield scrapy.Request(url=next_url, callback=self.parse)

    def close_spider(self, spider):
        self.file.close()
