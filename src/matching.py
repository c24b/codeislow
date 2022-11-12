#!/usr/bin/env python3
# filename: matching.py
"""
The matching module

Ce module permet la detection des articles du code de droit français

"""
import logging
import re

from code_references import filter_code_regex, filter_code_reference, get_code_full_name_from_short_code

ARTICLE_REGEX = r"(?P<art>(Articles?|Art\.))"

ARTICLE_REF = r"\d+"
ARTICLE_NUM = r"(?P<ref>.*?\d{1,4}(.?-\d{1,4}.?)?)"

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
        return re.compile(f"{code_regex}", flags=re.I), re.compile(f"({ARTICLE_REGEX})"+r"?.*?(?P<ref>.*\d*)", flags=re.I)
        
def get_code_refs_reversed_pattern(full_text, pattern_regex, selected_codes):
    code_regex, article_regex = pattern_regex
    # code_regex = filter_code_regex(None)
    # code_regex = re.compile(f"{code_regex}", flags=re.I)
    # article_regex = re.compile(f"{ARTICLE_REGEX}.*?(?P<ref>.*\d*)", flags=re.I)
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
    for i,item in enumerate(code_name_list):
        chunk0, chunk1 = full_text.split(item,1)
        if i != 0:
            text_by_codes.append(chunk0)
        full_text = chunk1
        if i+1 == len(code_name_list):
            text_by_codes.append(chunk1) 
    for code, chunk_text in zip(code_list,text_by_codes): 
        for match in re.finditer(article_regex, chunk_text):
            if code in list(selected_codes):
                match = match.group("ref").strip()
                if match != '':
                    yield code, get_code_full_name_from_short_code(code), match
    
def get_code_refs_classical_pattern(full_text:str, article_pattern:str, selected_codes:list):
    
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
            if match != '':
                yield code, get_code_full_name_from_short_code(code), match
            
def get_code_refs(full_text, pattern_format, selected_codes):
    #Force to detect every article of every code
    article_pattern = switch_pattern(None, pattern_format)
    if pattern_format == "article_code":
        return get_code_refs_classical_pattern(full_text, article_pattern, selected_codes)
    else:
        return get_code_refs_reversed_pattern(full_text, article_pattern, selected_codes)

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
        ref = re.sub(r'-{2,}', "", ref)
        #remove first caret -2323 => 2323
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
    full_text = re.sub(r"\s{2,}|\r{1,}|\n{1,}|\t{1,}|\xa0{1,}", " ", " ".join(full_text))
    for short_code, code, ref in get_code_refs(full_text, pattern_format,selected_codes):
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
    code_short_name:str

    article_number:str
    """
    selected_codes = filter_code_reference(selected_shortcodes)
    
    full_text = re.sub(r"\s{2,}|\r{1,}|\n{1,}|\t{1,}|\xa0{1,}", " ", " ".join(full_text))
    for short_code, code, refs in get_code_refs(full_text, pattern_format,selected_codes):
        for ref in normalize_references(refs):
            yield (short_code, code, ref)
    
