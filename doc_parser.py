# coding: utf-8

import os
from pathlib import Path
import re
import time
import datetime
from dateutil.relativedelta import relativedelta

import requests
import docx
from PyPDF2 import PdfReader
from odf import text, teletype
from odf.opendocument import load

from bottle import Bottle
from bottle import request, static_file, template, HTTPError, run
from bottle_sslify import SSLify

from dotenv import load_dotenv, find_dotenv

from wsgiref import headers
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

API_ROOT_URL = "https://sandbox-api.piste.gouv.fr/dila/legifrance-beta/lf-engine-app/"
# API_ROOT_URL =  "https://api.piste.gouv.fr/dila/legifrance-beta/lf-engine-app/",
MAIN_CODELIST = {
    "CCIV": "Code civil",
    "CPRCIV": "Code de procédure civile",
    "CCOM": "Code de commerce",
    "CTRAV": "Code du travail",
    "CPI": "Code de la propriété intellectuelle",
    "CPEN": "Code pénal",
    "CPP": "Code de procédure pénale",
    "CASSUR": "Code des assurances",
    "CCONSO": "Code de la consommation",
    "CSI": "Code de la sécurité intérieure",
    "CSP": "Code de la santé publique",
    "CSS": "Code de la sécurité sociale",
    "CESEDA": "Code de l'entrée et du séjour des étrangers et du droit d'asile",
    "CGCT": "Code général des collectivités territoriales",
    "CPCE": "Code des postes et des communications électroniques",
    "CENV": "Code de l'environnement",
    "CJA": "Code de justice administrative",
}
CODE_DICT = {
    "CCIV": "(?P<CCIV>du Code civil|C\. civ\.|civ\.)",
    "CPRCIV": "(?P<CPRCIV>du Code de procédure civile|C\. pr\. civ\.|CPC|du CPC)",
    "CCOM": "(?P<CCOM>du Code de commerce|C\. com\.)",
    "CTRAV": "(?P<CTRAV>du Code du travail|C\. trav\.)",
    "CPI": "(?P<CPI>du Code de la propriété intellectuelle|CPI|C\. pr\. int\.|du CPI)",
    "CPEN": "(?P<CPEN>du Code pénal|C\. pén\.)",
    "CPP": "(?P<CPP>du Code de procédure pénale|du CPP|CPP)",
    "CASSU": "(?P<CASSUR>du Code des assurances|C\. assur\.)",
    "CCONSO": "(?P<CCONSO>du Code de la consommation|C\. conso\.)",
    "CSI": "(?P<CSI>du Code de la sécurité intérieure|CSI|du CSI)",
    "CSP": "(?P<CSP>du Code de la santé publique|C\. sant\. pub\.|CSP|du CSP)",
    "CSS": "(?P<CSS>du Code de la sécurité sociale|C\. sec\. soc\.|CSS|du CSS)",
    "CESEDA": "(?P<CESEDA>du Code de l'entrée et du séjour des étrangers et du droit d'asile|CESEDA|du CESEDA)",
    "CGCT": "(?P<CGCT>du Code général des collectivités territoriales|CGCT|du CGCT)",
    "CPCE": "(?P<CPCE>du Code des postes et des communications électroniques|CPCE|du CPCE)",
    # Trop large CE
    "CENV": "(?P<CENV>du Code de l'environnement|C. envir.|\sCE(\s|\.)|\sdu CE)",
    "CJA": "(?P<CJA>du Code de justice administrative|CJA|du CJA)",
}

CODE_REGEX = "|".join(CODE_DICT.values())
ARTICLE_REGEX = "(?P<art>((A|a)rticles?|(A|a)rt\.))"
ARTICLE_P = f"{ARTICLE_REGEX}\s(?P<ref>.*?)\s({CODE_REGEX}$)"
REF_PATTERN = re.compile("^(?:L\.?|R\.?|A\.?|D\.?)?(?:\s*)(?:\d+)$")

JURI_PATTERN = re.compile(ARTICLE_P, flags=re.I)
ACCEPTED_EXTENSIONS = ("odt", "pdf", "docx", "doc")
SUPPORTED_CODES = list(CODE_DICT.keys())

def convert_epoch_to_date_str(epoch):
    '''convert epoch (seconds till 01/01/1970) to date '''
    # return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch / 1000))
    return datetime.datetime.utcfromtimestamp(epoch/1000).strftime('%d-%m-%Y')

def convert_date_str_to_epoch(date_str):
    '''convert date to epoch'''
    date_time = date_str.strptime("%d-%m-%Y")
    return datetime.datetime(date_time.tuple[:4]).timestamp()  

def validity_period(user_past=3, user_future=3):
    """Définition des bornes de la période déclenchant une alerte
    si l'article a été modifié / va être modifié
    """
    past_reference = (
        datetime.datetime.now() - relativedelta(years=int(user_past))
    ).timestamp()*1000
    future_reference = (
        datetime.datetime.now() + relativedelta(years=int(user_future))
    ).timestamp()*1000
    return (past_reference, future_reference)


def check_upload(upload):
    '''Téléverser le document et le valider'''
    if upload is None:
        raise Exception("Erreur: Aucun fichier proposé")
    # print(upload.filename)
    if "filename" in upload:
        doc_name, doc_ext = upload.filename.split("/")[-1].split(".")
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        file_path = f"{save_path}/{filename}"
        upload.save(file_path, overwrite="true")
        file_size = os.stat(file_path).st_size
        if file_size > 2000000:
            raise Exception(
                "Erreur: Fichier trop lourd: la taille du fichier doit être < à 2Mo"
            )
        save_path = Path.cwd() / Path("tmp")
    else:
        file_path = upload
        doc_name, doc_ext = upload.split("/")[-1].split(".")
    
    filename = ".".join([doc_name, doc_ext])
    if doc_ext not in ACCEPTED_EXTENSIONS:
        raise Exception(
            "Erreur: Extension incorrecte: les fichiers acceptés terminent par *.odt, *docx, *.pdf"
        )
    
    return file_path


def parse_doc(file_path):
    """
    parse document from absolute file_path
    return full_text
    """
    doc_name, doc_ext = file_path.split("/")[-1].split(".")
    if doc_ext not in ACCEPTED_EXTENSIONS:
        raise Exception(
            "Extension incorrecte: les fichiers acceptés terminent par *.odt, *docx, *.pdf"
        )

    full_text = []
    if doc_ext == "docx":

        with open(file_path, "rb") as f:
            document = docx.Document(f)
            paragraphs = document.paragraphs
            paragraph_nb = len(paragraphs)
            for i in range(paragraph_nb):
                print(f"Extracting and parsing document {i}/{paragraph_nb} ...")
                full_text.append((paragraphs[i].text))

    elif doc_ext == "pdf":
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            paragraphs = reader.pages
            paragraph_nb = len(paragraphs)
            for i in range(paragraph_nb):
                print(f"Extracting and parsing document {i}/{paragraph_nb} ...")
                page = reader.pages[i]
                full_text.append((page.extract_text()))

    elif doc_ext == "odt":
        with open(file_path, "rb") as f:
            document = load(f)
            paragraphs = document.getElementsByType(text.P)
            paragraph_nb = len(paragraphs)
            for i in range(paragraph_nb):
                print(f"Extracting and parsing document {i}/{paragraph_nb} ...")
                full_text.append((teletype.extractText(paragraphs[i])))

    print("Parsing completed")
    # print("Deleting file")
    # os.remove(file_path)
    return re.sub("\r|\n|\t", " ", "".join(full_text))


def match_code_and_article(full_text, past_reference, future_reference):
    """Match and extract code and article"""
    code_list = "".join([f"<li>{code_name}</li>" for code_name in SUPPORTED_CODES])
    info_msg = f"<ul>Les différents codes du droit Français supportés:{code_list}</ul>"
    # print(info_msg)
    code_found = {}
    for i, match in enumerate(re.finditer(JURI_PATTERN, full_text)):
        needle = match.groupdict()
        qualified_needle = {
            key: value for key, value in needle.items() if value is not None
        }
        # print(i+1, qualified_needle)
        ref = match.group("ref").strip()
        article_ids = [re.sub("(\s|\.\s|\.)", "", n) for n in re.split("(\set\s|,\s)", ref) if n not in [" et ", ", ", "alinea", "al", "C"]]
        code = [k for k in qualified_needle.keys() if k not in ["ref", "art"]][0]
        if code not in code_found:
            code_found[code] = [get_article(code, a, past_reference, future_reference) for a in article_ids]
        else:
            code_found[code].extend([get_article(code, a, past_reference, future_reference) for a in article_ids])
    for code, articles in code_found.items():
        print(code, MAIN_CODELIST[code])
        for article in articles:
            print(article["number"], article["message"])

    # articles_by_code = 
    # for code_name, articles in articles_by_code.items():
        # code_full_name = MAIN_CODELIST[code_name]
        # list_articles = "".join(
        #     [f"<li>Article: <code>{a}</code></li>" for a in articles]
        # )
        # print(f"<ul> Articles du {code_full_name}:{list_articles}</ul>")
    return code_found


def get_legifrance_auth():
    """Get auth token from SECRETS into dotenv"""
    # TOKEN_URL = "https://sandbox-oauth.aife.economie.gouv.fr/api/oauth/token"
    TOKEN_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
    # 1. connect using the "client credentials" grant type
    # the regular authentication methods don't work, we are passing
    # the client id and secret as form data, as suggested by the PISTE team
    load_dotenv()
    client_id = os.getenv("OAUTH_KEY_2")
    client_secret = os.getenv("OAUTH_SECRET_2")
    if client_id is None or client_secret is None:
        # return HTTPError(401, "No credential have been set")
        raise Exception("No credential have been set")

    res = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "openid",
        },
    )
    
    if res.status_code in [400, 401]:
        # return HTTPError(res.status_code, "Unauthorized: invalid credentials")
        raise Exception(f"HTTP Error code: {res.status_code}: Invalid credentials")
    token = res.json()
    access_token = token["access_token"]
    # token["expires_in"] = str(token["expires_in"])
    return {"Authorization": f"Bearer {access_token}"}
    

def get_article_uid(code_name, article_number, headers=headers):
    """
    GET article_id from LEGIFRANCE API using POST /search
    return article_id
    see documentation at https://developer.aife.economie.gouv.fr/index.php?option=com_apiportal&view=apitester&usage=api&apitab=tests&apiName=L%C3%A9gifrance+Beta&apiId=426cf3c0-1c6d-46ba-a8b0-f79289086ed5&managerId=2&type=rest&apiVersion=1.6.2.5&Itemid=402&swaggerVersion=2.0&lang=fr
    """
    code_fullname = MAIN_CODELIST[code_name]
    session = requests.Session()
    
    today_epoch = int(time.time())* 1000
    data = {
        "recherche": {
            "champs": [
                {
                    "typeChamp": "NUM_ARTICLE",
                    "criteres": [
                        {
                            "typeRecherche": "EXACTE",
                            "valeur": article_number,
                            "operateur": "ET"
                        }
                    ],
                    "operateur": "ET"
                }
            ],
            "filtres": [
                {"facette": "NOM_CODE", "valeurs": [code_fullname]},
                {"facette": "DATE_VERSION", "singleDate": today_epoch}
            ],
            "pageNumber": 1,
            "pageSize": 10,
            "operateur": "ET",
            "sort": "PERTINENCE",
            "typePagination": "ARTICLE"
        },
        "fond": "CODE_DATE"
    }
    response = session.post("/".join([API_ROOT_URL, "search"]),
        headers=headers,
        json=data,
    )
    if response.status_code > 399:
        print(response)
        return None
    
    article_informations = response.json()
    if not article_informations["results"]:
        return None
    
    results = article_informations["results"]
    if len(results) == 0:
        return None
    else:
        #get the first results
        try:
            article_uid = results[0]["sections"][0]["extracts"][0]["id"]
        except IndexError:
            return None
    return article_uid


def get_article_content(article):
    """
    GET article_content from LEGIFRANCE API using POST /consult/getArticle
    return article_content
    see documentation at https://developer.aife.economie.gouv.fr/index.php?option=com_apiportal&view=apitester&usage=api&apitab=tests&apiName=L%C3%A9gifrance+Beta&apiId=426cf3c0-1c6d-46ba-a8b0-f79289086ed5&managerId=2&type=rest&apiVersion=1.6.2.5&Itemid=402&swaggerVersion=2.0&lang=fr
    """
    session = requests.Session()
    response = session.post("/".join([API_ROOT_URL, "consult", "getArticle"]),
        headers = get_legifrance_auth(),
        json = article
    )
    if response.status_code > 399:
        return None
    article_content = response.json()
    return article_content["article"]
    

def get_article(
    code_name, article_number, past_reference, future_reference
):
    """
    store article info
    1. Get article ID
    2. Get article content
    3. Check validity
    """
    article = {
        "code_name": MAIN_CODELIST[code_name],
        "number": article_number,
        "id": get_article_uid(code_name, article_number, headers=get_legifrance_auth()),
    }
    
    
    if article["id"] is None:
        article["status"] = 404
        article["message"] =  "Not found"
        article["url"] = None
        return article
    else:
        article["url"] = f"https://www.legifrance.gouv.fr/codes/article_lc/{article['id']}"
        article_content = get_article_content(article)
        if article_content is None:
            article["status"] = 404
            article["message"] =  "Not found"
            return article
        
        article["start"] = article_content["dateDebut"]
        article["end"] = article_content["dateFin"]
        if article["start"] < past_reference and article["end"] > future_reference:
            article["status"] = 204
            article["message"] = "Pas de modification"
        elif article["start"] > past_reference:
            article["status"] = 301
            article["message"] = "Modifié le {}".format(convert_epoch_to_date_str(article["start"]))
            
        elif article["end"] < future_reference:
            article["status"] = 302
            article["message"] = "Valable jusqu'au {}".format(convert_epoch_to_date_str(article["end"]))
            
    article["start"] = convert_epoch_to_date_str(article["start"])
    article["end"] = convert_epoch_to_date_str(article["end"])
    return article

def get_articles(articles_by_code, user_past, user_future):
    '''Récupérer tous les articles sur légifrance triés par code puis par status'''
    final_articles_by_code = {code: [] for code in articles_by_code.keys()} 
    for code, articles in articles_by_code.items():
        articles = [get_article(code, a, user_past, user_future) for a in articles ]
        sorted_articles = sorted(articles, key= lambda x:x["status"])
        final_articles_by_code[code] = sorted_articles
    return final_articles_by_code


def main(upload_doc, user_past=3, user_future=3):
    document = check_upload(upload_doc)
    full_text = parse_doc(document)
    articles_by_codes = match_code_and_article(full_text,user_past, user_future)
    for code, articles in articles_by_codes.items():
        print("#", code, MAIN_CODELIST[code])
        for article in articles:
            print("\t", article["number"], article["url"],  article["message"], article["status"])
    # results = get_articles(articles_by_codes, user_past, user_future)
    # print(results)
    # return results
app = Bottle()


@app.route("/")
def root():
    return static_file("index.html", root=".")


@app.route("/upload", method="POST")
def upload():
    """Quand l'utilisateur"""
    user_past, user_future = validity_period(
        request.forms.get("user_past"), request.forms.get("user_future")
    )
    upload_doc = request.files.get("upload")
    if upload_doc is None:
        raise Exception("Aucun fichier selectionné")
    return """<html><code></code></html>""".format(main(upload_doc, user_past, user_future))

if __name__ == "__main__":
    # test_path = "./tests/docs/"
    f = "newtest.pdf"
    # file_abspath = os.path.join(test_path, f)
    main(f)
    # for f in os.listdir(test_path):
    #     file_abspath = os.path.join(test_path, f)
    #     if os.path.isfile(file_abspath):
    #         print(file_abspath)
    #         # full_text = parse_doc(file_abspath)
    #         # code_by_articles = match_code_and_article(full_text)
    #         main(file_abspath)
    #         break
    # except FileNotFoundError:
    #     print(f"{file_abspath} not found")
    #     pass
    # except Exception as e:
    #     print(e)
    #     pass
    # retry_strategy = Retry(
    #     total=3,
    #     status_forcelist=[429, 500, 502, 503, 504],
    #     allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],
    # )
    # adapter = HTTPAdapter(max_retries=retry_strategy)
    # session = requests.Session()
    # session.mount("https://", adapter)
    # session.mount("http://", adapter)

    # if os.environ.get("APP_LOCATION") == "heroku":
    #     SSLify(app)
    #     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    # else:
    # app.run(host="localhost", port=8080, debug=True, reloader=True)