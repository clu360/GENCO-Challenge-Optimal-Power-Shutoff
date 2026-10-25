import json
def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
