#!/usr/bin/env python3
# filename: matching.py
"""
The matching module

Ce module permet la detection des articles du code de droit français

"""
from logs import logger
import re
import itertools
from code_references import (
    get_selected_codes_regex,
    get_code_full_name_from_short_code,
    CODE_REFERENCE
)

ARTICLE_REGEX = re.compile(r"(?P<art>(Articles?|Art\.))")
#ARTICLE_NUM = r"(?P<ref>(L|A|R|D)?\.?\s?\d{1,5}(-\d{1,5})?(-\d{1,5})?(-\d{1,5})?(-\d{1,5})?.*?(\d{1,5})?)"


        
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
    # but maintaining the option to build the regex
    code_regex = re.compile(get_selected_codes_regex(selected_codes), re.I)
    if pattern_format not in ["article_code", "code_article"]:
        raise ValueError(
            "Wrong pattern name: choose between 'article_code' or 'code_article'"
        )
    # Then filter codes  
    if selected_codes is None:
        selected_codes = CODE_REFERENCE.keys()
    split_text = [n for n in re.split(code_regex, full_text) if n is not None and n != ' ']
    remove_subs_dups = [g for g, _ in itertools.groupby(split_text)]
    codes_found = []
    refs_found = []
    for chunk in remove_subs_dups:
        m = re.match(code_regex, chunk) 
        if m is not None:
            needle = m.groupdict()
            qualified_needle = [
                (key,value) for key, value in needle.items() if value is not None
            ]
            code_short = qualified_needle[0][0]
            codes_found.append(code_short)
        else:
            
            refs = re.split(ARTICLE_REGEX, chunk)
            if len(refs) > 4:
                raise Exception(f"Multiple mentions of articles: {chunk}")
            else:
                refs_found.append(refs[-1])
    if len(refs_found) > len(codes_found):
        if pattern_format == "code_article":
            codes_found.insert(0,"")
        else:
            codes_found.append("")
        
    for code, ref in zip(codes_found, refs_found):
        if code != "" and ref != "":
            if code in selected_codes:
                code_name = get_code_full_name_from_short_code(code)
                for art_num in normalize_references(ref):
                    yield [code, code_name, art_num]
                

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
