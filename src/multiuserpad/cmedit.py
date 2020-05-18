from cmpos import cmpos


class cmedit:
    def __init__(self, cm_edit):
        # TODO: remove this
        self._debug_rawedit = cm_edit

        from_line = cm_edit["from"]["line"]
        from_ch = cm_edit["from"]["ch"]
        self.frompos = cmpos(from_line, from_ch)

        to_line = cm_edit["to"]["line"]
        to_ch = cm_edit["to"]["ch"]
        self.topos = cmpos(to_line, to_ch)

        self.text_lines = cm_edit["text"]
        self.remove_lines = cm_edit["removed"]


    def get_removed_text(self):
        return "\n".join(self.remove_lines)


    def __repr__(self):
        return "cmedit[%s]" % self._debug_rawedit
