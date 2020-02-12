# Application for FedSpend

The web interface is a Flask app served with Apache Server via a WSGI.

![](https://github.com/sanoke/fedspend/raw/master/img/UI.png)

The app structure itself is very straightforward. It consists of 

1. A Python script (`flaskapp.py`) that translates user input into its corresponding SQL query and retrieves the results (`database_conn.py`)
2. A single HTML file (`templates/index.html`) that displays the results in a plot. 
   * The plot is created with an inline JavaScript script and styled by [Chart.js](https://www.chartjs.org/) and website styled with the [Bootstrap](https://getbootstrap.com) CSS library (`static/css/dashboard.css`).
3. A WSGI file (`flaskapp.wsgi`) that's used to manage communication between the Apache server and the Flask app.
