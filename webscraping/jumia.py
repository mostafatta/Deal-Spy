import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os
import re

MAX_PAGES_TO_SCRAPE = 1 

options = Options()
options.add_experimental_option("detach", True)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

OUTPUT_FOLDER = "raw"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def safe_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name[:50]

def extra_data(url):
    details = {"brand": None, "seller": None, "rating_numbers": None}
    try:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(url)

        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 500)")
            time.sleep(1)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        brand = soup.find('a', class_='_more')
        seller = soup.find('span', class_='-m -pbs')
        rating_numbers = soup.find('a', class_='-plxs _more')

        details["brand"] = brand.text.strip() if brand else None
        details["seller"] = seller.text.strip() if seller else None
        details["rating_numbers"] = rating_numbers.text.strip() if rating_numbers else None

    except Exception as e:
        print(f"Error extracting extra data: {e}")
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    return details

def get_product_details_jumia(product_keyword):
    time_scraped = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    all_products = []

    category_name = safe_filename(product_keyword)
    url = f"https://www.jumia.com.eg/catalog/?q={product_keyword.replace(' ', '+')}"
    driver.get(url)
    page = 1

    while True:
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.prd._fb.col.c-prd")))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            product_cards = soup.find_all('article', class_='prd _fb col c-prd')

            if not product_cards:
                print(f"No products found on page {page}.")
                break

            print(f"{category_name.upper()} - PAGE {page}")
            for card in product_cards:
                name_tag = card.find('h3', class_='name')
                price_tag = card.find("div", class_="prc")
                old_price_tag = card.find("div", class_="old")
                discount_tag = card.find("div", class_="bdg _dsct _sm")
                rating_star_tag = card.find("div", class_="stars _m _al")
                product_link_tag = card.find('a', class_='core')

                product_link_href = product_link_tag['href'] if product_link_tag else None
                product_link = f"https://www.jumia.com.eg{product_link_href}" if product_link_href else None

                extra_info = extra_data(product_link) if product_link else {}

                if name_tag and price_tag:
                    product_name = name_tag.text.strip()
                    price = price_tag.text.strip()
                    old_price = old_price_tag.text.strip() if old_price_tag else "N/A"
                    discount = discount_tag.text.strip() if discount_tag else "N/A"
                    rating = rating_star_tag.text.strip() if rating_star_tag else "N/A"

                    product_data = {
                        "category": category_name,
                        "name": product_name,
                        "price": price,
                        "source": "jumia",
                        "old_price": old_price,
                        "discount": discount,
                        "brand": extra_info.get("brand"),
                        "seller": extra_info.get("seller"),
                        "rating": rating,
                        "total reviwes": extra_info.get("rating_numbers"),
                        "url": product_link,
                        "time_scraped": time_scraped,
                        "page_number": page
                    }

                    all_products.append(product_data)
                    print(f"Found: {product_name}")
                else:
                    print("Missing data.")
        except Exception as e:
            print(f"Error while scraping {category_name} page {page}: {e}")
            break

        if MAX_PAGES_TO_SCRAPE and page >= MAX_PAGES_TO_SCRAPE:
            break

        try:
            next_button = driver.find_element(By.CSS_SELECTOR, 'a.pg[aria-label="Next Page"]')
            driver.execute_script("arguments[0].click();", next_button)
            page += 1
            time.sleep(3)
        except:
            print("No more pages.")
            break

    if all_products:
        filename = f"jumia_{category_name}_{timestamp}.xlsx"
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        pd.DataFrame(all_products).to_excel(filepath, index=False)
        print(f"Saved {len(all_products)} {category_name} products to: {filepath}")
    else:
        print(f"No products found for {category_name}")

try:
    df_products = pd.read_csv("products.csv")
    product_list = df_products["product_name"].dropna().tolist()
except Exception as e:
    print("Error loading product list from Excel:", e)
    product_list = []

for product in product_list:
    get_product_details_jumia(product)

driver.quit()