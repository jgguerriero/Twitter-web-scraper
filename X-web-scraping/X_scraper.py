
##### SETUP #####

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from getpass import getpass
import numpy as np
from time import sleep
from selenium.common.exceptions import NoSuchElementException



##### LOGGING INTO TWITTER #####

# assign driver and go to website
# need to locate path for chromedriver
driver = webdriver.Chrome(service = Service('/Users/jgg5264/Library/CloudStorage/OneDrive-ThePennsylvaniaStateUniversity/Twitter scraping/chromedriver-mac-arm64/chromedriver'))
driver.get("https://www.twitter.com/login")
sleep(5)

# navigate to login and enter email
username_login = driver.find_element(By.XPATH, "//input[@name]")
username_login.send_keys('josephgguerriero@gmail.com') # replace with your email
username_login.send_keys(Keys.RETURN)
sleep(5)

# run next chunk if there is an intemerediate login page, then enter username
# this happens if you try to login too many times 
# username_extra = driver.find_element(By.XPATH, "//input")
# username_extra.send_keys("_joeguerriero") # replace with your handle
# username_extra.send_keys(Keys.RETURN)
# sleep(5)

# enter my password and log in 
my_password = getpass() # need to pause here and manually enter your login password
password_entry = driver.find_element(By.XPATH, "//input[@name='password']")
password_entry.send_keys(my_password)
password_entry.send_keys(Keys.RETURN)



##### SCRAPING TWITTER POSTS #####

search_terms = "threat to humanity lang:en -filter:replies" # this could be some kind of array if you want to loop through different searches
n_cases = 50 # small number just for demonstration 

# get to posts specific to the search term (again, this could be looped if you have multiple terms)
search_term_location = driver.find_element(By.XPATH, "//input[@data-testid='SearchBox_Search_Input']")
search_term_location.send_keys(search_terms)
search_term_location.send_keys(Keys.RETURN)
sleep(5)

# loop through posts on multiple pages
full_scrape = pd.DataFrame([])
while len(full_scrape) < n_cases:
    
    # grab the individual posts on the page (specifically, grab the last 20 to prevent duplicates)
    page_posts = driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")[-20:]
    # loop through posts on each page 
    page_scrapes = pd.DataFrame([])
    for post in page_posts:
        
        # get link to profile pages
        link = post.find_element(By.XPATH, ".//div[@data-testid='User-Name']//a").get_attribute("href")
                
        # get post text (also include the text of the original tweet if available)
        tweet_and_original = post.find_elements(By.XPATH, ".//div[@data-testid='tweetText']")
        tweet_and_original_text = str()
        for i in range(len(tweet_and_original)): 
            tweet_and_original_text = tweet_and_original_text + " " + tweet_and_original[i].text
        # get rid of "\n" character 
        tweet_and_original_text = tweet_and_original_text.replace('\n', ' ')
        
        # get likes on post 
        likes = post.find_element(By.XPATH, ".//div[@data-testid='like']").get_attribute("aria-label")
        
        # get date/time when tweet was posted 
        try: 
            date_time = post.find_element(By.XPATH, ".//time").get_attribute("datetime")
        except NoSuchElementException:
            date_time = "sponsored content" # sponsored content doesnt have a datetime attribute - so we use this as a filter
            
        # see if poster is verified 
        try: 
            verified_badge = post.find_element(By.XPATH, ".//*[local-name()='svg'][@aria-label='Verified account']").get_attribute("class")
        except NoSuchElementException:
            verified_badge = "no badge" 
            
        # add extracted post characterists to common dataframe 
        page_scrapes = pd.concat([page_scrapes, pd.DataFrame([link, tweet_and_original_text, likes, date_time, verified_badge, search_terms]).T], axis=0)
    
    # add extracted post collection characterists to the common dataframe 
    full_scrape = pd.concat([full_scrape, page_scrapes], axis=0)
    
    # EXCLUSIONS 
    # only include cases that have tweets greater than 200 characters in length (can be modified)
    full_scrape = full_scrape.loc[full_scrape[1].str.len() > 100]
    
    # remove cases that have duplicate users, keep earlier oldest post 
    full_scrape = full_scrape.drop_duplicates(subset=[0], keep='last')
    
    # remove cases that are sponsored content
    full_scrape = full_scrape.loc[full_scrape[3] != "sponsored content"]
          
    # scroll down page 
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(4)
    
    # print length so that monitoring is easy
    print(len(full_scrape))
    

full_scrape.shape
full_scrape.head()



##### SCRAPE USER INFO  #####

full_scrape_user_info = pd.DataFrame([])
for i in range(0,len(full_scrape)):
    
    driver.get(full_scrape.iloc[i,0])
    sleep(4)
    num_twts = driver.find_element(By.XPATH, "//div[@class='css-1rynq56 r-dnmrzs r-1udh08x r-3s2u2q r-bcqeeo r-qvutc0 r-37j5jr r-n6v787 r-1cwl3u0 r-16dba41']").text
    num_followers = driver.find_element(By.XPATH, "(//div[@class='css-175oi2r']//span[@class='css-1qaijid r-bcqeeo r-qvutc0 r-poiln3 r-1b43r93 r-1cwl3u0 r-b88u0q'])[2]").text
    full_scrape_user_info = pd.concat([full_scrape_user_info, pd.DataFrame([full_scrape.iloc[i,0], num_twts, num_followers]).T], axis=0)
    
    print(i)
    
full_scrape_user_info.shape
full_scrape_user_info.head()    



##### MERGE POST AND USER DATA #####

final_data = pd.merge(full_scrape, full_scrape_user_info, on=0)
final_data.columns = ["user_link", "post_text", "post_likes", "post_time", "verified badge", "search_term", "user_n_posts", "user_followers_n"]

# then export data
final_data.to_csv('final_data.csv', index=False)











