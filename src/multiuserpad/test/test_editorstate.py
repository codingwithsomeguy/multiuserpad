"""editorstate tests vs. finalstate text files"""

import os
from glob import glob

import pytest
import multiuserpad.editorstate as es


def get_json_records_with_finalstate(base_dir):
    """find test records files with a corresponding final state"""
    result = []
    for base_json_file in glob(os.path.join(base_dir, "*.json")):
        file_stem = os.path.splitext(os.path.split(base_json_file)[-1])[0]
        final_file = os.path.join(base_dir, file_stem + ".txt")
        if os.path.exists(final_file):
            result.append((base_json_file, final_file))
    return result


def test_enough_editorstate_finalstate_testcases():
    """Verify there are a minimum number of editorstate tests"""
    test_set = get_json_records_with_finalstate("data")
    assert len(test_set) > 7, (
        "not enough editorstate/finalstate test cases")


def test_editorstate_finalstate():
    """check the computed final state matches the final state"""
    test_set = get_json_records_with_finalstate("data")
    for json_file, final_file in test_set:
        es.doc_lines = []
        es.apply_doc_edit_calls = -1
        final_state = open(final_file).read()
        computed_final_state = es.compute_final_state(json_file)
        err_mesg = "%s doesn't match" % json_file
        assert computed_final_state == final_state, err_mesg


def test_editorstate_invalidinput():
    json_file = "data/invalidinput/insert-oneafter-lineend.json"
    with pytest.raises(es.EditorStateException):
        es.doc_lines = []
        es.apply_doc_edit_calls = -1
        es.compute_final_state(json_file)

    json_file = "data/invalidinput/insert-twoafter-lineend.json"
    with pytest.raises(es.EditorStateException):
        es.doc_lines = []
        es.apply_doc_edit_calls = -1
        es.compute_final_state(json_file)
