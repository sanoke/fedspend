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
# @app.route('/flaskapp/<industry>')
def index():
  yvals = [15339,
           21345,
           18483,
           13000,
           23489,
           24092, 
           12034]
  query = '''
  SELECT *
  FROM legis_by_year_hr
  LIMIT 1;
  '''
  data_list = get_data(query)
  industry = request.args.get('industry')
  if industry is None:
    return render_template('index.html', \
                          industry = industry, \
                          yvals = yvals, \
                          industry_list = industry_list,
                          dem_totals = [(0,0)],
                          repub_totals = [(0,0)],
                          legis_totals = None)
  else:
    industry_totals_q = '''
    SELECT SUM(amount), party, year, description
    FROM indus_by_year_hr
    WHERE description = %s
    GROUP BY year, party, description
    ORDER BY year, party
    '''
    industry_totals = get_data_filtered(industry_totals_q, (industry,))

    dem_totals = [(amt[0],amt[2]) for amt in industry_totals if amt[1] == 'Democrat']
    repub_totals = [(amt[0],amt[2]) for amt in industry_totals if amt[1] == 'Republican']

    legis_totals_q = '''
     SELECT firstname, lastname, description,
            party, district, state_name, year,
            ROUND( amount / 10^6, 2) AS amount_r,
            ROUND( amount / population, 2) AS contract_pp,
            ROUND( amount / med_hh_income, 2) as contract_income
      FROM legis_by_year_hr
      WHERE description = %s
      AND year > '2014'
      ORDER BY amount DESC
      LIMIT 15
    '''
    legis_totals = get_data_filtered(legis_totals_q, (industry,))

    return render_template('index.html', \
                          industry = industry, \
                          industry_list = industry_list, \
                          dem_totals = dem_totals, \
                          repub_totals = repub_totals,
                          legis_totals = legis_totals)


if __name__ == '__main__':
  app.run()