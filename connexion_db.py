from flask import g

import pymysql.cursors

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = pymysql.connect(
            host="localhost",
            # host="serveurmysql",
            user="snicod",
            password="2502",
            database="BDD_snicod",
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    return db
