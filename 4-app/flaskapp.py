# WEB UI BACKEND
# scp -r 4-app/* ubuntu@$WEBUI_PUBLIC_IP_DNS:~/flaskapp
# remember to restart apache after every change! sudo apachectl restart
# scp ubuntu@$WEBUI_PUBLIC_IP_DNS:/var/log/apache2/error.log ./setup-scripts

from flask import Flask, escape, url_for, render_template, \
                  redirect, request
from flask_sqlalchemy import SQLAlchemy
from database_conn import *

app = Flask(__name__)

@app.route('/')
def root():
  return redirect(url_for('index'))


@app.route('/flaskapp/')
# @app.route('/flaskapp/<name>')
# def index(name=None):
#   author = request.args.get('author')
#   return render_template('index.html', name=author)
def index(name=None):
  yvals = [15339,
           21345,
           18483,
           13000,
           23489,
           24092,
           12034]
  query = ''' 
  SELECT year, sum(amount) FROM (
    SELECT DISTINCT * FROM (
        SELECT *
        FROM govcontract_data
        WHERE "firstName" = 'Tim'
        AND "lastName" = 'Ryan'
        AND state = 'OH'
        AND district = '13'))
    GROUP BY year;
  '''
  data_list = get_data(query)
  return render_template('index.html', name=data_list, yvals=yvals)           


if __name__ == '__main__':
  app.run()