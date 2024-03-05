import requests
from bs4 import BeautifulSoup
import re

csv_columns = ['doi', 'Title', 'Publication Date',
               'Authors', 'Link', 'Abstract']

dois_list = []
titles_list = []

for start_num in range(1, 32):
    response = requests.get(
        f"https://www.preprints.org/covid19?order_by=most_recent&page_num={start_num}")
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    # 0: title
    titles = soup.findAll('a', class_='title', id='title')
    for title in titles:
        # print(title.string)
        titles_list.append(title.string)


# doi

# dois = soup.findAll('span', class_='content-box-header-element-5')
# for doi in dois:
#     doi = doi.find('a')
#     # todo:
#     # remove empty space
#     print(doi.string)
# print('doi:')
# print(doi.string)


# 1: publication date


# 2: authors
# 找到所有包含作者信息的<div>标签

# author_boxes = soup.find_all('div', class_='search-content-box-author')

# # 初始化一个列表用于存储每个<div>中的作者
# all_authors = []

# # 遍历每个<div>元素，提取作者信息并添加到列表中
# for box in author_boxes:
#     author_elements = box.find_all('a', class_='author-selector')
#     authors = ', '.join([author.get_text() for author in author_elements])
#     all_authors.append(authors)
#     print(all_authors)
#     break


# 3: link
# link = soup.find('a', class_='title', id='title')['href']
# link = 'https://www.preprints.org'+link
# print(link)

# 1: publication date
# response = requests.get(link)

# html = response.text
# soup1 = BeautifulSoup(html, 'html.parser')
# submission_content = soup1.find(
#     'div', id='submission-content').get_text(strip=True)

# # 使用正则表达式提取时间信息
# pattern = r'Online:\s*(\d+\s+\w+\s+\d{4})'  # 匹配 "Online:" 后面的日期
# match = re.search(pattern, submission_content)

# # 如果找到匹配项，则提取时间信息
# if match:
#     online_date_info = match.group(1)
#     print(online_date_info)
# else:
#     print("No 'Online:' keyword found in the submission content.")

# 4: abstract
# abstract = soup.find('div', attrs={'class': 'abstract-content'})
# print(abstract.string)


titles_list = []
dois_list = []
all_authors = []
links = []
abstracts = []


for start_num in range(1, 32):
    print(start_num)

    response = requests.get(
        f"https://www.preprints.org/covid19?order_by=most_recent&page_num={start_num}")
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    info_boxes = soup.findAll(
        'div', class_='search-content-box margin-serach-wrapper-left')

    for box in info_boxes:
        title = box.find('a', class_='title', id='title')
        doi_span = box.find('span', class_='content-box-header-element-5')
        author_elements = box.find_all('a', class_='author-selector')
        link = box.find('a', class_='title', id='title')['href']
        abstract = box.find('div', attrs={'class': 'abstract-content'})

        # authors
        if author_elements:
            authors = ', '.join([author.get_text()
                                for author in author_elements])
            all_authors.append(authors)
        else:
            all_authors.append(None)

        # links
        if link:
            link = 'https://www.preprints.org'+link
            links.append(link)
        else:
            links.append(None)

        # abstracts
        if abstract:
            abstract = abstract.string
            cleaned_abstract = abstract.replace('\n', '').strip()
            abstracts.append(cleaned_abstract)
        else:
            abstracts.append(None)

        # doi
        if doi_span:
            doi = doi_span.find('a')
            doi_str = doi.string.replace(" ", "")
            # print(doi_str)

            pattern = r"doi:(\S+)"
            match = re.search(pattern, doi_str)

            dois_list.append(match.group(1))
        else:
            dois_list.append(None)

        if title:
            titles_list.append(title.string)
        else:
            titles_list.append(None)
