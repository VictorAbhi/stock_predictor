from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import time
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# Initialize Edge WebDriver
service = Service(EdgeChromiumDriverManager().install())
options = webdriver.EdgeOptions()
driver = webdriver.Edge(service=service, options=options)

def get_price_history(symbol):
    print(f"🔄 Extracting data for {symbol}...")
    
    try:
        # Ensure a fresh start for each company
        driver.get(f"https://www.sharesansar.com/company/{symbol}")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btn_cpricehistory"))).click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "myTableCPriceHistory")))

        all_data = []
        headers = None

        while True:
            # Wait for table update
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#myTableCPriceHistory tbody")))
            time.sleep(2)  # Small delay for data load

            # Get the table HTML
            soup = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.find("table", {"id": "myTableCPriceHistory"})

            if not table:
                print(f"⚠️ No data found for {symbol}")
                return

            # Extract headers only once
            if headers is None:
                headers = [th.text.strip() for th in table.find("thead").find("tr").find_all("th")]

            # Extract table rows
            rows = table.find("tbody").find_all("tr", {"role": "row"})
            for row in rows:
                data = [td.text.strip() for td in row.find_all("td")]
                if data:
                    all_data.append(data)

            # Check if a "Next" button is available
            next_button = driver.find_elements(By.CSS_SELECTOR, "a.paginate_button.next")
            if next_button and next_button[0].is_displayed():
                driver.execute_script("arguments[0].click();", next_button[0])  # Click using JavaScript
                time.sleep(3)  # Allow time for new data to load
            else:
                break  # Exit loop if no next page is found

            filename = f"{symbol}_price_history.csv"

    # Open the file and write the data directly
            with open(filename, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
        
        # Write header only once
                writer.writerow(headers)

        # Write all rows
                writer.writerows(all_data)
                print(f"✅ Data saved for {symbol} in {filename}")


    except Exception as e:
        print(f"❌ Error extracting {symbol}: {e}")

# List of company symbols
symbols = ["SADBL"]

# Loop through all symbols, ensuring the driver is properly reset
for symbol in symbols:
    get_price_history(symbol)
    driver.delete_all_cookies()  # Clear session cookies
    driver.refresh()  # Ensure fresh page load

# Close browser
driver.quit()
