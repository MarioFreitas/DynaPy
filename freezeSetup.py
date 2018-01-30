from cx_Freeze import setup, Executable
import os
import datetime

year = datetime.date.today().year
month = datetime.date.today().month
day = datetime.date.today().day

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

# executable options
script = 'main.py'
base = 'Win32GUI'  # Win32GUI para gui's e None para console
icon = 'icon_64.ico'
targetName = 'Dynapy TLCD Analyser.exe'

# build options
directory = 'C:/Users/MarioRaul/Desktop/DynaPy Builds/build - {}.{:02d}.{:02d}/exe.win32-3.6/'.format(year, month, day)
packages = ['matplotlib', 'atexit', 'tkinter', 'numpy']
includes = []
include_files = [os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'),
                 os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'),
                 './img/icon_64.ico',
                 './save',
                 './GUI']
excludes = ['zmq']
zip_include_packages = ['asncio', 'ctypes', 'collections', 'curses', 'dateutil', 'distutils', 'DynaPy', 'email',
                        'encodings', 'imageformats', 'importlib', 'lib2to3', 'logging', 'matplotlib', 'mpl-data',
                        'numpy', 'packaging', 'PyQt5', 'pytz', 'tcl', 'tk', 'tkinter', 'unittest', 'urllib',
                        'colorama', 'concurrent', 'html', 'http', 'ipykernel', 'IPython',
                        'ipython_genutils', 'jinja2', 'json', 'jsonschema', 'jupyter_client', 'jupyter_core',
                        'markupsafe', 'mistune', 'multiprocessing', 'nbconvert', 'nbformat', 'nose', 'notebook',
                        'pkg_resources', 'platforms', 'prompt_toolkit', 'pydoc_data', 'pygments', 'setuptools',
                        'sqlite3', 'test', 'testpath', 'tornado', 'traitlets', 'wcwidth', 'xml', 'xmlrpc',
                        ]
silent = True
optimize = 2

# shortcut options
shortcut_name = 'Dynapy TLCD Analyser'

# bdist_msi options
company_name = 'Mario Raul Freitas'
product_name = 'Dynapy TLCD Analyser'
upgrade_code = '{66620F3A-DC3F-11E2-D341-112219E9B01E}'
add_to_path = False

# setup options
name = 'Dynapy TLCD Analyser'
version = '0.4'
description = 'Dynapy TLCD Analyser'

"""
Edit the code above this comment.
Don't edit any of the code bellow.
"""

msi_data = {'Shortcut': [
    ("DesktopShortcut",  # Shortcut
     "DesktopFolder",  # Directory_
     shortcut_name,  # Name
     "TARGETDIR",  # Component_
     "[TARGETDIR]/{}".format(targetName),  # Target
     None,  # Arguments
     None,  # Description
     None,  # Hotkey
     None,  # Icon
     None,  # IconIndex
     None,  # ShowCmd
     "TARGETDIR",  # WkDir
     ),

    ("ProgramMenuShortcut",  # Shortcut
     "ProgramMenuFolder",  # Directory_
     shortcut_name,  # Name
     "TARGETDIR",  # Component_
     "[TARGETDIR]/{}".format(targetName),  # Target
     None,  # Arguments
     None,  # Description
     None,  # Hotkey
     None,  # Icon
     None,  # IconIndex
     None,  # ShowCmd
     "TARGETDIR",  # WkDir
     )
]
}

opt = {
    'build_exe': {'packages': packages,
                  'includes': includes,
                  'include_files': include_files,
                  'excludes': excludes,
                  'zip_include_packages': zip_include_packages,
                  'build_exe': directory,
                  'silent': silent,
                  'optimize': optimize
                  },
    'bdist_msi': {'upgrade_code': upgrade_code,
                  'add_to_path': add_to_path,
                  'initial_target_dir': r'[ProgramFilesFolder]\%s\%s' % (company_name, product_name),
                  'data': msi_data
                  }
}

exe = Executable(
    script=script,
    base=base,
    icon=icon,
    targetName=targetName,
    # shortcutName=shortcut_name,
    # shortcutDir='DesktopFolder'
)

setup(name=name,
      version=version,
      description=description,
      options=opt,
      executables=[exe]
      )
