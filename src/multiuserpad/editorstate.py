import json
from time import sleep
from hashlib import md5
import logging
from cmedit import cmedit

logging.basicConfig(level=logging.INFO)


doc_lines = []
apply_doc_edit_calls = -1


class EditorStateException(Exception):
    pass


# DOES NOT TERMINATE FILE WITH A NEWLINE!!!!
def get_document_state():
    global doc_lines
    return "\n".join(doc_lines)


def edit_last_line(edit):
    global doc_lines
    # appending the last line:
    logging.info("edit_last_line")
    for line in edit.text_lines:
        doc_lines.append(line)

    if edit.get_removed_text() != "":
        raise EditorStateException("trying to remove from last line")


def edit_nll_single_line_removal(edit):
    logging.info("edit_nll_single_line_removal: %s" % str(edit.get_removed_text()))
    doc_line = doc_lines[edit.frompos.line]
    # on removal, edit.topos.ch is one char after
    removal_len = edit.topos.ch - edit.frompos.ch
    lhs = doc_line[0 : edit.frompos.ch]
    rhs = doc_line[edit.topos.ch :]
    logging.info("  lhs[%s]  rhs[%s]" % (lhs, rhs))
    doc_lines[edit.frompos.line] = lhs + rhs


def edit_nll_multi_line_removal(edit):
    # edit.frompos.line != edit.topos.line.
    logging.info("edit_nll_multi_line_removal")

    # first line, remove from edit.frompos.ch on for it
    # middle lines, remove everything
    # last line, remove from 0 to edit.topos.ch

    # do this backwards to deal with deletions mid iteration
    for line_count in range(edit.topos.line, edit.frompos.line - 1, -1):
        logging.info("removing on line [%s]" % doc_lines[line_count])
        if line_count == edit.frompos.line:
            logging.info("first line")
            if edit.frompos.ch == 0:
                del doc_lines[line_count]
            else:
                lhs = doc_lines[line_count][0 : edit.frompos.ch]
                doc_lines[line_count] = lhs
        elif line_count == edit.topos.line:
            logging.info("last line")
            if len(doc_lines[line_count]) == edit.topos.ch:
                del doc_lines[line_count]
            else:
                rhs = doc_lines[line_count][edit.topos.ch :]
                doc_lines[line_count] = rhs
        else:
            logging.info("middle lines")
            del doc_lines[line_count]
            # stop_after = True


def edit_nll_last_ch_append(edit):
    logging.info("edit_nll_last_ch_append")
    for line_count in range(len(edit.text_lines) - 1, -1, -1):
        logging.info("  line: %s" % edit.text_lines[line_count])
        if line_count == 0:
            logging.info("first line")
            # If not adding at the last char, it has a deletion too
            assert len(doc_lines[edit.frompos.line]) == edit.frompos.ch
            doc_lines[edit.frompos.line] += edit.text_lines[line_count]
        else:
            logging.info("middle/last line")
            # should assert edit.topos.ch is the same (pure insert)
            logging.info("MAYBE BUG - INSERT +1")
            doc_lines.insert(edit.frompos.line + 1, edit.text_lines[line_count])


def edit_nll_mid_line_insertion(edit):
    logging.info("edit_nll_mid_line_insertion")
    doc_line = doc_lines[edit.frompos.line]

    # abc --> aDbc, first + new + second
    # insert the first line around from
    lhs = doc_line[0 : edit.frompos.ch]
    rhs = doc_line[edit.frompos.ch :]
    # only add lines if it's multiline
    if len(edit.text_lines) > 1:
        # insertion has several lines
        for line_count in range(len(edit.text_lines) - 1, -1, -1):
            logging.info("  line: %s" % edit.text_lines[line_count])
            if line_count == 0:
                logging.info("mid line insertion - first line")
                # If not adding at the last char, it has a deletion too
                doc_lines[edit.frompos.line] = lhs + edit.text_lines[line_count]
            else:
                logging.info("mid line insertion - middle/last line")
                # should assert edit.topos.ch is the same (pure insert)
                logging.info("MAYBE BUG - INSERT +1")
                doc_lines.insert(
                    edit.frompos.line + 1, edit.text_lines[line_count] + rhs
                )
    else:
        # single line insertion
        logging.info("mid line insertion - single line")
        added_text = "\n".join(edit.text_lines)
        doc_lines[edit.frompos.line] = lhs + added_text + rhs


def edit_non_last_line(edit):
    # TODO: multiline insertions on an existing line
    logging.info("edit_non_last_line")
    doc_line = doc_lines[edit.frompos.line]
    removed_text = edit.get_removed_text()
    if removed_text != "":
        if edit.frompos.line == edit.topos.line:
            edit_nll_single_line_removal(edit)
        else:
            edit_nll_multi_line_removal(edit)
    elif edit.frompos.ch == len(doc_line):
        edit_nll_last_ch_append(edit)

    elif edit.frompos.ch < len(doc_line):
        if edit.frompos.line == edit.topos.line:
            edit_nll_mid_line_insertion(edit)
        else:
            raise EditorStateException("ODD MULTI LINE INSERTION")
    else:
        raise EditorStateException("unimplemented: " + str(edit))


# returns boolean True if edit was accepted
def apply_doc_edit(rawedit, client_md5_hash):
    global apply_doc_edit_calls, doc_lines
    apply_doc_edit_calls += 1
    logging.info("Doc state change [%d]: %s" % (apply_doc_edit_calls, str(rawedit)))

    if client_md5_hash != "" and client_md5_hash is not None:
        server_md5_hash = md5(get_document_state().encode()).hexdigest()
        if client_md5_hash != server_md5_hash:
            logging.info(
                "  rejecting edit, mismatched md5, client: %s, server: %s"
                % (client_md5_hash, server_md5_hash)
            )
            return

    logging.info("  before change: %s" % json.dumps(doc_lines))

    edit = cmedit(rawedit)
    num_doc_lines = len(doc_lines)

    # TODO: BUG: if the last line is removed, append gets triggered
    #   Can we treat the last line as a normal line?

    if num_doc_lines == edit.frompos.line and edit.get_removed_text() == "":
        edit_last_line(edit)
    else:
        edit_non_last_line(edit)

    logging.info("  after change: %s" % json.dumps(doc_lines))

    return True


# test code / test utilities
# TODO: put elsewhere
def dump_extract(edits, out_file, start, end):
    json.dump(edits[start : (end + 1)], open(out_file, "w"), indent=2)
    logging.info("dumped to %s" % out_file)


def compute_final_state(test_dump_file):
    global doc_lines
    doc_lines = []
    edits = json.load(open(test_dump_file))
    # dump_extract(edits, "log.json", 0, 39)
    for edit_num, raw_edit in enumerate(edits):
        edit = json.loads(raw_edit)
        apply_doc_edit(edit["contents"], None)
        # if edit_num == 5:
        #    break
        # sleep(0.2)
    # add a final newline, always, to match other editors
    return "\n".join(doc_lines) + "\n"
