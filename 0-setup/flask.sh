# - # - # - # - # - # - # - # - # - # - # - #
#
#   SETTING UP FLASK / WEB UI
#   https://github.com/sanoke/fedspend/wiki/Setting-up:-Flask
#
# - # - # - # - # - # - # - # - # - # - # - #

# RESOURCES
# https://flask.palletsprojects.com/en/1.1.x/installation/#python-version
# hello world: https://www.datasciencebytes.com/bytes/2015/02/24/running-a-flask-app-on-aws-ec2/
# templates:   https://flask.palletsprojects.com/en/1.0.x/templating/

ssh ubuntu@$WEBUI_PUBLIC_IP_DNS

# - 1 - INSTALL APACHE WEBSERVER AND MOD_WGSI
sudo apt update
sudo apt install apache2
sudo apt install libapache2-mod-wsgi

# - 2 - INSTALL FLASK
sudo apt install python3-pip
sudo pip3 install flask

# - 3 - CREATE FLASKAPP: DIRECTORIES, FLASKAPP.PY AND FLASKAPP.WSGI 
# ----- components of the Flask app, that create dynamic parts of webpage
mkdir ~/flaskapp
sudo ln -sT ~/flaskapp /var/www/html/flaskapp

# testing whether the soft link above is working...
echo "Hello World" > ~/flaskapp/index.html

# - 4 - ENABLE MOD_WSGI
# ----- helps Apache display the dynamic content from our app

sudo nano /etc/apache2/sites-enabled/000-default.conf
# ----- add the following block just after the DocumentRoot /var/www/html line
#       in 000-default.conf

WSGIDaemonProcess flaskapp threads=5
WSGIScriptAlias / /var/www/html/flaskapp/flaskapp.wsgi
<Directory flaskapp>
    WSGIProcessGroup flaskapp
    WSGIApplicationGroup %{GLOBAL}
    Order deny,allow
    Allow from all
</Directory>


# - 5 - CONNECT COCKROACHDB TO FLASK
# https://www.cockroachlabs.com/docs/stable/build-a-python-app-with-cockroachdb.html
pip3 install psycopg2
# 


# - 6 - MOVE FLASK FILES TO EC2 INSTANCE 
# ----- (from local machine)
scp 4-app/flaskapp.py 4-app/flaskapp.wsgi ubuntu@$WEBUI_PUBLIC_IP_DNS:~/flaskapp


# - 7 - RESTART WEBSERVER
# ----- remember to restart the webserver any time there's a change to 
# ----- the Flask app!!!
sudo apachectl restart