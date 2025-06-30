import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CLEANED_FOLDER = "cleaned"
ALERTS_FOLDER = "alerts"

os.makedirs(ALERTS_FOLDER, exist_ok=True)

LATEST_FILE = os.path.join(CLEANED_FOLDER, "latest_alerts.xlsx")
ALERT_FILE = os.path.join(ALERTS_FOLDER, "price_alerts.csv")
def load_latest_alerts():
    if os.path.exists(LATEST_FILE):
        return pd.read_excel(LATEST_FILE)
    return pd.DataFrame(columns=["name", "source", "price"])
def save_latest_prices(df):
    df.to_excel(LATEST_FILE, index=False)
def send_email(subject,html_content) :
    sender_email = "sender@gmail.com"
    receiver_email = "business@gmail.com"
    password = "password"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email
    part = MIMEText(html_content, "html")
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

def check_price_changes():
    alerts = []
    latest_prices = load_latest_prices()

    all_files = [f for f in os.listdir(CLEANED_FOLDER) if f.endswith(".xlsx")]
    combined_df = pd.concat([
        pd.read_excel(os.path.join(CLEANED_FOLDER, f)) for f in all_files
    ])

    combined_df["price"] = pd.to_numeric(combined_df["price"], errors="coerce")
    latest_prices["price"] = pd.to_numeric(latest_prices["price"], errors="coerce")

    for _, row in combined_df.iterrows():
        product_id = f"{row['name']}_{row['source']}"
        latest_row = latest_prices[
            (latest_prices["name"] == row["name"]) & (latest_prices["source"] == row["source"])
        ]

        if not latest_row.empty:
            old_price = latest_row.iloc[0]["price"]
            if row["price"] != old_price:
                alerts.append({
                    "Product": row["name"],
                    "Source": row["source"],
                    "Old Price": old_price,
                    "New Price": row["price"],
                    "URL": row["url"]
                })
        else:
            # First time seeing this product
            alerts.append({
                "Product": row["name"],
                "Source": row["source"],
                "Old Price": "N/A",
                "New Price": row["price"],
                "URL": row["url"]
            })

    if alerts:
        df_alerts = pd.DataFrame(alerts)
        df_alerts.to_csv(ALERT_FILE, index=False)
        print("🔔 Alerts found and saved.")

        # Send email
        html = df_alerts.to_html(index=False)
        send_email("🛒 Price Change Alert", html)
    else:
        print("✅ No price changes found.")

    # Save latest snapshot
    save_latest_prices(combined_df[["name", "source", "price"]])

if __name__ == "__main__":
    check_price_changes()
