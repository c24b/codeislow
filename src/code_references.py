#!/usr/bin/env python3.8
# filename: code_references
"""
Code references module:

- Build regex for codes
- Get name and abbreviation for codes

"""
from typing import Any, Tuple, Union

CODE_REGEX = {
    "CCIV": r"(?P<CCIV>Code\scivil|C\.\s?civ\.|Code\sciv\.|civ\.|CCIV)",
    "CPRCIV": r"(?P<CPRCIV>Code\sde\sprocédure\scivile|C\.\spr\.\sciv\.|CPC)",
    "CCOM": r"(?P<CCOM>Code\sd(e|u)\scommerce|C\.\scom\.)",
    "CTRAV": r"(?P<CTRAV>Code\sdu\stravail|C\.\strav\.)",
    "CPI": r"(?P<CPI>Code\sde\sla\spropriété\sintellectuelle|CPI|C\.\spr\.\sint\.)",
    "CPEN": r"(?P<CPEN>Code\sp(é|e)nal|C\.\s?p(é|e)n\.)",
    "CPP": r"(?P<CPP>Code\sde\sprocédure\spénale|CPP)",
    "CASSUR": r"(?P<CASSUR>Code\sdes\sassurances|C\.\sassur\.)",
    "CCONSO": r"(?P<CCONSO>Code\sde\sla\sconsommation|C\.\sconso\.)",
    "CSI": r"(?P<CSI>Code\sde\slasécurité\sintérieure|CSI)",
    "CSP": r"(?P<CSP>Code\sde\slasanté\spublique|C\.\ssant\.\spub\.|CSP)",
    "CSS": r"(?P<CSS>Code\sde\slasécurité\ssociale|C\.\ssec\.\ssoc\.|CSS)",
    "CESEDA": r"(?P<CESEDA>Code\sde\sl'entrée\set\sdu\sséjour\sdes\sétrangers\set\sdu\sdroit\sd'asile|CESEDA)",
    "CGCT": r"(?P<CGCT>Code\sgénéral\sdes\scollectivités\sterritoriales|CGCT)",
    "CPCE": r"(?P<CPCE>Code\sdes\spostes\set\sdes\scommunications\sélectroniques|CPCE)",
    "CENV": r"(?P<CENV>Code\sde\sl'environnement|C.\senvir.|CE\.)",
    "CJA": r"(?P<CJA>Code\sde\sjustice\sadministrative|CJA)",
}

CODE_REFERENCE = {
    "CCIV": "Code civil",
    "CPRCIV": "Code de procédure civile",
    "CCOM": "Code de commerce",
    "CTRAV": "Code du travail",
    "CPI": "Code de la propriété intellectuelle",
    "CPEN": "Code pénal",
    "CPP": "Code de procédure pénale",
    "CASSUR": "Code des assurances",
    "CCONSO": "Code de la consommation",
    "CSI": "Code de la sécurité intérieure",
    "CSP": "Code de la santé publique",
    "CSS": "Code de la sécurité sociale",
    "CESEDA": "Code de l'entrée et du séjour des étrangers et du droit d'asile",
    "CGCT": "Code général des collectivités territoriales",
    "CPCE": "Code des postes et des communications électroniques",
    "CENV": "Code de l'environnement",
    "CJA": "Code de justice administrative",
}


def get_long_and_short_code(code_name: str) -> Tuple[str, str]:
    """
    Accéder aux deux versions du nom du code: le nom complet et son abréviation

    Parameters
    ----------
    code_name : str
        le nom du code (version longue ou courte)

    Returns
    ----------
    long_code: str
        le nom complet du code
    short_code: str
        l'abréviation du code

    Notes
    ----------
    Si le nom du code n'a pas été trouvé les valeurs sont nulles (None, None)
    """

    if code_name in CODE_REFERENCE.keys():
        short_code = code_name
        long_code = CODE_REFERENCE[code_name]
    elif code_name in CODE_REFERENCE.values():
        long_code = code_name
        short_code_results = [k for k, v in CODE_REFERENCE.items() if v == code_name]
        if len(short_code_results) > 0:
            short_code = short_code_results[0]
        else:
            short_code = None
    else:
        short_code, long_code = None, None
    return (long_code, short_code)


def get_code_full_name_from_short_code(short_code: str) -> str:
    """
    Shortcut to get corresponding full_name from short_code

    Arguments
    ----------
    short_code: str
        short form of Code eg. CCIV

    Returns
    ----------
    full_name: str
        long form of code eg. Code Civil

    """
    try:
        return CODE_REFERENCE[short_code]

    except KeyError:
        if get_short_code_from_full_name(short_code) is not None:
            return short_code
        else:
            return None


def get_short_code_from_full_name(full_name: str) -> str:
    """
    Shortcut to get corresponding short_code from full_name

    Arguments
    ----------
    full_name: str
        long form of code eg. Code Civil

    Returns
    ----------
    short_code: str
        short form of Code eg. CCIV
    """
    keys = [k for k, v in CODE_REFERENCE.items() if v == full_name]
    if len(keys) > 0:
        return keys[0]
    else:
        return None


def get_selected_codes_regex(selected_codes: list) -> str:
    '''
    Contruire l'expression régulière pour détecter les différents codes dans le document.
    Selectionner les codes choisis parmi la liste des codes supportés
    et renvoyer les regex correspondants. Si la liste est vide ou None:
    l'intégralité des regex est renvoyée dans une regex composée. 
    Si un seul code est selectionné, la regex renvoyée est simple.

    Arguments
    ---------
    selected_codes: array
        [short_code, ...]. Default: None (no filter)

    Returns
    ----------
    regex: str
        the corresponding regex string
    '''
    if selected_codes is None:
        return "({})".format("|".join(list(CODE_REGEX.values())))
    if len(selected_codes) == 1:
        try:
            return CODE_REGEX[selected_codes[0]]
        except KeyError:
            try:
                #if short code not found: try from full_name
                short_code = get_short_code_from_full_name(selected_codes[0])
                return CODE_REGEX[short_code]
            except:
                #if not found return all codes
                return "({})".format("|".join(list(CODE_REGEX.values())))
    selected_code_regex = []
    for x in selected_codes:
        try:
            selected_code_regex.append(CODE_REGEX[x])
        except KeyError:
            try:
                #if short code not found: try from full_name
                short_code = get_short_code_from_full_name(x)
                selected_code_regex.append(CODE_REGEX[short_code])
            except Exception:
                pass
    #if nothing selected: return all
    if selected_codes is None or len(selected_codes) == 0 or len(selected_code_regex) == 0:
        selected_code_regex = CODE_REGEX.values()
    return "({})".format("|".join(selected_code_regex))



