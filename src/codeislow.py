#!/usr/bin/env python

import os
from dotenv import load_dotenv
from parsing import parse_doc
from matching import get_matching_result_item, get_matching_results_dict
from request_api import get_article


def main_result_sorted(
    file_path, selected_codes=None, pattern_format="article_code", past=3, future=3
):
    """
    Version initiale de présentation des résultats: un dictionnaire trié par code et ses articles associés

    Arguments
    ----------
    file_path: str
        nom du fichier chargé
    selected_codes: array
        liste des codes selectionnés
    pattern_format: str
        le format de notation des références: article_code ou code_article
    past: int
        Nombre d'années en arrière à surveiller
    future: int
        Nombre d'années en avant à surveiller
    """
    # parse
    full_text = parse_doc(file_path)
    results_dict = get_matching_results_dict(full_text, selected_codes, pattern_format)
    if len(results_dict) == 0:
        raise ValueError("ERREUR: pas d'article detecté....")
    else:
        return results_dict


def main(
    file_path, selected_codes=None, pattern_format="article_code", past=3, future=3
):
    """
    Version 'brute' sans renvoi de HTML

    Arguments
    ----------
    file_path: str
        nom du fichier chargé
    selected_codes: array
        liste des codes selectionnés
    pattern_format: str
        le format de notation des références: article_code ou code_article
    past: int
        Nombre d'années en arrière à surveiller
    future: int
        Nombre d'années en avant à surveiller
    """
    load_dotenv()

    client_id = os.getenv("API_KEY")
    client_secret = os.getenv("API_SECRET")
    # parse
    full_text = parse_doc(file_path)
    # matching_results = yield from get_matching_result_item(full_text,selected_codes, pattern_format)
    results = []
    for short_code, code, article_nb in get_matching_result_item(
        full_text, selected_codes, pattern_format
    ):
        # request and check validity
        # article = get_article(code, article_nb, client_id, client_secret, past_year_nb=past, future_year_nb=future)
        # print(article)
        article = get_article(
            code,
            article_nb,
            client_id,
            client_secret,
            past_year_nb=past,
            future_year_nb=future,
        )
        results.append(article)
        yield article
    if len(results) == 0:
        raise ValueError("ERROR: pas d'article detecté....")


def load_result(
    file_path, selected_codes=None, pattern_format="article_code", past=3, future=3
):
    """
    Load result in HTML

    Arguments
    ---------
    filepath: str
        le chemin du fichier
    selected_codes: array
        la liste des codes (version abbréviée) à détecter
    pattern_format: str
        le format des références: Article xxx du Code yyy ou Code yyyy Article xxx
    past: int
        nombre d'années dans le passé
    future: int
        nombre d'années dans le futur
    Yields
    ------
    html_results: str
        resultat sous forme de cellule d'une table HTML
    """
    load_dotenv()
    client_id = os.getenv("API_KEY")
    client_secret = os.getenv("API_SECRET")
    # parse
    full_text = parse_doc(file_path)
    _exhausted = object()
    result_generator = get_matching_result_item(
        full_text, selected_codes, pattern_format
    )
    if next(result_generator, _exhausted) is _exhausted:
        wrong_row = f"""
        <tr class="warning">
            <th scope="row">ERROR</th>
            <td>/td>
            <td></td>
            <td>Something went wrong</td>
        <tr>
        """
        yield (wrong_row)
    else:
        for short_code, code, article_nb in get_matching_result_item(
            full_text, selected_codes, pattern_format
        ):
            # request and check validity
            article = get_article(
                code,
                article_nb,
                client_id,
                client_secret,
                past_year_nb=past,
                future_year_nb=future,
            )
            row = f"""
            <tr>
                <th scope="row"><a href='{article["url"]}'>{article["code"]} ({short_code}) - {article["article"]}</a></th>
                <td><span class="badge badge-pill badge-{article["color"]}">{article["status"]}</span></td>
                <td>{article["texte"]}</td>
                <td>{article["date_debut"]}-{article["date_fin"]}</td>
            <tr>
            """
            yield (row)
