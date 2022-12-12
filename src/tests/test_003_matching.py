import os
import pytest
import re
from .context import matching, parsing, code_references
import difflib
from parsing import parse_doc
from code_references import CODE_REFERENCE, get_short_code_from_full_name
from matching import (
    get_matching_results_dict,
    get_matching_result_item,
    get_code_refs,
    normalize_references,
)
from .test_001_parsing import restore_test_file, archive_test_file

class TestNormalize:
    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "238-4 al. 2",
                ["238-4-2"],
            ),
            (
                "238-4 alinéa 2",
                ["238-4-2"],
            ),
            (
                "2-3-4-5-6 alinéa 7 ",
                ["2-3-4-5-6-7"],
            ),
            ("R2-3-4", ["R2-3-4"]),
            (
                "\n-\n L.278",
                ["L278"],
            ),
            (
                "LL278",
                ["L278"],
            ),
            (
                "LL.278",
                ["L278"],
            ),
            (
                "RL.278",
                ["L278"],
            ),
            (
                " L. 385-2, R. 343-4, D 419 et A421-13",
                [
                    "L385-2",
                    "R343-4",
                    "D419",
                    "A421-13",
                ],
            ),
            (
                " L. 385-2, R. 343-4 et A421-13",
                [
                    "L385-2",
                    "R343-4",
                    "A421-13",
                ],
            ),
            ("L. 112-3 al. 2", ["L112-3-2"]),
            ("L 122-1", ["L122-1"]),
        ],
    )
    def test_normalize_article(self, input_expected):
        input, expected = input_expected
        results = normalize_references(input)
        assert results == expected, (results, expected)

class TestSplitMethod:
    def test_split_multiple_refs_art_code(self):
        input1 = "Articles 23, 24 et 25-1 du CJA Art. 238, 2887-4-12 du CENV  art. 244-2 et 287-18-24 du CCONSO"
        output = []
        output1 = ['Articles 23, 24 et 25-1 du ', ' Art. 238, 2887-4-12 du ', '  art. 244-2 et 287-18-24 du ']
        for code in ["CJA", "CENV", "CCONSO"]:
            first, second = input1.split(code,1)
            output.append(first)
            input1 = second
        assert output == output1, output
    
    def test_split_multiple_refs_code_art(self):
        input1 = "CJA Articles 23, 24 et 25-1, CENV Art. 238, 2887-4-12, CCONSO art. 244-2 et 287-18-24"
        output1 = [' Articles 23, 24 et 25-1, ', ' Art. 238, 2887-4-12, ', ' art. 244-2 et 287-18-24'] 
        output = []
        codes = ["CJA", "CENV", "CCONSO"]
        for i,code in enumerate(codes):
            first, second = input1.split(code,1)
            if i != 0:
                output.append(first)
            if i+1 == len(codes):
                # output.append(first)
                output.append(second)
            else:
                input1 = second
            
        assert output == output1, output
class TestTextGetRef:
    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "Comme il est mentionné dans le code de la consommation article 238-4 alinéa 2.",
                [["CCONSO", "Code de la consommation", "238-4"]],
            ),
            (
                "Comme il est mentionné dans  le C.conso. art.238-4 alinéa 2  qui blablabla",
                [["CCONSO", "Code de la consommation", "238-4"]],
            ),
            (
                "Code de l'Environnement Art. 2-3-4",
                [["CENV", "Code de l'environnement", "2-3-4"]],
            ),
            (   "C.Env Art. R2-3-4", 
                [["CENV", "Code de l'environnement", "R2-3-4"]]
            ),
            (
                "\n-\n  cjaaa article L.278 ",
                [["CJA", "Code de justice administrative", "L278"]],
            ),
            (
                "C. assur. articles L. 385-2, R. 343-4 et A421-13.",
                [
                    ["CASSUR", "Code des assurances", "L385-2"],
                    ["CASSUR", "Code des assurances", "R343-4"],
                    ["CASSUR", "Code des assurances", "A421-13"]
                ],
            ),
            (
                "C. assur. Art. L. 385-2, R.343-4 et A421-13",
                [
                    ["CASSUR", "Code des assurances", "L385-2"],
                    ["CASSUR", "Code des assurances", "R343-4"],
                    ["CASSUR", "Code des assurances", "A421-13"]
                ],
            ),
            
        ],
    )
    def test_text_1_code_x_article(self, input_expected):
        input, expected = input_expected
        
        for item, expect in zip(get_code_refs(
            input, selected_codes=None, pattern_format="code_article"
        ), expected):
            assert item == expect, ("ITEM:", item, "EXPECT:", expect, input)

    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "Comme il est mentionné dans l'article 238-4 alinéa 2 du code de la consommation .",
                [["CCONSO", "Code de la consommation", "238-4"]],
            ),
            (
                "Comme il est mentionné dans l'art.238-4 alinéa 2 du C.conso.",
                [["CCONSO", "Code de la consommation", "238-4"]],
            ),
            (
                "Art. 2-3-4 du Code de l'Environnement",
                [["CENV", "Code de l'environnement", "2-3-4"]],
            ),
            (
                "Art. R2-3-4 du CE.", 
                [["CENV", "Code de l'environnement", "R2-3-4"]]
            ),
            (
                "\n-\n article L.278 du cjaaa",
                [["CJA", "Code de justice administrative", "L278"]],
            ),
            (
                "Art. L. 112-3 al. 2 CPI.",
                [["CPI", "Code de la propriété intellectuelle", "L112-3"]],
            ),
            (
                "La Commission des clauses abusives rappelle « qu’un certain nombre de conditions générales de vente prévoient la possibilité pour le vendeur de refuser au consommateur, pour quelque raison que ce soit, la possibilité de confirmer l’acceptation de l’offre ; que ces clauses qui contreviennent à l’article L 122-1 du code de la consommation, sont illicites »",
                [["CCONSO", "Code de la consommation", "L122-1"]],
            ),
            (
                "Art. L. 385-2, R.343-4 et A421-13 C. assur.",
                [
                    ["CASSUR", "Code des assurances", "L385-2"],
                    ["CASSUR", "Code des assurances", "R343-4"],
                    ["CASSUR", "Code des assurances", "A421-13"],
                ],
            ),
        ],
    )
    def test_text_x_article_1_code(self, input_expected):
        input, expected = input_expected
        for item, expect in zip(list(get_code_refs(
            input, selected_codes=None, pattern_format="article_code"
        )), expected):
            assert item == expect, ("ITEM:", item, "EXPECT:", expect)

    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "CSI Articles L22-7 et R314-7  Code de l'environnement Articles L124-1, 228. CJA Art. L214-4 et 495",
                "code_article",
                [
                    ["CSI", "Code de la sécurité intérieure", "L22-7"],
                    ["CSI", "Code de la sécurité intérieure", "R314-7"],
                    ["CENV", "Code de l'environnement", "L124-1"],
                    ["CENV", "Code de l'environnement", "228"],
                    ["CJA", "Code de justice administrative", "L214-4"],
                    ["CJA", "Code de justice administrative", "495"]
                ],
            ),
            (
                "Comme on peut le voir dans les articles L22-7 et R314-7 du CSI, les articles L124-1 et 228  du   Code de l'environnement. Les art. L214-4 et 495 du CJA ",
                "article_code",
                [
                    ["CSI", "Code de la sécurité intérieure", "L22-7"],
                    ["CSI", "Code de la sécurité intérieure", "R314-7"],
                    ["CENV", "Code de l'environnement", "L124-1"],
                    ["CENV", "Code de l'environnement", "228"],
                    ["CJA", "Code de justice administrative", "L214-4"],
                    ["CJA", "Code de justice administrative", "495"]
                ],
            ),
        ],
    )
    def test_text_x_code_x_articles(self, input_expected):
        input, regex_fmt, expected = input_expected
        items = list(get_code_refs(
            input, selected_codes=None, pattern_format=regex_fmt
        ))
        assert len(expected) == len(items), items
        for item, expect in zip(sorted(items), sorted(expected)):
            assert item == expect, ("ITEM:", item, "EXPECT:", expect)

class TestTextMatchingIterator:
    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "Comme il est mentionné dans le code de la consommation article 238-4 alinéa 2.",
                ["CCONSO", "Code de la consommation", "238-4"],
            ),
            (
                "Comme il est mentionné dans  le C.conso. art.238-4 alinéa 2  qui blablabla",
                ["CCONSO", "Code de la consommation", "238-4"],
            ),
            (
                "Code de l'Environnement Art. 2-3-4",
                ["CENV", "Code de l'environnement", "2-3-4"],
            ),
            ("CE. Art. R2-3-4", ["CENV", "Code de l'environnement", "R2-3-4"]),
            (
                "\n-\n  cjaaa article L.278 ",
                ["CJA", "Code de justice administrative", "L278"],
            ),
        ],
    )
    def test_text_pattern_code_article(self, input_expected):
        input, expected = input_expected

        for item in list(get_matching_result_item(input, None, "code_article")):
            assert item == expected, (item, expected)

    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "C. assur. Art. L. 385-2, R. 343-4 et A421-13",
                "code_article",
                [
                    ["CASSUR", "Code des assurances", "L385-2"],
                    ["CASSUR", "Code des assurances", "R343-4"],
                    ["CASSUR", "Code des assurances", "A421-13"],
                ],
            ),
            (
                "Art. L. 385-2, R. 343-4 et A421-13 du C. assur. ",
                "article_code",
                [
                    ["CASSUR", "Code des assurances", "L385-2"],
                    ["CASSUR", "Code des assurances", "R343-4"],
                    ["CASSUR", "Code des assurances", "A421-13"],
                ],
            ),
        ],
    )
    def test_text_multiple_art_same_code(self, input_expected):
        input, regex_fmt, expected = input_expected
        # for item in list(get_code_refs(input, None, regex_fmt)):
        #     assert item == expected, (item, expected)
        for item, expect in zip(list(get_matching_result_item(input, None, regex_fmt)), expected):
            assert item == expect, (item, expect)
        # for item in get_matching_result_item(input, None, regex_fmt):
        #     for i in item:
        #         assert list(i) == expected, (i, expected)

    def test_text_pattern_code_article_1(self):
        
        code_reference_test = CODE_REFERENCE
        # del code_reference_test["CPCE"]

        chunk = "C’est la solution posée dans le Code civil article 1120"
        for item in get_matching_result_item(chunk, ):
            assert item == ["CCIV", "Code civil", "1120"], item
        
    def test_text_pattern_code_article_x(self):
        multi_chunk = "C’est la solution posée dans le Code civil article 1120 et de C. civ. art. 2288"
        for i, item in enumerate(list(get_matching_result_item(multi_chunk, None, "code_article"))):
            if i == 0:
                assert item == ["CCIV", "Code civil", "1120"], item
            else:
                assert item == ["CCIV", "Code civil", "2288"], item


class TestDocMatchingIterator:
    def test_doc_pattern_article_code(self):
        # NO CPCE ref dans le doc
        code_reference_test = CODE_REFERENCE
        del code_reference_test["CPCE"]
        del code_reference_test["CMF"]

        file_paths = ["newtest.odt", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:

            tmp_abspath = archive_test_file(file_path)
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            full_text = parse_doc(abspath)
            restored_abspath = restore_test_file(file_path)
            results_dict = get_matching_results_dict(full_text, None, "article_code")
            code_list = list(results_dict.keys())

            assert len(code_list) == len(code_reference_test), (set(
                code_reference_test
            ) - set(code_list), code_list)
            assert sorted(code_list) == sorted(code_reference_test), set(
                code_reference_test
            ) - set(code_list)
            articles_detected = [
                item for sublist in results_dict.values() for item in sublist
            ]
            assert len(articles_detected) == 39, len(articles_detected)
            assert list(results_dict.keys()) == [
                'CCIV',
                'CPRCIV',
                'CASSUR',
                'CCOM',
                'CTRAV',
                'CPI',
                'CPEN',
                'CPP',
                'CCONSO',
                'CSI',
                'CSS',
                'CSP',
                'CESEDA',
                'CGCT',
                'CJA',
                'CENV'
            ], list(results_dict.keys())
            assert results_dict["CCIV"] == [
                "1120",
                "2288",
                "1240-1",
                "1140",
                "1",
                "349",
                "39999",
                "3-12",
                "12-4-6",
                "14",
                "15",
                "27",
            ], results_dict["CCIV"]
            # assert results_dict["CPRCIV"] == ["1038", "1289-2"], results_dict["CPRCIV"]
            # assert results_dict["CASSUR"] == [
            #     "L385-2",
            #     "R343-4",
            #     "A421-13",
            # ], results_dict["CASSUR"]
            # assert results_dict["CCOM"] == ['L611-2', 'L132-1', 'R811-3'], results_dict["CCOM"]
            # assert results_dict["CTRAV"] == ["L1111-1"], ("CTRAV", results_dict["CTRAV"])
            # assert results_dict["CPI"] == ["L112-1", "L331-4"], results_dict["CPI"]
            # assert results_dict["CPEN"] == ["131-4", "225-7-1"], results_dict["CPEN"]
            # assert results_dict["CPP"] == ["694-4-1", "R57-6-1"], results_dict["CPP"]
            # assert results_dict["CCONSO"] == ["L121-14", "R742-52"], results_dict[
            #     "CCONSO"
            # ]
            # assert results_dict["CSI"] == ["L622-7", "R314-7"], results_dict["CSI"]
            # assert results_dict["CSS"] == ["L173-8"], results_dict["CSS"]
            # assert results_dict["CSP"] == ["L1110-1"], results_dict["CSP"]
            # assert results_dict["CENV"] == ["L124-1"], ("CENV", results_dict["CENV"])
            # assert results_dict["CJA"] == ["L121-2"], ("CJA", results_dict["CJA"])
            # assert results_dict["CGCT"] == ["L1424-71", "L1"], (
            #     "CGCT",
            #     results_dict["CGCT"],
            # )
            # assert results_dict["CESEDA"] == ["L753-1", "12"], (
            #     "CESEDA",
            #     results_dict["CESEDA"],
            # )

    def test_doc_pattern_article_code_filter1(self):
        selected_codes = ["CASSUR"]
        file_paths = ["newtest.odt", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:
            archive_test_file(file_path)
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            full_text = parse_doc(abspath)
            restore_test_file(file_path)
            results_dict = get_matching_results_dict(
                full_text, selected_codes, "article_code"
            )
            code_list = list(results_dict.keys())
            assert len(code_list) == len(selected_codes), len(code_list)
            assert sorted(code_list) == ["CASSUR"], sorted(code_list)
            articles_detected = [
                item for sublist in results_dict.values() for item in sublist
            ]
            assert len(articles_detected) == 3, len(articles_detected)
            assert results_dict["CASSUR"] == [
                "L385-2",
                "R343-4",
                "A421-13",
            ], results_dict["CASSUR"]

    def test_doc_pattern_article_code_filterX(self):
        selected_codes = ["CASSUR", "CENV", "CSI", "CCIV"]
        file_paths = ["newtest.odt", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            archive_test_file(file_path)
            full_text = parse_doc(abspath)
            restore_test_file(file_path)
            results_dict = get_matching_results_dict(
                full_text, selected_codes, "article_code"
            )
            code_list = list(results_dict.keys())
            assert len(code_list) == len(selected_codes), len(code_list)
            assert sorted(code_list) == [
                "CASSUR",
                "CCIV",
                "CENV",
                "CSI",
            ], sorted(code_list)

            articles_detected = [
                item for sublist in results_dict.values() for item in sublist
            ]
            assert len(articles_detected) == 18, len(articles_detected)
            assert results_dict["CCIV"] == [
                "1120",
                "2288",
                "1240-1",
                "1140",
                "1",
                "349",
                "39999",
                "3-12",
                "12-4-6",
                "14",
                "15",
                "27",
            ], results_dict["CCIV"]
            assert results_dict["CASSUR"] == [
                "L385-2",
                "R343-4",
                "A421-13",
            ], results_dict["CASSUR"]
            assert results_dict["CSI"] == ["L622-7", "R314-7"], results_dict["CSI"]
            assert results_dict["CENV"] == ["L124-1"], ("CENV", results_dict["CENV"])

    def test_doc_pattern_code_article(self):
        code_reference_test_002 = CODE_REFERENCE
        file_paths = ["testnew.odt", "testnew.pdf", "testnew.docx"]
        for file_path in file_paths:

            tmp_abspath = archive_test_file(file_path)
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            full_text = parse_doc(abspath)
            restored_abspath = restore_test_file(file_path)
            results_dict = get_matching_results_dict(full_text, None, "article_code")
            assert sorted(list(results_dict.keys())) == sorted(
                code_reference_test_002
            ), sorted(code_reference_test_002)
            assert len(results_dict) == 16, len(results_dict)
            assert len(list(results_dict.values())) == 16, len(
                list(results_dict.values())
            )
            assert results_dict["CCIV"] == [
                "1120",
                "2288",
                "1240-1",
                "1140",
                "1",
                "349",
                "39999",
            ], results_dict["CCIV"]
            # assert results_dict["CASSUR"] == ["L385-2", "R343-4", "A421-13"], results_dict[
            #     "CASSUR"
            # ]
            # assert results_dict["CSI"] == ["L622-7", "R314-7"], results_dict["CSI"]
            # assert results_dict["CENV"] == ["L124-1"], ("CENV", results_dict["CENV"])

    def test_doc_article_code(self):
        file_path = "HDR_NETTER_V1_07.odt"
        tmp_abspath = archive_test_file(file_path)
        abspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_path)
        full_text = parse_doc(abspath)
        restored_abspath = restore_test_file(file_path)

        results_dict = get_matching_results_dict(full_text, None, "article_code")
        assert sorted(results_dict) == sorted(
            [
                "CASSUR",
                "CENV",
                "CCIV",
                "CSS",
                "CPEN",
                "CPI",
                "CPP",
                "CCONSO",
                "CTRAV",
                "CPRCIV",
                "CSP",
                "CCOM",
            ]
        ), results_dict
        assert False, results_dict["CASSUR"]

    def test_doc_code_article(self):
        file_path = "HDR_NETTER_V1_07.odt"
        tmp_abspath = archive_test_file(file_path)
        abspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_path)
        full_text = parse_doc(abspath)
        restored_abspath = restore_test_file(file_path)

        results_dict = get_matching_results_dict(full_text, None, "code_article")
        assert sorted(results_dict) == sorted(
            [
                "CASSUR",
                "CENV",
                "CCIV",
                "CSS",
                "CPEN",
                "CPI",
                "CPP",
                "CCONSO",
                "CTRAV",
                "CPRCIV",
                "CSP",
                "CCOM",
            ]
        ), results_dict
        assert False, results_dict.items()
