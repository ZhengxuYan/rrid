import json
import re
from datetime import datetime

from pymongo import HASHED
from scrapy import Request
import scrapy
import csv

# from ._base import BaseSpider


class NBERSpider(scrapy.Spider):
    name = 'nber'
    allowed_domains = ['nber.org']

    # Creating csv file for nber
    def __init__(self, *args, **kwargs):
        super(NBERSpider, self).__init__(*args, **kwargs)
        # Open the file in append mode with newline='' to avoid blank lines in Windows
        self.file = open('results/nber_results.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        # Write the header row if the file is new/empty
        self.writer.writerow(['Title', 'Publication Date', 'Authors', 'Link', 'DOI', 'Abstract'])
    
    def close_spider(self, spider):
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

        article_number = response.meta['article_number']
        data = {
            'NBER_Article_Number': article_number,
            'Doi': doi,
            'Link': response.request.url,
            'Authors': authors,
            'Title': title,
            'Abstract': abstract,
            'Publication_Date': pub_date,
        }

        # stop the spider if the publication date is before 2024
        if pub_date < datetime(2024, 1, 1):
            # Use close_spider to stop the spider if the publication date is before 2024
            self.crawler.engine.close_spider(self, 'Reached publication date before 2024')
            return
    
        self.writer.writerow([title, pub_date, ', '.join(authors), response.request.url, doi, abstract])

        # # Check if "infectious disease" is in title or abstract
        # if 'infectious disease' in title.lower() or 'infectious disease' in abstract.lower():
        #     # Existing code to process and save the paper
        #     self.writer.writerow([title, pub_date, ', '.join(authors), response.request.url, doi, abstract])
        # else:
        # # Skip this paper as it's not related to infectious disease
        #     pass


    def handle_pdf(self, response):
        data = response.meta['Data']

        pdf_id = self.save_pdf(
            response.body,
            pdf_fn=f'NBER-{data["NBER_Article_Number"]}.pdf',
            pdf_link=response.request.url,
            fs='Scraper_nber_org_fs')

        data['PDF_gridfs_id'] = pdf_id
        self.save_article(data, to='Scraper_nber_org')