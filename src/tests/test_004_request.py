import requests
import os
from pathlib import Path
import datetime
import time
from dotenv import load_dotenv
import pytest

from .context import code_references, check_validity, request_api
from request_api import (
    get_legifrance_auth,
    get_article_uid,
    get_article_content,
    get_article,
)
from check_validity import get_validity_status, time_delta


class TestOAuthLegiFranceAPI:
    def test_token_requests(self):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        json_response = get_legifrance_auth(client_id, client_secret)
        assert "Authorization" in json_response
        assert json_response["Authorization"].startswith("Bearer")

    def test_token_requests_wrong_credentials(self):
        load_dotenv()
        client_id = os.getenv("API_KEY2")
        client_secret = os.getenv("API_SECRET2")
        with pytest.raises(ValueError) as exc_info:
            get_legifrance_auth(client_id, client_secret)
            assert (
                str(exc_info.value)
                == "No credential: client_id or/and client_secret are not set. \nPlease register your API at https://developer.aife.economie.gouv.fr/"
            ), str(exc_info.value)


class TestLoadDotEnv:
    def test_dotenv_file(self):
        curr_dir = os.path.dirname(os.path.dirname(os.getcwd()))
        assert "src" not in curr_dir
        my_file = curr_dir + "/.env"
        # assert my_file == "", my_file
        assert Path(my_file).is_file() is True, "Error: no .env file"
        assert Path(my_file).exists() is True, "Error: no .env file"

    def test_dotenv_values(self):
        load_dotenv()
        assert os.getenv("API_KEY") is not None, "Error no API_KEY set in .env file"
        assert (
            os.getenv("API_SECRET") is not None
        ), "Error no API_SECRET set in .env file"


class TestGetArticleId:
    def test_get_article_uid(self):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        assert client_id is not None, "Error no API KEY"
        client_secret = os.getenv("API_SECRET")
        assert client_secret is not None, "Error no API_SECRET"
        headers = get_legifrance_auth(client_id, client_secret)
        assert headers is not None, "Errors no token"
        article = get_article_uid("CCIV", "1120", headers)
        assert article == "LEGIARTI000032040861", article

    @pytest.mark.parametrize(
        "input_expected",
        [
            ("CCONSO", "L121-14", "LEGIARTI000032227262"),
            ("CCONSO", "R742-52", "LEGIARTI000032808914"),
            ("CSI", "L622-7", "LEGIARTI000043540586"),
            ("CSI", "R314-7", "LEGIARTI000037144520"),
        ],
    )
    def test_article_uid(self, input_expected):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        code_name, art_num, expected = input_expected
        headers = get_legifrance_auth(client_id, client_secret)
        article_uid = get_article_uid(code_name, art_num, headers)
        assert expected == article_uid

    def test_get_article_uid_wrong_article_num(self):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        headers = get_legifrance_auth(client_id, client_secret)
        article_uid = get_article_uid("CCIV", "11-20", headers)
        assert article_uid is None, article_uid

    def test_get_article_uid_wrong_code_name(self):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        headers = get_legifrance_auth(client_id, client_secret)

        with pytest.raises(ValueError) as exc_info:
            # Note: Le code est sensible à la casse.
            # FEATURE: faire une base de référence insensible à la casse
            article_uid = get_article_uid("Code Civil", "1120", headers)
            assert str(exc_info.value) == "", str(exc_info.value)
            assert article_uid is None, article_uid


class TestGetArticleContent:
    def test_get_article_full_content(
        self, input_id=("CCONSO", "L121-14", "LEGIARTI000032227262")
    ):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        headers = get_legifrance_auth(client_id, client_secret)
        article_num, code, article_uid = input_id
        article_content = get_article_content(article_uid, headers)
        assert (
            article_content["url"]
            == "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032227262"
        ), article_content["url"]
        assert article_content["dateDebut"] == 1467331200000, article_content[
            "dateDebut"
        ]
        assert article_content["dateFin"] == 32472144000000, article_content["dateFin"]
        # assert article_content["nb_versions"] == 1, article_content["nb_versions"]
        assert article_content["articleVersions"][0] == {
            "dateDebut": 1467331200000,
            "dateFin": 32472144000000,
            "etat": "VIGUEUR",
            "id": "LEGIARTI000032227262",
            "numero": None,
            "ordre": None,
            "version": "1.0",
        }, article_content["articleVersions"][0]

    @pytest.mark.parametrize(
        "input_id",
        [
            ("CCONSO", "L121-14", "LEGIARTI000032227262"),
            ("CCONSO", "R742-52", "LEGIARTI000032808914"),
            ("CSI", "L622-7", "LEGIARTI000043540586"),
            ("CSI", "R314-7", "LEGIARTI000037144520"),
        ],
    )
    def test_get_article_content(self, input_id):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        headers = get_legifrance_auth(client_id, client_secret)
        article_num, code, article_uid = input_id
        article_content = get_article_content(article_uid, headers)
        assert (
            article_content["url"]
            == f"https://www.legifrance.gouv.fr/codes/article_lc/{article_uid}"
        ), article_content["url"]
        assert type(article_content["dateDebut"]) == int
        assert type(article_content["dateFin"]) == int
        assert article_content["nb_versions"] >= 1, article_content["nb_versions"]


class TestGetArticle:
    def test_get_single_article(self):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        article = get_article(
            "CCONSO",
            "L121-14",
            client_id,
            client_secret,
            past_year_nb=3,
            future_year_nb=3,
        )
        assert article["date_debut"] == "01/07/2016", article["date_debut"]
        assert article["date_fin"] == "01/01/2999", article["date_fin"]
        assert (
            article["url"]
            == "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032227262"
        ), article["url"]
        assert (
            article["texte"]
            == "Le paiement résultant d'une obligation législative ou réglementaire n'exige pas d'engagement exprès et préalable."
        )
        assert article["code"] == "CCONSO", article["code"]
        assert article["article"] == "L121-14"
        assert article["status"] == "Pas de modification"
        assert article["status_code"] == 204
        assert article["id"] == "LEGIARTI000032227262"
        assert article["color"] == "success"
        # assert article["nb_versions"] == 1, article["nb_versions"]

    @pytest.mark.parametrize(
        "input_expected",
        [
            ("CCONSO", "L121-14", "LEGIARTI000032227262", 204),
            ("CCONSO", "R742-52", "LEGIARTI000032808914", 204),
            ("CSI", "L622-7", "LEGIARTI000043540586", 301),
            ("CSI", "R314-7", "LEGIARTI000037144520", 204),
            ("CGCT", "L1424-71", "LEGIARTI000028529379", 204),
            ("CJA", "L121-2", "LEGIARTI000043632528", 301),
            ("CESEDA", "L753-1", "LEGIARTI000042774802", 301),
            ("CENV", "L124-1", "LEGIARTI000033140333", 204),
            ("CENV", "L122224-1", None, 404),
        ],
    )
    def test_get_multiple_articles(self, input_expected):
        load_dotenv()

        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        code_short_name, art_num, art_id, status_code = input_expected
        article = get_article(code_short_name, art_num, client_id, client_secret)
        assert article["id"] == art_id, (code_short_name, art_num, article["id"])
        if status_code == 204:
            status_color = "success"
        if status_code == 301:
            status_color = "warning"
        if status_code == 302:
            status_color = "danger"
        if status_code == 404:
            status_color = "dark"
        # assert article["short_code"] == code_short_name, article["code_short_name"]
        # assert article["long_code"] == CODE_REFERENCE[code_short_name], article[
        #     "long_code"
        # ]
        assert article["status_code"] == status_code, (
            status_code,
            code_short_name,
            art_num,
        )
        assert article["color"] == status_color, article["color"]

    @pytest.mark.parametrize(
        "input_expected",
        [
            ("CCONSO", "L121-14", "01/07/2016", "01/01/2999"),
            ("CCONSO", "R742-52", "01/07/2016", "01/01/2999"),
            ("CSI", "L622-7", "27/05/2021", "26/11/2022"),
            ("CSI", "R314-7", "01/08/2018", "01/01/2999"),
            ("CGCT", "L1424-71", "01/01/2015", "01/01/2999"),
            ("CJA", "L121-2", "01/01/2022", "01/01/2999"),
            ("CESEDA", "L753-1", "01/05/2021", "01/01/2999"),
            ("CENV", "L124-1", "01/01/2016", "01/01/2999"),
        ],
    )
    def test_get_multiple_articles_validity(self, input_expected):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        code_short_name, art_num, start_date, end_date = input_expected
        article = get_article(code_short_name, art_num, client_id, client_secret)
        assert article["date_debut"] == start_date, (
            article["date_debut"],
            code_short_name,
            art_num,
        )
        assert article["date_fin"] == end_date, (
            article["date_fin"],
            code_short_name,
            art_num,
        )

    @pytest.mark.parametrize(
        "input_expected",
        [
            ("CCONSO", "R11-14", None),
            ("CCONSO", "742-52", None),
            ("CSI", "622-7", None),
            ("CSI", "314-7", None),
            ("CGCT", "1424-71", None),
            ("CJA", "121-2", None),
            ("CESEDA", "753-1", None),
            ("CENV", "124-1", None),
        ],
    )
    def test_get_not_found_articles(self, input_expected):
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        code_short_name, art_num, art_id = input_expected
        article = get_article(code_short_name, art_num, client_id, client_secret)
        assert article["id"] == art_id, (code_short_name, art_num, article["id"])
        # assert article["code_short_name"] == code_short_name, article["code_short_name"]
        # assert article["code_full_name"] == CODE_REFERENCE[code_short_name], article[
        #     "code_full_name"
        # ]
        assert article["status_code"] == 404
        assert article["color"] == "dark"


class TestTimeDelta:
    def test_time_delta_3(self):
        past_3, future_3 = time_delta("-", 3), time_delta("+", 3)
        today = datetime.date.today()
        assert past_3.year == today.year - 3, (past_3.year, past_3.month, past_3.day)
        assert future_3.year == today.year + 3, (
            future_3.year,
            future_3.month,
            future_3.day,
        )

    def test_time_delta_2(self):
        today = datetime.date.today()
        past_2, future_2 = time_delta("-", 2), time_delta("+", 2)
        assert past_2.year == (today.year) - 2, (past_2.year, past_2.month, past_2.day)
        assert future_2.year == (today.year) + 2, (
            future_2.year,
            future_2.month,
            future_2.day,
        )

    def test_time_delta_wrong_op(self):

        with pytest.raises(ValueError) as e:
            time_delta("*", 3)
            assert e == "ValueError: Wrong operator", e

    def test_time_delta_wrong_nb(self):
        with pytest.raises(TypeError) as e:
            time_delta("+", "9")
            assert e == "TypeError: Year must be an integer", e


class TestValidityArticle:
    def test_validity_soon_deprecated(self):
        year_nb = 2
        start = datetime.datetime(2018, 1, 1, 0, 0, 0)
        # past_boundary = time_delta("-", year_nb)
        end = datetime.datetime(2023, 1, 1, 0, 0, 0)
        future_boundary = time_delta("+", year_nb)
        # QUESTION: avons nous besoin de différencier avant et après?
        status_code, status_msg, color = get_validity_status(
            start, end, year_nb, year_nb
        )
        assert end < future_boundary, (
            bool(end < future_boundary),
            end,
            future_boundary,
        )
        assert status_code == 302, status_code
        assert status_msg == "Valable jusqu'au 01/01/2023", status_msg
        assert color == "danger", color

    def test_validity_recently_modified(self):
        year_nb = 2
        start = datetime.datetime(2022, 8, 4, 0, 0, 0)
        past_boundary = time_delta("-", year_nb)
        end = datetime.datetime(2025, 1, 1, 0, 0, 0)
        # future_boundary = time_delta("+", year_nb)
        # QUESTION: avons nous besoin de différencier avant et après?
        assert start > past_boundary, (start > past_boundary, start, past_boundary)
        status_code, status_msg, color = get_validity_status(
            start, end, year_nb, year_nb
        )
        assert status_code == 301, status_code
        assert status_msg == "Modifié le 04/08/2022", status_msg
        assert color == "warning", color

    def test_validity_ras(self):
        year_nb = 2
        start = datetime.datetime(1801, 8, 4, 0, 0, 0)
        past_boundary = time_delta("-", year_nb)
        end = datetime.datetime(2040, 1, 1, 0, 0, 0)
        future_boundary = time_delta("+", year_nb)
        # QUESTION: avons nous besoin de différencier avant et après?
        assert start < past_boundary, (start < past_boundary, start, past_boundary)
        assert end > future_boundary, (end > future_boundary, end, future_boundary)
        status_code, status_msg, color = get_validity_status(
            start, end, year_nb, year_nb
        )
        assert status_code == 204, status_code
        assert status_msg == "Pas de modification", status_msg
        assert color == "success", color
