#!/usr/bin/env python3
# filename: matching.py
"""
The matching module

Ce module permet la detection des articles du code de droit français

"""
# from logs import logger
import re
from code_references import (
    get_selected_codes_regex,
    get_code_full_name_from_short_code,
    CODE_REFERENCE
)

ARTICLE_REGEX = r"(?P<art>(Articles?|Art\.))"

ARTICLE_NUM = r"(?P<num>((L|A|R|D)?(\.|\s|\.\s)?\d{1,4}(-\d{1,3})?)(-\d{1,2})?)"

BLACKLIST = ["convention", "loi", "page", ".com", "p.", "www", "http", "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août"," septembre", "octobre", "novembre", "décembre"]

ART_NUM_REGEX = re.compile(ARTICLE_NUM)
CODE_REGEX = get_selected_codes_regex(None)

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
    #keep the possibility to generate regexp for only selected codes
    code_regex = get_selected_codes_regex(None)

    if pattern not in ["article_code", "code_article"]:
        raise ValueError(
            "Wrong pattern name: choose between 'article_code' or 'code_article'"
        )
    if pattern == "article_code":
        return re.compile(ARTICLE_REGEX+'(?P<ref>.*?)'+code_regex, re.I)
    else:
        return re.compile(code_regex+".*?"+ARTICLE_REGEX+r"(?P<ref>.*?((L|A|R|D)?(\.|\s|\.\s))?\d{1,4}(-\d{1,3})?(-\d{1,2})?)", re.I)

        
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
        # remove first and last caret -2323 or 2323- => 2323
        ref = re.sub(r"(^-|-$)", "", ref)
        # remove if more than one letter
        del_add_letter = [i for i, c in enumerate(ref) if c in ["L", "A", "R", "D"]]
        if len(del_add_letter) > 1:
            list_ref = list(ref)
            for c in del_add_letter[0:-1]:
                list_ref.pop(c)
            ref = "".join(list_ref)    
        special_ref = ref.split("-", 1)
        if special_ref[0] in ["L", "A", "R", "D"]:
            ref = "".join(special_ref)    
        if ref not in ["", " "]:
            normalized_refs.append(ref)

    return normalized_refs

def get_code_refs(full_text, selected_codes=None, pattern_format="article_code"):
    # Force to detect every code in case an unselected code is present
    if pattern_format not in ["article_code", "code_article"]:
        raise ValueError(
            "Wrong pattern name: choose between 'article_code' or 'code_article'"
        )
    article_pattern = switch_pattern(None, pattern_format)
    if selected_codes is None:
        selected_codes =  list(CODE_REFERENCE)
    not_found_codes = {}
    for match in re.finditer(article_pattern, full_text):
        needle = match.groupdict()
            
        qualified_needle = {
            key: value for key, value in needle.items() if value is not None
        }
        codes = {k:v for k,v in qualified_needle.items() if k not in ["ref", "art"]}
        short_code = list(codes.keys())[0]
        if needle["ref"] is None:
            print("NOT_FOUND", codes)
            not_found_codes.update(codes)
        else:
            if short_code in selected_codes:
                references = qualified_needle["ref"].strip()
                for ref in re.finditer(ART_NUM_REGEX, references):
                    if ref is not None:
                        for art_nb in normalize_references(ref.group('num')):
                            
                            yield [short_code, get_code_full_name_from_short_code(short_code), art_nb]
              
    # DANS LE CAS où la regex n'est pas passée
    # SPLITTER le texte en autant de morceaux que de codes trouvés
    # print(not_found_codes)
    # if len(not_found_codes) > 0 :

    #     codes_fulltext = not_found_codes.values()
    #     print(codes_fulltext)
    #     codes_shortcode = not_found_codes.keys()
    #     split_text_by_codes = []
    #     original_text = full_text
    #     for i,code_text in enumerate(codes_fulltext):
    #         first, second = original_text.split(code_text,1)
    #         if pattern_format == "article_code":
    #             split_text_by_codes.append(first)
    #             original_text = second
    #         else:
    #             if i != 0:
    #                 split_text_by_codes.append(first)
    #             if i+1 == len(codes):
    #                 split_text_by_codes.append(second)
    #             else:
    #                 original_text = second
    #     for short_code, chunk in zip(codes_shortcode, split_text_by_codes):
    #         if short_code in selected_codes:
    #             print(chunk)
    #             for ref in re.finditer(ART_NUM_REGEX, chunk):
    #                 if ref is not None:
    #                     print(ref.group("num"))
    #                     for art_nb in normalize_references(ref.group('num')):
    #                         yield [short_code, get_code_full_name_from_short_code(short_code), art_nb]
def get_matching_results_dict(
    full_text, selected_codes=None, pattern_format="article_code"
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
    
    code_found = {}
    # normalisation
    
    for code_refs in get_code_refs(
        full_text, selected_codes, pattern_format
    ):
        short_code, code_name, ref = code_refs
        if short_code not in code_found:
            # append article references
            code_found[short_code] = [ref]
        else:
            # append article references to existing list
            code_found[short_code].append(ref)
    return code_found

#@logger
def get_matching_result_item(
    full_text, selected_codes=None, pattern_format="article_code"
):
    """
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
    yield from get_code_refs(full_text,selected_codes, pattern_format)
        
    