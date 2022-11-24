#!/usr/bin/env python3
# coding: utf-8
# filename: app.py
"""
Main Bottle app

"""
import os

from bottle_sslify import SSLify
import bottle
from bottle import Bottle, request
from jinja2 import Environment, FileSystemLoader
from result_templates import start_results, end_results
from code_references import CODE_REFERENCE, CODE_REGEX
from codeislow import load_result
from dotenv import load_dotenv

app = Bottle()
curr_dir = os.path.dirname(os.path.realpath(__file__))
environment = Environment(loader=FileSystemLoader(os.path.join(curr_dir, "templates/")))


@app.route("/")
def home():
    template = environment.get_template("home.html")
    return template.render(code_names=list(CODE_REFERENCE.items()))


@app.route("/cgu/")
def cgu():
    template = environment.get_template("cgu.html")
    return template.render()


@app.route("/about/")
def about():
    template = environment.get_template("about.html")
    return template.render()


@app.route("/codes/")
def codes():
    code_full_list = []
    for short_code, long_code in CODE_REFERENCE.items():
        regex_c = CODE_REGEX[short_code]
        regex = f"<code>{regex_c}</code>"
        comment = """<a href="https://github.com/c24b/codeislow/issues/new?assignees=c24b&labels=enhancement&template=-feature--am%C3%A9lioration-de-la-regex.md&title=%5BREGEX%5D" class="badge badge-pill badge-primary">?</a>"""
        code_full_list.append((long_code, short_code, regex, comment))
    template = environment.get_template("codes.html")
    return template.render(codes_full_list=code_full_list)


@app.route("/upload/", method="POST")
def upload():
    if not os.path.exists("tmp"):
        os.makedirs("tmp")
    upload = request.files.get("upload")
    name, ext = os.path.splitext(upload.filename)

    if ext not in (".docx", ".odt", ".pdf", ".doc"):
        return "Le format du fichier est incorrect"
    file_path = os.path.join("tmp", upload.filename)
    try:
        upload.save(file_path)
    except OSError:
        pass
    yield """<div id="processing" class="alert alert-info" role="alert">
    <button type="button" class="close" onclick="style.display = 'none'" data-dismiss="alert" aria-label="Close">
  <span aria-hidden="true">&times;</span>
</button>Traitement et détection des articles en cours...<br>Veuillez patientez...</div>
"""
    past = int(request.forms.get("user_past"))
    future = int(request.forms.get("user_future"))
    selected_codes = [
        short_name
        for short_name in CODE_REFERENCE.keys()
        if request.forms.get(short_name) is not None
    ]
    if len(selected_codes) == 0:
        selected_codes = None
    
    yield start_results

    try:
        for row in load_result(file_path, None, "article_code", past, future):
            yield row
    except Exception as e:
        row = f"""
        <div class="alert alert-warning" role="alert">
        <h2> Erreur</h2>
        <p>Quelque chose s'est mal passé: <code>{e}</code>
        <p> Contactez
        <a href="#" class="alert-link">l'administrateur</a></p>
        </div>
        """
        yield row

    yield end_results

# app = SSLify(app)

if __name__ == "__main__":
    load_dotenv()
    if os.environ.get("APP_LOCATION") == "heroku":
        SSLify(app)
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    elif os.environ.get("APP_LOCATION") == "gunicorn":
        SSLify(app)
        # n'est pas pris en compte par gunicorn
        app.run(host=os.environ.get("APP_HOST", "0.0.0.0"), port=os.environ.get("APP_PORT", 5000), server=os.environ.get("APP_LOCATION"), debug=os.environ.get("DEBUG", False), reloader=os.environ.get("RELOAD", False), workers=4)

    else:
        app.run(host="localhost", port=8080, debug=os.environ.get("DEBUG", True), reloader=os.environ.get("RELOAD", True))
        

