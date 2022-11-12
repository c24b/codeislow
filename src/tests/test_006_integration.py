#!/usr/bin/env python

import os
from dotenv import load_dotenv
from .context import parsing, matching, request_api, codeislow, code_references
from parsing import parse_doc
from matching import get_matching_result_item
from request_api import get_article
from codeislow import main
from code_references import CODE_REFERENCE
from .test_001_parsing import restore_test_file, archive_test_file


class TestMainProcess:
    def test_main_process_step_by_step_default(self):
        # usert input set to defaults
        past = 3
        future = 3
        selected_codes = None
        pattern_format = "article_code"
        file_paths = ["newtest.odt", "newtest.docx", "newtest.pdf"]
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        for file_path in file_paths:

            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )

            archive_test_file(file_path)
            full_text = parse_doc(abspath)
            restore_test_file(file_path)
            for item in get_matching_result_item(
                full_text, selected_codes, pattern_format
            ):
                assert len(item) == 3, item
                short_code, code, article_nb = item
                assert code in list(
                    CODE_REFERENCE.values()
                ), f"{code} is in a wrong format"
                assert isinstance(article_nb, str), f"{article_nb} is not a string"
                assert any(
                    [c.isdigit() for c in article_nb]
                ), f"{article_nb} has no number"
                article = get_article(
                    code,
                    article_nb,
                    client_id,
                    client_secret,
                    past_year_nb=past,
                    future_year_nb=future,
                )
                assert isinstance(article, dict), article
                assert "date_debut" in article, article
                assert "date_fin" in article, article
                assert "status" in article, article
                assert article["color"] in [
                    "danger",
                    "warning",
                    "success",
                    "primary",
                    "dark",
                ], article
                assert "url" in article, article
                assert "texte" in article, article
            # for result in main(abspath, selected_codes, pattern_format, past, future):
            #     assert isinstance(result, dict), result

    def test_main_process_step_by_step_reversed(self):
        # usert input set to defaults
        past = 3
        future = 3
        selected_codes = None
        pattern_format = "code_article"
        file_paths = ["testnew.odt", "testnew.docx", "testnew.pdf"]
        load_dotenv()
        client_id = os.getenv("API_KEY")
        client_secret = os.getenv("API_SECRET")
        for file_path in file_paths:

            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )

            archive_test_file(file_path)
            full_text = parse_doc(abspath)
            restore_test_file(file_path)
            for item in get_matching_result_item(
                full_text, selected_codes, pattern_format
            ):
                assert len(item) == 3, item
                short_code, code, article_nb = item
                assert code in list(
                    CODE_REFERENCE.values()
                ), f"{code} is in a wrong format"
                assert isinstance(article_nb, str), f"{article_nb} is not a string"
                assert any(
                    [c.isdigit() for c in article_nb]
                ), f"{article_nb} has no number"
                article = get_article(
                    code,
                    article_nb,
                    client_id,
                    client_secret,
                    past_year_nb=past,
                    future_year_nb=future,
                )
                assert isinstance(article, dict), article
                assert "date_debut" in article, article
                assert "date_fin" in article, article
                assert "status" in article, article
                assert article["color"] in [
                    "danger",
                    "warning",
                    "success",
                    "primary",
                    "dark",
                ], article
                assert "url" in article, article
                assert "texte" in article, article
