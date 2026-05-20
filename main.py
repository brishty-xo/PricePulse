import os
import json
import csv
import requests
import smtplib
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Browser headers
HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
}


def load_products():
    with open("products.json", "r") as file:
        return json.load(file)


def get_product_details(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS
        )


        # Save HTML for debugging
        with open(
            "amazon_page.html",
            "w",
            encoding="utf-8"
        ) as file:
            file.write(response.text)

        if response.status_code != 200:
            print(
                "Request failed."
            )
            return None

        soup = BeautifulSoup(
            response.content,
            "lxml"
        )

        # Find title
        title_tag = soup.find(
            id="productTitle"
        )

        # Try multiple price selectors
        price_tag = (
            soup.find(
                "span",
                class_="a-price-whole"
            )
            or soup.find(
                "span",
                class_="a-offscreen"
            )
            or soup.find(
                "span",
                attrs={
                    "class":
                    "a-price aok-align-center"
                }
            )
        )

        if not title_tag:
            print(
                "Product title "
                "not found."
            )
            return None

        if not price_tag:
            print(
                "Price not found."
            )
            return None

        title = (
            title_tag
            .get_text()
            .strip()
        )

        price_text = (
            price_tag
            .get_text()
            .strip()
        )


        # Keep only digits and decimal
        clean_price = ""

        for char in price_text:
            if (
                char.isdigit()
                or char == "."
            ):
                clean_price += char

        if not clean_price:
            print(
                "Could not parse "
                "price."
            )
            return None

        price = float(clean_price)

        return {
            "title": title,
            "price": price
        }

    except Exception as e:
        print(
            f"Scraping error: "
            f"{e}"
        )
        return None


def save_price_history(
    title,
    price
):
    file_exists = os.path.exists(
        "price_history.csv"
    )

    with open(
        "price_history.csv",
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "Date",
                "Product",
                "Price"
            ])

        writer.writerow([
            datetime.now(),
            title,
            price
        ])


def send_email(
    title,
    price,
    url
):
    smtp_address = os.getenv(
        "SMTP_ADDRESS"
    )

    email = os.getenv(
        "EMAIL"
    )

    password = os.getenv(
        "PASSWORD"
    )

    subject = (
        "Amazon Price Alert!"
    )

    body = f"""
Product:
{title}

Current Price:
₹{price}

Product Link:
{url}
"""

    message = (
        f"Subject:{subject}"
        f"\n\n{body}"
    )

    try:
        with smtplib.SMTP(
            smtp_address,
            587
        ) as connection:

            connection.starttls()

            connection.login(
                email,
                password
            )

            connection.sendmail(
                from_addr=email,
                to_addrs=email,
                msg=message.encode(
                    "utf-8"
                )
            )

        print(
            "Email sent!"
        )

    except Exception as e:
        print(
            f"Email error: "
            f"{e}"
        )


def main():
    products = load_products()

    for product in products:

        url = (
            product["url"]
        )

        buy_price = (
            product[
                "buy_price"
            ]
        )

        print(
            "\nChecking "
            "product..."
        )

        details = (
            get_product_details(
                url
            )
        )

        if not details:
            print(
                "Could not "
                "find title "
                "or price."
            )
            continue

        title = (
            details["title"]
        )

        current_price = (
            details["price"]
        )

        print(
            f"Title: "
            f"{title}"
        )

        print(
            f"Price: "
            f"₹{current_price}"
        )

        save_price_history(
            title,
            current_price
        )

        if (
            current_price
            <= buy_price
        ):
            print(
                "Price dropped!"
            )

            send_email(
                title,
                current_price,
                url
            )

        else:
            print(
                f"Price above "
                f"target "
                f"(₹{buy_price})"
            )


if __name__ == "__main__":
    main()