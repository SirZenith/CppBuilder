import os
import shutil
import sublime
import sublime_plugin

from .MakerClass import Makerfile
from .ProjectHandler import ProjectHandler


class MakefileFromFileCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        stgname = "CppBuilder.sublime-settings"
        settings = sublime.load_settings(stgname)

        pwd = os.path.dirname(self.view.file_name())

        maker = Makerfile(settings, pwd, is_single_file=True)
        makefile_path = os.path.join(pwd, 'Makefile')
        with open(makefile_path, "w") as f:
            f.write(maker.make_file())

        sublime.active_window().open_file("Makefile")


class NewCppProjectCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        sublime.active_window().show_input_panel(
            "Enter Project Name: ", "", make_project, None, None
        )


def make_project(test):
    proj = ProjectHandler(test)
    proj.create_base_project()


def plugin_loaded():
    # check if settigns file exists if not, extract one from the package file
    # downloaded.
    ls = sublime.packages_path()
    setting_path = os.path.join(ls, 'User', 'CppBuilder.sublime-settings')
    if not os.path.isfile(setting_path):
        os.chdir(ls)
        shutil.copy(
            os.path.join(ls, 'CppBuilder', 'CppBuilder.sublime-settings'),
            os.path.join(ls, 'User', '')
        )
