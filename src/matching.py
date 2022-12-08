#!/usr/bin/env python3
# filename: matching.py
"""
The matching module

Ce module permet la detection des articles du code de droit français

"""
import logging
import re

from code_references import (
    get_selected_codes_regex,
    get_code_full_name_from_short_code,
    CODE_REFERENCE
)

ARTICLE_REGEX = r"(?P<art>(Articles?|Art\.))"


ARTICLE_NUM = r"(?P<num>((L|A|R|D)?(\.|\s|\.\s)?\d{1,4}(-\d{1,3})?)(-\d{1,2})?)"

BLACKLIST = ["convention", "loi", "page", ".com", "p.", "www", "http", "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août"," septembre", "octobre", "novembre", "décembre"]


def switch_pattern(selected_codes=None, pattern="article_code"):
    """
    Build pattern recognition using pattern short code switch

    Arguments
    ---------
    selected_codes: array
        a list of short codes to select. Default to None
    pattern: str
        a string article_code or code_article. Default to article_code
    Returns
    ---------
    regex_pattern: str
        a compiled regex pattern
    Raise
    --------
    ValueError:
        pattern name is wrong
    """

    code_regex = get_selected_codes_regex(None)

    if pattern not in ["article_code", "code_article"]:
        raise ValueError(
            "Wrong pattern name: choose between 'article_code' or 'code_article'"
        )
    # if pattern == "article_code":
    #     return re.compile(f"{ARTICLE_REGEX}(?P<ref>.*?){code_regex}", flags=re.I)
    # else:
    #     return re.compile(f"{code_regex}", flags=re.I), re.compile(
    #         f"({ARTICLE_REGEX})" + r"?.*?(?P<ref>.*\d*)", flags=re.I
    #     )
    if pattern == "article_code":
        return re.compile(ARTICLE_REGEX+'(?P<ref>.*?)'+code_regex, re.I)
    else:
        return re.compile(code_regex+".*?"+ARTICLE_REGEX+r"(?P<ref>.*?((L|A|R|D)?(\.|\s|\.\s))?\d{1,4}(-\d{1,3})?(-\d{1,2})?)", re.I)
    
def get_code_refs(full_text, pattern_format, selected_codes):
    # Force to detect every article of every code
    article_pattern = switch_pattern(None, pattern_format)
    for i, match in enumerate(re.finditer(article_pattern, full_text)):
        needle = match.groupdict()
        qualified_needle = {
            key: value for key, value in needle.items() if value is not None
        }
        # msg = f"#{i+1}\t{qualified_needle}"
        # print(msg)
        # logging.debug(msg)
        # get the code shortname based on regex group name <code>
        code = [k for k in qualified_needle.keys() if k not in ["ref", "art"]][0]
        if code in selected_codes:
            references = match.group("ref").strip()
            for ref in re.finditer(re.compile(ARTICLE_NUM), references):
                if ref is not None:
                    for art_num in normalize_references(ref): 
                        yield code, get_code_full_name_from_short_code(code), ref



def normalize_references(ref):
    # split multiple articles of a same code
    refs = [
        n
        for n in re.split(r"(\set\s|,\s|\sdu)", ref)
        if n not in [" et ", ", ", " du", " ", ""]
    ]
    # normalize articles to remove dots, spaces, caret and 'alinea'
    # with keeping only accepted caracters for article
    # i.e. numbers, (L|A|R|D) and caret
    # exemple: 1224 du => Non 298 al 32 => Non R-288 => oui A-24-14=> oui
    refs = [
        "-".join(
            [
                r
                for r in re.split(r"\s|\.|-", ref)
                if r not in [" ", "", "al", "alinea", "alinéa"]
            ]
        )
        for ref in refs
    ]

    normalized_refs = []
    for ref in refs:
        ref = "".join([r for r in ref if r.isdigit() or r in ["L", "A", "R", "D", "-"]])
        ref = re.sub(r"-{2,}", "", ref)
        # remove first caret -2323 => 2323
        if ref.endswith("-"):
            ref = ref[:-1]
        if ref.startswith("-"):
            ref = ref[1:]
        # remove caret separating article nb between first letter
        # exemple: L-248-1 = > L248-1
        special_ref = ref.split("-", 1)
        if special_ref[0] in ["L", "A", "R", "D"]:
            normalized_refs.append("".join(special_ref))

        else:
            if ref not in ["", " "]:
                normalized_refs.append(ref)
    return normalized_refs


def get_matching_results_dict(
    full_text, selected_short_codes=[], pattern_format="article_code"
):
    """
    Une fonction qui renvoie un dictionnaire de resultats:
    trié par code (version abbréviée) avec la liste des articles
    détectés lui appartenant.

    Arguments
    ----------
    full_text: str
        a string of the full document normalized
    pattern_format: str
        a string representing the pattern format article_code or code_article. Defaut to article_code

    Returns
    ----------
    code_found: dict
        a dict compose of short version of code as key and list of the detected articles references  as values {code: [art_ref, art_ref2, ... ]}
    """
    if selected_codes is None:
        selected_codes = CODE_REFERENCES

    code_found = {}
    # normalisation
    full_text = re.sub(
        r"\s{2,}|\r{1,}|\n{1,}|\t{1,}|\xa0{1,}", " ", " ".join(full_text)
    )
    for short_code, code, ref in get_code_refs(
        full_text, pattern_format, selected_codes
    ):
        if short_code not in code_found:
            # append article references
            code_found[short_code] = normalize_references(ref)
        else:
            # append article references to existing list
            code_found[short_code].extend(normalize_references(ref))
    return code_found


def get_matching_result_item(
    full_text, selected_codes=[], pattern_format="article_code"
):
    """ "
    Renvoie les références des articles détectés dans le texte

    Arguments
    -----------
    full_text: str
        a string of the full document normalized
    selected_shortcodes: array
        a list of selected codes in short format for filtering article detection. Default is an empty list (which stands for no filter)
    pattern_format: str
    a string representing the pattern format article_code or code_article. Defaut to article_code

    Yields
    --------
    code_short_name:str

    article_number:str
    """
    if selected_codes is None or len(selected_codes) == 0:
        selected_codes = CODE_REFERENCE

    full_text = re.sub(
        r"\s{2,}|\r{1,}|\n{1,}|\t{1,}|\xa0{1,}", " ", " ".join(full_text)
    )
    for short_code, code, refs in get_code_refs(
        full_text, pattern_format, selected_codes
    ):
        if short_code in selected_codes:
            yield (short_code, code, refs)
