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
    build_code_regex,
    filter_code_reference,
    get_code_full_name_from_short_code,
)

ARTICLE_REGEX = r"(?P<art>(Articles?|Art\.))"
COMPILED_ARTICLE = re.compile(ARTICLE_REGEX, re.I)

ARTICLE_NUM = r"(?P<ref>.*?(L|A|R|D)?.?\d{1,4}(.?-\d{1,4}.?)?(-\d{1,4}.?))"

def switch_pattern(pattern="article_code"):
    """
    Build pattern recognition using pattern short code switch

    Arguments
    ---------
    pattern: str
        a string article_code or code_article. Default to article_code
    Returns
    ---------
    regex_pattern: str
        a compiled regex pattern or a tuple of regex pattern
    Raise
    --------
    ValueError:
        pattern name is wrong
    """
    if pattern not in ["article_code", "code_article"]:
        raise ValueError(
            "Wrong pattern name: choose between 'article_code' or 'code_article'"
        )
    # Pas de filtre en fonction des codes selectionnés
    # si un code n'est pas sélectionné mais présent décalle l'attribution des articles
    code_regex = filter_code_regex(None)
    if pattern == "article_code":
        return re.compile(f"{ARTICLE_REGEX}(?P<ref>.*?){code_regex}", flags=re.I)
    else:
        return re.compile(f"{code_regex}", flags=re.I), re.compile(
            f"({ARTICLE_REGEX})" + r"(?P<ref>(L|A|R|D)?.*?\d*)", flags=re.I
        )

def detect_pattern(full_text):
    """
    Detecter le format des références
    
    Arguments
    ==========
    full_text: str
        Le texte sous forme de chaine de caractère

    Returns
    ========
    pattern 
    """
    # code_regex = build_code_regex(None)
    code_regex = filter_code_regex(None)
    print(code_regex)
    # split_text = re.split(code_regex, full_text, re.I)
    split_text = re.split(f"{code_regex}", full_text, re.I)
    if re.search(COMPILED_ARTICLE, split_text[-1]):
        return "code_article"
    else:
        return "article_code"

def get_code_refs(full_text, selected_codes, pattern_format=None):
    """
    Renvoyer les references aux articles de loi des codes selectionnées à partir du texte
    selon le format des références utilisé

    Arguments
    ==========
    full_text: str
        Le texte complet 
    selected_codes: list
        Une liste de codes selectionnés si la liste est vide ou None: tous les codes
    pattern_format: str
        Le format des références aux articles article_code ou code_article s'il n'est pas défini il est autodétecté  
    
    Returns
    =======
    refs: generator
        Générateur de références
    """
    if pattern_format is None:
        pattern_format = detect_pattern(full_text)
    else:
        if pattern_format == "code_article":
            return get_code_refs_reversed_pattern(full_text, switch_pattern(pattern_format), selected_codes)
        else:
            return get_code_refs_classical_pattern(full_text, switch_pattern(pattern_format), selected_codes)

def get_code_refs_reversed_pattern(full_text, pattern_regex, selected_codes):
    """
    Renvoyer les references aux articles de loi des codes selectionnées à partir du texte
    selon le format code_article

    Arguments
    ==========
    full_text: str
        Le texte complet 
    selected_codes: list
        Une liste de codes selectionnés si la liste est vide ou None: tous les codes
    pattern_regex: tuple(str, str)
        Un tuple d'expressions régulières  
    
    Yields
    =======
    references: list
        renvoie une liste (short_code, code_name, article_number_expressions )
    """
    code_regex, article_regex = pattern_regex
    selected_codes = filter_code_reference(selected_codes)
    code_list = []
    code_name_list = []
    for i, match in enumerate(re.finditer(code_regex, full_text)):
        needle = match.groupdict()
        for key, value in needle.items():
            if value is not None:
                code_list.append(key)
                code_name_list.append(value)

    #Split into sequence text using <CODE>
    text_by_codes = []
    for i, item in enumerate(code_name_list):
        chunk0, chunk1 = full_text.split(item, 1)
        if i != 0:
            text_by_codes.append(chunk0)
        full_text = chunk1
        if i + 1 == len(code_name_list):
            text_by_codes.append(chunk1)
    #ZIP code, numero 
    for code, chunk_text in zip(code_list, text_by_codes):
        for match in re.finditer(article_regex, chunk_text):
            if code in selected_codes:
                match = match.group("ref").strip()
                if match != "":
                    yield code, get_code_full_name_from_short_code(code), match


def get_code_refs_classical_pattern(
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
        # get the code shortname based on regex group name <code>
        code = [k for k in qualified_needle.keys() if k not in ["ref", "art"]][0]
        if code in selected_codes:
            match = match.group("ref").strip()
            if match != "":
                yield code, get_code_full_name_from_short_code(code), match



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
    selected_codes = filter_code_reference(selected_short_codes)

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
    full_text, selected_shortcodes=[], pattern_format="article_code"
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
    reference: list
        Une liste composée de (code_short_name:str,long_name_code:str,article_number:str)
    """
    selected_codes = filter_code_reference(selected_shortcodes)

    for short_code, code, refs in get_code_refs(
        full_text, pattern_format, selected_codes
    ):
        for ref in normalize_references(refs):
            yield (short_code, code, ref)
