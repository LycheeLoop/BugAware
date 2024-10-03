from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

##----------Selenium code below works, however is not implemented into web app at this time
def get_roach_reviews_count(google_place_url):
    # DRIVER SETUP #
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Open the Google Place URL
        driver.get(google_place_url)
        # Wait for the page to load
        time.sleep(8)  # Adjust if necessary

        # Scroll to and click the 'Reviews' tab
        reviews_tab = driver.find_element(By.XPATH, "//button[@role='tab' and contains(@aria-label, 'Reviews')]")
        reviews_tab.click()

        # Wait for the reviews section to load
        time.sleep(5)

        # Scroll down the reviews section (if needed)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Additional logic can be added here to scrape reviews, etc.
        print("Successfully clicked on the Reviews tab!")
#
        # Wait for scroll completion
        time.sleep(5)  # Adjust if necessary

        # Scroll to the "Refine reviews" section
        refine_reviews_section = driver.find_element(By.XPATH, "//div[@aria-label='Refine reviews']")

        # Scroll to the element using JavaScript
        driver.execute_script("arguments[0].scrollIntoView();", refine_reviews_section)

        # Wait for the scroll to complete and the section to load
        time.sleep(5)


        # Locate the button for "roaches" using its class name and partial text match
        roaches_button = driver.find_element(By.XPATH, "//button[@class='e2moi '][contains(., 'roaches')]")

        # Extract the number next to the word "roaches"
        roaches_count = roaches_button.find_element(By.CLASS_NAME, 'bC3Nkc').text

        # Print the number of reviews mentioning "roaches"
        print(f"Number of reviews mentioning roaches: {roaches_count}")

    except Exception as e:
        print(f"Error: {e}")
#
#       # Close the browser
        driver.quit()


