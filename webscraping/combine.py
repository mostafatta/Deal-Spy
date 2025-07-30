import pandas as pd
import os
from datetime import datetime

RAW_FOLDER = "raw"
COMBINED_FOLDER = "combined"
os.makedirs(COMBINED_FOLDER, exist_ok=True)

def extract_datetime(filename):
    basename = os.path.basename(filename).replace(".xlsx", "")
    parts = basename.split("_")
    datetime_str = f"{parts[-2]}_{parts[-1]}"  
    return datetime.strptime(datetime_str, "%Y-%m-%d_%H-%M")

def combine_files():
    product_files = {}
    
    for filename in os.listdir(RAW_FOLDER):
        if filename.endswith(".xlsx"):
            parts = filename.split("_")
            source = parts[0].lower()
            product = '_'.join(parts[1:-2])  
            filepath = os.path.join(RAW_FOLDER, filename)
            
            if product not in product_files:
                product_files[product] = {}
            
            if source not in product_files[product]:
                product_files[product][source] = filepath
            else:
                if extract_datetime(filepath) > extract_datetime(product_files[product][source]):
                    product_files[product][source] = filepath
    
    for product, sources in product_files.items():
        combined_df = pd.DataFrame()
        for filepath in sources.values():
            df = pd.read_excel(filepath)
            combined_df = pd.concat([combined_df, df], ignore_index=True)
        
        output_path = os.path.join(COMBINED_FOLDER, f"combined_{product}.xlsx")
        combined_df.to_excel(output_path, index=False)
        print(f"Combined files for {product} into {output_path}")

if __name__ == "__main__":
    combine_files()
