import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, urlparse
import urllib.robotparser
import re
import os
from data_cleaning import clean_and_normalize_text

#Check if the URL can be scraped (robots.txt)
def can_scrape(url):
    rp = urllib.robotparser.RobotFileParser()
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    rp.set_url(robots_url)
    rp.read()
    return rp.can_fetch("*", url)

#Send a request to the webpage and parse the content
def get_page_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve the page {url}. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error occurred while fetching {url}: {e}")
        return None

#Extract title and content
def extract_content(page_html):
    soup = BeautifulSoup(page_html, 'html.parser')
    
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else soup.find('title').get_text(strip=True) if soup.find('title') else "No Title Found"

    content = ""
    for element in soup.find_all(['h2', 'h3', 'p']):
        if element.name in ['h2', 'h3']:
            content += f"\n{element.get_text(strip=True)}\n"
        elif element.name == 'p':
            content += element.get_text(separator=' ', strip=True) + " "
    
    content = re.sub(r'[\n\r\t]', ' ', content)
    content = re.sub(r'[^\x00-\x7F]+', '', content)
    content = re.sub(r'\s+', ' ', content)
    return title, content.strip()

#Crawl the domain and scrape pages
def crawl_domain(start_url):
    visited = set()
    pages_to_visit = [start_url]
    all_data = []
    
    while pages_to_visit:
        current_url = pages_to_visit.pop(0)

        if current_url in visited:
            continue

        if can_scrape(current_url):
            print(f"Visiting: {current_url}")
            page_html = get_page_content(current_url)
            if page_html:
                title, content = extract_content(page_html)
                if content:
                    cleaned_content = clean_and_normalize_text(content)
                    all_data.append({'title': title, 'content': cleaned_content})
                
                links = extract_links(page_html, current_url)
                pages_to_visit.extend(links)
            
            visited.add(current_url)
        
        time.sleep(1)
    
    return visited, all_data

#Extract links from a page
def extract_links(page_html, base_url):
    soup = BeautifulSoup(page_html, 'html.parser')
    links = set()

    for link_tag in soup.find_all('a', href=True):
        href = link_tag.get('href')
        if href.startswith('#'):
            continue
        full_url = urljoin(base_url, href)
        if base_url in full_url:
            links.add(full_url)
    
    return links

#Save data to a JSON file
def save_data_to_json(data, filename='scraped_info.json'):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = []
    
    existing_data.extend(data)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)
    print(f"All data has been saved to {filename}.")

if __name__ == "__main__":
    start_url = "https://csd.uwo.ca"
    visited_urls, all_data = crawl_domain(start_url)
    save_data_to_json(all_data)
