import glob
import os
import sublime


class Makerfile():

    def __init__(self, settings, pwd, is_single_file):
        self.makefile = ""

        self.variables = {}
        self.output_file = "output"
        self.string_template = ""

        if sublime.platform() == "windows":
            self.output_file += ".exe"

        self.settings = settings
        self.src = settings.get('src_dir', '').strip()
        self.obj = settings.get('obj_dir', '').strip()
        self.build = settings.get('build_dir', '').strip()
        self.header = settings.get('include_dir', '')
        if is_single_file:
            self.sources = self.get_source_files(pwd)
        else:
            self.sources = self.get_source_files(os.path.join(pwd, self.src))

    def make_file(self):
        '''Exported API for making final makefile content'''
        if not self.sources:
            return '# No sources provided'

        self.makefile = self.handle_variable(self.settings)
        self.make_string_template()

        return '\n'.join([
            self.makefile,
            self.str_main_file(),
            '\n' + self.str_recipe_target(),
            self.str_make_run(),
            self.str_make_clean()
        ])

    def handle_variable(self, settings):
        '''Dealing with make variables'''
        var_string = ""
        if self.header:
            string = " ".join(self.header)
            header = "$(addprefix -I,$(HDR_DIR))"
            self.variables["HDR_DIR"] = string
            self.variables["HEADER"] = header

            var_string += "HDR_DIR = %s\nHEADER = %s\n" % (string, header)

        if settings.get("lib_dir") and settings.get("lib_names"):
            lib_dir = " ".join(settings.get("lib_dir"))
            lib = "$(addprefix -L, $(LIB_DIR))"
            self.variables["LIB_DIR"] = lib_dir
            self.variables["LIB"] = lib

            libnames = " ".join(settings.get("lib_names"))
            libn = "$(addprefix -l,$(LIB_NAMES))"
            self.variables["LIB_NAMES"] = libnames
            self.variables["Library"] = libn

            var_string += "LIB_DIR = %s\nLIB = %s\n" % (lib_dir, lib)
            var_string += "LIB_NAMES = %s\nLIBRARY = %s\n" % (libnames, libn)

        if settings.get("additional_flags"):
            self.variables["CCOPTION"] = " ".join(
                settings.get("additional_flags"))
            self.variables["FLAGS"] = "$(addprefix -,$(FLAGS))"

            var_string += "CCOPTION = %s\n" % self.variables.get("CCOPTION")
            var_string += "FLAGS = $(addprefix -,$(CCOPTION))\n"

        if settings.get("cc"):
            self.variables["CC"] = settings.get("cc")
            var_string += "CC = %s\n" % settings.get("cc")
        else:
            var_string += "CC = %s\n" % "g++"

        exe_ext = '.exe' if sublime.platform == 'windows' else '.out'
        if settings.get("project_name"):
            self.variables["main_file"] = settings.get(
                "project_name") + exe_ext

        elif settings.get("main_file"):
            self.variables["main_file"] = settings.get(
                "main_file") + exe_ext
        else:
            self.variables["main_file"] = "output" + exe_ext

        if self.obj:
            var_string += "OBJ_DIR = %s\n" % self.obj

        if self.sources:
            self.variables["OBJ"] = ""
            for x in self.sources:
                self.variables["OBJ"] += x.replace(".cpp", ".o") + " "

            var_string += "OBJ = %s\n" % self.variables.get("OBJ")

        if self.build:
            self.variables["BUILD_DIR"] = self.build
            var_string += "BUILD_DIR = %s\n" % self.build

        if self.src:
            self.variables["SRC_DIR"] = self.src
            var_string += "SRC_DIR = %s\n" % self.src

        return var_string

    def str_main_file(self):
        '''Generate final output recipe for make'''
        string = ""
        if self.build:
            string += "{2}" + os.sep  # build dir

        string += "{0}: {1} \n\t$(CC) "

        if self.variables.get("FLAGS"):
            string += "$(FLAGS) "

        if self.build:
            string += "{1} -o {2}" + os.sep + "{0} "
        else:
            string += "{1} -o {0} "

        if self.variables.get("LIB"):
            string += "$(LIB) $(LIBRARY)"

        if self.obj:
            objs = "$(addprefix $(OBJ_DIR){},$(OBJ))".format(os.sep)
        else:
            objs = "$(OBJ)"

        main_exe = string.format(
            self.variables.get("main_file"), objs, "$(BUILD_DIR)")
        return main_exe

    def str_make_run(self):
        return 'run: {0}{1}{2}\n\t{0}{1}{2}\n'.format(
            '$(BUILD_DIR)', os.sep, self.variables.get("main_file"))

    def str_make_clean(self):
        '''Generate `clean` recipe for make'''
        clean_content = ['clean: ']
        del_command = "rm " if sublime.platform() != 'windows' else 'del /Q'

        if bool(self.settings.get("clean")):
            for i in self.settings.get("clean"):
                i = i.replace('\\', os.sep)
                clean_content.append(del_command + i)
        else:
            clean_content.append(del_command + "$(OBJ_DIR)%s*.o" % os.sep)
            clean_content.append(del_command + "$(BUILD_DIR)%s*.out" % os.sep)

        return "\n\t".join(clean_content)  # strip last `\t`

    def str_recipe_target(self):
        tempmk = []
        if self.sources:
            for x in self.sources:
                tempmk.append(self.string_template.format(
                    x.replace(".cpp", ".o"), x, "$(OBJ_DIR)", "$(SRC_DIR)")
                )
            return '\n\n'.join(tempmk) + '\n\n'
        else:
            print("No Source files found")
            return None

    def make_string_template(self):
        '''Generate template string based on variables passed for the object'''
        tmp = ""
        if self.obj:
            tmp += "{2}" + os.sep  # obj dir

        tmp += "{0}: "  # object .o

        if self.src:
            tmp += "{3}" + os.sep  # src dir

        tmp += "{1}\n\t$(CC) $(FLAGS) -c "  # recipe for object

        if self.src:
            tmp += "{3}" + os.sep

        tmp += "{1} "

        if self.obj:
            tmp += "-o {2}" + os.sep + "{0} "
        else:
            tmp += "-o {0} "

        if self.variables.get("HEADER"):
            tmp += "$(HEADER)"

        self.string_template = tmp

    def get_source_files(self, src_dir):
        '''Find all .cpp source file in src_dir'''
        back_out = './'
        if src_dir:
            try:
                back_out = os.getcwd()
                os.chdir(src_dir)
            except FileNotFoundError:
                sublime.error_message("Couldn't find source Folder: " + src_dir)

        file_sources = glob.glob("*.cpp")

        os.chdir(back_out)

        return file_sources

    # setter methods
    def set_src(self, src_dir):
        self.src = src_dir

    def set_obj(self, obj_dir):
        self.obj = obj_dir

    def set_build(self, build_dir):
        self.build = build_dir

    def set_header(self, header_dir):
        self.header = header_dir
