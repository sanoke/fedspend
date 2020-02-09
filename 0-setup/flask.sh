# - # - # - # - # - # - # - # - # - # - # - #
#
#   SETTING UP FLASK / WEB UI
#   https://github.com/sanoke/fedspend/wiki/Setting-up:-Flask
#
# - # - # - # - # - # - # - # - # - # - # - #

# RESOURCES
# https://flask.palletsprojects.com/en/1.1.x/installation/#python-version
# templates:   https://flask.palletsprojects.com/en/1.0.x/templating/

ssh ubuntu@$WEBUI_PUBLIC_IP_DNS

# - 1 - INSTALL APACHE WEBSERVER, MOD_WGSI, and VIRTUALENV
sudo apt update
sudo apt install apache2
sudo apt install libapache2-mod-wsgi-py3
sudo apt install python3-pip


# - 2 - INSTALL FLASK
sudo pip3 install flask


# - 3 - CREATE FLASKAPP: DIRECTORIES, FLASKAPP.PY AND FLASKAPP.WSGI 
# ----- components of the Flask app, that create dynamic parts of webpage
mkdir ~/flaskapp
sudo ln -sT ~/flaskapp /var/www/html/flaskapp

# testing whether the soft link above is working...
# (go to public IP in browser and check)
echo "Hello World" > ~/flaskapp/index.html

# - 4 - ENABLE MOD_WSGI
# ----- helps Apache display the dynamic content from our app

sudo nano /etc/apache2/sites-enabled/000-default.conf
# ----- add the following block just after the DocumentRoot /var/www/html line
#       in 000-default.conf

# WSGIDaemonProcess flaskapp threads=5
# WSGIScriptAlias / /var/www/html/flaskapp/flaskapp.wsgi
# <Directory flaskapp>
#     WSGIProcessGroup flaskapp
#     WSGIApplicationGroup %{GLOBAL}
#     Order deny,allow
#     Allow from all
# </Directory>

# initialize WSGI
sudo a2enmod wsgi

# - 5 - CONNECT COCKROACHDB TO FLASK
# https://www.cockroachlabs.com/docs/stable/build-a-python-app-with-cockroachdb.html
sudo apt install postgresql postgresql-contrib postgresql-server-dev-all
pip3 install setuptools

wget https://files.pythonhosted.org/packages/84/d7/6a93c99b5ba4d4d22daa3928b983cec66df4536ca50b22ce5dcac65e4e71/psycopg2-2.8.4.tar.gz
tar -xf psycopg2-2.8.4.tar.gz
cd psycopg2-2.8.4/
python3 setup.py build
sudo python3 setup.py install
# Extracting psycopg2-2.8.4-py3.6-linux-x86_64.egg to /usr/local/lib/python3.6/dist-packages
# Adding psycopg2 2.8.4 to easy-install.pth file

pip3 install flask_sqlalchemy

# ----- set some environment variables
export DATABASE_URL="postgresql://10.0.0.13:26257/fedspend"


# - 6 - MOVE FLASK FILES TO EC2 INSTANCE 
# ----- (from local machine)
scp -r 4-app/* ubuntu@$WEBUI_PUBLIC_IP_DNS:~/flaskapp


# - 7 - RESTART WEBSERVER
# ----- remember to restart the webserver any time there's a change to 
# ----- the Flask app!!!
sudo apachectl restart

# check this file when debugging
nano /var/log/apache2/error.log 