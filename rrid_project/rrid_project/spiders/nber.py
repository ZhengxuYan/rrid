import json
import re
from datetime import datetime
from datetime import timedelta

from pymongo import HASHED
from scrapy import Request
import scrapy
import csv

# get today's date in the format YYYY-MM-DD
today = datetime.now().date().isoformat()
# get the date 1 month ago in the format YYYY-MM-DD
one_month_ago = (datetime.now() - timedelta(days=30)).date().isoformat()


class NBERSpider(scrapy.Spider):
    name = 'nber'
    allowed_domains = ['nber.org']

    # Creating csv file for nber
    def __init__(self, start_date=one_month_ago, end_date=today, *args, **kwargs):
        super(NBERSpider, self).__init__(*args, **kwargs)
        # Open the file in append mode with newline='' to avoid blank lines in Windows
        self.file = open('results/nber_results.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        # Write the header row if the file is new/empty
        self.writer.writerow(['Link/DOI', 'Publication Date', 'Title', 'Authors', 'Abstract'])
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.older_publications_count = 0  # Add a counter for publications before 2024

    def close_spider(self):
        self.file.close()
    
    # DB specs
    collections_config = {
        'Scraper_nber_org': [
            [('Doi', HASHED)],
            [('NBER_Article_Number', HASHED)],
            'Publication_Date',
        ],
    }
    gridfs_config = {
        'Scraper_nber_org_fs': [],
    }

    pdf_parser_version = 'nber_20200715'
    pdf_laparams = {
        'char_margin': 3.0,
        'line_margin': 2.5
    }

    def start_requests(self):
        yield Request(
            url='https://www.nber.org/api/v1/working_page_listing/'
                'contentType/working_paper/_/_/search?page=1&perPage=50&sortBy=public_date',
            callback=self.parse_all_links,
            meta={'page': 1}
        )

    # removed has_duplicate() logic
    def parse_all_links(self, response):
        data = json.loads(response.body)
        for result in data['results']:
            m = re.match(r'/papers/(.+)$', result['url'])
            if not m:
                continue

            article_number = m.group(1)
            url = f'https://www.nber.org{result["url"]}'
            # Directly yield the request without checking for duplicates
            yield Request(
                url=url,
                callback=self.parse_page,
                meta={'article_number': article_number}
            )

        # Logic for pagination without checking has_dup
        page = response.meta.get('page', 1)  # Default to page 1 if not set
        yield Request(
            url=f'https://www.nber.org/api/v1/working_page_listing/'
                f'contentType/working_paper/_/_/search?page={page + 1}&perPage=50&sortBy=public_date',
            callback=self.parse_all_links,
            meta={'page': page + 1}
        )

    def parse_page(self, response):
        title = response.xpath(
            '//h1[contains(@class, "page-header__title")]/span/text()').extract_first().strip()
        authors = list(map(
            str.strip,
            response.xpath('//div[contains(@class, "page-header__authors")]//a/text()').extract()))
        abstract = ' '.join(map(str.strip, filter(lambda x: x is not None, response.xpath(
            '//div[contains(@class, "page-header__intro")]//p/text()').extract())))
        doi = response.xpath(
            '//meta[@name="citation_doi"]/@content').extract_first().strip()
        pub_date = response.xpath(
            '//meta[@name="citation_publication_date"]/@content').extract_first().strip()
        pub_date = datetime.strptime(pub_date, '%Y/%m/%d')

        if self.start_date <= pub_date <= self.end_date:
            # Reset the counter for older publications if within date range
            self.older_publications_count = 0
            self.writer.writerow([doi, pub_date, title, ', '.join(authors), abstract])
        else:
            # Increment the counter for older publications and possibly stop the spider
            self.older_publications_count += 1
            if self.older_publications_count > 500:  # Adjust this threshold as needed
                self.crawler.engine.close_spider(self, 'Encountered multiple publications outside the specified date range, stopping spider.')