import scrapy
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin


class GatesSpider(scrapy.Spider):
    name = 'gates'
    start_urls = ['https://gatesopenresearch.org/browse/articles?term0=Medical_and_health_sciences'] 

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': 'results/gates_results.csv',
    }

    def parse(self, response):
        num_days = 180
        for articles in response.css('div.article-browse-wrapper'):
            publication_date_str = articles.css('div.article-bottom-bar::text').re_first('PUBLISHED (.+)')
            publication_date = datetime.strptime(publication_date_str, '%d %b %Y')

            if publication_date >= datetime.now() - timedelta(days=num_days):
                article_link = articles.css('a.article-link').attrib['href']
                data = {
                    'link': article_link,
                    'publication_date': publication_date_str,
                    'title': articles.css('span.article-title::text').get(),
                    'authors': articles.css('span.js-article-author::text').getall(),
                    'article_funders': articles.css('span.article-funder-brand::text').getall(),
                    'downloads': articles.css('span.article-metrics-wrapper::attr(data-downloads)').get(),
                    'views': articles.css('span.article-metrics-wrapper::attr(data-views)').get(),
                }
                yield scrapy.Request(url=article_link, callback=self.get_abstract, meta={'data': data})
        
        next_page_url = response.css('a.js-pagination-next::attr(href)').get()
        if next_page_url:
            next_page_url = urljoin(response.url, next_page_url)
            time.sleep(1)
            yield scrapy.Request(next_page_url, callback=self.parse)

    def get_abstract(self, response):
        data = response.meta['data']
        data['abstract'] = ' '.join(response.css('div.abstract-text::text').getall()).strip() or 'No abstract found'
        yield data
