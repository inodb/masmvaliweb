import os
import errno
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
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            os.environ["FASTA_FILE"] = save_path
            notebook = read(open("masmvaliweb/notebooks/assembly_stats.ipynb"), 'json')
            r = NotebookRunner(notebook)
            r.run_notebook()
            os.remove(save_path)
            exportHTML = HTMLExporter(config=Config({'HTMLExporter':{'default_template':'basic'}}))
            #return writes(r.nb, 'json')
            return exportHTML.from_notebook_node(r.nb)[0]
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
    <form action="/asmstats" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    <p>%s</p>
    """ % "<br>".join(os.listdir(app.config['UPLOAD_FOLDER'],))


if __name__ == "__main__":
    make_dir(app.config["UPLOAD_FOLDER"])
    app.run(host='0.0.0.0', port=5000, debug=True)
