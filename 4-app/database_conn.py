from flask import current_app, g
import click
from flask.cli import with_appcontext
import psycopg2

def get_db():
    connection = psycopg2.connect(database='fedspend',
                                  user='sanoke',
                                  sslmode='require',
                                  sslrootcert='certs/ca.crt',
                                  sslkey='certs/client.sanoke.key',
                                  sslcert='certs/client.sanoke.crt',
                                  password='RWwuvdj75Me4',
                                  port=26257,
                                  host='10.0.0.17')
    return connection

def get_data(query):
    con = get_db()
    curs = con.cursor()
    curs.execute(query)
    data_list = curs.fetchall()
    curs.close()
    con.close()
    return data_list

def get_data_filtered(query1, query2):
    con = get_db()
    curs = con.cursor()
    curs.execute(query1, query2)
    data_list = curs.fetchall()
    curs.close()
    con.close()
    return data_list

industry_list_q = '''
SELECT DISTINCT description 
FROM legis_by_year_hr
WHERE description != 'None'
ORDER BY description;
'''
industry_list = get_data(industry_list_q)