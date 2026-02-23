import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta

def fetch_article_content(url, timeout=10):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        article_body = (soup.find('article') or 
                        soup.find('div', class_='detail__body') or
                        soup.find('div', class_='content') or
                        soup.find('div', class_='read__content'))
        if article_body:
            paragraphs = article_body.find_all('p')
            return ' '.join([p.get_text(strip=True) for p in paragraphs])[:5000]
    except Exception as e:
        print(f"Error fetch article {url}: {e}")
    return None

def scrape_kompas_by_keyword(keyword, timeout=10):
    today = date.today()
    five_days_ago = today - timedelta(days=5)
    url = f"https://search.kompas.com/search?q={keyword}&sort=latest&site_id=all&start_date={five_days_ago}&end_date={today}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    berita_list = []
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        soup = BeautifulSoup(response.text, 'html.parser')
        for article in soup.select('div.articleItem'):
            link_elem = article.select_one('a.article-link')
            if not link_elem:
                continue
            judul = article.select_one('h2.articleTitle').get_text(strip=True)
            link = link_elem.get('href')
            tanggal = article.select_one('div.articlePost-date')
            tanggal = tanggal.get_text(strip=True) if tanggal else ''
            berita_list.append({
                'judul': judul,
                'link': link,
                'tanggal': tanggal,
                'keyword': keyword,
                'sumber': 'kompas.com'
            })
    except Exception as e:
        print(f"Error scraping kompas {keyword}: {e}")
    return berita_list

def scrape_detik_by_keyword(keyword, timeout=10):
    today = date.today()
    five_days_ago = today - timedelta(days=5)
    fromdate = five_days_ago.strftime("%d/%m/%Y")
    todate = today.strftime("%d/%m/%Y")
    url = f"https://www.detik.com/search/searchall?query={keyword}&result_type=latest&fromdatex={fromdate}&todatex={todate}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    berita_list = []
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        soup = BeautifulSoup(response.text, 'html.parser')
        for article in soup.select('article'):
            title_elem = article.select_one('h3.media__title a')
            if not title_elem:
                continue
            judul = title_elem.get_text(strip=True)
            link = title_elem.get('href')
            date_elem = article.select_one('div.media__date span')
            tanggal = date_elem.get_text(strip=True) if date_elem else ''
            berita_list.append({
                'judul': judul,
                'link': link,
                'tanggal': tanggal,
                'keyword': keyword,
                'sumber': 'detik.com'
            })
    except Exception as e:
        print(f"Error scraping detik {keyword}: {e}")
    return berita_list