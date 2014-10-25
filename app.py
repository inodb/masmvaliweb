import os
import time
import errno
import subprocess

import flask
from flask import Flask, request, redirect, url_for
from werkzeug import secure_filename

from runipy.notebook_runner import NotebookRunner
from IPython.nbformat.current import read
from IPython.nbformat.current import writes
from IPython.nbconvert import HTMLExporter
from IPython.config import Config

UPLOAD_FOLDER = '/tmp/masmvali/'
ALLOWED_EXTENSIONS = set(['fa', 'fasta'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def make_dir(directory):
    """Make directory unless existing. Ignore error in the latter case."""
    try:
        os.makedirs(directory)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route("/asmstats", methods=['GET', 'POST'])
def asm_stats():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            make_dir(app.config["UPLOAD_FOLDER"])
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            os.environ["FASTA_FILE"] = save_path
            notebook = read(open("masmvaliweb/notebooks/assembly-stats.ipynb"), 'json')
            r = NotebookRunner(notebook)
            r.run_notebook()
            os.remove(save_path)
            exportHTML = HTMLExporter(config=Config({'HTMLExporter': {'default_template': 'basic'}}))
            #return writes(r.nb, 'json')
            return exportHTML.from_notebook_node(r.nb)[0]
    return "Post assembly file"


@app.route("/mummer", methods=['GET', 'POST'])
def run_mummer():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            make_dir(app.config["UPLOAD_FOLDER"])
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            def inner():
                # run MUMmer
                #mummer_cmd = "echo RUNNING NUCMER && bash -x ~/github/metassemble/scripts/validate/nucmer/run-nucmer.sh test/references/Mircea_07102013_selected_refs.fasta {0} /tmp/nucmer && echo SUCCESS!".format(save_path)
                mummer_cmd = "echo fakka"
                proc = subprocess.Popen(mummer_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

                while True:
                    char = proc.stdout.read(1)
                    if char:
                        if str(char) != '\n':
                            yield str(char)
                        else:
                            yield '<br />\n'
                    else:
                        break

                #TODO: not working, points to relative dir
                yield '<a href="/tmp/nucmer/nucmer.coords">nucmer.coords</a>\n'

                notebook = read(open("masmvaliweb/notebooks/mgcov-comparison-mpld3.ipynb"), 'json')
                r = NotebookRunner(notebook)
                r.run_notebook()
                exportHTML = HTMLExporter(config=Config({'HTMLExporter': {'default_template': 'basic'}}))
                #yield exportHTML.from_notebook_node(r.nb)[0]
                yield open("masmvaliweb/notebooks/mgcov-comp.html").read()

            #return open("/tmp/nucmer.coords").read()
            return flask.Response(inner(), mimetype='text/html')
    return "Post assembly file"


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('index'))
    return """
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="/mummer" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    <p>%s</p>
    """ % "<br>".join(os.listdir(app.config['UPLOAD_FOLDER'],))


if __name__ == "__main__":
    make_dir(app.config["UPLOAD_FOLDER"])
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
