import pandas as pd
import os
import re

COMBINED_FOLDER = "combined"
CLEANED_FOLDER = "cleaned"

os.makedirs(CLEANED_FOLDER, exist_ok=True)

def clean_product_name(name):
    if pd.isna(name):
        return None
    name = name.lower()
    name = re.sub(r'[^a-z0-9 ]', '', name)  # Allow spaces
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def clean_price(price):
    if pd.isna(price):
        return None
    if isinstance(price, str):
        price = price.replace(",", "").replace("EGP", "").strip()
    try:
        return float(price)
    except:
        return None

def clean_total_reviews(reviews):
    if pd.isna(reviews):
        return None
    reviews = re.sub(r'[^0-9]', '', str(reviews))
    try:
        return int(reviews)
    except:
        return None

def clean_discount(discount):
    if pd.isna(discount):
        return None
    discount = re.sub(r'[A-Za-z%]', '', str(discount))
    try:
        return int(discount)
    except:
        return None

def clean_files():
    for filename in os.listdir(COMBINED_FOLDER):
        if filename.endswith(".xlsx"):
            df = pd.read_excel(os.path.join(COMBINED_FOLDER, filename))

            if 'name' in df.columns:
                df['name'] = df['name'].apply(clean_product_name)

            if 'price' in df.columns:
                df['price'] = df['price'].apply(clean_price)

            if 'old_price' in df.columns:
                df['old_price'] = df['old_price'].apply(clean_price)

            if 'total_reviews' in df.columns:
                df['total_reviews'] = df['total_reviews'].apply(clean_total_reviews)

            if 'discount' in df.columns:
                df['discount'] = df['discount'].apply(clean_discount)

            df.to_excel(os.path.join(CLEANED_FOLDER, filename), index=False)
            print(f"✅ Cleaned: {filename}")

if __name__ == "__main__":
    clean_files()
