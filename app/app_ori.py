import random
import requests
import cPickle as pickle
from flask import Flask, request, render_template
import flask
from AnomalyDetect import AnomalyDetect
from werkzeug import secure_filename
import os

app = Flask(__name__)

background_img = '/home/wilber/work/Galvanize/gcp/app/static/background/white100x100.png'

UPLOAD_FOLDER = '/home/wilber/work/Galvanize/gcp-data/iForest/tmp'
PROCESSED_FOLDER = '/home/wilber/work/Galvanize/gcp/app/static'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# app.config['ALLOWED_EXTENSIONS'] = set(['PNG', 'JPG', 'JPEG', 'GIF',
#                                         'png', 'jpg', 'jpeg', 'gif'])

app.config['ALLOWED_EXTENSIONS'] = set(['PNG', 'JPG', 'JPEG',
                                        'png', 'jpg', 'jpeg'])

@app.route('/')
def index():
    return '''
    <html>
    <body>
    <h2>Welcome to Anomaly Detection.</h2>
    <a href="/form">Let's get started</a>
    </body>
    </html>
    '''

@app.route('/form', methods=["GET", "POST"])
def form():
    return '''
    <html>
    <body>
    <h2>Start by Uploading</h2>
    Each time you upload files, previous uploads will be removed from the server.
    <p>
    At this time, GIF format files will be ignored.
    <p>
    <table>
    <tr><td>
            <form method="POST" enctype="multipart/form-data" action="/upload">
                <input type="file" name="file[]" multiple="">
                <input type="submit" value="Upload">
            </form>
        </td>
    </tr>
    <tr><td>
            <form action="/do_it" method="POST">
                <input type="radio" name="action" value="process images" checked>Process my images<br>
                <input type="radio" name="action" value="show images" disabled>Show my images<br>
                <input type="radio" name="action" value="show anomalies" disabled>Show anomaly scores<br>
                <select name="anomaly count">
                    <option value="4">4</option>
                    <option value="8">8</option>
                    <option value="12" selected>12</option>
                    <option value="16">16</option>
                    <option value="20">20</option>
                </select>
                <input type="submit" value="Submit">
            </form>
        </td>
    </tr>
    </table>
    '''

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload', methods=["POST"])
def upload():
    myModel.src_file_list = []
    myModel.proc_file_list = []
    os.system('rm {0}/*'.format(UPLOAD_FOLDER))
    retPage = '''
    <html>
    <body>
    <h3>Your uploads</h3>
    <p>&nbsp;</p>
    <form action="/do_it" method="POST">
    <input type="radio" name="action" value="process images" checked hidden>
    <input type="submit" value="Prepare these files for testing.">
    <p>&nbsp;</p>
    <table>
    <tr align="left"><th>i</th><th>File name</th><th>Status</th></tr>
    '''
    uploaded_files = flask.request.files.getlist("file[]")
    OKstr = "<tr><td>{0}</td><td>{1}</td><td>OK</td></tr>"
    sadStr = "<tr><td>{0}</td><td>{1}</td><td>Not permitted (ignored)</td></tr>"
    for i, file in enumerate(uploaded_files):
#       print file.filename.encode('utf-8', 'ignore')
        print file.filename.encode('utf-8')
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            retPage += OKstr.format(i + 1, file.filename.encode('utf-8', 'ignore'))
        else:
            retPage += sadStr.format(i + 1, file.filename.encode('utf-8', 'ignore'))

    retPage += "</table>\n</body>\n</html>"
    return retPage

@app.route('/do_it', methods=['POST'])
def do_something():
    action = str(request.form['action'])
    if action == "process images":
        print "\nAction selected: process images\n"
        os.system('rm {0}/*.png'.format(PROCESSED_FOLDER))
        myModel.process_files(UPLOAD_FOLDER)
        os.system('scp {0} {1}/'.format(background_img, PROCESSED_FOLDER))
        return '''
    <form action="/do_it" method="POST">
        <input type="radio" name="action" value="show images" checked>Show my images
        <br>
        <input type="radio" name="action" value="show anomalies">Show anomaly scores<br>
         <select name="anomaly count">
             <option value="4">4</option>
             <option value="8">8</option>
             <option value="12" selected>12</option>
             <option value="16">16</option>
             <option value="20">20</option>
        </select>
        <input type="submit" value="Submit">
    </form> 
        '''
    elif action == "show images":
        print "\nAction selected: show images\n"
        files = myModel.proc_file_list
#       print "\nfiles:", files
        modulo6 = len(files) % 6
        if modulo6 != 0:
            files += ['white100x100.png']*(6 - modulo6)
        print "\nfiles:", files
        files = [files[x:x+6] for x in xrange(0, len(files), 6)]
        return render_template('display_images.html', data = files)

    elif action == "show anomalies":
        print "\nAction selected: show anomalies\n"
        k = str(request.form['anomaly count'])
        print "\nk: {0}".format(k)
        myModel.load_files()
        myModel.fit()
        return render_template('display_top_k.html',
                               data = myModel.show_top_k(int(k)))


if __name__ == '__main__':
    myModel = AnomalyDetect(use_color=False)
#   myModel = AnomalyDetect(use_color=True)
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)