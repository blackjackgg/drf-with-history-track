import json
from rest_framework.utils.encoders import JSONEncoder


def serdata2json(serdata):
    ret = json.loads(json.dumps(dict(serdata), cls=JSONEncoder,))
    return ret
