#!/usr/bin/env python
import pytest
import os

import docx
from PyPDF2 import PdfReader
from odf import text, teletype
from odf.opendocument import load

ACCEPTED_EXTENSIONS = ("odt", "pdf", "docx", "doc")

def parse_doc(file_path):
    """
    Parsing document
    Arguments:
        file_path: a string representing the filepath of the document
    Returns:
        full_text: a list of sentences
    Raises:
        FileNotFoundError: File has not been found. file_path must be incorrect
    """
    doc_name, doc_ext = file_path.split("/")[-1].split(".")
    if doc_ext not in ACCEPTED_EXTENSIONS:
        raise Exception("Extension incorrecte: les fichiers acceptés terminent par *.odt, *docx, *.pdf")
        
    full_text = []
    if doc_ext == "pdf":
        with open(file_path, "rb") as f:    
            reader = PdfReader(f)
            
            for i in range(len(reader.pages)):
                page = reader.pages[i]
                full_text.extend((page.extract_text()).split("\n"))
            
    elif doc_ext == "odt":
        with open(file_path, "rb") as f:
            document = load(f)
            paragraphs = len(document.getElementsByType(text.P))
            for i in range(paragraphs):
                full_text.append((teletype.extractText(paragraphs[i])))
    else:
        # if doc_ext in ["docx", "doc"]:
        with open(file_path, "rb") as f:
            document = docx.Document(f)
            paragraphs = document.paragraphs
            for i in range(len(paragraphs)):
                full_text.append((paragraphs[i].text))
    full_text = [n for n in full_text if n not in  ["\n", "", " "]]
    return full_text
    
class TestFileUpload:
    def test_wrong_extension(self):
        '''testing accepted extensions'''
        file_paths = ["document.rtf", "document.md", "document.xlsx"]
        with pytest.raises(Exception):
            for file_path in file_paths:
                parse_doc(file_path)

    def test_wrong_file_path(self):
        '''testing FileNotFound Error'''
        filepath = "./document.doc"
        with pytest.raises(FileNotFoundError):
            parse_doc(filepath)

    def test_content(self):
        '''test content'''
        file_paths = ["newtest.doc", "newtest.docx", "newtest.pdf"]
        for file_path in file_paths:
            abspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_path)
            full_text = parse_doc(abspath)
            doc_name, doc_ext = abspath.split("/")[-1].split(".")
            assert doc_name == "newtest"
            if abspath.endswith(".pdf"):
                assert len(full_text) == 21, (len(full_text), abspath)
            else:
                assert len(full_text) == 22, (len(full_text), abspath)
            assert any("art." in _x for _x in full_text) is True
            assert any("Art." in _x for _x in full_text) is True
            