import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin
import urllib.robotparser
from urllib.parse import urlparse
import os
from data_cleaning import clean_and_normalize_text

#Check if the URL can be scraped 
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

#Extract title and content from the div with id "CourseInformationDiv"
def extract_content(page_html):
    soup = BeautifulSoup(page_html, 'html.parser')
    content_div = soup.find(id='CourseInformationDiv')
    
    if not content_div:
        content = soup.get_text(separator=' ', strip=True)
        titles = [tag.get_text(separator=' ', strip=True) for tag in soup.find_all(['h2', 'h3'])]
    else:
        content = content_div.get_text(separator=' ', strip=True)
        titles = [tag.get_text(separator=' ', strip=True) for tag in content_div.find_all(['h2', 'h3'])]
    
    if not titles:
        titles.append("No Title Found")
    
    for tag in content_div.find_all(['h2', 'h3']):
        tag.decompose()
    
    
    title = ' '.join(titles)
    
    return title, content

#Crawl the domain and scrape pages
def crawl_domain(start_url, base_url):
    visited = set()
    pages_to_visit = [start_url]
    unique_links = set()
    course_page = "https://westerncalendar.uwo.ca/Courses.cfm?Subject=COMPSCI&SelectedCalendar=Live&ArchiveID="
    pages_to_visit.append(course_page)

    while pages_to_visit:
        current_url = pages_to_visit.pop(0)

        if current_url in visited:
            continue

        if can_scrape(current_url):
            print(f"Visiting: {current_url}")
            page_html = get_page_content(current_url)
            if page_html:
                links = extract_links(page_html, base_url)
                unique_links.update(links)

                if "Courses.cfm" in current_url:
                    more_details_links = extract_more_details_links(page_html, base_url)
                    unique_links.update(more_details_links)
                    pages_to_visit.extend(more_details_links)
            
            visited.add(current_url)
        
        time.sleep(1)
    
    return visited, unique_links

#Extract links from the page
def extract_links(page_html, base_url):
    soup = BeautifulSoup(page_html, 'html.parser')
    links = set()

    rows = soup.find_all('tr')
    for row in rows:
        dept_name_cell = row.find('a', class_='moduleDeptName')
        if dept_name_cell and dept_name_cell.get_text() == "Computer Science":
            for link_tag in row.find_all('a', href=True):
                href = link_tag.get('href')
                if href.startswith('#'):
                    continue
                full_url = urljoin(base_url, href)
                links.add(full_url)
    
    return links

#Extract "More Details" links
def extract_more_details_links(page_html, base_url):
    soup = BeautifulSoup(page_html, 'html.parser')
    links = set()

    for link_tag in soup.find_all('a', href=True):
        if "More details" in link_tag.get_text():
            href = link_tag.get('href')
            full_url = urljoin(base_url, href)
            links.add(full_url)
    
    return links

#Save data to a JSON file
def save_to_json(new_data, filename='scraped_info.json'):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = []
    
    existing_data.extend(new_data)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)
    print(f"Data has been saved to {filename}.")

if __name__ == "__main__":
    base_url = "https://westerncalendar.uwo.ca/"
    start_url = "https://westerncalendar.uwo.ca/Modules.cfm?SelectedCalendar=Live&ArchiveID="

    visited_urls, unique_links = crawl_domain(start_url, base_url)

    scraped_data = []
    for link in unique_links:
        print(f"Scraping text from {link}")
        page_html = get_page_content(link)
        if page_html:
            title, content = extract_content(page_html)
            if title and content:
                cleaned_content = clean_and_normalize_text(content)
                scraped_data.append({'title': title, 'content': cleaned_content})
        
        time.sleep(1)

    save_to_json(scraped_data)
