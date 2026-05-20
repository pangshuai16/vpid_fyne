import os
import sys
import tempfile

if getattr(sys, 'frozen', False):
    os.environ['PATH'] = sys._MEIPASS + os.pathsep + os.environ.get('PATH', '')

    # Linux: Use system fontconfig to avoid version compatibility issues
    if sys.platform.startswith('linux'):
        os.environ.pop('FONTCONFIG_FILE', None)
        os.environ.pop('FONTCONFIG_PATH', None)
        os.environ.pop('XDG_DATA_HOME', None)
        os.environ.pop('XDG_CONFIG_HOME', None)

    try:
        import win32com
        gen_py_dir = os.path.join(tempfile.gettempdir(), 'vpid_viewer_gen_py')
        if not os.path.exists(gen_py_dir):
            os.makedirs(gen_py_dir)
        win32com.__gen_path__ = gen_py_dir
    except ImportError:
        pass
