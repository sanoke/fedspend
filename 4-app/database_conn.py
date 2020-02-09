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
                                  host='10.0.0.13')
    return connection	

def get_data(query):
	con = get_db()
	curs = con.cursor()
	curs.execute(query)
	data_list = curs.fetchall()
	# port_list = [port[0] for port in port_list]
	return data_list