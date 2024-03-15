import scrapy
import time
from urllib.parse import urljoin


class OsfSpider(scrapy.Spider):
    name = 'osf'
    start_urls = ['https://osf.io/search?activeFilters=%5B%7B%22propertyVisibleLabel%22%3A%22Subject%22%2C%22propertyPathKey%22%3A%22subject%22%2C%22label%22%3A%22Medicine%20and%20Health%20Sciences%22%2C%22value%22%3A%22https%3A%2F%2Fapi.osf.io%2Fv2%2Fsubjects%2F584240da54be81056cecaaaa%22%7D%5D&q=&resourceType=Preprint&sort=-relevance&view_only='] 

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': 'osf.csv',
    }

    # TODO: figure out if get is sufficient for article funders vs getall
    def parse(self, response):
        for articles in response.css('div.article-browse-wrapper'):
            article_link = articles.css('a.data-test-search-result-card-title').attrib['href']
            data = {
                'link': article_link,
                'publication_date': [text.split('PUBLISHED ')[1].strip() for text in response.css('div.article-bottom-bar::text').getall() if 'PUBLISHED ' in text][-1],
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