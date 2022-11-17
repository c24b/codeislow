import os
import pytest
import re
from .context import matching, parsing, code_references
from parsing import parse_doc
from code_references import build_code_regex, filter_code_regex
from matching import (
    switch_pattern,
    get_code_refs,
    detect_pattern,
    normalize_references,
    get_matching_results_dict,
    get_matching_result_item,
)
from .test_001_parsing import restore_test_file, archive_test_file


class TestPattern:
    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "Comme il est mentionné dans l'article 238-4 alinéa 2 du code de la consommation .",
                "article_code",
            ),
            (
                "Comme il est mentionné dans l'art.238-4 alinéa 2 du C.conso.",
                "article_code",
            ),
            (
                "Comme il est mentionné dans le code de la consommation article 238-4 alinéa 2.",
                "code_article",
            ),
            (
                "Comme il est mentionné dans  le C.conso. art.238-4 alinéa 2  qui blablabla",
                "code_article",
            ),
            ("Art. L. 385-2, R. 343-4 et A421-13 du C. assur. ", "article_code"),
            (
                "Art. 2-3-4 du Code de l'Environnement",
                "article_code",
            ),
            ("Art. R2-3-4 du CE.", "article_code"),
            (
                "\n-\n article L.278 du cjaaa",
                "article_code",
            ),
            ("C. assur. Art. L. 385-2, R. 343-4 et A421-13", "code_article"),
            ("CE. Article L. 189-2, 343-4 et L-421-13", "code_article"),
            ("Dans les articles suivants: CSP Art. L214", "code_article"),
            ("CSP Art. L214", "code_article")
        ],
    )
    def test_detect_pattern_txt(self, input_expected):
        input, expected = input_expected
        code_regex = build_code_regex(None)
        assert detect_pattern(input) == expected, (expected, re.split(code_regex, input)[-1])
        article_pattern = switch_pattern(expected)
        if expected == "code_article":
            assert len(article_pattern) == 2, (input, "=>", expected)

    @pytest.mark.parametrize(
        "filepath_expected",
        [
            (
                "newtest.pdf",
                "article_code",
            ),
            (
                "testnew.pdf",
                "code_article",
            ),
            (
                "newtest.odt",
                "article_code",
            ),
            (
                "testnew.odt",
                "code_article",
            ),
            (
                "newtest.docx",
                "article_code",
            ),
            (
                "testnew.docx",
                "code_article",
            ),
        ],
    )
    def test_detect_pattern_doc(self, filepath_expected):
        filepath, expected = filepath_expected
        archive_test_file(filepath)
        full_text = parse_doc(filepath)
        print(full_text)
        restore_test_file(filepath)
        
        assert detect_pattern(full_text) == expected, re.split(
            build_code_regex(None), input
        )[-1]
        article_pattern = switch_pattern(expected)
        if expected == "code_article":
            assert len(article_pattern) == 2, (input, "=>", expected)

    def test_switch_pattern_wrong_pattern(self):
        with pytest.raises(ValueError) as e:
            switch_pattern("code_code")
            assert e.info_msg == "", e

    def test_switch_pattern_classical_pattern(self):
        pattern = switch_pattern("article_code")
        assert repr(pattern).startswith("re.compile("), repr(pattern)

    def test_switch_pattern_reverse_pattern(self):
        pattern_code, pattern_article = switch_pattern("code_article")
        assert repr(pattern_code).startswith("re.compile("), repr(pattern_code)
        assert repr(pattern_article).startswith("re.compile("), repr(pattern_article)


class TestNormalizeRef:
    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "238-4 alinéa 2",
                ["238-4"],
            ),
            (
                "238 alinéa 2",
                ["238"],
            ),
            (
                "2-3-4",
                ["2-3-4"],
            ),
            ("a R2-3-4", ["R2-3-4"]),
            ("-AR2-3-4", ["R2-3-4"]),
            (
                "L.278",
                ["L278"],
            ),
            (
                "L. 385-2, R. 343-4 et A421-13",
                ["L385-2", "R343-4", "A421-13"],
            ),
            ("Articles L-214 et L228-2 alinéa 33", ["L214", "L228-2"]),
            ("Art. L. 385-2, R. 343-4 et A421-13", ["L385-2", "R343-4", "A421-13"]),
        ],
    )
    def test_text_normalize_refs(self, input_expected):
        input, expected = input_expected
        assert normalize_references(input) == expected, input


class TestGetRefs:
    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "Comme il est mentionné dans l'article 238-4 alinéa 2 du code de la consommation .",
                ("CCONSO", "Code de la consommation", "238-4 alinéa 2 du"),
            ),
            (
                "Comme il est mentionné dans l'art.238 alinéa 2 du C.conso.",
                ("CCONSO", "Code de la consommation", "238 alinéa 2 du"),
            ),
            (
                "Dans les art.238 alinéa 2, 248-4-5, 263-7 et 86  du CJA.",
                (
                    "CJA",
                    "Code de justice administrative",
                    "238 alinéa 2, 248-4-5, 263-7 et 86  du",
                ),
            ),
            (
                "Art. 2-3-4 du Code de l'Environnement",
                ("CENV", "Code de l'environnement", "2-3-4 du"),
            ),
            (
                "Dans le CE. Art. R2-3-4, il est fait mention de l'obligation pour les entreprises",
                (
                    "CENV",
                    "Code de l'environnement",
                    "R2-3-4, il est fait mention de l'obligation pour les entreprises",
                ),
            ),
            (
                "Tenir compte des articles L. 611-2 C. com., L. 132-1 C. com. et R. 811-3 du Code de commerce.",
                ("CCOM", "Code de commerce", "L.\xa0611-2"),
            ),
            (
                # ici cela marche parce il n'y a pas de répétition du code
                "Tenir compte des articles L. 611-2, L. 132-1 et R. 811-3 du Code de commerce.",
                ("CCOM", "Code de commerce", "L.\xa0611-2, L.\xa0132-1 et R. 811-3 du"),
            ),
        ],
    )
    def test_text_no_filter(self, input_expected):
        full_text, expected = input_expected
        results = get_code_refs(full_text, selected_codes=None, pattern_format=None)
        assert results[0] == expected, results

    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                ("newtest.odt", "newtest.docx", "newtest.pdf"),
                [
                    ("CCIV", "Code civil", "1120 du"),
                    ("CCIV", "Code civil", "2288"),
                    ("CCIV", "Code civil", "1240 al. 1"),
                    ("CCIV", "Code civil", "1140."),
                    ("CCIV", "Code civil", "1 et 349 du"),
                    ("CCIV", "Code civil", "39999"),
                    ("CCIV", "Code civil", "3-12, 12-4-6, 14, 15 et 27"),
                    ("CPRCIV", "Code de procédure civile", "1038 et 1289-2"),
                    ("CASSUR", "Code des assurances", "L. 385-2, R. 343-4 et A421-13"),
                    ("CCOM", "Code de commerce", "L. 611-2"),
                    # ('CCOM', 'Code de commerce', 'L. 132-1 et'), avec repetion du code art. => non trouvé
                    # ('CCOM', 'Code de commerce', 'R. 811-3.'),
                    ("CTRAV", "Code du travail", "L. 1111-1"),
                    ("CPI", "Code de la propriété intellectuelle", "L. 112-1"),
                    ("CPI", "Code de la propriété intellectuelle", "L. 331-4 du"),
                    ("CPEN", "Code pénal", "131-4 et 225-7-1"),
                    ("CPP", "Code de procédure pénale", "694-4-1 et R57-6-1"),
                    ("CCONSO", "Code de la consommation", "L. 121-14, R. 742-52"),
                    (
                        "CSI",
                        "Code de la sécurité intérieure",
                        "L. 622-7 et R. 314-7 du",
                    ),
                    ("CSS", "Code de la sécurité sociale", "L. 173-8 du"),
                    ("CSP", "Code de la santé publique", "L. 1110-1 du"),
                    (
                        "CESEDA",
                        "Code de l'entrée et du séjour des étrangers et du droit d'asile",
                        "L. 753-1 et 12 du",
                    ),
                    (
                        "CGCT",
                        "Code général des collectivités territoriales",
                        "L. 1424-71 et L1",
                    ),
                    ("CJA", "Code de justice administrative", "L. 121-2"),
                    ("CENV", "Code de l'environnement", "L.124-1 du"),
                ],
            ),
            (
                ("testnew.odt", "testnew.docx"),
                [
                    ("CCIV", "Code civil", "1120. Voir aussi, dans le même sens,"),
                    (
                        "CCIV",
                        "Code civil",
                        "2288 Cette phrase ne contient pas le mot recherché. Cette autre phrase est "
                        "également un piège. Toutefois, la prise en compte de",
                    ),
                    (
                        "CCIV",
                        "Code civil",
                        "1240 al. 1 est de nature à changer la donne. C’est aussi le cas de",
                    ),
                    ("CCIV", "Code civil", "1140. Ce sont aussi les"),
                    ("CCIV", "Code civil", "1 et 349"),
                    ("CCIV", "Code civil", "39999"),
                    ("CCIV", "Code civil", "3-12, 12-4-6, 14, 15 et 27"),
                    ("CPRCIV", "Code de procédure civile", ".  1038 et 1289-2"),
                    (
                        "CASSUR",
                        "Code des assurances",
                        "L. 385-2, R. 343-4 et A421-13 Tenir compte de",
                    ),
                    ("CCOM", "Code de commerce", "L. 611-2 ,"),
                    ("CCOM", "Code de commerce", "L. 132-1 et"),
                    ("CCOM", "Code de commerce", "R. 811-3."),
                    ("CTRAV", "Code du travail", "L. 1111-1 et  R. 4512-15."),
                    ("CPI", "Code de la propriété intellectuelle", "L. 112-1"),
                    ("CPI", "Code de la propriété intellectuelle", "L. 331-4 ."),
                    ("CPEN", "Code pénal", "131-4 et 225-7-1"),
                    ("CPP", "Code de procédure pénale", ".  694-4-1 et R57-6-1 ."),
                    ("CCONSO", "Code de la consommation", "L. 121-14, R. 742-52"),
                    ("CSI", "Code de la sécurité intérieure", "L. 622-7 et R. 314-7"),
                    ("CSS", "Code de la sécurité sociale", "L. 173-8."),
                    ("CSP", "Code de la santé publique", "L. 1110-1."),
                    (
                        "CESEDA",
                        "Code de l'entrée et du séjour des étrangers et du droit d'asile",
                        "L. 753-1 et 12.",
                    ),
                    (
                        "CGCT",
                        "Code général des collectivités territoriales",
                        "L. 1424-71 et L1.",
                    ),
                    ("CJA", "Code de justice administrative", "L. 121-2"),
                    ("CENV", "Code de l'environnement", "L.124-1"),
                ],
            ),
        ],
    )
    def test_doc_no_filter(self, input_expected):
        file_paths, expected = input_expected
        for file_path in file_paths:
            print(file_path)
            archive_test_file(file_path)
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            print(abspath)
            full_text = parse_doc(abspath)
            restore_test_file(file_path)
            results = get_code_refs(full_text, selected_codes=None, pattern_format=None)
            assert results == expected, (file_path, results)


class TestFilterRefs:
    pass

class TestMatchingItem:
    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "Comme il est mentionné dans l'article 238-4 alinéa 2 du code de la consommation .",
                [("CCONSO", "Code de la consommation", "238-4")],
            ),
            (
                "Comme il est mentionné dans l'art.238 alinéa 2 du C.conso.",
                [("CCONSO", "Code de la consommation", "238")],
            ),
            (
                "Art. 2-3-4 du Code de l'Environnement",
                [("CENV", "Code de l'environnement", "2-3-4")],
            ),
            ("Art. R2-3-4 du CE.", [("CENV", "Code de l'environnement", "R2-3-4")]),
            (
                "\n-\n article L.278 du cjaaa",
                [('CJA', 'Code de justice administrative', 'L278')],
            ),
            (
                #articles pose problème
                "Dans les articles suivants: \n-\n  cjaaa article L.278 ",
                [('CJA', 'Code de justice administrative', 'L278')],
            ),
            (
                "Art. L. 385-2, R. 343-4 et A421-13 du C. assur. ",
                [
                    ("CASSUR", "Code des assurances", "L385-2"),
                    ("CASSUR", "Code des assurances", "R343-4"),
                    ("CASSUR", "Code des assurances", "A421-13")
                ]
            ),
        ],
    )
    def test_text_article_code_no_filter(self, input_expected):
        input, expected = input_expected
        items = list(get_matching_result_item(input, None, "article_code"))
        assert expected == items, items


