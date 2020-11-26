#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
# File       : models.py                                                       #
# License    : GNU GPL                                                         #
# Author     : rabarba <rabarbrablad@gmail.com>                                #
# Created    : 26.11.2020                                                      #
# Modified   : 26.11.2020                                                      #
# Modified by: rabarba <rabarbrablad@gmail.com>                                #
################################################################################
import requests
import shutil
import pdfplumber
import docx2txt
import html2text
import textract
import os
import re
from datetime import date, timedelta
from bs4 import BeautifulSoup
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import exists
from data import Base, db_session
from pyth.plugins.rtf15.reader import Rtf15Reader
from pyth.plugins.xhtml.writer import XHTMLWriter

user_bills = Table('user_bills', Base.metadata,
        Column('bill_id', Integer, ForeignKey('bill.id'), primary_key=True),
        Column('user_id', Integer, ForeignKey('user.chat_id'), primary_key=True)
        )

user_keywords = Table('user_keywords', Base.metadata,
        Column('keyword_id', Integer, ForeignKey('keyword.id'), primary_key = True),
        Column('user_id', Integer, ForeignKey('user.chat_id'), primary_key = True),
        )

link_keywords = Table('link_keywords', Base.metadata,
        Column('keyword_id', Integer, ForeignKey('keyword.id'), primary_key = True),
        Column('link_id', Integer, ForeignKey('link.id'), primary_key = True),
        )

bill_keywords = Table('bill_keywords', Base.metadata,
        Column('keyword_id', Integer, ForeignKey('keyword.id'), primary_key = True),
        Column('bill_id', Integer, ForeignKey('bill.id'), primary_key = True),
        )

class Bill(Base):

    __tablename__="bill"
    id = Column(Integer, primary_key=True)
    num = Column(String(120), unique=True)
    description = Column(String(500))
    authors = Column(String(500))
    date = Column(Date)
    updated_date = Column(Date)
    events = relationship("Event", backref = 'bill', lazy = True)
    links = relationship("Link", backref = 'bill', lazy = True)
    users = relationship("User", secondary = user_bills, back_populates = 'bills')
    keywords = relationship("Keyword", secondary = bill_keywords, back_populates = 'bills')

    def __init__(self, num):    
        self.num = num
        self.add_params()
        db_session.add(self)
        db_session.commit()
    
    def __repr__(self):
        return '<Bill %r>' % (self.num)

    def add_params(self):
        url = "https://sozd.duma.gov.ru/bill/" + self.num
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'lxml')
        descr = soup.find(id = "oz_name").text.strip()
        comm = soup.find(id = "oz_name_comment")
        if comm != None:
            descr += "\n" + comm.text.strip()
        self.description = descr
        print(descr)
        self.authors = soup.find("div", class_="opch_r").text.strip()
        print(self.authors)
        date_arr = [int(i) for i in soup.find("span", class_="mob_not").text.strip().split(".")[::-1]]
        print(date_arr)
        self.date = date(*date_arr)
        for keyword in Keyword.query.all():
            if re.search(fr'.*{keyword.word}.*', (descr + self.authors).lower().replace(" ", "")):
                self.keywords.append(keyword)

    def update_links(self, links, date):
        for link in links:
            if db_session.query(exists().where(Link.link == link[1])).scalar():
                continue
            else:
                self.links.append(Link(*link, self, date))
        db_session.commit()

    def update_events(self, events, date):
        for event in events:
            self.events.append(Event(event, date, self))
        db_session.commit()

    def update_date(self, updated_date):
        self.updated_date = updated_date
        db_session.commit()

    def get_links(self):
        return ([i.link for i in self.links])

class Link(Base):

    __tablename__ = "link"
    id = Column(Integer, primary_key=True)
    link = Column(String(120), unique=True)
    typ = Column(String(10))
    text = Column(Text)
    date = Column(Date)
    bill_id = Column(Integer, ForeignKey("bill.id"), nullable = False)
    keywords = relationship("Keyword", secondary = link_keywords, back_populates = 'links')
    
    def __init__(self, link, typ, bill, date):

        self.typ = typ
        self.link = link
        self.bill_id = bill.id
        self.date = date
        self.download_text()
        db_session.add(self)
        self.add_keywords()
        db_session.commit()

    def __repr__(self):
        return "<Link {} {}>".format(self.typ, self.link)

    def download_text(self):
        filename = self.link[33:] + "." + self.typ
        try:
            with requests.get(self.link, stream=True) as r:
                with open(filename, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
        except:
            print("Error downloading " + self.link)
        text = ""
        if self.typ == "pdf":
            try:
                print("Extracting " + filename)
                with pdfplumber.open(filename) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text()
            except:
                try:
                    text += textract.process(filename, method = "tesseract", language = "rus").decode("utf-8")
                except:
                    print("Error extracting " + filename)
        elif self.typ == "doc":
            try: 
                text += docx2txt.process(filename)
            except:
                try:
                    output = filename[:-3] + "txt"
                    os.system("antiword {} > {}".format(filename, output))
                    with open(output) as f:
                        text += f.read()
                    os.remove(output)
                except:
                    print("Error extracting " + filename)
        elif self.typ == "rtf":
            try:
                doc = Rtf15Reader.read(open(filename, "rb"))
                text += html2text.html2text(XHTMLWriter.write(doc, pretty=True).read().decode("utf-8"))
            except:
                print("Error extracting " + filename)
        os.remove(filename)
        self.text = text

    def add_keywords(self):
        for keyword in Keyword.query.all():
            if re.search(fr'.*{keyword.word}.*', self.text.replace(" ", "").lower()):
                self.keywords.append(keyword)

class Keyword(Base):

    __tablename__ = 'keyword'
    id = Column(Integer, primary_key = True)
    word = Column(String(120), unique = True)
    users = relationship("User", secondary = user_keywords, back_populates = 'keywords')
    links = relationship("Link", secondary = link_keywords, back_populates = 'keywords')
    bills = relationship("Bill", secondary = bill_keywords, back_populates = 'keywords')

    def __init__(self, user, word):
        self.word = word.lower().strip()
        self.users.append(user)
        db_session.add(self)
        self.find_new_keyword()
        db_session.commit()

    def __repr__(self):
        return "<Keyword {}>".format(self.word)

    def return_or_create(user, word):
        if db_session.query(exists().where(Keyword.word == word)).scalar():
            keyword_obj = db_session.query(Keyword).filter_by(word=word).first()
            return(keyword_obj)
        else:
            return(Keyword(user, word))
    
    def get_all_keywords():
        return([k.word for k in Keyword.query.all()])

    def find_new_keyword(self):
        for link in Link.query.all():
            if re.search(fr'.*{self.word}.*', link.text.replace(" ", "").lower()):
                link.keywords.append(self)
        for bill in Bill.query.all():
            if re.search(fr'.*{self.word}.*', (bill.description + bill.authors).replace(" ", "").lower()):
                bill.keywords.append(self)

class Event(Base):

    __tablename__ = 'event'
    id = Column(Integer, primary_key=True)
    descr = Column(Text)
    date = Column(Date)
    bill_id = Column(Integer, ForeignKey("bill.id"), nullable = False)

    def __init__(self, descr, date, bill):
        self.descr = descr
        self.date = date
        self.bill_id = bill.id
        db_session.add(self)
        db_session.commit()

    def __repr__(self):
        return "<Event {}>".format(self.descr[:50])

class User(Base):

    __tablename__ = "user"
    chat_id = Column(Integer, primary_key=True)
    bills = relationship("Bill", secondary = user_bills, back_populates = 'users')
    keywords = relationship("Keyword", secondary = user_keywords, back_populates = 'users')

    def __init__(self, chat_id):
        self.chat_id = chat_id
        db_session.add(self)
        db_session.commit()

    def __repr__(self):
        return "<User {}>".format(self.chat_id)

    def add_keywords(self, keywords):
        if len(keywords) > 0:
            added = set(self.get_keywords())
            to_add = set(keywords).difference(added)
            print("added: {}\nto_add: {}\nkeywords: {}".format(added, to_add, keywords))
            for word in to_add:
                self.keywords.append(Keyword.return_or_create(self, word))
            db_session.commit()

    def get_keywords(self):
        return([i.word for i in self.keywords])

    def add_bills(self, bills):
        for bill in bills:
            if db_session.query(exists().where(Bill.num == bill)).scalar():
                bill_obj = db_session.query(Bill).filter_by(num=bill).first()
                self.bills.append(bill_obj)
            else:
                self.bills.append(Bill(bill))
        db_session.commit()

    def compose_message(self, date):
        msg = ""
        for bill in Bill.query.filter_by(updated_date = date):
            if bill in self.bills:
                msg += bill.num + "\n"
            if not set(self.keywords).isdisjoint(set(bill.keywords)):
                msg += bill.num + ': ' + ", ".join([i.word for i in (set(self.keywords) & set(bill.keywords))]) + "\n"
        for link in Link.query.filter_by(date = date):
            if not set(self.keywords).isdisjoint(set(link.keywords)):
                msg += link.link + ': ' + ", ".join([i.word for i in (set(self.keywords) & set(link.keywords))]) + "\n"
        return(msg)
