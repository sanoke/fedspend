from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
  return 'go to bit.ly/federalSpend'

@app.route('/flaskapp/')
def hello_world2():
  return 'hello! congrats!'  

if __name__ == '__main__':
  app.run()