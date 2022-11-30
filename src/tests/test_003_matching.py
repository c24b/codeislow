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
    switch_pattern,
    get_code_refs,
    normalize_references
)
from .test_001_parsing import restore_test_file, archive_test_file


class TestPattern:
    def test_switch_pattern_wrong_pattern(self):
        with pytest.raises(ValueError) as e:
            switch_pattern(None, "code_code")
            assert e.info_msg == "", e
   
    def test_switch_pattern_classical_pattern(self):
        # expected = "(?P<art>(Articles?|Art\.)).*?(?P<ref>(L|A|R|D)?\.?\s?\d{1,5}(-\d{1,5})?(-\d{1,5})?(-\d{1,5})?(-\d{1,5})?.*?(\d{1,5})?)((?P<CCIV>Code\scivil|C\.\s?civ\.|Code\sciv\.|civ\.|CCIV)|(?P<CPRCIV>Code\sde\sprocédure\scivile|C\.\spr\.\sciv\.|CPC)|(?P<CCOM>Code\sd(e|u)\scommerce|C\.\scom\.)|(?P<CTRAV>Code\sdu\stravail|C\.\strav\.)|(?P<CPI>Code\sde\sla\spropriété\sintellectuelle|CPI|C\.\spr\.\sint\.)|(?P<CPEN>Code\sp(é|e)nal|C\.\s?p(é|e)n\.)|(?P<CPP>Code\sde\sprocédure\spénale|CPP)|(?P<CASSUR>Code\sdes\sassurances|C\.\sassur\.)|(?P<CCONSO>Code\sde\sla\sconsommation|C\.\sconso\.)|(?P<CSI>Code\sde\slasécurité\sintérieure|CSI)|(?P<CSP>Code\sde\slasanté\spublique|C\.\ssant\.\spub\.|CSP)|(?P<CSS>Code\sde\slasécurité\ssociale|C\.\ssec\.\ssoc\.|CSS)|(?P<CESEDA>Code\sde\sl'entrée\set\sdu\sséjour\sdes\sétrangers\set\sdu\sdroit\sd'asile|CESEDA)|(?P<CGCT>Code\sgénéral\sdes\scollectivités\sterritoriales|CGCT)|(?P<CPCE>Code\sdes\spostes\set\sdes\scommunications\sélectroniques|CPCE)|(?P<CENV>Code\sde\sl'environnement|C.\senvir.|CE\.)|(?P<CJA>Code\sde\sjustice\sadministrative|CJA))"
        regex_pattern = switch_pattern(None, "article_code")
        # assert regex_pattern == expected, list(difflib.ndiff(expected, regex_pattern))
        assert regex_pattern.startswith("(?P<art>(Articles?|Art\.))")
        assert "Code" in regex_pattern, regex_pattern
        assert "Article" in regex_pattern, regex_pattern
        art_posx, art_posy = re.search("<art>", str(regex_pattern)).span(0)
        code_posx, code_posy = re.search("Code", str(regex_pattern)).span(0)
        assert (art_posx, art_posy) < (code_posx, code_posy),  ("Art:",(art_posx, art_posy), "Code:", (code_posx, code_posy))
        # assert False, re.search("Code", str(regex_pattern)).span(0)
    
    def test_switch_pattern_reversed_pattern(self):
        # expected = "((?P<CCIV>Code\scivil|C\.\s?civ\.|Code\sciv\.|civ\.|CCIV)|(?P<CPRCIV>Code\sde\sprocédure\scivile|C\.\spr\.\sciv\.|CPC)|(?P<CCOM>Code\sd(e|u)\scommerce|C\.\scom\.)|(?P<CTRAV>Code\sdu\stravail|C\.\strav\.)|(?P<CPI>Code\sde\sla\spropriété\sintellectuelle|CPI|C\.\spr\.\sint\.)|(?P<CPEN>Code\sp(é|e)nal|C\.\s?p(é|e)n\.)|(?P<CPP>Code\sde\sprocédure\spénale|CPP)|(?P<CASSUR>Code\sdes\sassurances|C\.\sassur\.)|(?P<CCONSO>Code\sde\sla\sconsommation|C\.\sconso\.)|(?P<CSI>Code\sde\slasécurité\sintérieure|CSI)|(?P<CSP>Code\sde\slasanté\spublique|C\.\ssant\.\spub\.|CSP)|(?P<CSS>Code\sde\slasécurité\ssociale|C\.\ssec\.\ssoc\.|CSS)|(?P<CESEDA>Code\sde\sl'entrée\set\sdu\sséjour\sdes\sétrangers\set\sdu\sdroit\sd'asile|CESEDA)|(?P<CGCT>Code\sgénéral\sdes\scollectivités\sterritoriales|CGCT)|(?P<CPCE>Code\sdes\spostes\set\sdes\scommunications\sélectroniques|CPCE)|(?P<CENV>Code\sde\sl'environnement|C.\senvir.|CE\.)|(?P<CJA>Code\sde\sjustice\sadministrative|CJA)).*?(?P<art>(Articles?|Art\.)).*?(?P<ref>(L|A|R|D)?\.?\s?\d{1,5}(-\d{1,5})?(-\d{1,5})?(-\d{1,5})?(-\d{1,5})?.*?(\d{1,5})?)"
        regex_pattern = switch_pattern(None, "code_article")
        # assert regex_pattern == expected, list(difflib.ndiff(expected, regex_pattern))
        assert regex_pattern.startswith("(?P<art>(Articles?|Art\.))") is False, regex_pattern
        assert "Code" in regex_pattern, regex_pattern
        assert "Article" in regex_pattern, regex_pattern
        art_posx, art_posy = re.search("<art>", regex_pattern).span(0)
        code_posx, code_posy = re.search("Code", regex_pattern).span(0)
        assert (art_posx, art_posy) > (code_posx, code_posy),  ("Art:",(art_posx, art_posy), "Code:",(code_posx, code_posy))

class TestMatch:
    @pytest.mark.parametrize(
        "input_expected",[
            (
                '''C’est elle qui crée le Code civil article 9.''',
                ["CCIV", "9"]
            ),
            (
                "C’est pourquoi un tel comportement a été incriminé dans le code pénal à l'article 226-4-1",
                ["CPEN", "226-4-1"]    
            ),
            (
                "Code des Assurances, articles 29 et 33",
                
                ["CASSUR", "29 et 33"],
            ),
            (
            "C. Assur. L. 385-2, R. 343-4 et A421-13 du",
            ["CASSUR", "L. 385-2, R. 343-4 et A421-13"]
            )

        ]
    )
    def test_match_reversed_pattern(self, input_expected):
        input,expected = input_expected 
        regex_pattern = re.compile(switch_pattern(None, "code_article"), re.I)
        for i, match in enumerate(re.finditer(regex_pattern, input)):
            needle = match.groupdict()
            qualified_needle = {
                key: value for key, value in needle.items() if value is not None
            }
            msg = f"#{i+1}\t{qualified_needle}"
            code = [k for k in qualified_needle.keys() if k not in ["ref", "art"]][0]
            match = match.group("ref").strip()
            assert code == expected[0], qualified_needle
            assert match == expected[1], qualified_needle
    
    @pytest.mark.parametrize(
        "input_expected",[
            (
                '''C’est elle qui crée l’article 9 du Code civil.''',
                ["CCIV", "9"]
            ),
            (
                "C’est pourquoi un tel comportement a été incriminé à l’article 226-4-1 du Code pénal ",
                ["CPEN", "226-4-1"]    
            ),
            (
                "les articles 29 et 33 du Code des Assurances",
            
                    ["CASSUR", "29 et 33"]
            ),
            (
                "Art. L. 385-2, R. 343-4 et A421-13 du C. assur.",
                ["CASSUR", "L. 385-2, R. 343-4 et A421-13"]
            )

        ]
    )
    def test_match_classical_pattern(self, input_expected):
        input,expected = input_expected 
        regex_pattern = re.compile(switch_pattern(None, "article_code"), re.I)
        for i, match in enumerate(re.finditer(regex_pattern, input)):
            needle = match.groupdict()
            qualified_needle = {
                key: value for key, value in needle.items() if value is not None
            }
            msg = f"#{i+1}\t{qualified_needle}"
            code = [k for k in qualified_needle.keys() if k not in ["ref", "art"]][0]
            match = match.group("ref").strip()
            assert code == expected[0], msg
            assert match == expected[1], match

class TestNormalize:
    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "238-4 al. 2",
                ['238-4-2'],
            ),
            (
                "238-4 alinéa 2",
                ['238-4-2'],
            ),
            (
                "2-3-4-5-6 alinéa 7 ",
                ["2-3-4-5-6-7"],
            ),
            (
                "R2-3-4", 
                ["R2-3-4"]
            ),
            (
                "\n-\n L.278",
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
            (
                "L. 112-3 al. 2",
                ["L112-3-2"]
            ),
            (
                "L 122-1",
                ["L122-1"]
            )
        ],
    )
    def test_normalize_article(self, input_expected):
        input, expected = input_expected
        results = normalize_references(input)
        assert results == expected, (results, expected)




#         "input_expected",
#         [
class TestTextGetRef:
    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "Comme il est mentionné dans le code de la consommation article 238-4 alinéa 2.",
                ["CCONSO", "238-4"],
            ),
            (
                "Comme il est mentionné dans  le C.conso. art.238-4 alinéa 2  qui blablabla",
                ["CCONSO", "238-4"],
            ),
            (
                "Code de l'Environnement Art. 2-3-4",
                ["CENV", "2-3-4"],
            ),
            ("CE. Art. R2-3-4", ["CENV", "R2-3-4"]),
            ("\n-\n  cjaaa article L.278 ", ["CJA", "L278"]),
            (
                "C. assur. Art. L. 385-2, R. 343-4 et A421-13",
                [
                    ["CASSUR", "L385-2"],
                    ["CASSUR", "R343-4"],
                    ["CASSUR", "A421-13"],
                ],
            ),
                        
        ],
    )
    def test_text_refs_pattern_code_article(self, input_expected):
        input, expected = input_expected
        for items in get_code_refs(input, selected_codes=None, pattern_format="code_article"):
            assert list(items) == expected, (items, expected)
    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "Comme il est mentionné dans l'article 238-4 alinéa 2 du code de la consommation .",
                ["CCONSO", "238-4"],
            ),
            (
                "Comme il est mentionné dans l'art.238-4 alinéa 2 du C.conso.",
                ["CCONSO", "238-4"],
            ),
            (
                "Art. 2-3-4 du Code de l'Environnement",
                ["CCONSO", "2-3-4"],
            ),
            (
                "Art. R2-3-4 du CE.", 
                ["CENV", "R2-3-4"]
            ),
            (
                "\n-\n article L.278 du cjaaa",
                ["CJA", "L278"],
            ),
            (
                "Art. L. 385-2, R. 343-4 et A421-13 du C. assur. ",
                [
                    ["CASSUR", "L385-2"],
                    ["CASSUR", "R343-4"],
                    ["CASSUR", "A421-13"],
                ],
            ),
            (
                "Art. L. 112-3 al. 2 CPI.",
                ["CPI", "L112-3"]
            ),
            (
                "La Commission des clauses abusives rappelle « qu’un certain nombre de conditions générales de vente prévoient la possibilité pour le vendeur de refuser au consommateur, pour quelque raison que ce soit, la possibilité de confirmer l’acceptation de l’offre ; que ces clauses qui contreviennent à l’article L 122-1 du code de la consommation, sont illicites »",
                ["CCONSO","L122-1"]
            )
        ]
    )
    def test_text_refs_pattern_article_code(self, input_expected):
        input, expected = input_expected
        for items in get_code_refs(input, selected_codes=None, pattern_format="code_article"):
            assert list(items) == expected, (items, expected)
            
class TestTextMatchingIterator:
    @pytest.mark.parametrize(
        "input_expected",
        [
            (
                "Comme il est mentionné dans le code de la consommation article 238-4 alinéa 2.",
                ["Code de la consommation", "238-4"],
            ),
            (
                "Comme il est mentionné dans  le C.conso. art.238-4 alinéa 2  qui blablabla",
                ["Code de la consommation", "238-4"],
            ),
            (
                "Code de l'Environnement Art. 2-3-4",
                ["Code de l'environnement", "2-3-4"],
            ),
            ("CE. Art. R2-3-4", ["Code de l'environnement", "R2-3-4"]),
            ("\n-\n  cjaaa article L.278 ", ["Code de justice administrative", "L278"]),
            (
                "C. assur. Art. L. 385-2, R. 343-4 et A421-13",
                [
                    ["Code des assurances", "L385-2"],
                    ["Code des assurances", "R343-4"],
                    ["Code des assurances", "A421-13"],
                ],
            ),
        ],
    )
    def test_text_pattern_code_article(self, input_expected):
        input, expected = input_expected
        
        for item in get_matching_result_item(input, None, "code_article"):
            
            assert item == expected, (item,input)
    
    def test_text_pattern_code_article_ref1(self):
        full_text = (
            "CSI Article LL22-7 et R314-7  Code de l'environnement L124-1 CJA L214-4"
        )

        results = [
            n for n in (get_code_refs(full_text, None, "code_article"))
        ]
        assert len(results) == 3, results

    def test_text_pattern_code_article_refx(self):
        full_text = "Comme on peut le voir dans CSI Article LL22-7 et R314-7  Code de l'environnement L124-1 CJA L214-4"

        results = [
            n for n in (get_code_refs(full_text, None, "code_article" ))
        ]
        assert len(results) == 3, results

    def test_text_pattern_code_article_ref1x(self):
        # NO CPCE ref dans le doc
        code_reference_test = CODE_REFERENCE
        # del code_reference_test["CPCE"]

        chunk = "C’est la solution posée dans le Code civil article 1120"
        for item in get_matching_result_item(chunk):
            assert item == ("Code civil", "1120"), item
        for code, item in get_matching_results_dict(chunk):
            assert code == "Code civil"
            assert item == "1120"

        multi_chunk = "C’est la solution posée dans le Code civil article 1120 et de C. civ. art. 2288"
        for i, item in enumerate(get_matching_result_item(multi_chunk)):
            if i == 0:
                assert item == ("Code civil", "1120"), item
            else:
                assert item == ("Code civil", "2288"), item

class TestDocMatchingIterator:
    
    def test_doc_pattern_article_code(self):
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
            results_dict = get_matching_results_dict(full_text, None, "article_code")

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
        abspath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), file_path
        )
        full_text = parse_doc(abspath)
        restored_abspath = restore_test_file(file_path)
        
        results_dict = get_matching_results_dict(full_text, None, "article_code")
        assert sorted(results_dict) == sorted(['CASSUR', 'CENV', 'CCIV', 'CSS', 'CPEN', 'CPI', 'CPP', 'CCONSO', 'CTRAV', 'CPRCIV', 'CSP', 'CCOM']), results_dict
        assert False, results_dict["CASSUR"]
        
    def test_doc_code_article(self):
        file_path = "HDR_NETTER_V1_07.odt"
        tmp_abspath = archive_test_file(file_path)
        abspath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), file_path
        )
        full_text = parse_doc(abspath)
        restored_abspath = restore_test_file(file_path)
        
        results_dict = get_matching_results_dict(full_text, None, "code_article")
        assert sorted(results_dict) == sorted(['CASSUR', 'CENV', 'CCIV', 'CSS', 'CPEN', 'CPI', 'CPP', 'CCONSO', 'CTRAV', 'CPRCIV', 'CSP', 'CCOM']), results_dict
        assert False, results_dict.items()

