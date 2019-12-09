from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

url = "https://sso.wis.ntu.edu.sg/webexe88/owa/sso_login1.asp?t=1&p2=https://wish.wis.ntu.edu.sg/pls/webexe/aus_stars_planner.main&extra=&pg="
course_reg_url = "https://wish.wis.ntu.edu.sg/pls/webexe/"

def prebid(user):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless') # for server
    options.add_argument('--no-sandbox')
    #driver = webdriver.Chrome(executable_path="../chromedriver.exe", chrome_options=options)
    driver = webdriver.Chrome(chrome_options=options)
    driver.get(url)
    driver.find_element_by_name('UserName').send_keys(user.username)
    select = Select(driver.find_element_by_name('Domain'))
    select.select_by_value('STUDENT')
    driver.find_element_by_name("bOption").click()
    driver.find_element_by_name('PIN').send_keys(user.password)
    driver.find_element_by_name("bOption").click()
    element_present = expected_conditions.presence_of_element_located((By.NAME, 'plan_no'))
    WebDriverWait(driver, 10).until(element_present)
    select = Select(driver.find_element_by_name('plan_no'))
    select.select_by_value(user.plan)
    return driver

def add_course(driver):
    driver.find_element_by_xpath("//input[@value='Add (Register) Selected Course(s)']").click()
    try:
        element_present = expected_conditions.presence_of_element_located((By.ID, 'ui_body_container'))
        WebDriverWait(driver, 60).until(element_present)
        driver.find_element_by_xpath("//input[@value='Confirm to add course(s)']").click()
        message = driver.page_source
        flag = True
    except Exception as e:
        message = str(e).split("\n")[1]
        flag = False
    finally:
        driver.quit()
        #message = unicode(message, 'utf-8')
	    #message = message.encode('utf-8')
        return str(message), flag

def bid(user, target_time, messages, flags, index):
    driver = prebid(user)
    while target_time != datetime.now().strftime("%d/%m/%Y %H:%M:%S.0"):
        pass
    else:
        messages[index], flags[index] = add_course(driver)
