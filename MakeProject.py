import sublime
import sublime_plugin
import os
import json
from .MakerClass import Makerfile


class MakefileFromProjectCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        project_folder = self.view.window().folders()[0]

        back_out = os.getcwd()
        os.chdir(project_folder)
        try:
            settings = self.get_settings(project_folder)
            if settings:
                pwd = self.view.window().folders()[0]

                maker = Makerfile(settings, pwd, is_single_file=False)
                make_string = maker.make_file()

                makefile_name = os.path.join(pwd, 'Makefile')
                with open(makefile_name, "w") as f:
                    f.write(make_string)

                sublime.active_window().open_file(makefile_name)

            sublime.status_message("Error in .sublime-project file")
        finally:
            os.chdir(back_out)

    def get_settings(self, project_folder):
        proj_name = os.path.basename(project_folder)
        setting_name = "{}{}.sublime-project".format(os.sep, proj_name)

        print('Loading settings for:', project_folder + setting_name)
        return self.load_json(project_folder + setting_name)

    def load_json(self, json_file):
        f = open(json_file)
        j = None
        try:
            j = json.load(f).get('settings')
        except ValueError:
            sublime.error_message(
                "Error while reading .sublime-project file.\n"
                "Check if there is unecessary comma at end of line in file"
            )
        except Exception:
            sublime.error_message(
                "CppBuilder - Making Project: Unknown error while reading .sub"
                "lime-project file"
            )
        finally:
            f.close()

        return j
