import sublime
import sublime_plugin
import os
import subprocess
import string


class SendToRappCommand(sublime_plugin.WindowCommand):
    """Sends lines to R"""
    @staticmethod
    def cleanString(str):
        str = string.replace(str, '\\', '\\\\')
        str = string.replace(str, '"', '\\"')
        return str

    def run(self, lines):
        s = sublime.load_settings("Rtools.sublime-settings")
        app = s.get("r_gui")

        # define osascript arguments
        args = ['osascript']

        if s.get("r_submit_single_lines"):
            # add code lines to list of arguments individually
            lines = self.cleanString(lines).split("\n")
            for part in lines:
                args.extend(['-e', 'tell app "' + app + '" to cmd "' + part + '"\n'])
        else:
            args.extend(['-e', 'tell app "' + app + '" to cmd "' + self.cleanString(lines) + '"\n'])
        # execute code
        subprocess.Popen(args)


class RSourceFileCommand(sublime_plugin.WindowCommand):
    """Source Current File in R"""
    def run(self, *args, **kwargs):
        # Get the given filepath
        filepath = kwargs.get('filepath', "")
        force_run = kwargs.get('force', False)
        if filepath == "":
            # if not passed a filename, assume the windows active file
            filepath = self.window.active_view().file_name()

        # Check to see if it is an R file that would run if sourced, unless forced to
        if os.path.splitext(filepath)[1] == ".R" or force_run:  # Any other extensions that should be allowed?
            self.window.run_command("send_to_rapp", {"lines": "source(\"" + filepath + "\")\n"})
        else:
            sublime.error_message("Not a .R file.")


class RDocsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        sel = self.view.sel()[0]

        params_reg = self.view.find('(?<=\().*(?=\))', sel.begin())
        params_txt = self.view.substr(params_reg)
        params = params_txt.split(',')

        snippet = "#'<brief desc>\n#'\n#'<full description>\n"

        for p in params:
            snippet += "#' @param %s <what param does>\n" % p

        snippet += "#' @export\n#' @keywords\n#' @seealso\n#' @return\n#' @alias\n#' @examples \dontrun{\n#'\n#'}\n"

        self.view.insert(edit, sel.begin(), snippet)


class SendSelectionCommand(sublime_plugin.TextCommand):
    @staticmethod
    def cleanString(str):
        str = string.replace(str, '\\', '\\\\')
        str = string.replace(str, '"', '\\"')
        return str

    def run(self, edit):
        # Check if it's an R file
        filescope = self.view.syntax_name(self.view.sel()[0].b)
        if ("source.r " not in filescope) and ("source.r." not in filescope):
            return

        # get selection
        selection = ""
        for region in self.view.sel():
            if region.empty():
                selection += self.view.substr(self.view.line(region)) + "\n"
                self.advanceCursor(region)
            else:
                selection += self.view.substr(region) + "\n"

        selection = (selection[::-1].replace('\n'[::-1], '', 1))[::-1]

        # only proceed if selection is not empty
        if(selection == ""):
            return

        self.view.window().run_command("send_to_rapp", {"lines": selection})

    def advanceCursor(self, region):
        (row, col) = self.view.rowcol(region.begin())

        # Make sure not to go past end of next line
        nextline = self.view.line(self.view.text_point(row + 1, 0))
        if nextline.size() < col:
            loc = self.view.text_point(row + 1, nextline.size())
        else:
            loc = self.view.text_point(row + 1, col)

        # Remove the old region and add the new one
        self.view.sel().subtract(region)
        self.view.sel().add(sublime.Region(loc, loc))


class RPromptCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.get_window().show_input_panel("R Prompt", "",
            self.on_input, None, None)

    def get_window(self):
        return self.window

    def on_input(self, rcommand):
        if rcommand.strip() == "":
            return
        self.window.run_command("send_to_rapp", {"lines": rcommand})
