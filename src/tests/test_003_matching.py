import os
import pytest
import re
from .context import matching, parsing, code_references
from parsing import parse_doc
from code_references import CODE_REFERENCE
from matching import (
    get_matching_results_dict,
    get_matching_result_item,
    switch_pattern,
    get_code_refs,
    detect_format_pattern,
    normalize_references,
    COMPILED_ARTICLE,
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
            ("Dans les articles suivants: CSP Art. L214", "code_article")
        ],
    )
    def test_detect_format_pattern_txt(self, input_expected):
        input, expected = input_expected
        assert detect_format_pattern(input) == expected, input
        article_pattern = switch_pattern(None, expected)
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
        ],
    )
    def test_detect_format_pattern_doc(self, filepath_expected):
        filepath, expected = filepath_expected
        archive_test_file(filepath)
        full_text = parse_doc(filepath)
        restore_test_file(filepath)
        assert detect_format_pattern(full_text) == expected, re.split(
            COMPILED_ARTICLE, input
        )[0]
        article_pattern = switch_pattern(None, expected)
        if expected == "code_article":
            assert len(article_pattern) == 2, (input, "=>", expected)

    def test_switch_pattern_wrong_pattern(self):
        with pytest.raises(ValueError) as e:
            switch_pattern(None, "code_code")
            assert e.info_msg == "", e

    def test_switch_pattern_classical_pattern(self):
        pattern = switch_pattern(None, "article_code")
        assert repr(pattern).startswith("re.compile("), repr(pattern)

    def test_switch_pattern_reverse_pattern(self):
        pattern_code, pattern_article = switch_pattern(None, "code_article")
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
            archive_test_file(file_path)
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            full_text = parse_doc(abspath)
            restore_test_file(file_path)
            results = get_code_refs(full_text, selected_codes=None, pattern_format=None)
            assert results == expected, (file_path, results)


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
                [],
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
        items = list(get_matching_result_item(input, None, None))
        assert expected == items, items


#     @pytest.mark.parametrize(
#         "input_expected",
#         [
#             (
#                 "Comme il est mentionné dans le code de la consommation article 238-4 alinéa 2.",
#                 "code_article",
#                 ("CCONSO", "Code de la consommation", "238-4"),
#             ),
#             (
#                 "Comme il est mentionné dans  le C.conso. art.238 alinéa 2  qui blablabla",
#                 "article_code",
#                 ("CCONSO", "Code de la consommation", "238"),
#             ),
#             (
#                 "Code de l'Environnement Art. 2-3-4",
#                 "code_article",
#                 ("CENV", "Code de l'environnement", "2-3-4"),
#             ),
#             (
#                 "CE. Art. R2-3-4",
#                 "code_article",
#                 ("CENV", "Code de l'environnement", "R2-3-4"),
#             ),
#             (
#                 "\n-\n  cjaaa article L.278 ",
#                 "code_article",
#                 ("CJA", "Code de justice administrative", "L278"),
#             ),
#         ],
#     )
#     def test_text_code_article_no_filter(self, input_expected):
#         input, pattern_format, expected = input_expected
#         for item in get_matching_result_item(input, None, pattern_format):
#             assert item == expected, item

#     def test_doc_article_code_no_filter(self):
#         # NO CPCE ref dans le doc
#         code_reference_test = CODE_REFERENCE
#         del code_reference_test["CPCE"]

#         file_paths = ["newtest.odt", "newtest.docx", "newtest.pdf"]
#         for file_path in file_paths:

#             tmp_abspath = archive_test_file(file_path)
#             abspath = os.path.join(
#                 os.path.dirname(os.path.realpath(__file__)), file_path
#             )
#             full_text = parse_doc(abspath)
#             restored_abspath = restore_test_file(file_path)
#             results_dict = get_matching_results_dict(full_text, None)

#             # del code_reference_test["CPCE"]
#             code_list = list(results_dict.keys())

#             assert len(code_list) == len(code_reference_test), set(
#                 code_reference_test
#             ) - set(code_list)
#             assert sorted(code_list) == sorted(code_reference_test), set(
#                 code_reference_test
#             ) - set(code_list)
#             articles_detected = [
#                 item for sublist in results_dict.values() for item in sublist
#             ]
#             assert len(articles_detected) == 37, len(articles_detected)
#             assert results_dict["CCIV"] == [
#                 "1120",
#                 "2288",
#                 "1240-1",
#                 "1140",
#                 "1",
#                 "349",
#                 "39999",
#                 "3-12",
#                 "12-4-6",
#                 "14",
#                 "15",
#                 "27",
#             ], results_dict["CCIV"]
#             assert results_dict["CPRCIV"] == ["1038", "1289-2"], results_dict["CPRCIV"]
#             assert results_dict["CASSUR"] == [
#                 "L385-2",
#                 "R343-4",
#                 "A421-13",
#             ], results_dict["CASSUR"]
#             assert results_dict["CCOM"] == ["L611-2"], results_dict["CCOM"]
#             assert results_dict["CTRAV"] == ["L1111-1"], results_dict["CTRAV"]
#             assert results_dict["CPI"] == ["L112-1", "L331-4"], results_dict["CPI"]
#             assert results_dict["CPEN"] == ["131-4", "225-7-1"], results_dict["CPEN"]
#             assert results_dict["CPP"] == ["694-4-1", "R57-6-1"], results_dict["CPP"]
#             assert results_dict["CCONSO"] == ["L121-14", "R742-52"], results_dict[
#                 "CCONSO"
#             ]
#             assert results_dict["CSI"] == ["L622-7", "R314-7"], results_dict["CSI"]
#             assert results_dict["CSS"] == ["L173-8"], results_dict["CSS"]
#             assert results_dict["CSP"] == ["L1110-1"], results_dict["CSP"]
#             assert results_dict["CENV"] == ["L124-1"], ("CENV", results_dict["CENV"])
#             assert results_dict["CJA"] == ["L121-2"], ("CJA", results_dict["CJA"])
#             assert results_dict["CGCT"] == ["L1424-71", "L1"], (
#                 "CGCT",
#                 results_dict["CGCT"],
#             )
#             assert results_dict["CESEDA"] == ["L753-1", "12"], (
#                 "CESEDA",
#                 results_dict["CESEDA"],
#             )


# class TestMatchingDict:
#     @pytest.mark.parametrize(
#         "input_expected",
#         [
#             [
#                 "Art. L. 385-2, R. 343-4 et A421-13 du C. assur. ",
#                 {"CASSUR": ["L385-2", "R343-4", "A421-13"]},
#             ],
#             [
#                 "Article L. 189-2, 343-4 et L-421-13 du CE.",
#                 {"CENV": ["L189-2", "343-4", "L421-13"]},
#             ],
#             [
#                 "C. assur. Art. L. 385-2, R. 343-4 et A421-13",
#                 {"CASSUR": ["L385-2", "R343-4", "A421-13"]},
#             ],
#             [
#                 "CE. Article L. 189-2, 343-4 et L-421-13",
#                 {"CENV": ["L189-2", "343-4", "L421-13"]},
#             ],
#         ],
#     )
#     def test_matching_item_multi_dict(self, input_expected):
#         input, expected = input_expected
#         expected = [n[2] for n in expected]
#         results_dict = get_matching_results_dict(input)
#         for key, item in results_dict.items():
#             assert key == expected.keys()[0]
#             assert item == expected.values()

#     def test_matching_result_dict_codes_unique_filter_pattern_article_code(self):
#         selected_codes = ["CASSUR"]
#         file_paths = ["newtest.odt", "newtest.docx", "newtest.pdf"]
#         for file_path in file_paths:
#             archive_test_file(file_path)
#             abspath = os.path.join(
#                 os.path.dirname(os.path.realpath(__file__)), file_path
#             )
#             full_text = parse_doc(abspath)
#             restore_test_file(file_path)
#             results_dict = get_matching_results_dict(full_text, selected_codes)
#             code_list = list(results_dict.keys())
#             assert len(code_list) == len(selected_codes), len(code_list)
#             assert sorted(code_list) == ["CASSUR"], sorted(code_list)
#             articles_detected = [
#                 item for sublist in results_dict.values() for item in sublist
#             ]
#             assert len(articles_detected) == 3, len(articles_detected)
#             assert results_dict["CASSUR"] == [
#                 "L385-2",
#                 "R343-4",
#                 "A421-13",
#             ], results_dict["CASSUR"]

#     def test_matching_result_dict_codes_multiple_filter_pattern_article_code(self):
#         selected_codes = ["CASSUR", "CENV", "CSI", "CCIV"]
#         file_paths = ["newtest.odt", "newtest.docx", "newtest.pdf"]
#         for file_path in file_paths:
#             abspath = os.path.join(
#                 os.path.dirname(os.path.realpath(__file__)), file_path
#             )
#             archive_test_file(file_path)
#             full_text = parse_doc(abspath)
#             restore_test_file(file_path)
#             results_dict = get_matching_results_dict(full_text, selected_codes)
#             code_list = list(results_dict.keys())
#             assert len(code_list) == len(selected_codes), len(code_list)
#             assert sorted(code_list) == [
#                 "CASSUR",
#                 "CCIV",
#                 "CENV",
#                 "CSI",
#             ], sorted(code_list)

#             articles_detected = [
#                 item for sublist in results_dict.values() for item in sublist
#             ]
#             assert len(articles_detected) == 18, len(articles_detected)
#             assert results_dict["CCIV"] == [
#                 "1120",
#                 "2288",
#                 "1240-1",
#                 "1140",
#                 "1",
#                 "349",
#                 "39999",
#                 "3-12",
#                 "12-4-6",
#                 "14",
#                 "15",
#                 "27",
#             ], results_dict["CCIV"]
#             assert results_dict["CASSUR"] == [
#                 "L385-2",
#                 "R343-4",
#                 "A421-13",
#             ], results_dict["CASSUR"]
#             assert results_dict["CSI"] == ["L622-7", "R314-7"], results_dict["CSI"]
#             assert results_dict["CENV"] == ["L124-1"], ("CENV", results_dict["CENV"])

#     def test_get_code_refs_reversed_pattern(self):
#         full_text = (
#             "CSI Article LL22-7 et R314-7  Code de l'environnement L124-1 CJA L214-4"
#         )

#         results = [
#             n for n in (get_code_refs(full_text, "code_article", selected_codes=None))
#         ]
#         assert len(results) == 3, results

#     def test_get_code_refs_reversed_pattern_001(self):
#         full_text = "Comme on peut le voir dans CSI Article LL22-7 et R314-7  Code de l'environnement L124-1 CJA L214-4"

#         results = [
#             n for n in (get_code_refs(full_text, "code_article", selected_codes=None))
#         ]
#         assert len(results) == 3, results

#     def test_matching_result_dict_codes_no_filter_reversed_pattern_paragraphs(self):
#         # NO CPCE ref dans le doc
#         code_reference_test = CODE_REFERENCE
#         # del code_reference_test["CPCE"]

#         chunk = "C’est la solution posée dans le Code civil article 1120"
#         for item in get_matching_result_item(chunk, None):
#             assert item == ("Code civil", "1120"), item
#         for code, item in get_matching_results_dict(chunk):
#             assert code == "Code civil"
#             assert item == "1120"

#         multi_chunk = "C’est la solution posée dans le Code civil article 1120 et de C. civ. art. 2288"
#         for i, item in enumerate(get_matching_result_item(multi_chunk, None)):
#             if i == 0:
#                 assert item == ("Code civil", "1120"), item
#             else:
#                 assert item == ("Code civil", "2288"), item

#     def test_matching_result_dict_codes_no_filter_pattern_code_article(self):

#         code_reference_test_002 = CODE_REFERENCE
#         file_paths = ["testnew.odt", "testnew.pdf", "testnew.docx"]
#         for file_path in file_paths:

#             tmp_abspath = archive_test_file(file_path)
#             abspath = os.path.join(
#                 os.path.dirname(os.path.realpath(__file__)), file_path
#             )
#             full_text = parse_doc(abspath)
#             restored_abspath = restore_test_file(file_path)
#             results_dict = get_matching_results_dict(full_text, None)
#             assert sorted(list(results_dict.keys())) == sorted(
#                 code_reference_test_002
#             ), sorted(code_reference_test_002)
#             assert len(results_dict) == 16, len(results_dict)
#             assert len(list(results_dict.values())) == 16, len(
#                 list(results_dict.values())
#             )
#             assert results_dict["CCIV"] == [
#                 "1120",
#                 "2288",
#                 "1240-1",
#                 "1140",
#                 "1",
#                 "349",
#                 "39999",
#             ], results_dict["CCIV"]
