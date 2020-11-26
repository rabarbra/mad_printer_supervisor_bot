#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
# File       : alch_data.py                                                    #
# License    : GNU GPL                                                         #
# Author     : rabarba <rabarbrablad@gmail.com>                                #
# Created    : 23.11.2020                                                      #
# Modified   : 23.11.2020                                                      #
# Modified by: rabarba <rabarbrablad@gmail.com>                                #
################################################################################

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import alch_models
    Base.metadata.create_all(bind=engine)
