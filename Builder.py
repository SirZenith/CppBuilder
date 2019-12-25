import sublime
import sublime_plugin

from collections import namedtuple
import glob
import os
import re
import subprocess
import threading
import time


Target = namedtuple('Target', 'fullname basename')


class CppBuilderListCommand(sublime_plugin.WindowCommand):

    encoding = 'utf-8'
    killed = False
    proc = None
    panel = None
    panel_lock = threading.Lock()
    st = 0
    ed = 0

    def run(self, kill=False):
        if kill:
            if self.proc:
                self.killed = True
                self.proc.terminate()
            return

        vars = self.window.extract_variables()
        self.working_dir = vars['file_path']

        content = self.read_makefile()
        if not content:
            return

        try:
            self.targets = list(self.get_targets(content))
            sublime.active_window().show_quick_panel(
                [target.basename for target in self.targets],
                self.on_done
            )
        except Exception:
            self.proc = None

    def on_done(self, chosen):
        if chosen == -1:
            return

        with self.panel_lock:
            self.panel = self.window.create_output_panel('exec')
            settings = self.panel.settings()
            settings.set(
                'result_file_regex',
                r'^File "([^"]+)" line (\d+) col (\d+)'
            )
            settings.set(
                'result_line_regex',
                r'^\s+line (\d+) col (\d+)'
            )
            settings.set('result_base_dir', self.working_dir)

            self.window.run_command('show_panel', {'panel': 'output.exec'})

        if self.proc is not None:
            self.proc.terminate()
            self.proc = None

        make_target = self.targets[chosen].fullname
        self.st = time.perf_counter()
        self.proc = subprocess.Popen(
            ['make', make_target],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=self.working_dir
        )

        threading.Thread(
            target=self.read_handle,
            args=(self.proc.stdout,)
        ).start()

    def is_enabled(self, lint=False, integration=False, kill=False):
        # The Cancel build option should only be available
        # when the process is still running
        if kill:
            return self.proc is not None and self.proc.poll() is None
        return True

    def read_makefile(self):
        '''Read Makefile/makefile in pwd, return its content'''
        back_out = os.getcwd()
        os.chdir(self.working_dir)
        matches = glob.glob("[mM]akefile")

        content = ''
        try:
            if len(matches) == 1:
                with open(matches[0], 'r', encoding='utf8') as f:
                    content = f.read()

            elif len(matches) < 1:
                sublime.message_dialog(
                    "No Makefile/makefile found in current directory")

            elif len(matches) > 1:
                sublime.message_dialog(
                    "More than one Makefile/makefile found in current directory")
        except Exception:
            sublime.message_dialog(
                "Error occur when looking for Makefile/makefile")
        finally:
            os.chdir(back_out)

        return content

    def get_targets(self, content):
        '''Set self.targets with named tuple for targets info

        Target(<full target content>, <target base name>)'''
        tar_patt = re.compile(r'(?<=\n)(.+?)(?=:)')
        matches = tar_patt.finditer(content)
        targets = map(
            lambda match: Target(
                match.group(0), os.path.basename(match.group(1))
            ),
            matches
        )

        var_patt = re.compile(r'^(.+?)\s*=\s*(.+)$', re.M)
        matches = var_patt.findall(content)

        var_table = {}
        for match in matches:
            var_table[match[0]] = match[1]

        place_holder_patt = re.compile(r'\$\((.+)\)')
        expan_result = []
        for target in targets:
            result = place_holder_patt.sub(
                lambda match: var_table[match.group(1)],
                target.fullname
            )
            expan_result.append(Target(result, target.basename))

        return expan_result

    def read_handle(self, handle):
        chunk_size = 2 ** 13
        out = b''
        while True:
            try:
                data = os.read(handle.fileno(), chunk_size)
                # If exactly the requested number of bytes was
                # read, there may be more data, and the current
                # data may contain part of a multibyte char
                out += data
                if len(data) == chunk_size:
                    continue
                if data == b'' and out == b'':
                    raise IOError('EOF')
                # We pass out to a function to ensure the
                # timeout gets the value of out right now,
                # rather than a future (mutated) version
                self.queue_write(out.decode(self.encoding))
                if data == b'':
                    raise IOError('EOF')
                out = b''
            except (UnicodeDecodeError) as e:
                msg = 'Error decoding output using %s - %s'
                self.queue_write(msg % (self.encoding, str(e)))
                break
            except (IOError):
                if self.killed:
                    msg = 'Cancelled'
                else:
                    self.ed = time.perf_counter()
                    msg = 'Finished in %.2fs' % (self.ed - self.st)
                self.queue_write('[%s]' % msg)
                break

    def queue_write(self, text):
        sublime.set_timeout(lambda: self.do_write(text), 1)

    def do_write(self, text):
        with self.panel_lock:
            self.panel.run_command('append', {'characters': text})
