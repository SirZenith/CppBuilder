import sublime
import json
import os


class ProjectHandler:
    # contains the workspace folder defined in settings file

    def __init__(self, project_name="temp"):
        self.project_data = self.extract_proj_data()
        self.settings = self.project_data['settings']

        self.workspace_dir = self.settings["workspace_dir"]
        self.proj_base_dir = project_name

    def create_base_project(self):
        self.mkdirs(self.workspace_dir)

        proj_dir = os.path.join(self.workspace_dir, self.proj_base_dir)
        dires = [
            self.settings['build_dir'],
            self.settings['obj_dir'],
            self.settings['src_dir'],
        ] + self.settings['include_dir']

        for dire in dires:
            folder_full_path = os.path.join(proj_dir, dire)
            os.makedirs(folder_full_path, exist_ok=True)
            print('Made directory:', folder_full_path)

        self.project_data["folders"].append({"path": proj_dir})

        self.mk_subl_proj()
        sublime.active_window() .set_project_data(self.project_data)

    def mkdirs(self, path):
        if 3000 <= int(sublime.version()) < 3088:
            # Fixes as best as possible a new directory permissions issue
            # See https://github.com/titoBouzout/SideBarEnhancements/issues/203
            # See https://github.com/SublimeTextIssues/Core/issues/239
            oldmask = os.umask(0o000)
            if oldmask == 0:
                os.makedirs(path, 0o755, exist_ok=True)
            else:
                os.makedirs(path, exist_ok=True)
            os.umask(oldmask)
        else:
            os.makedirs(path, exist_ok=True)

    def mk_subl_proj(self):
        '''Creat Sublime project file, using self.project_data'''
        proj_dir = os.path.join(self.workspace_dir, self.proj_base_dir)
        project_file_name = os.path.join(
            proj_dir,
            self.proj_base_dir + ".sublime-project"
        )

        with open(project_file_name, "w") as f:
            json.dump(self.project_data, f, indent=4, sort_keys=True)

    def get_wrkspc_dir(self):
        return self.workspace_dir

    def extract_proj_data(self):
        stg = sublime.load_settings("CppBuilder.sublime-settings")
        proj_data = {
            "folders": [],
            "settings": {
                'lib_dir': stg.get('lib_dir', []),
                'lib_name': stg.get('lib_names', []),
                'include_dir': stg.get('include_dir', ['./include']),

                'src_dir': stg.get('src_dir', './src'),
                "main_file": stg.get("main", "main"),
                'obj_dir': stg.get('obj_dir', './build/obj'),
                'build_dir': stg.get('build_dir', './build'),
                "cc": stg.get('cc', "g++"),
                "clean": stg.get('clean', []),

                "terminal_emu": stg.get(
                    'terminal_emu', "x-terminal-emulator"),
                "terminal_opts": stg.get('terminal_opts', ["-x"]),

                "additional_flags": stg.get('additional_flags', []),

                "workspace_dir": stg.get('workspace_dir', "")
            },
            "build_systems": []
        }

        return proj_data
