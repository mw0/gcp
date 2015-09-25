import random
import requests
import cPickle as pickle
from flask import Flask, request, render_template
import flask
from AnomalyDetect import AnomalyDetect
from werkzeug import secure_filename
import os
from collections import OrderedDict

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
    '''
    This is the welcome page. A simple messagge and a couple of buttons to
    push to get started.
    '''

    return '''
    <html>
    <body>
    <h2>Anomaly Detection Using Isolation Forest.</h2>
    This application finds anomalies in images. It does this by feeding images through a pre-trained deep learning neural network&sup1;, extracting high-level feature weights, and constructing isolation trees&sup2; using those weights.

    <p>For more infomation on this, see the <a href="http://github.com/mw0/gcp">project description</a>.

    <p>
    You can view anomaly scores computed for images we provide, or you can upload your own:

    <form action="/provided_images" method="POST">
        <input type="submit" value="Use existing examples" disabled>
    </form>
    <form action="/upload_form" method="POST">
        <input type="submit" value="I have images to upload">
    </form>
    </p>

    <p>&nbsp;</p><p class="footnote">
    &sup1;<a href="http://www.cs.toronto.edu/~fritz/absps/imagenet.pdf">Krizhevsky, Alex, Ilya Sutskever, and Geoffrey E. Hinton. ~Imagenet classification with deep convolutional neural networks.~ Advances in neural information processing systems. 2012</a>.
    &sup2;<a href="http://dx.doi.org/10.1109/ICDM.2008.17">Liu, F.T., K. M. Ting and Z.-H. Zhou, <em>Isolation Forest</em>, Eighth IEEE International Conference on Data Mining, 2008, ICDM 08., p413., 2008.</a><br>
    </p>
    </body>
    </html>
    '''

@app.route('/provided_images', methods=["GET", "POST"])
def provided_images():
    '''
    This is a form for selecting amoung previously-processsed image sets to see
    how well iForest does with them.
    '''

    return '''
    <html>
    <body>
    <h2>Pre-processed image sets:</h2>
    <ul><li><form action="/show_images" method="POST"><input type="submit" value="Lunar"></form>
        <li><form action="/show_images" method="POST"><input type="submit" value="Boats"></form>
        <li><form action="/show_images" method="POST"><input type="submit" value="Cats (obligatory option)"></form>
    </ul>
    '''

@app.route('/upload_form', methods = ["GET", "POST"])
def upload_form():
    '''
    A simple form permitting users to select a local directory, and files
    within, for upload.
    '''

    return '''
    <html>
    <body>
    <h2>Upload Your Files</h2>
    Each time you upload files, previous uploads will be removed from the server.
    <p>
    Images in formats other than PNG and JPEG will be ignored.
    <p>
    <table>
    <tr><td>
            <form method="POST" enctype="multipart/form-data" action="/upload_process">
                <input type="file" name="file[]" multiple="">
                <input type="submit" value="Upload">
            </form>
        </td>
    </tr>
    </table>
    '''


# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    '''
    Returns True if file name has a permitted extension.
    '''
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def test_process(upload_list):
    '''
    INPUT:
        upload_list	list, names of files user selected for upload.
    RETURN:
        file_status	OrderedDict, keys are file names, values are status
			codes.
    Returns file_status, where status codes default to "OK", but are changed to
    "not permitted" if extension not in ALLOWED_EXTENSIONS.
    '''

    file_status = OrderedDict(list)
    for filethang in upload_list:
        filename = filethang.filename
        if allowed_file(filename):
            file_status[filename] = 'OK'
        else:
            file_status[filename] = 'not permitted'

    return file_status


@app.route('/upload_process', methods = ["GET", "POST"])
def upload_process():
    """
    Pre-processes uploaded files containing allowed extensions. This includes
    re-sizing, and (perhaps) converting to B&W. In cases where files cannot be
    re-sized/converted, the status code in file_dict associated with the file is
    changed to 'unable to process'.
    """

    # <tr> element in which to inject un-processed file names and status codes
    # for table :
    sad_str = "<tr><td>{0}</td><td>&nbsp;</td><td>{1}</td><td>&nbsp;</td><td>Not&nbsp;permitted</td></tr>\n"

    # Get list of files uploaded:
    uploaded_files = flask.request.files.getlist("file[]")

    # get status_dict indicating whether these files were permitted or could be
    # pre-processed:
    status_dict = test_process(uploaded_files)

    # Removing existing files from PROCESSED_FOLDER:
    os.system('rm -rf {1}/*.png'.format(PROCESSED_FOLDER))

    # Build the web page:
    retPage = '''
    <html>
    <body>
    <h2>Processing your images</h2>
    <table>
    '''

    tableStr = '''
    <caption>Ignored Files</caption>
    <tr align="left"><th>index</th><th>&nbsp;</th><th>name</th><th>&nbsp;</th><th>reason</th></tr>
    '''

    omitted_files = False
    i = 0
    for file in status_dict.iterkeys():
        print file.filename.encode('utf-8')	#, 'ignore')
        if status_dict[file] == 'OK' and  allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            omitted_files = True
            tableStr += sadStr.format(i + 1, file.filename.encode('utf-8', 'ignore'))


    # files in UPLOAD_FOLDER, and put resuting files into PROCESSED_FOLDER.
    myModel.process_files(UPLOAD_FOLDER)

    # Copy a blank image into PROCESSED_FOLDER in case needed to finish table
    # constructed within /show_images.
    os.system('scp {0} {1}/'.format(background_img, PROCESSED_FOLDER))

    # Test to see which files are not in myModel.proc_file_list, and for those
    # change status to 'unable to process'.
    for file in file_status.keys():
        if file not in myModel.proc_file_list:
            file_status[file] = 'unable to process'


        os.system('rm {0}/*.png'.format(PROCESSED_FOLDER))
        myModel.process_files(UPLOAD_FOLDER)
        os.system('scp {0} {1}/'.format(background_img, PROCESSED_FOLDER))
        i += 1

    if omitted_files:
        retPage += tableStr + "\n</table>"

    retPage += """
    <table>
    <tr><td>
            <form action="/do_it" method="POST">
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
    """

    return retPage

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
