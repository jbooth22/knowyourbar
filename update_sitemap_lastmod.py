"""Set every <lastmod> in sitemap.xml to the date the page was last rebuilt.

For each URL in the sitemap, reads the matching page (index.html for "/",
otherwise <slug>.html) and takes the newest date it finds in either a
"dateModified" JSON-LD field or the footer "Updated YYYY-MM-DD" line. Adds a
<lastmod> where one is missing. Pages with no date are left as they are and
listed. Run it last, after the page builds:

    python3 update_sitemap_lastmod.py
"""
import os, re

SITEMAP = 'sitemap.xml'


def page_date(path):
    if not os.path.exists(path):
        return None
    s = open(path, encoding='utf-8').read()
    dates = re.findall(r'"dateModified":\s*"(\d{4}-\d{2}-\d{2})"', s) + re.findall(r'Updated (\d{4}-\d{2}-\d{2})<', s)
    return max(dates) if dates else None


def main():
    xml = open(SITEMAP, encoding='utf-8').read()
    changed, undated = 0, []

    def fix(m):
        nonlocal changed
        block = m.group(0)
        loc = re.search(r'<loc>https://knowyourbar\.com/([^<]*)</loc>', block).group(1)
        page = 'index.html' if loc == '' else f'{loc}.html'
        d = page_date(page)
        if not d:
            undated.append(loc or '/')
            return block
        if '<lastmod>' in block:
            new = re.sub(r'<lastmod>[^<]*</lastmod>', f'<lastmod>{d}</lastmod>', block)
        else:
            new = re.sub(r'(</loc>)', rf'\1\n    <lastmod>{d}</lastmod>', block, count=1)
        if new != block:
            changed += 1
        return new

    xml = re.sub(r'<url>.*?</url>', fix, xml, flags=re.S)
    open(SITEMAP, 'w', encoding='utf-8').write(xml)
    print(f'{SITEMAP}: {changed} lastmod dates updated' + (f'; no date found for: {", ".join(undated)}' if undated else ''))


if __name__ == '__main__':
    main()
