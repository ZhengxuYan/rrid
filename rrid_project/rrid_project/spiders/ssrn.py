import re
import csv
import urllib
from urllib.parse import urljoin
from datetime import datetime, timedelta
import scrapy
from scrapy import Request
from pymongo import HASHED

# get today's date in the format YYYY-MM-DD
today = datetime.now().date().isoformat()
# get the date 1 month ago in the format YYYY-MM-DD
one_year_ago = (datetime.now() - timedelta(days=1000)).date().isoformat()

class SSRNSpider(scrapy.Spider):

    custom_settings = {
        'ROBOTSTXT_OBEY': False
    }

    name = 'ssrn'
    allowed_domains = ['papers.ssrn.com']

    # DB specs
    collections_config = {
        'Scraper_papers_ssrn_com': [
            [('Doi', HASHED)],
            [('Title', HASHED)],
            'Publication_Date',
        ],
    }
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    # Creating csv file for nber
    def __init__(self, start_date=one_year_ago, end_date=today, *args, **kwargs):
        super(SSRNSpider, self).__init__(*args, **kwargs)
        # Open the file in append mode with newline='' to avoid blank lines in Windows
        self.file = open('results/ssrn_results.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        # Write the header row if the file is new/empty
        self.writer.writerow(['Link/DOI', 'Publication Date', 'Title', 'Authors', 'Abstract'])
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.older_publications_count = 0  # Add a counter for publications before 2024

    def start_requests(self):
        collections = ['3526423']

        for collection in collections:
            query_dict = {
                'form_name': 'journalBrowse',
                'journal_id': collection,
                'orderBy': 'ab_approval_date',
                'orderDir': 'desc',
                'strSelectedOption': '6',
                'lim': 'false',
                'Network': 'no'
            }
            url = 'https://papers.ssrn.com/sol3/Jeljour_results.cfm?' + urllib.parse.urlencode(query_dict)

            yield Request(
                url=url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                                  '(KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.58'},
                callback=self.parse_query_result,
                meta={'collection': collection}
            )

    def parse_query_result(self, response):
        papers = response.xpath("//div[contains(@class, 'papers-list')]//div[contains(@class, 'description')]")
        for paper in papers:
            url = paper.xpath('.//a[contains(@class, "title")]/@href').extract_first()
            url = urljoin(response.request.url, url)
            yield Request(
                url=url,
                priority=100,
                headers={'User-Agent':
                             'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.58'},
                callback=self.parse_article,
                dont_filter=True,
                meta={'collection': response.meta['collection']}
            )
        next_page = response.xpath(
            "//div[@class='pagination']//li[@class='next']/a/@href").extract_first()
        if next_page is not None:
            yield response.follow(
                next_page,
                callback=self.parse_query_result,
                meta={'collection': response.meta['collection']}
            )

    def parse_article(self, response):
        meta = {
            'JournalCollectionId': response.meta['collection'],
            'Journal': 'ssrn',
            'Origin': 'All preprints from srnn',
            'Title': response.xpath("//body//div[@class='box-container box-abstract-main']/h1/text()").get(),
            'Link': response.request.url
        }

        # Doi
        paper_id = re.search(r'^https://papers.ssrn.com/sol3/papers.cfm\?abstract_id=(.*)$', meta['Link']).group(1)
        meta['Doi'] = "10.2139/ssrn." + paper_id

        # Abstract
        meta['Abstract'] = (response.xpath(
            "string(//body//div[@class='box-container box-abstract-main']/div[@class='abstract-text']/p)").get()).strip()

        # Publication Date
        date = response.xpath(
            "//body//div[@class='box-container box-abstract-main']/p[@class='note note-list']/span/text()").extract()
        r_date = re.compile(r'^Posted:.*$')
        date = list(filter(r_date.match, date))[0]

        meta['Publication_Date'] = None
        time_s = re.search(r'^Posted:\s(.*)$', date).group(1)
        if time_s.strip():
            meta['Publication_Date'] = datetime.strptime(time_s, '%d %b %Y')
        if meta['Publication_Date'] is None:
            meta_pub_date = response.xpath('//meta[@name="citation_publication_date"]/@content').extract_first()
            if meta_pub_date:
                meta['Publication_Date'] = datetime.strptime(meta_pub_date, '%Y/%m/%d')

        assert meta['Publication_Date'] is not None

        # Authors
        authors = response.xpath(
            "//div[@class='box-container box-abstract-main']/div[@class='authors authors-full-width']/h2/a/text()").extract() or response.xpath(
            "//div[@class='box-container box-abstract-main']/div[@class='authors cell authors-full-width']/h2/a/text()").extract()
        meta['Authors'] = [{'Name': x} for x in authors]

        if not self.has_duplicate(
                'Scraper_papers_ssrn_com',
                {'Doi': meta['Doi'],
                 'Publication_Date': meta['Publication_Date']}):
            self.save_article(meta, to='Scraper_papers_ssrn_com')
