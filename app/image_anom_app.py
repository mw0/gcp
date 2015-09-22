#!/usr/bin/python

# alternate: /home/wilber/work/Galvanize/gcp/dato-env/bin/python

import os
from flask import Flask
# from flask import request
# from flask import redirect
# from flask import render_template
# from flask import url_for
# from flask import send_from_directory

from werkzeug import secure_filename

upload_folder = '../../gcp-data/iForest/tmp'
allowed_extensions = set(['PNG', 'JPG', 'JPEG', 'GIF', 'png', 'jpg',
                          'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = upload_folder

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in allowed_extensions

# OUR HOME PAGE
#============================================
@app.route('/')
def submission_page():
    return '''
    <form action="/process_photos" method='POST' >
        <input type="text" name="user_input"/>
        <input type="submit" value="write something" />
    </form>
    '''

@app.route('/process_photos')
def list_em():
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
