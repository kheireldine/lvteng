from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)


@app.route('/')
def index():
   print('Request for index page received')
   return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/hello', methods=['POST'])
def hello():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(f.filename))
        print(f.filename)
        #chunk_name_list = process_sudio(f.filename)
        #chunk_name_list = f.filename
        #print(chunk_name_list)
        
        return f.filename
    else:
        return "Hello World"


if __name__ == '__main__':
   app.run()