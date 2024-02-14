import scrapy
import json
import csv

class BiorxivSpider(scrapy.Spider):
    name = 'biorxiv'
    allowed_domains = ['api.biorxiv.org']

    def __init__(self, server='biorxiv', start_date="2023-01-01", end_date="2023-12-31", *args, **kwargs):
        super(BiorxivSpider, self).__init__(*args, **kwargs)
        self.server = server
        self.start_date = start_date
        self.end_date = end_date
        self.cursor = 0
        self.file = open(f'results/{server}_results.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['biorxiv_doi', 'published_doi', 'published_journal', 'preprint_platform', 'preprint_title', 'preprint_authors', 'preprint_category', 'preprint_date', 'published_date', 'preprint_abstract', 'preprint_author_corresponding', 'preprint_author_corresponding_institution'])

    def start_requests(self):
        url = f'https://api.biorxiv.org/pubs/{self.server}/{self.start_date}/{self.end_date}/{self.cursor}'
        yield scrapy.Request(url=url, method='GET', callback=self.parse)
    
    def parse(self, response):
        data = json.loads(response.text)
        articles = data.get('collection', [])

        for article in articles:
            title = article.get('preprint_title', '').lower()
            abstract = article.get('preprint_abstract', '').lower()
            
            # Keywords related to infectious diseases
            keywords = ['infectious disease', 'virus', 'covid-19', 'sars-cov-2', 'pandemic', 'epidemic']
            if any(keyword in title or keyword in abstract for keyword in keywords):
                # This article is related to infectious diseases, process it further
                preprint_authors = article.get('preprint_authors', 'Not available')
            
                self.writer.writerow([
                    article.get('biorxiv_doi', ''),
                    article.get('published_doi', ''),
                    article.get('published_journal', ''),
                    article.get('preprint_platform', ''),
                    article.get('preprint_title', ''),
                    preprint_authors,  # Directly use the string
                    article.get('preprint_category', ''),
                    article.get('preprint_date', ''),
                    article.get('published_date', ''),
                    article.get('preprint_abstract', ''),
                    article.get('preprint_author_corresponding', ''),
                    article.get('preprint_author_corresponding_institution', '')
                ])



        messages = data.get('messages', [])
        if messages:
            message = messages[0]  # Assuming there's always at least one message with the cursor info
            next_cursor = message.get('cursor')
            total = message.get('count')

            if next_cursor is not None and total > next_cursor:
                next_url = f'https://api.biorxiv.org/pubs/{self.server}/{self.start_date}/{self.end_date}/{next_cursor}'
                yield response.follow(next_url, self.parse)


    def close_spider(self, spider):
        self.file.close()
