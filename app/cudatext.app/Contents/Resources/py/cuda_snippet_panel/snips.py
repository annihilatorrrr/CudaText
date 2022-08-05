
def parse_usual_snip(s):

    name, text = s.split('=', maxsplit=1) if '=' in s else (s, s)
    return {'kind': 'line', 'name': name, 'text': text}

