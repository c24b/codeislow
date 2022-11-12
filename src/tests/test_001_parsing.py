#!/usr/bin/env python

import os
import shutil
import pytest
from .context import parsing
from parsing import ACCEPTED_EXTENSIONS, parse_doc


TEST_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.dirname(TEST_DIR)
TMP_DIR = os.path.join(TEST_DIR, "tmp")
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)


def archive_test_file(filename: str) -> str:
    abspath = os.path.join(TEST_DIR, filename)
    tmp_abspath = os.path.join(TEST_DIR, "tmp", filename)
    shutil.copy(abspath, tmp_abspath)
    return tmp_abspath


def restore_test_file(filename: str) -> str:
    abspath = os.path.join(TEST_DIR, filename)
    tmp_abspath = os.path.join(TEST_DIR, "tmp", filename)
    shutil.move(tmp_abspath, abspath)
    return abspath


class TestFileParsing:
    def test_wrong_extension(self):
        """testing accepted extensions"""
        file_paths = ["document.rtf", "document.md", "document.xlsx"]

        for file_path in file_paths:
            with pytest.raises(ValueError) as e:
                # archive_test_file(file_path)
                parse_doc(file_path)
                assert (
                    e
                    == "Extension incorrecte: les fichiers acceptés terminent par *.odt, *.docx, *.doc,  *.pdf"
                )
                # restore_test_file(file_path)

    def test_wrong_file_path(self):
        """testing FileNotFound Error"""
        filepath = "./document.doc"
        with pytest.raises(FileNotFoundError) as e:
            parse_doc(filepath)
            assert e == "", e

    def test_content(self):
        """test content text"""
        file_paths = ["newtest.docx", "newtest.pdf", "testnew.odt"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            # as file is removed during parse_doc
            # archive it
            archive_test_file(file_path)
            full_text = parse_doc(abspath)
            # and restore it
            restore_test_file(file_path)
            doc_name, doc_ext = abspath.split("/")[-1].split(".")
            assert doc_name == "newtest" or doc_name == "testnew"
            if abspath.endswith(".pdf"):
                assert len(full_text) == 23, (len(full_text), abspath)
            else:
                assert len(full_text) == 22, (len(full_text), abspath)
            assert any("art." in _x for _x in full_text) is True
            assert any("Art." in _x for _x in full_text) is True
            assert any("Code" in _x for _x in full_text) is True

    def test_reversed_pattern_content(self):
        """test content text"""
        file_paths = ["testnew.pdf", "testnew.odt"]
        for file_path in file_paths:
            abspath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), file_path
            )
            archive_test_file(file_path)
            full_text = parse_doc(abspath)
            restore_test_file(file_path)
            doc_name, doc_ext = abspath.split("/")[-1].split(".")
            assert doc_name == "newtest" or doc_name == "testnew"
            if abspath.endswith(".pdf"):
                assert len(full_text) == 24, (len(full_text), abspath)
            else:
                assert len(full_text) == 22, (len(full_text), abspath)
            assert any("art." in _x for _x in full_text) is True
            assert any("Art." in _x for _x in full_text) is True
            assert any("Code" in _x for _x in full_text) is True

    def test_HDR_document(self):
        file_path = "HDR_NETTER_V1_07.odt"
        abspath = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_path)
        archive_test_file(file_path)
        full_text = parse_doc(abspath)
        restore_test_file(file_path)
        doc_name, doc_ext = abspath.split("/")[-1].split(".")
        assert doc_ext == "odt", doc_ext
        assert len(full_text) == 3589, (len(full_text), abspath)
        assert any("art." in _x for _x in full_text) is True
        assert any("Art." in _x for _x in full_text) is True
        assert any("Code" in _x for _x in full_text) is True
