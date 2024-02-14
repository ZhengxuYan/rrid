import re
import time
from datetime import datetime
import scrapy
from scrapy import Request
import urllib.parse

class ArxivSpider(scrapy.Spider):
    name = 'arxiv'

    sleep_time = 5

    def build_query_url(self):
        query_dict = {
            "advanced": "",
            "terms-0-operator": "AND",
            "terms-0-term": "infectious disease",
            "terms-0-field": "all",
            "classification-physics_archives": "all",
            "classification-include_cross_list": "include",
            "date-filter_by": "all_dates",
            "date-year": "",
            "date-from_date": "",
            "date-to_date": "",
            "date-date_type": "submitted_date",
            "abstracts": "show",
            "size": "50",
            "order": "-announced_date_first",
        }
        return 'https://arxiv.org/search/advanced?' + urllib.parse.urlencode(query_dict)

    def start_requests(self):
        yield Request(
            url=self.build_query_url(),
            callback=self.parse_query_result,
            meta={'dont_obey_robotstxt': True}
        )

    def parse_query_result(self, response):
        titles = [p.xpath('string(p[@class="title is-5 mathjax"])').get() for p in response.xpath('//body//ol/li[@class="arxiv-result"]')]
        titles = [re.search(r'([^\n\s].*)\n', title).group(1) for title in titles]

        publication_dates = [h2.xpath('string(p[@class="is-size-7"])').get() for h2 in response.xpath('//body//ol/li[@class="arxiv-result"]')]
        publication_dates = [datetime.strptime(re.search(r'^Submitted\s(.*?);', publication_date).group(1), '%d %B, %Y') for publication_date in publication_dates]

        authors = []
        for a in response.xpath('//body//ol[@class="breathe-horizontal"]/li[@class="arxiv-result"]/p[@class="authors"]'):
            authors.append([{'Name': x} for x in a.xpath('a/text()').getall()])

        arxiv_ids = response.xpath('//body//ol[@class="breathe-horizontal"]/li[@class="arxiv-result"]//p[@class="list-title is-inline-block"]/a/text()').getall()
        arxiv_ids = [re.search(r'^arXiv:(.*)$', arxiv_id).group(1) for arxiv_id in arxiv_ids]

        abstracts = [h.xpath('string(span[@class="abstract-full has-text-grey-dark mathjax"])').get() for h in response.xpath('//body//ol[@class="breathe-horizontal"]/li[@class="arxiv-result"]/p[@class="abstract mathjax"]')]
        abstracts = [re.search(r'([^\n\s].*)\n', abstract).group(1) for abstract in abstracts]

        for paper_num in range(0, len(titles)):
            print("Title:", titles[paper_num])
            print("Publication Date:", publication_dates[paper_num])
            print("Authors:", [a['Name'] for a in authors[paper_num]])
            print("Link:", "https://arxiv.org/abs/" + arxiv_ids[paper_num])
            print("Abstract:", abstracts[paper_num])
            print("------------------------------------------------------")

        print("Sleeping for {} seconds".format(self.sleep_time))
        time.sleep(self.sleep_time)

        try:
            next_page = response.xpath('//body//nav[@class="pagination is-small is-centered breathe-horizontal"]/a[@class="pagination-next"]/@href').extract()[0]
            if next_page is not None:
                yield response.follow(next_page, callback=self.parse_query_result, meta=response.meta)
        except:
            pass
