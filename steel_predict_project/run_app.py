from steel_predict_project.wsgi import application
from waitress import serve
import django
import os
import sys
import threading
import webbrowser
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "steel_predict_project.settings"
)

django.setup()


def open_browser():
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    threading.Thread(target=open_browser).start()
    serve(application, host="127.0.0.1", port=8000)
