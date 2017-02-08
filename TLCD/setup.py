from cx_Freeze import setup, Executable

# executable options
script = 'main.py'
base = 'Win32GUI'       # Win32GUI para gui's e None para console
icon = 'icon_64.ico'
targetName = 'Dynapy TLCD Analyser.exe'

# build options
packages = ['matplotlib', 'atexit', 'PyQt4.QtCore', 'tkinter', 'C:/Python34/Lib/site-packages/DynaPy']
includes = []
include_files = ['icon_64.ico']

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
    ("DesktopShortcut",         # Shortcut
     "DesktopFolder",           # Directory_
     shortcut_name,      # Name
     "TARGETDIR",               # Component_
     "[TARGETDIR]/{}".format(targetName),  # Target
     None,                      # Arguments
     None,                      # Description
     None,                      # Hotkey
     None,                      # Icon
     None,                      # IconIndex
     None,                      # ShowCmd
     "TARGETDIR",               # WkDir
     ),

    ("ProgramMenuShortcut",         # Shortcut
     "ProgramMenuFolder",           # Directory_
     shortcut_name,      # Name
     "TARGETDIR",               # Component_
     "[TARGETDIR]/{}".format(targetName),  # Target
     None,                      # Arguments
     None,                      # Description
     None,                      # Hotkey
     None,                      # Icon
     None,                      # IconIndex
     None,                      # ShowCmd
     "TARGETDIR",               # WkDir
     )
    ]
}

opt = {
    'build_exe': {'packages': packages,
                  'includes': includes,
                  'include_files': include_files
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
