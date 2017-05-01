import re

def find_img_src(src):
    if re.search(r'(p[a-z]\.)jpg', src):
        return src.replace(re.search(r'(p[a-z]\.)jpg', src).group(1), 'pl.')
    elif re.search(r'/consumer_game/', src):
        return src.replace('js-', '-')
    elif re.search(r'js\-([0-9]+)\.jpg$', src):
        return src.replace('js-', 'jp-')
    elif re.search(r'ts\-([0-9]+)\.jpg$', src):
        return src.replace('ts-', 'tl-')
    elif re.search(r'(\-[0-9]+\.)jpg$', src):
        return src.replace(re.search(r'(\-[0-9]+\.)jpg$', src).group(1),
                           'jp' + re.search(r'(\-[0-9]+\.)jpg$', src).group(1))
    else:
        return src.replace('-', 'jp-')

urls = ['http://pics.dmm.co.jp/digital/video/181dse01182/181dse01182-1.jpg',
        'http://pics.dmm.co.jp/digital/video/33svs00035/33svs00035pt.jpg',
        'http://pics.dmm.co.jp/digital/video/jusd00490/jusd00490pt.jpg']
for url in urls:
    print find_img_src(url)