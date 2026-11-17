import sys
import os

# PythonAnywhere fayl yo'li
# Masalan: /home/<username>/any_file_to_pdf_bot
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from flask_app import app as application
