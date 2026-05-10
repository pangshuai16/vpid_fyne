import os
import sys
import tempfile

if getattr(sys, 'frozen', False):
    os.environ['PATH'] = sys._MEIPASS + os.pathsep + os.environ.get('PATH', '')

    try:
        import win32com
        gen_py_dir = os.path.join(tempfile.gettempdir(), 'vpid_viewer_gen_py')
        if not os.path.exists(gen_py_dir):
            os.makedirs(gen_py_dir)
        win32com.__gen_path__ = gen_py_dir
    except ImportError:
        pass
