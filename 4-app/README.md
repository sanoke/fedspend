# Application for FedSpend

The web interface is a Flask app served with Apache Server via a WSGI.

![](https://github.com/sanoke/fedspend/raw/master/img/UI.png)

The app structure itself is very straightforward. It consists of 

1. A Python script (`flaskapp.py`) that translates user input into its corresponding SQL query and retrieves the results (`database_conn.py`)
2. A single HTML file (`templates/index.html`) that displays the results in a plot. 
   * The plot is rendered with an inline JavaScript script (Chart.js) and website styled with the Bootstrap CSS library.
