import logging
import os
import requests

CATHSM_DEBUG=os.environ['CATHSM_DEBUG'] if 'CATHSM_DEBUG' in os.environ else False 

#logging.basicConfig(level=logging.INFO)

debug = logging.StreamHandler()
debug.setLevel(logging.DEBUG)
debug_format = logging.Formatter('%(asctime)s %(name)15s:%(lineno)-5s %(levelname)-8s | %(message)s')
debug.setFormatter(debug_format)

info = logging.StreamHandler()
info.setLevel(logging.INFO)
info_format = logging.Formatter('%(asctime)s %(levelname)-8s | %(message)s', 
    datefmt='%Y-%m-%d %H:%M')
info.setFormatter(info_format)

# add the handler to the root logger
root = logging.getLogger('')
if CATHSM_DEBUG:
    root.setLevel(logging.DEBUG)
    root.addHandler(debug)

    # sort requests logging
    # http://docs.python-requests.org/en/master/api/#api-changes
    try:
        from http.client import HTTPConnection
    except ImportError:
        from httplib import HTTPConnection
    HTTPConnection.debuglevel = 1

    requests_log = logging.getLogger('urllib3')
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

else:
    root.setLevel(logging.INFO)
    root.addHandler(info)
