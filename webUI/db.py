'''
Created on Apr. 25, 2021

@author: Pete Harris
'''
import sqlite3

DATABASE = "../Beercadia.db"


''' Original dict_gen from Python Essential Reference by David Beazley '''
def dict_gen_one(curs):
    field_names = [d[0].lower() for d in curs.description]
    row = curs.fetchone()
    if row:
        return dict(zip(field_names, row))
    return None

def dict_gen_many(curs):
    field_names = [d[0].lower() for d in curs.description]
    while True:
        rows = curs.fetchmany()
        if not rows: return
        for row in rows:
            yield dict(zip(field_names, row))

def hardware_data():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM Hardware")
    out = {}
    for d in dict_gen_many(c):
        out[d["key"]] = d["value"]
    conn.close()
    return out
