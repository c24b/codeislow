#!/usr/bin/env python3
# filename: matching.py
"""
The matching module

Ce module permet la detection des articles du code de droit français

"""
import logging
import re

from code_references import (
    filter_code_regex,
    filter_code_reference,
    get_code_full_name_from_short_code,
)

ARTICLE_REGEX = r"(?P<art>(Articles?|Art\.))"
COMPILED_ARTICLE = re.compile(ARTICLE_REGEX, re.I)
# ARTICLE_REF = r"\d+"
# ARTICLE_NUM = r"(?P<ref>.*?\d{1,4}(.?-\d{1,4}.?)?)"


def detect_format_pattern(full_text):
    """
    Détecter le format des références juridiques: article XXX du code YYY ou code YYY article XXX

    Arguments
    ---------
    full_text: str
        le texte du document à analyser
    Returns
    -------
    format_pattern: str
        le type de format des références juridiques: code_article ou article_code
    """

    split_text = re.split(COMPILED_ARTICLE, full_text)
    code_regex = filter_code_regex(None)
    if re.search(re.compile(f"{code_regex}", flags=re.I), split_text[0]):

        return "code_article"
    else:
        return "article_code"


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

    code_regex = filter_code_regex(None)

    if pattern not in ["article_code", "code_article"]:
        raise ValueError(
            "Wrong pattern name: choose between 'article_code' or 'code_article'"
        )
    if pattern == "article_code":
        return re.compile(f"{ARTICLE_REGEX}(?P<ref>.*?){code_regex}", flags=re.I)
    else:
        return re.compile(f"{code_regex}", flags=re.I), re.compile(
            f"({ARTICLE_REGEX})" + r"?.*?(?P<ref>.*\d*)", flags=re.I
        )

def get_code_refs(full_text, pattern_format, selected_codes):
    """
    Fonction qui en fonction du format de références 
    et des codes à detecter renvoie le code (abbréviation), 
    le nom complet du code et la référence de l'article
    
    Arguments
    =========
    full_text: str
        le texte complet du document
    pattern_format: str
        le format de références article code ou code article
    select_codes: list
        liste des codes à detecter
    Yields
    ======
        code: str
            l'abbréviation du code
        long_code: str
            le nom complet du code
        ref: le numéro de l'article
    """
    # Force to detect every code
    
    article_pattern = switch_pattern(None, pattern_format)

    if article_pattern == "article_code":
        return get_code_refs_article_code(full_text,article_pattern, selected_codes)
    else:
        print(len(article_pattern))
        return get_code_refs_code_article(full_text,article_pattern, selected_codes)

def get_code_refs_code_article(full_text, pattern_regex, selected_codes):
    '''
    Detection des articles selon le motif code article 
    '''
    code_regex, article_regex = pattern_regex
    selected_codes = filter_code_reference(selected_codes)
    code_list = []
    code_name_list = []
    for i, match in enumerate(re.finditer(code_regex, full_text)):
        needle = match.groupdict()
        assert needle is not None, needle
        for key, value in needle.items():
            if value is not None and key in list(selected_codes):
                code_list.append(key)
                code_name_list.append(value)

    text_by_codes = []
    for i, item in enumerate(code_name_list):
        chunk0, chunk1 = full_text.split(item, 1)
        if i != 0:
            text_by_codes.append(chunk0)
        full_text = chunk1
        if i + 1 == len(code_name_list):
            text_by_codes.append(chunk1)
    for code, chunk_text in zip(code_list, text_by_codes):
        long_code = get_code_full_name_from_short_code(code)
        for match in re.finditer(article_regex, chunk_text):
            if code in list(selected_codes):
                art_num = match.group("ref").strip()
                if art_num != "":
                    for art_nb in normalize_references(art_num):
                        yield code, long_code, art_nb


def get_code_refs_article_code(
    full_text: str, article_pattern: str, selected_codes: list
):

    for i, match in enumerate(re.finditer(article_pattern, full_text)):
        needle = match.groupdict()
        qualified_needle = {
            key: value for key, value in needle.items() if value is not None
        }
        # msg = f"#{i+1}\t{qualified_needle}"
        # print(msg)
        # logging.debug(msg)
        # get the code shortname based on regex group name (P?<code>)
        code = [k for k in qualified_needle.keys() if k not in ["ref", "art"]][0]
        if code in selected_codes:
            long_code = get_code_full_name_from_short_code(code)
            art_num = match.group("ref").strip()
            if art_num != "":
                for art_nb in normalize_references(art_num):
                    yield code, long_code, art_nb
                

   

def normalize_references(ref: str) -> list:
    """
    Normaliser les références aux articles: nettoyer,
    supprimer les mentions aux alineas,
    séparer les mentions à plusieurs articles,
    supprimer les tirets en trop, en double, en début ou en fin
    ou en séparation entre une lettre et un nombre
    supprimer les lettres différentes de L,A,R ou D
    supprimer toutes celles qui ne sont pas en 1ere position

    Arguments:
    =========
    ref: string
        une chaine de caractère qui contient une ou plusieurs références
    Returns:
    =======
    normalized_references: list
        une liste contenant les références aux articles mentionnés dans le text
    """
    if ref == "" or ref is None:
        return None
    normalized_refs = []
    # remove article mention just in case
    clean_ref = re.sub(COMPILED_ARTICLE, "", ref)
    # re.sub(COMPILED_ARTICLE, ref)
    clean_refs = re.split(r"\s?(al\.|alin(e|é)a)\s?", clean_ref)
    ref = clean_refs[0]
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

    for ref in refs:
        ref = "".join([r for r in ref if r.isdigit() or r in ["L", "A", "R", "D", "-"]])
        ref = re.sub(r"-{2,}", "", ref).strip()
        if ref == "":
            continue
        if ref.startswith("-"):
            ref = ref[1:]
        # remove first caret -2323 => 2323
        if ref.startswith("-"):
            ref = ref[1:]
        if ref.endswith("-"):
            ref = ref[:-1]
        # remove if last is not a digit
        if not ref[-1].isdigit():
            ref = ref[:-1]
        # remove first if more than one letter at the beginning
        if not ref[0].isdigit() and ref[1] in ["L", "A", "R", "D"]:
            ref = ref[1:]
        # remove caret separating article nb between first letter
        # exemple: L-248-1 = > L248-1
        special_ref = ref.split("-", 1)
        if special_ref[0] in ["L", "A", "R", "D"]:
            ref = "".join(special_ref)
        if ref not in ["", " "]:
            normalized_refs.append(ref)
    return normalized_refs


def get_matching_results_dict(
    full_text, selected_short_codes=[], pattern_format=None
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
    selected_codes = filter_code_reference(selected_short_codes)
    if pattern_format is None:
        pattern_format = detect_format_pattern(full_text)
    code_found = {}
    for short_code, code, ref in get_code_refs(
        full_text, pattern_format, selected_codes
    ):
        if short_code not in code_found:
            # append article references
            code_found[short_code] = [ref]
        else:
            # append article references to existing list
            code_found[short_code].extend(ref)
    return code_found


def get_matching_result_item(
    full_text, selected_shortcodes=None, pattern_format=None):
    """ 
    Renvoie les références des articles détectés dans le texte sous forme de générateur

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
        Abbréviation du code
    code:str
        Nom complet du code
    article_numbers: list
        Liste des numéros d'articles
    """
    selected_codes = filter_code_reference(selected_shortcodes)
    if pattern_format is None:
        pattern_format = detect_format_pattern(full_text)
    for short_code, code, ref in get_code_refs(
        full_text, pattern_format, selected_codes
    ):
        yield(short_code, code, ref)