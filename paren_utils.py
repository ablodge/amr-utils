import re

def mark_depth(text):
    Paren_RE = re.compile('^(?P<pre>([^()])*)(?P<paren>[()])')
    i = 0
    while Paren_RE.match(text):
        s = Paren_RE.match(text).group('pre')
        p = Paren_RE.match(text).group('paren')
        if p == '(':
            i += 1
            text = Paren_RE.sub(s + f'<{i}>', text, 1)
        else:
            text = Paren_RE.sub(s + f'</{i}>', text, 1)
            i -= 1
    return text


def unmark_depth(deep_text):
    text = re.sub('<[0-9]+>','(',deep_text)
    text = re.sub('</[0-9]+>', ')', text)
    return text

def depth_at(text, i):
    depth = 0
    for j, ch in enumerate(text):
        if ch == ')': depth -= 1
        if j==i: return depth
        if ch == '(': depth += 1
    return -1

def paren_iter(text):
    deep_text = mark_depth(text)
    j = 1
    while f'<{j}>' in deep_text:
        Paren_RE = re.compile(f'<{j}>(?P<text>.*?)</{j}>', re.DOTALL)
        for p in Paren_RE.finditer(deep_text):
            p = p.group('text')
            p = re.sub('<[0-9]+>', '(', p)
            p = re.sub('</[0-9]+>', ')', p)
            yield p
        j+=1

def test_parens(text):
    depth = 0
    for ch in text:
        if ch == '(': depth += 1
        if ch == ')': depth -= 1
        if depth < 0: return False
    if not depth == 0: return False
    return True

def max_depth(text):
    max = 0
    depth = 0
    for ch in text:
        if ch == '(': depth += 1
        if max < depth: max = depth
        if ch == ')': depth -= 1
    return max
