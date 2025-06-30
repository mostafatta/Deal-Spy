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

# === Setup ===
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
        brand = soup.find('span', class_='BrandStoreCtaV2_textContent__6tPjk')
        seller = soup.find('strong', class_='PartnerRatingsV2_soldBy__IOCr1')
        rating = soup.find('span', class_='RatingPreviewStarV2_countText__OVzD2')

        details["brand"] = brand.text.strip() if brand else None
        details["seller"] = seller.text.strip() if seller else None
        details["rating_numbers"] = rating.text.strip() if rating else None

    except Exception as e:
        print(f"Error extracting extra data: {e}")
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    return details

def get_product_details(product_keyword, pages_to_scrape=1):
    time_scraped = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    all_products = []

    category_name = safe_filename(product_keyword)
    url = f"https://www.noon.com/egypt-en/search/?q={product_keyword.replace(' ', '+')}"

    for page in range(1, pages_to_scrape + 1):
        page_url = f"{url}&page={page}"
        driver.get(page_url)

        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProductBoxLinkHandler_linkWrapper__b0qZ9")))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            product_cards = soup.find_all('div', class_='ProductBoxLinkHandler_linkWrapper__b0qZ9')

            if not product_cards:
                print(f"[{category_name}] No products found on page {page}.")
                continue

            print(f"\n=== {category_name.upper()} - PAGE {page} ===")
            for card in product_cards:
                name_tag = card.find('h2', {"data-qa": "plp-product-box-name"})
                price_tag = card.find("strong", class_="Price_amount__2sXa7")
                old_price_tag = card.find("span", class_="Price_oldPrice__ZqD8B")
                ranting_star=card.find("div",class_="RatingPreviewStar_textCtr__sfsJG")
                discount_tag = card.find("span", class_="PriceDiscount_discount__1ViHb")
                product_link_tag = card.find('a', class_='ProductBoxLinkHandler_productBoxLink__FPhjp')
                product_link_href = product_link_tag['href'] if product_link_tag else None
                product_link = f"https://www.noon.com{product_link_href}" if product_link_href else None

                extra_info = extra_data(product_link) if product_link else {}

                if name_tag and price_tag:
                    product_name = name_tag.text.strip()
                    price = price_tag.text.strip()
                    old_price = old_price_tag.text.strip() if old_price_tag else "N/A"
                    discount = discount_tag.text.strip() if discount_tag else "N/A"

                    product_data = {
                        "category": category_name,
                        "name": product_name,
                        "price": price,
                        "source": "noon",
                        "old_price": old_price,
                        "discount": discount,
                        "brand": extra_info.get("brand"),
                        "seller": extra_info.get("seller"),
                        
                        "total_reviews": extra_info.get("rating_numbers"),
                        "url": product_link,
                        "time_scraped": time_scraped,
                        "page_number": page
                    }

                    all_products.append(product_data)
                    print(f"✅ Found: {product_name}")
                else:
                    print("⚠️ Missing data.")

        except Exception as e:
            print(f"❌ Error while scraping {category_name} page {page}: {e}")
        time.sleep(2)

    if all_products:
        filename = f"noon_{category_name}_{timestamp}.xlsx"
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        pd.DataFrame(all_products).to_excel(filepath, index=False)
        print(f"\n💾 Saved {len(all_products)} {category_name} products to: {filepath}")
    else:
        print(f"\n❌ No products found for {category_name}")

# === Load Products from File ===
try:
    df_products = df_products = pd.read_csv("products.csv")
    product_list = df_products["product_name"].dropna().tolist()
except Exception as e:
    print("❌ Error loading product list from Excel:", e)
    product_list = []

# === Run Scraper for Each Product ===
PAGES_TO_SCRAPE = 1
for product in product_list:
    get_product_details(product, pages_to_scrape=PAGES_TO_SCRAPE)

driver.quit()
