import re
import penman
from pathlib import Path
def replace_slash(input_string):
    # Pattern to match '/' followed by any non-letter character
    pattern = r'/\s(?!(name|[a-zA-Z]))'

    # Replace matched patterns with a space
    result_string = re.sub(pattern, ' ', input_string)

    return result_string

def replace_func(match):
    # If the character following '>' is a letter, replace '>' with '/'
    if match.group(1).isalpha():
        return '/ '
    # Otherwise, replace '>' with an empty string
    else:
        return ' '


output = 'generated_predictions.txt'
sents = 'amr/test_all.txt'
o = Path(output).read_text().strip().split('\n')
sents = Path(sents).read_text().strip().split('\n')
assert len(o) == len(sents)
with open('amr/post_test_all.txt', 'w') as out, open('amr/error.txt', 'a') as error:
    e = 0
    for i, x in enumerate(o):
        if x.endswith('</AMR>'):
            try:
                new = re.sub(r"\s*</lit>\s*", "\" ", x[:-6])
                new = re.sub(r"\s*<lit>\s*", " \"", new)
                new = re.sub(r'<pointer:', 'p', new)
                new = re.sub(r'>\s*', " / ", new)
                new = re.sub(r'\)\s*', ')', new)
                new = replace_slash(new)
                new = re.sub(r':\s', ':', new)
                new = new.strip()
                text = sents[i]
                out.write(f'# ::snt {text}\n')
                p = penman.decode(new)
                g = penman.encode(p)
                out.write(f'{g}\n\n')
            except:
                e += 1
                print(e)
                text = sents[i]
                out.write(f'# ::snt {text}\n')
                out.write(f'( p0/ entity)\n\n')
                error.write(f'# ::snt {text}\n')
                error.write(f'{new}\n\n')



