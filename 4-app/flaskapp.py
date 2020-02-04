from flask import Flask, escape, url_for, render_template, redirect
app = Flask(__name__)

@app.route('/')
def root():
  return redirect(url_for('index'))

@app.route('/flaskapp/')
def index():
  return "hello! congrats!"

@app.route('/flaskapp/hello/')
@app.route('/flaskapp/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)  

@app.route('/flaskapp/legislator/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'Legislator %s' % escape(username)

if __name__ == '__main__':
  app.run()