#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
# File       : extract_bill_info.py                                            #
# License    : GNU GPL                                                         #
# Author     : rabarba <rabarbrablad@gmail.com>                                #
# Created    : 26.11.2020                                                      #
# Modified   : 26.11.2020                                                      #
# Modified by: rabarba <rabarbrablad@gmail.com>                                #
################################################################################
from bs4 import BeautifulSoup
from datetime import date, timedelta
from alch_data import db_session
from sqlalchemy.sql import exists
from alch_models import Bill
import requests
import re

yesterday = date.today() - timedelta(days=1)
http = "https://sozd.duma.gov.ru/calendar/b/day/{}/{}".format(yesterday, yesterday)
resp = requests.get(http)
soup = BeautifulSoup(resp.text, 'lxml')
bills = []
for link in soup.find_all("a", class_="calen_num"):
    if link.text not in bills:
        bills.append(link.text)

for bill in bills:

    if db_session.query(exists().where(Bill.num == bill)).scalar():
        bill_obj = db_session.query(Bill).filter_by(num=bill).first()
        added_links = bill_obj.get_links()
    else:
        bill_obj = Bill(bill)
        added_links = []
    url = "https://sozd.duma.gov.ru/bill/" + bill
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'lxml')
    links = []
    for link_ in soup.find_all(href = re.compile("download")):
        if link_["href"][0] == "/":
            link = "http://sozd.duma.gov.ru" + link_["href"]
        else:
            link = link_["href"]
        if link in added_links:
            continue
        typ = link_.find("span", class_=re.compile("format"))
        if typ == None:
            typ = "rtf"
            continue
        elif typ["class"][0][7:] == "msword":
            typ = "doc"
        else:
            typ = typ["class"][0][7:]
        if (link, typ) not in links:
            links.append((link, typ))
    for link in links:
        print("{}\t{}".format(link[1], link[0]))

    events_soup = soup.find_all(attrs={"data-eventdate": re.compile(yesterday.isoformat())})
    events = []
    for event in events_soup:
        event = event.find("li")
        if event != None and event.text.strip() not in events:
            events.append(event.text.strip())
    print("================================================")
    print(url)
    print("events:\n{}".format("\n".join(events)))
    
    bill_obj.update_links(links, yesterday)
    bill_obj.update_events(events, yesterday)
    bill_obj.update_date(yesterday)

for user in User.query.all():
    print(str(user.chat_id) + '\n' + user.compose_message()) 
