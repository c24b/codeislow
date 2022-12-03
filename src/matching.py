#!/usr/bin/env python3
# filename: matching.py
"""
The matching module

Ce module permet la detection des articles du code de droit français

"""
from logs import logger
import re

from code_references import (
    get_selected_codes_regex,
    get_code_full_name_from_short_code,
    CODE_REFERENCE
)

ARTICLE_REGEX = r"(?P<art>(Articles?|Art\.))"
#ARTICLE_NUM = r"(?P<ref>(L|A|R|D)?\.?\s?\d{1,5}(-\d{1,5})?(-\d{1,5})?(-\d{1,5})?(-\d{1,5})?.*?(\d{1,5})?)"

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

    
    if pattern not in ["article_code", "code_article"]:
        raise ValueError(
            "Wrong pattern name: choose between 'article_code' or 'code_article'"
        )
    
    code_regex = get_selected_codes_regex(selected_codes)
    assert code_regex is not None or code_regex != ""

    #default pattern is article_code
    if pattern == "article_code":
        # pattern_r = f"{ARTICLE_REGEX}.*?{ARTICLE_NUM}.*?d(u|e).*?{code_regex}"
        pattern_r = f"{ARTICLE_REGEX}\s?(?P<ref>.*)du\s{code_regex}"
        return pattern_r
    if pattern == "code_article":
        pattern_r = f"{code_regex}.*?{ARTICLE_REGEX}(?P<ref>.*?\d)$"
        return pattern_r

        
#@logger
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
        # remove last caret 2232- => 2232
        ref = re.sub(r"(^-|-$)", "", ref)
        # ref = re.sub(r"-$", "", ref)
        print(">>>", ref)
        
        # remove if more than one letter
        del_add_letter = [i for i, c in enumerate(ref) if c in ["L", "A", "R", "D"]]
        if len(del_add_letter) > 1:
            list_ref = list(ref)
            for c in del_add_letter[0:-1]:
                list_ref.pop(c)
            ref = "".join(list_ref)    
        special_ref = ref.split("-", 1)
        print(special_ref)
        if special_ref[0] in ["L", "A", "R", "D"]:
            ref = "".join(special_ref)    

        if ref not in ["", " "]:
            normalized_refs.append(ref)

    return normalized_refs

def get_code_refs(full_text, selected_codes=None, pattern_format="article_code"):
    # Force to detect every code in case an unselected code is present
    regex_pattern = re.compile(switch_pattern(None, pattern_format), re.I)
    
    if selected_codes is None:
        selected_codes = CODE_REFERENCE.keys()
    for i, match in enumerate(re.finditer(regex_pattern, full_text)):
        needle = match.groupdict()
        qualified_needle = {
            key: value for key, value in needle.items() if value is not None
        }
        msg = f"#{i+1}\t{qualified_needle}"
        # logging.debug(msg)
        # get the code shortname based on regex group name <code>
        code = [k for k in qualified_needle.keys() if k not in ["ref", "art"]][0]
        
        if code in selected_codes:
            code_name = get_code_full_name_from_short_code(code)
            match = match.group("ref").strip()
            if match != "":
                
                yield [[code, code_name, art_num] for art_num in normalize_references(match)]
                    
                    

    



#@logger
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
            code_found[(short_code, code_name)] = normalize_references(ref)
        else:
            # append article references to existing list
            code_found[(short_code, code_name)].extend(normalize_references(ref))
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
        
    # print(results)
    
    # for code_refs in get_code_refs(
    #     full_text, selected_codes, pattern_format
    # ):
    #     for code_ref in code_refs:
    #         short_code, ref = code_ref
    #         code_name = get_code_full_name_from_short_code(short_code)
    #         yield (short_code, code_name, ref)
