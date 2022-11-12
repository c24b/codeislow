import pytest
import random
from .context import code_references
from code_references import CODE_REFERENCE, CODE_REGEX
from code_references import get_code_full_name_from_short_code
from code_references import get_short_code_from_full_name
from code_references import (
    get_long_and_short_code,
    filter_code_regex,
    filter_code_reference,
)


class TestCodeFormats:
    @pytest.mark.parametrize("input", list(CODE_REFERENCE.keys()))
    def test_short2long_code(self, input):

        assert get_code_full_name_from_short_code(input) == CODE_REFERENCE[input], (
            input,
            CODE_REFERENCE[input],
        )

    @pytest.mark.parametrize("input", list(CODE_REFERENCE.values()))
    def test_long2short_code(self, input):
        print(input)
        result = get_short_code_from_full_name(input)
        expected = [k for k, v in CODE_REFERENCE.items() if v == input][0]
        assert result == expected, (result, expected)

    @pytest.mark.parametrize("input", list(CODE_REFERENCE.keys()))
    def test_get_long_and_short_code(self, input):
        result = get_long_and_short_code(input)
        expected = (CODE_REFERENCE[input], input)
        assert expected == result, result

    def test_short_code_not_found(self):
        result = get_long_and_short_code("RGPD")
        assert result == (None, None)

    def test_long_code_not_found(self):
        result = get_short_code_from_full_name(
            "Règlement Général sur la Protection des Données"
        )
        assert result is None


class TestFilterRegexCode:
    def test_code_regex_not_found(self):
        assert filter_code_regex(["RG2A"]) is None

    def test_code_regex_match_code_ref(self):
        assert set(CODE_REFERENCE) - set(CODE_REGEX) == set()

    def test_filter_regex_empty(self):
        result = filter_code_regex([])
        expected = "({})".format("|".join(list(CODE_REGEX.values())))
        assert result == expected, result

    def test_filter_regex_unique(self):
        result = filter_code_regex(["CJA"])
        expected = CODE_REGEX["CJA"]
        assert result == expected, (result, expected)

    def test_filter_code_regex_manual(self):
        code_list = sorted(["CJA", "CPP", "CCIV"])
        result = filter_code_regex(code_list)
        expected = "({})".format("|".join([CODE_REGEX[x] for x in code_list]))
        assert result == expected, (result, expected)

    def test_filter_code_regex_random(self):
        random_code_list = sorted(random.choices(list(CODE_REFERENCE), k=5))
        result = filter_code_regex(random_code_list)
        expected = "({})".format("|".join([CODE_REGEX[c] for c in random_code_list]))
        assert result == expected, result


class TestFilterCodeReference:
    def test_filter_reference_empty(self):
        result = filter_code_reference([])
        assert result == CODE_REFERENCE

    def test_filter_reference_single(self):
        result = filter_code_reference(["CPP"])
        assert result == {"CPP": CODE_REFERENCE["CPP"]}

    def test_filter_reference_manual(self):
        code_list = sorted(["CPP", "CPEN", "CENV"])
        result = filter_code_reference(code_list)
        expected = {x: CODE_REFERENCE[x] for x in code_list}
        assert result == expected, result

    def test_filter_reference_random(self):
        random_code_list = sorted(random.choices(list(CODE_REFERENCE), k=5))
        result = filter_code_reference(random_code_list)
        expected = {k: CODE_REFERENCE[k] for k in random_code_list}
        assert result == expected, result
