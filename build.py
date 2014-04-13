# build exe

 
try:
    from distutils.core import setup
    import py2exe, pygame
    from modulefinder import Module
    import glob, fnmatch
    import sys, os, shutil
except ImportError, message:
    raise SystemExit,  "Sorry, you must install py2exe, pygame. %s" % message


origIsSystemDLL = py2exe.build_exe.isSystemDLL
def isSystemDLL(pathname):
    if os.path.basename(pathname).lower() in ("libfreetype-6.dll", "libogg-0.dll", "sdl_ttf.dll"):
        return 0
    return origIsSystemDLL(pathname)

py2exe.build_exe.isSystemDLL = isSystemDLL
 
class pygame2exe(py2exe.build_exe.py2exe):
    def copy_extensions(self, extensions):
        pygamedir = os.path.split(pygame.base.__file__)[0]
        pygame_default_font = os.path.join(pygamedir, pygame.font.get_default_font())
        extensions.append(Module("pygame.font", pygame_default_font))
        py2exe.build_exe.py2exe.copy_extensions(self, extensions)

class BuildExe:
    def __init__(self):
        self.script = "main.py"
        self.project_name = "Renne"
        self.project_url = "https://github.com/busuncle/renne"
        self.project_version = "0.8.1"
        self.license = "Free"
        self.author_name = "busuncle"
        self.author_email = "lizhij2@gmail.com"
        self.copyright = "Copyright (c) 2014 Busuncle."
        self.project_description = "Renne, a fan-works ARPG"
        self.icon_file = "renne.ico"
        self.extra_datas = ["res", "renne.png", "etc\maps", "config.txt", "readme.txt"]
        self.extra_modules = ["pygame", "gameobjects", "etc.setting", 
            "etc.ai_setting", "base"]
        self.exclude_modules = []
        self.exclude_dll = ['']
        self.extra_scripts = ["gamesprites", "gameworld", 
            "simulator", "controller", "pathfinding", "gamedirector", 
            "renderer", "animation", "debug_tools", "musicbox"]
        self.zipfile_name = None
        self.dist_dir ='Release'

    def opj(self, *args):
        path = os.path.join(*args)
        return os.path.normpath(path)

    def find_data_files(self, srcdir, *wildcards, **kw):
        def walk_helper(arg, dirname, files):
            if '.svn' in dirname or '.git' in dirname:
                return
            names = []
            lst, wildcards = arg
            for wc in wildcards:
                wc_name = self.opj(dirname, wc)
                for f in files:
                    filename = self.opj(dirname, f)
                    base_name = os.path.basename(filename)
                    if base_name.startswith(".") or base_name.endswith("~") or base_name.endswith(".pyc") \
                        or base_name.endswith(".pyo"):
                        continue

                    if fnmatch.fnmatch(filename, wc_name) and not os.path.isdir(filename):
                        names.append(filename)
            if names:
                lst.append( (dirname, names ) )

        file_list = []
        recursive = kw.get('recursive', True)
        if recursive:
            os.path.walk(srcdir, walk_helper, (file_list, wildcards))
        else:
            walk_helper((file_list, wildcards),
                        srcdir,
                        [os.path.basename(f) for f in glob.glob(self.opj(srcdir, '*'))])
        return file_list

    def run(self):
        if os.path.isdir(self.dist_dir): 
            shutil.rmtree(self.dist_dir)

        if self.icon_file == None:
            path = os.path.split(pygame.__file__)[0]
            self.icon_file = os.path.join(path, 'pygame.ico')

        extra_datas = []
        for data in self.extra_datas:
            if os.path.isdir(data):
                extra_datas.extend(self.find_data_files(data, '*'))
            else:
                extra_datas.append(('.', [data]))

        setup(
            cmdclass = {'py2exe': pygame2exe},
            version = self.project_version,
            description = self.project_description,
            name = self.project_name,
            url = self.project_url,
            author = self.author_name,
            author_email = self.author_email,
            license = self.license,
 
            # console = [{
            windows = [{
                'script': self.script,
                'icon_resources': [(0, self.icon_file)],
                'copyright': self.copyright
            }],
            options = {'py2exe': {'optimize': 2, 'bundle_files': 1,
                                  'compressed': True,
                                  'excludes': self.exclude_modules,
                                  'packages': self.extra_modules,
                                  'dist_dir': self.dist_dir,
                                  'dll_excludes': self.exclude_dll,
                                  'includes': self.extra_scripts} },
            zipfile = self.zipfile_name,
            data_files = extra_datas,
            )

        if os.path.isdir('build'): 
            shutil.rmtree('build')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.argv.append('py2exe')
    BuildExe().run()
    raw_input("Finished! Press any key to exit.")

