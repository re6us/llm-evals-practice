import requests
from bs4 import BeautifulSoup

url = "https://news.ycombinator.com/item?id=49984923"

def fetch_page(url):
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)

    return text[:3000]

result = fetch_page(url)
print(result)