import requests
from bs4 import BeautifulSoup
import re

for start_num in range(1, 501):
    # print(start_num)

    response = requests.get(
        f"https://zenodo.org/search?q=&l=list&p={start_num}&s=20&sort=newest")
    print(response.status_code)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    # print(html)

    h2_tag = soup.findAll('span', class_='creatibutor-name')
    print(h2_tag)
# 输出结果
    for label in h2_tag:
        print(label.text)
