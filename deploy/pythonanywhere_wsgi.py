"""Copy to the WSGI configuration file linked from PythonAnywhere's Web tab.

The private environment file is created on the server, never committed.
The Web tab's virtualenv must match its selected Python version.
"""

import json
import os
import sys
from pathlib import Path

HOME = Path('/home/EzekielADDUCorpuz')
PROJECT = HOME / 'Corpuz_MFD_todo'
ENVIRONMENT_FILE = HOME / '.config' / 'corpuz-todo' / 'environment.json'

with ENVIRONMENT_FILE.open() as environment_file:
    os.environ.update(json.load(environment_file))

if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

os.environ['DJANGO_SETTINGS_MODULE'] = 'MyFirstDjango.settings'

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
