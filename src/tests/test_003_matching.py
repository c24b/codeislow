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
        ],
    )
    def test_detect_format_pattern_txt(self, input_expected):
        input, expected = input_expected
        assert detect_format_pattern(input) == expected, input

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

class TestGetRefs:
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
            (
                "L.278",
                ["L278"],
            ),
            (
                "L. 385-2, R. 343-4 et A421-13",
                ["L385-2", "R343-4", "A421-13"],
            ),
            ("Articles L-214 et L228-2 alinéa 33", ["L214", "L228-2"]),
        ],
    )
    def test_normalize_refs(self, input_expected):
        input, expected = input_expected
        assert normalize_references(input) == expected, input

class TestMatching:
    
    
    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "Comme il est mentionné dans l'article 238-4 alinéa 2 du code de la consommation .",
                ("CCONSO", "Code de la consommation", "238-4"),
            ),
            (
                "Comme il est mentionné dans l'art.238 alinéa 2 du C.conso.",
                ("CCONSO", "Code de la consommation", "238"),
            ),
            (
                "Art. 2-3-4 du Code de l'Environnement",
                ("CENV", "Code de l'environnement", "2-3-4"),
            ),
            ("Art. R2-3-4 du CE.", ("CENV", "Code de l'environnement", "R2-3-4")),
            (
                "\n-\n article L.278 du cjaaa",
                ("CJA", "Code de justice administrative", "L278"),
            ),
            
        ],
    )
    def test_matching_result_item(self, input_expected):
        input, expected = input_expected
        for item in get_matching_result_item(input, None):
            assert expected == item, item
    
    @pytest.mark.parametrize(
        "input_expected",
        [
            [
                "Art. L. 385-2, R. 343-4 et A421-13 du C. assur. ",
                (
                    ("CASSUR", "Code des assurances", "L385-2"),
                    ("CASSUR", "Code des assurances", "R343-4"),
                    ("CASSUR", "Code des assurances", "A421-13"),
                )
            ],
            [
                "Article L. 189-2, 343-4 et L-421-13 du CE.",
                (
                    ("CENV", "Code de l'environnement", "L189-2"),
                    ("CENV", "Code de l'environnement", "343-4"),
                    ("CENV", "Code de l'environnement", "L421-13"),
                )
            ],
            [
                "C. assur. Art. L. 385-2, R. 343-4 et A421-13",
                (
                    ("CASSUR", "Code des assurances", "L385-2"),
                    ("CASSUR", "Code des assurances", "R343-4"),
                    ("CASSUR", "Code des assurances", "A421-13"),
                )
            ],
            [       
                "CE. Article L. 189-2, 343-4 et L-421-13",
                (
                    ("CENV", "Code de l'environnement", "L189-2"),
                    ("CENV", "Code de l'environnement", "343-4"),
                    ("CENV", "Code de l'environnement", "L421-13"),
                ),
            ]
        ]
    )
    def test_matching_item_multi(self, input_expected):
        input, expected = input_expected
        for item in get_matching_result_item(input, None):
            print(item)
            assert item == expected, item

    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "Comme il est mentionné dans le code de la consommation article 238-4 alinéa 2.",
                "code_article",
                ("CCONSO", "Code de la consommation", "238-4"),
            ),
            (
                "Comme il est mentionné dans  le C.conso. art.238 alinéa 2  qui blablabla",
                "article_code",
                ("CCONSO", "Code de la consommation", "238"),
            ),
            (
                "Code de l'Environnement Art. 2-3-4",
                "code_article",
                ("CENV", "Code de l'environnement", "2-3-4"),
            ),
            ("CE. Art. R2-3-4", "code_article",("CENV", "Code de l'environnement", "R2-3-4")),
            (
                "\n-\n  cjaaa article L.278 ",
                "code_article",
                ("CJA", "Code de justice administrative", "L278"),
            ),
            
        ],
    )
    def test_matching_result_item_reversed_pattern(self, input_expected):
        input, pattern_format, expected = input_expected
        for item in get_matching_result_item(input, None, pattern_format):
            assert item == expected, item

    def test_matching_result_dict_codes_no_filter_pattern_article_code(self):
        # NO CPCE ref dans le doc
        code_reference_test = CODE_REFERENCE
        del code_reference_test["CPCE"]

        file_paths = ["newtest.odt", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:

            tmp_abspath = archive_test_file(file_path)
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            full_text = parse_doc(abspath)
            restored_abspath = restore_test_file(file_path)
            results_dict = get_matching_results_dict(full_text, None)

            # del code_reference_test["CPCE"]
            code_list = list(results_dict.keys())

            assert len(code_list) == len(code_reference_test), set(
                code_reference_test
            ) - set(code_list)
            assert sorted(code_list) == sorted(code_reference_test), set(
                code_reference_test
            ) - set(code_list)
            articles_detected = [
                item for sublist in results_dict.values() for item in sublist
            ]
            assert len(articles_detected) == 37, len(articles_detected)
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
            assert results_dict["CPRCIV"] == ["1038", "1289-2"], results_dict["CPRCIV"]
            assert results_dict["CASSUR"] == [
                "L385-2",
                "R343-4",
                "A421-13",
            ], results_dict["CASSUR"]
            assert results_dict["CCOM"] == ["L611-2"], results_dict["CCOM"]
            assert results_dict["CTRAV"] == ["L1111-1"], results_dict["CTRAV"]
            assert results_dict["CPI"] == ["L112-1", "L331-4"], results_dict["CPI"]
            assert results_dict["CPEN"] == ["131-4", "225-7-1"], results_dict["CPEN"]
            assert results_dict["CPP"] == ["694-4-1", "R57-6-1"], results_dict["CPP"]
            assert results_dict["CCONSO"] == ["L121-14", "R742-52"], results_dict[
                "CCONSO"
            ]
            assert results_dict["CSI"] == ["L622-7", "R314-7"], results_dict["CSI"]
            assert results_dict["CSS"] == ["L173-8"], results_dict["CSS"]
            assert results_dict["CSP"] == ["L1110-1"], results_dict["CSP"]
            assert results_dict["CENV"] == ["L124-1"], ("CENV", results_dict["CENV"])
            assert results_dict["CJA"] == ["L121-2"], ("CJA", results_dict["CJA"])
            assert results_dict["CGCT"] == ["L1424-71", "L1"], (
                "CGCT",
                results_dict["CGCT"],
            )
            assert results_dict["CESEDA"] == ["L753-1", "12"], (
                "CESEDA",
                results_dict["CESEDA"],
            )

    def test_matching_result_dict_codes_unique_filter_pattern_article_code(self):
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
                full_text, selected_codes
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

    def test_matching_result_dict_codes_multiple_filter_pattern_article_code(self):
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
                full_text, selected_codes
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

    def test_get_code_refs_reversed_pattern(self):
        full_text = (
            "CSI Article LL22-7 et R314-7  Code de l'environnement L124-1 CJA L214-4"
        )

        results = [
            n for n in (get_code_refs(full_text, "code_article", selected_codes=None))
        ]
        assert len(results) == 3, results

    def test_get_code_refs_reversed_pattern_001(self):
        full_text = "Comme on peut le voir dans CSI Article LL22-7 et R314-7  Code de l'environnement L124-1 CJA L214-4"

        results = [
            n for n in (get_code_refs(full_text, "code_article", selected_codes=None))
        ]
        assert len(results) == 3, results

    def test_matching_result_dict_codes_no_filter_reversed_pattern_paragraphs(self):
        # NO CPCE ref dans le doc
        code_reference_test = CODE_REFERENCE
        # del code_reference_test["CPCE"]

        chunk = "C’est la solution posée dans le Code civil article 1120"
        for item in get_matching_result_item(chunk, None):
            assert item == ("Code civil", "1120"), item
        for code, item in get_matching_results_dict(chunk):
            assert code == "Code civil"
            assert item == "1120"

        multi_chunk = "C’est la solution posée dans le Code civil article 1120 et de C. civ. art. 2288"
        for i, item in enumerate(get_matching_result_item(multi_chunk, None)):
            if i == 0:
                assert item == ("Code civil", "1120"), item
            else:
                assert item == ("Code civil", "2288"), item

    def test_matching_result_dict_codes_no_filter_pattern_code_article(self):

        code_reference_test_002 = CODE_REFERENCE
        file_paths = ["testnew.odt", "testnew.pdf", "testnew.docx"]
        for file_path in file_paths:

            tmp_abspath = archive_test_file(file_path)
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            full_text = parse_doc(abspath)
            restored_abspath = restore_test_file(file_path)
            results_dict = get_matching_results_dict(full_text, None)
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
            