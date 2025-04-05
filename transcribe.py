## Packages
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# from sle import process_text_files
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
from translate import translate
import os
import pyperclip
import time

MAX_RETRIES = 3


def retry_operation(operation, *args):
    """
    Retry a given operation up to MAX_RETRIES times.
    Stops and raises an error after MAX_RETRIES failures.
    """
    for attempt in range(MAX_RETRIES):
        try:
            return operation(*args)  # Attempt the operation
        except Exception as e:
            print(f"Error in {operation.__name__}: {e}. This was Attempt  {attempt + 1} of {MAX_RETRIES}.")
            if attempt == MAX_RETRIES - 1:  # If last attempt, stop execution
                raise RuntimeError(f"{operation.__name__} failed after {MAX_RETRIES} attempts.") from e

def setup_driver():
    """
    Step 1: Set up the web driver
    """
    # Driver Set Up
    print("Setting up driver...")
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')  # Required for Docker
    chrome_options.add_argument('--start-maximized')  # Attempt to maximize window
    chrome_options.add_argument('--window-size=1920,1080')  # Explicitly set window size
    chrome_options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource issues
    chrome_options.add_argument('--log-level=3')  # Suppress logs
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Disable logging
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=chrome_options, service=service)
    return driver

def login(driver, credentials,wait):
    """
    Step 2: Log in to the website with credentials.
    """
    # Perform login
    print(f"Logging in with credentials: {credentials}")
    website = 'https://trakcarelabwebview.nhls.ac.za/trakcarelab/csp/system.Home.cls#/Component/SSUser.Logon'
    driver.get(website)

    

    #Wait for the login page elements
    username_id = "SSUser_Logon_0-item-USERNAME"
    password_id = "SSUser_Logon_0-item-PASSWORD"
    time.sleep(1)

    username_element = wait.until(EC.presence_of_element_located((By.ID, username_id)))
    password_element = wait.until(EC.presence_of_element_located((By.ID, password_id)))

    
    # Enter the credentials
    username_element.clear()
    username_element.send_keys(credentials['username'])
    password_element.clear()
    password_element.send_keys(credentials['password'] + Keys.ENTER) 
    time.sleep(1)
    record_id = "web_DEBDebtor_FindList_0-item-HospitalMRN"
    record_element = wait.until(EC.presence_of_element_located((By.ID, record_id))) ## STEP 1 - If this can be found then the User has logged in
    # Placeholder for actual login logic

def patient_search(patient_id,wait,driver):
    record_id = "web_DEBDebtor_FindList_0-item-HospitalMRN"
    surname_id = "web_DEBDebtor_FindList_0-item-SurnameParam"

    record_element = wait.until(EC.presence_of_element_located((By.ID, record_id))) ## STEP 1 - If this can be found then the User has logged in
    surname_element  = wait.until(EC.presence_of_element_located((By.ID, surname_id))) ## STEP 1 - If this can be found then the User has logged in
    
    surname_element.clear()
    record_element.clear()

    record_element.send_keys(patient_id + Keys.ENTER) 
    click_element_id = "web_DEBDebtor_FindList_0-row-0-item-Episodes"  # Element to click
    click_element = wait.until(EC.presence_of_element_located((By.ID, click_element_id)))
    time.sleep(1)
    print('Patient Found')

def copy_homepage_content(driver,wait):
    """
    Step 3: Copy and return homepage content.
    """
    print("Copying homepage content...")
    ## Waiting for the Page to load
    time.sleep(1)
    history_caption_id =   "web_EPVisitTestSet_CumulativeHistoryView_0-header-caption"
    history_page_element = wait.until(EC.presence_of_element_located((By.ID,history_caption_id)))
    history_page_element.click()


    # Use JavaScript to extract the content
    copied_content = driver.execute_script("return document.body.innerText")


    if copied_content == '':
        raise ValueError("Copied content is empty. Must retry")


    driver.back()
    time.sleep(1)
    # Placeholder for content scraping
    return copied_content

def count_labs(driver):
    rows = driver.find_elements(By.XPATH, '//md-icon[starts-with(@id, "web_DEBDebtor_FindList_0-row-")]')
    num_of_labs = len(rows)

    print("Number of Labs:", num_of_labs)
    return num_of_labs

def open_folder(wait,lab):
    time.sleep(1)
    if lab >= 1:
        prior_element_id = "web_DEBDebtor_FindList_0-row-"+ str(lab-1)+ "-item-Episodes"
        prior_element = click_elemment = wait.until(EC.presence_of_element_located((By.ID, prior_element_id)))
        prior_element.click()

    click_element_id = "web_DEBDebtor_FindList_0-row-"+ str(lab)+ "-item-Episodes"  # Element to click
    click_element = wait.until(EC.presence_of_element_located((By.ID, click_element_id)))
    click_element.click()

    misc_element_id = "web_EPVisitNumber_List_"+ str(lab) +"_0-row-0-misc-actionButton"
    misc_element = wait.until(EC.presence_of_element_located((By.ID, misc_element_id)))
    time.sleep(1)
    print("Labs Found")

def write_to_file(patient):
    with open("fault_patients.txt", "a") as file:
        file.write("Patient ID:" +  str(patient))

def find_history(wait,lab):

    misc_element_id = "web_EPVisitNumber_List_"+ str(lab) +"_0-row-0-misc-actionButton"
    misc_element = wait.until(EC.presence_of_element_located((By.ID, misc_element_id)))
    misc_element.click()

    cum_history_id = "tc_ActionMenu-link-CumulativeHistory"
    cum_history_element = wait.until(EC.presence_of_element_located((By.ID, cum_history_id)))
    print("Cumulative history found")

def find_data(wait):

    
    cum_history_id = "tc_ActionMenu-link-CumulativeHistory"
    cum_history_element = wait.until(EC.presence_of_element_located((By.ID, cum_history_id)))
    cum_history_element.click()


    history_caption_id =   "web_EPVisitTestSet_CumulativeHistoryView_0-header-caption"
    history_caption_element = wait.until(EC.presence_of_element_located((By.ID,history_caption_id)))
    time.sleep(1)

    print("Patient Data is found")


def main():
    patients  = ["25821273","187773908","132978255","639089310","23203490","136724358","22850861","134911767","69830727","51978906","24502099","19800127","26943928","187773908"]

    for patient in patients:
        try:
            # Step 1: Retry setting up the driver
            driver = retry_operation(setup_driver)
            
            # Step 2: Retry logging in
            username = 'MP0819174'
            password = 'Dermatology2025'

            wait = WebDriverWait(driver,60) ## Setting waiting between steps

            retry_operation(login, driver, {"username": username, "password": password}, wait)
            retry_operation(patient_search,patient,wait,driver)
            labs = int(retry_operation(count_labs,driver))

            patient_textfile_content = ''

            for lab in range(labs):
                try:
                    retry_operation(open_folder, wait, lab)
                    retry_operation(find_history, wait, lab)
                    retry_operation(find_data, wait)
                    content = retry_operation(copy_homepage_content, driver, wait)
                    patient_textfile_content += f"\n Lab : {lab+1} {content}\n"
                except RuntimeError as e:
                    raise RuntimeError(f"Failed while processing lab {lab+1}: {e}") from e


            # Use an absolute path for the textfiles directory
            output_file_path = 'output files\\' + str(patient) + '.txt'

            # Write to the file
            with open(output_file_path, 'w', encoding='utf-8') as file:
                file.write(patient_textfile_content)

            print(f"Textfile Content successfully copied to {output_file_path}")


            # Proceed with the translation
            # process_text_files('textfiles\\','sheets\\')
            # translate(patient_textfile_content, patient)
        

        
        except RuntimeError as error:
            
            print(f"Critical failure: {error}")
           
            file_name = 'fault_patients.txt'
            with open(file_name,'a') as file:
                file.write
                file.write(f"Patient ID: {patient}\n")
                file.write(f"Problem: {error}\n")
                file.write("-" * 40 + "\n")  # Divider for readability
        
        finally:
            print("Cleaning up resources...")
            driver.quit()

if __name__ == "__main__":
    main()