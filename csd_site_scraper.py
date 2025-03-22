import requests
from bs4 import BeautifulSoup
import time
import urllib.robotparser
import re
import sqlite3
from urllib.parse import urljoin, urlparse
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
def crawl_domain(start_url, conn):
    visited = set()
    pages_to_visit = [start_url]
    
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
                    insert_data_to_db(conn, title, cleaned_content)
                
                links = extract_links(page_html, current_url)
                pages_to_visit.extend(links)
            
            visited.add(current_url)
        
        time.sleep(1)
    
    return visited

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

#Create the SQLite database and table
def create_db():
    conn = sqlite3.connect('scraped_data.db')  
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS scraped_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT
                )''')
    conn.commit()
    return conn

#Insert data into the database
def insert_data_to_db(conn, title, content):
    c = conn.cursor()
    c.execute('''INSERT INTO scraped_info (title, content) 
                 VALUES (?, ?)''', (title, content))
    conn.commit()

if __name__ == "__main__":
    start_url = "https://csd.uwo.ca"
    
    #Create the SQLite database and table
    conn = create_db()
    
    #Start crawling and scraping the pages
    visited_urls = crawl_domain(start_url, conn)
    
    #Close the connection to the database
    conn.close()

    print("Crawling finished and data has been stored in 'scraped_data.db'.")
