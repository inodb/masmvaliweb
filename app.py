import os
import time
import errno
import subprocess
import settings
import glob

import flask
from flask import Flask, request, redirect, url_for
from werkzeug import secure_filename

from runipy.notebook_runner import NotebookRunner
from IPython.nbformat.current import read
from IPython.nbformat.current import writes
from IPython.nbconvert import HTMLExporter
from IPython.config import Config


app = Flask(__name__)
app.config.from_object(settings)
ALLOWED_EXTENSIONS = set(['fa', 'fasta'])


from celery import Celery


def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery
celery = make_celery(app)


@celery.task(name="tasks.add")
def add_together(a, b):
    return a + b


@celery.task(name="tasks.add_save")
def add_together_save(a, b, out_file):
    with open(out_file, 'w') as of:
        of.write(a + b)


@celery.task(name="tasks.run_asm_stats")
def run_asm_stats(assembly, out_file):
    os.environ["FASTA_FILE"] = assembly
    notebook = read(open("masmvaliweb/notebooks/assembly-stats.ipynb"), 'json')
    r = NotebookRunner(notebook)
    r.run_notebook()
    os.remove(assembly)
    exportHTML = HTMLExporter(config=Config({'HTMLExporter': {'default_template': 'basic'}}))
    with open(out_file, 'w') as of:
        of.write(exportHTML.from_notebook_node(r.nb)[0])


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


@app.route("/add", methods=['GET'])
def add_numbers():
    add_together_save.delay(request.args.get('a'), request.args.get('b'), os.path.join(app.config['UPLOAD_FOLDER'], "test_add.txt"))
    return "Request sent, result on <a href='/viewadd'>here</a>"


@app.route("/viewadd")
def view_add_numbers():
    if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], "test_add.txt")):
        return flask.Response(open(os.path.join(app.config['UPLOAD_FOLDER'], "test_add.txt")).read(), mimetype='text/html')
    else:
        return "No result"


@app.route("assembly/<asm_name>/notebooks/view/asmstats/")
def show_notebook(asm_name):
    fn = os.path.join(app.config["UPLOAD_FOLDER"], asm_name, "asmstats.html")
    if os.path.isfile(fn):
        return open(fn).read()
    else:
        return "{asm_name} does not have a asm_stats notebook".format(asm_name=asm_name)


@app.route("/notebooks/run/asmstats", methods=['GET', 'POST'])
def asm_stats():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename) and len(request.form['asm_name']) > 0:
            asm_name = secure_filename(request.form['asm_name'])
            make_dir(os.path.join(app.config["UPLOAD_FOLDER"], asm_name))
            save_asm = os.path.join(app.config['UPLOAD_FOLDER'], asm_name, "contigs.fa")
            file.save(save_asm)
            out_file = os.path.join(app.config["UPLOAD_FOLDER"], asm_name, "asmstats.html")
            run_asm_stats(save_asm, out_file)
            return "Result at <a href='{url}'>{asm_name}</a>".format(asm_name=asm_name, url=url_for('show_notebook', asm_name=asm_name))
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
                mummer_cmd = "echo RUNNING NUCMER && bash -x ~/github/metassemble/scripts/validate/nucmer/run-nucmer.sh test/references/Mircea_07102013_selected_refs.fasta {0} /tmp/nucmer && echo SUCCESS!".format(save_path)
                #mummer_cmd = "echo fakka"
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
                yield exportHTML.from_notebook_node(r.nb)[0]
                #yield open("masmvaliweb/notebooks/mgcov-comp.html").read()

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
    <form action="notebooks/run/asmstats" method=post enctype=multipart/form-data>
      <input type=file name=file><br />
      Name assembly recipe: <input type="text" name=asm_name><br />
      <input type=submit value=Upload><br />
    </form>
    <p>%s</p>
    """ % "<br>".join(os.listdir(app.config['UPLOAD_FOLDER'],))


if __name__ == "__main__":
    make_dir(app.config["UPLOAD_FOLDER"])
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
