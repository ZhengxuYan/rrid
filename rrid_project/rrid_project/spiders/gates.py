import scrapy
import time
from urllib.parse import urljoin


class GatesSpider(scrapy.Spider):
    name = 'gates'
    start_urls = ['https://gatesopenresearch.org/browse/articles'] 


    # TODO: figure out if get is sufficient for article funders vs getall
    def parse(self, response):
        for articles in response.css('div.article-browse-wrapper'):
            yield {
                'title': articles.css('span.article-title::text').get(),
                'authors': articles.css('span.js-article-author::text').getall(),
                'peer_reviewers': [name.strip() for names_group in articles.css('span.field-names::text').getall() 
                                   for name in names_group.replace(' and', ';').split(';') if name.strip()],
                # bill and melinda gates foundation keeps repeating
                'article_funders': articles.css('span.article-funder-brand::text').getall(), 
                'article_type': articles.css('span.article-type-text::text').get().strip(),
                'downloads': articles.css('span.article-metrics-wrapper::attr(data-downloads)').get(),
                'views': articles.css('span.article-metrics-wrapper::attr(data-views)').get(),
                'link': articles.css('a.article-link').attrib['href'],
            }

        
        next_page_url = response.css('a.js-pagination-next::attr(href)').get()


        
        if next_page_url:

            next_page_url = urljoin(response.url, next_page_url)

            time.sleep(1)

            yield scrapy.Request(next_page_url, callback=self.parse)

        
