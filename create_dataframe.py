from bs4 import BeautifulSoup
import requests
from lxml import html
from urllib.parse import urljoin
import re
import urllib3
import pandas as pd 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = 'https://www.tdcj.texas.gov/death_row/dr_executed_offenders.html'


### Inmate organization is organized as a table on the website with links for last statements and more info on the inmate. 
### Pull out 
def get_rows():
    html = requests.get(url, verify = False).text
    soup = BeautifulSoup(html, 'lxml')
    inmate_rows = soup.find_all('tr')[1:]
    return inmate_rows

# pull out the URL which contains last words 
def get_last_words_url(inmate_row):
    tds = inmate_row.select('td')
    lastword_td = tds[2]
    link = lastword_td.select('a')[0]
    href = link.attrs['href']
    return urljoin(url, href)

# format the last words better
def clean_last_words(last_statement): 
    if "Last Statement" in last_statement:
        last_statement.remove("Last Statement:")
    last_words = '\n'.join(last_statement[3:])
    last_words = last_words.replace("Last Statement:", '')
    last_words = re.sub("[’,'â\"“]+", "", last_words)
    last_words = " ".join(last_words.split())
    return last_words

# from URL, pull out the last words and clean them up
def get_last_words(last_words_url): 
     # fetch page
    html = requests.get(last_words_url, verify = False).text # get page 
    soup = BeautifulSoup(html, 'lxml')
    par = soup.select("p")
    last_statement_attributes = [] ## put attributes into list
    last_statement = []
    for i in range(1, (len(par) - 1)):
        # get last statements
        last_statement.append(par[i + 1].get_text())
        # get attributes of last statement
        last_statement_attributes.append(par[i].get_text())
    last_words = [clean_last_words(last_statement)]
    return last_words


# get demographic information URL 
def get_demographics_url(inmate):
    tds = inmate.select('td')
    demographics = tds[1]
    link = demographics.select('a')[0]
    href = link.attrs['href']
    return urljoin(url, href)


# get demographics
def get_demographics(inmate_row): 
        demo_url = get_demographics_url(inmate_row) # get demo URL 
        html2 = requests.get(demo_url, verify = False).text
        soup2 = BeautifulSoup(html2, 'lxml')
        rows = soup2.find_all('tr')
        attributes = []
        for i in rows:
            attributes.append(i.get_text().strip())
        if len(attributes) >= 8:
            education = re.sub("[^0-9]", "", attributes[5].split('\n')[1])
            age_offense = attributes[7].split('\n')[1]
            dob = attributes[2].split('\n')[1]

        else:
            education = ''
            age_offense = ''
            dob = ''
        race = inmate_row.select('td')[8].text
        execution_num = inmate_row.select('td')[0].text
        tcdj_num = inmate_row.select('td')[5].text
        date_executed = inmate_row.select('td')[7].text
        row_list = [execution_num, tcdj_num, race, dob, date_executed, age_offense, education]
        return row_list

def create_inmate_df(): 
    pd_list = []
    for row in get_rows():
        # last words
        lastwords_url = get_last_words_url(row)
        last_word_list = get_last_words(lastwords_url)
        demo_list = get_demographics(row)
        attrbs = demo_list + last_word_list
        pd_list.append(attrbs)
    inmate_df = pd.DataFrame(pd_list,columns = ['execution_num', 'tcdj_num', 'race', 'dob', 'date_executed', 'age_offense', 'education', 'last_words'])
    return inmate_df


