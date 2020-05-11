import json
from time import sleep
import logging

logging.basicConfig(level=logging.INFO)


FS_OUTPUT_FILE = "/tmp/finalstate.txt"

doc_lines = []
apply_doc_edit_calls = -1


class EditorStateException(Exception):
    pass


# DOES NOT TERMINATE FILE WITH A NEWLINE!!!!
def get_document_state():
    global doc_lines
    return "\n".join(doc_lines)


# TODO: refactor this monstrosity
def apply_doc_edit(edit):
    global apply_doc_edit_calls, doc_lines
    apply_doc_edit_calls += 1
    logging.info("Doc state change [%d]: %s" % (
        apply_doc_edit_calls, str(edit)))
    logging.info("  before change: %s" % json.dumps(doc_lines))

    stop_after = False
    from_line = edit["from"]["line"]
    from_ch = edit["from"]["ch"]
    to_line = edit["to"]["line"]
    to_ch = edit["to"]["ch"]
    text_lines = edit["text"]
    remove_lines = edit["removed"]
    num_doc_lines = len(doc_lines)

    # TODO: BUG: if the last line is removed, append gets triggered
    #   Can we treat the last line as a normal line?

    removed_text = "\n".join(remove_lines)
    if num_doc_lines == from_line and removed_text == "":
        # appending the last line:
        logging.info("working on the last line")
        for line in text_lines:
            doc_lines.append(line)
        if removed_text != "":
            raise EditorStateException("trying to remove from last line")
    else:
        # TODO: multiline insertions on an existing line
        logging.info("working on an existing line")
        doc_line = doc_lines[from_line]
        if removed_text != "":
            if from_line == to_line:
                logging.info("Single Line Removal: %s" % str(removed_text))
                # on removal, to_ch is one char after
                removal_len = to_ch - from_ch
                lhs = doc_line[0:from_ch]
                rhs = doc_line[to_ch:]
                logging.info("  lhs[%s]  rhs[%s]" % (lhs, rhs))
                doc_lines[from_line] = lhs + rhs
            else:
                # from_line != to_line.
                logging.info("Multi Line Removal")

                # first line, remove from from_ch on for it
                # middle lines, remove everything
                # last line, remove from 0 to to_ch

                # do this backwards to deal with deletions mid iteration
                for line_count in range(to_line, from_line-1, -1):
                    logging.info("removing on line [%s]" % doc_lines[line_count])
                    if line_count == from_line:
                        logging.info("first line")
                        if from_ch == 0:
                            del doc_lines[line_count]
                        else:
                            lhs = doc_lines[line_count][0:from_ch]
                            doc_lines[line_count] = lhs
                    elif line_count == to_line:
                        logging.info("last line")
                        if len(doc_lines[line_count]) == to_ch:
                            del doc_lines[line_count]
                        else:
                            rhs = doc_lines[line_count][to_ch:]
                            doc_lines[line_count] = rhs
                    else:
                        logging.info("middle lines")
                        del doc_lines[line_count]
                        #stop_after = True
                
        elif from_ch == len(doc_line):
            logging.info("last character append")
            for line_count in range(len(text_lines)-1, -1, -1):
                logging.info("  line: %s" % text_lines[line_count])
                if line_count == 0:
                    logging.info("first line")
                    # If not adding at the last char, it has a deletion too
                    assert len(doc_lines[from_line]) == from_ch
                    doc_lines[from_line] += text_lines[line_count]
                else:
                    logging.info("middle/last line")
                    # should assert to_ch is the same (pure insert)
                    logging.info("MAYBE BUG - INSERT +1")
                    doc_lines.insert(from_line + 1, text_lines[line_count])

        elif from_ch < len(doc_line):
            if from_line == to_line:
                logging.info("mid line insertion")

                # abc --> aDbc, first + new + second
                # insert the first line around from
                lhs = doc_line[0:from_ch]
                rhs = doc_line[from_ch:]
                # only add lines if it's multiline
                if len(text_lines) > 1:
                    # insertion has several lines
                    for line_count in range(len(text_lines)-1, -1, -1):
                        logging.info("  line: %s" % text_lines[line_count])
                        if line_count == 0:
                            logging.info("mid line insertion - first line")
                            # If not adding at the last char, it has a deletion too
                            doc_lines[from_line] = lhs + text_lines[line_count]
                        else:
                            logging.info("mid line insertion - middle/last line")
                            # should assert to_ch is the same (pure insert)
                            logging.info("MAYBE BUG - INSERT +1")
                            doc_lines.insert(from_line + 1, text_lines[line_count] + rhs)
                else:
                    # single line insertion
                    logging.info("mid line insertion - single line")
                    added_text = "\n".join(text_lines)
                    doc_lines[from_line] = lhs + added_text + rhs
            else:
                raise EditorStateException("ODD MULTI LINE INSERTION")
        else:
            raise EditorStateException("unimplemented: " + json.dumps(edit))
    logging.info("  after change: %s" % json.dumps(doc_lines))
    logging.info("")
    if stop_after == True:
        raise EditorStateException("stop_after set")


# test code / test utilities
# TODO: put elsewhere
# TODO: use tox

def dump_extract(edits, out_file, start, end):
    json.dump(edits[start:(end+1)], open(out_file, "w"), indent=2)
    logging.info("dumped to %s" % out_file)
    

def compute_final_state(test_dump_file):
    global doc_lines
    doc_lines = []
    edits = json.load(open(test_dump_file))
    #dump_extract(edits, "log.json", 0, 39)
    for edit_num, raw_edit in enumerate(edits):
        edit = json.loads(raw_edit)
        apply_doc_edit(edit["contents"])
        #if edit_num == 5:
        #    break
        #sleep(0.2)
    # add a final newline, always, to match other editors
    return "\n".join(doc_lines) + "\n"
