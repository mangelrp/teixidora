#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2018 Teixidora
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import html
import re
import time
import urllib
import urllib.parse
import urllib.request

import pwb
import pywikibot
from pywikibot import pagegenerators

#config
site = pywikibot.Site('ca', 'teixidora')
botname = 'TeixidoraBot'
catnameimport = 'Apunts per importar amb bot'
catnameimported = 'Apunts importats amb bot'

def testEdit():
    pagetitle = 'User:%s/Sandbox' % (botname)
    page = pywikibot.Page(site, pagetitle)
    page.text = 'test edit %s' % (datetime.datetime.now())
    page.save('BOT - Test edit')

def statsPadServices():
    category = pywikibot.Category(site, 'Esdeveniments')
    gen = pagegenerators.CategorizedPageGenerator(category)
    padservers = {}
    for page in gen:
        #print(page.title())
        padurls = re.findall(r'notes pad url\s*=\s*(https?://[^\s\|]+)', page.text)
        #print(padurls)
        for padurl in padurls:
            padserver = padurl.split('//')[1].split('/')[0]
            if padserver in padservers:
                padservers[padserver] += 1
            else:
                padservers[padserver] = 1
    padservers_list = [[v, k] for k, v in padservers.items()]
    padservers_list.sort(reverse=True)
    print('\n'.join(['%s %s' % (k, v) for k, v in padservers_list]))

def getPadContent(url=''):
    if 'pad.lamardebits.org' in url or \
        'etherpad.guifi.net' in url or \
        'public.etherpad-mozilla.org' in url or \
        'pad.riseup.net' in url or \
        'titanpad.com' in url or \
        'etherpad.wikimedia.org' in url or \
        'beta.etherpad.org' in url or \
        'geoartivismes.titanpad.com' in url:
        content = getEtherpadContent(url=url)
        return etherpad2mediawiki(content=content)
    elif 'hackpad.com' in url:
        content = getHackpadContent(url=url)
        return hackpad2mediawiki(content=content)
    #fallback default to Etherpad
    content = getEtherpadContent(url=url)
    return etherpad2mediawiki(content=content)

def getEtherpadContent(url=''):
    content = ''
    if url:
        urlhtml = ''
        if '/titanpad.com/' in url:
            urlhtml = 'https://titanpad.com/ep/pad/export/%s/latest?format=html' % (url.split('titanpad.com/')[1])
        elif '.titanpad.com/' in url:
            urlhtml = 'https://%s.titanpad.com/ep/pad/export/%s/latest?format=html' % (url.split('.titanpad.com/')[0].split('://')[1], url.split('titanpad.com/')[1])
        else:
            urlhtml = url + '/export/html'
        raw = getURL(url=urlhtml)
        #print(raw)
        if '<body>' in raw and '</body>' in raw:
            content = raw.split('<body>')[1].split('</body>')[0]
            content = urllib.parse.unquote(content)
            content = html.unescape(content)
            #remove trailing JS code in etherpad-mozilla
            content = content.replace('<div style="display:none"><a href="/javascript" data-jslicense="1">JavaScript license information</a></div>', '')
            content = content.strip()
    return content

def getEtherpadAuthors(url=''):
    authors = [[], 0]
    
    return authors

def getPadAuthors(url=''):
    if 'pad.lamardebits.org' in url or \
        'etherpad.guifi.net' in url or \
        'public.etherpad-mozilla.org' in url or \
        'pad.riseup.net' in url or \
        'titanpad.com' in url or \
        'etherpad.wikimedia.org' in url or \
        'beta.etherpad.org' in url or \
        'geoartivismes.titanpad.com' in url:
        authors = getEtherpadAuthors(url=url)
        return authors
    elif 'hackpad.com' in url:
        authors = getHackpadAuthors(url=url)
        return authors
    #fallback default to Etherpad
    authors = getEtherpadAuthors(url=url)
    return authors

def getURL(url=''):
    raw = ''
    req = urllib.request.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
    try:
        raw = urllib.request.urlopen(req, timeout=15).read().strip().decode('utf-8')
    except:
        sleep = 10 # seconds
        maxsleep = 100
        while sleep <= maxsleep:
            print('Error while retrieving: %s' % (url))
            print('Retry in %s seconds...' % (sleep))
            time.sleep(sleep)
            try:
                raw = urllib.request.urlopen(req, timeout=15).read().strip().decode('utf-8')
            except:
                pass
            sleep = sleep * 2
    return raw

def etherpad2mediawiki(content=''):
    content = re.sub(r'(?im)<\s*([^<>]+?)\s*>', r'<\1>', content)
    content = re.sub(r'(?im)<\s*br\s*/?\s*>', r'\n', content)
    content = re.sub(r'(?im)(\'\'+)', r'<nowiki>\1</nowiki>', content) #for seconds ''
    content = re.sub(r'(?im)<b>(.*?)</b>', r"'''\1'''", content)
    content = re.sub(r'(?im)<strong>(.*?)</strong>', r"'''\1'''", content)
    content = re.sub(r'(?im)<i>(.*?)</i>', r"''\1''", content)
    content = re.sub(r'(?im)<em>(.*?)</em>', r"''\1''", content)
    content = re.sub(r'(?im)<a href="([^<>]*?)">([^<>]*?)</a>', r"[\1 \2]", content)
    #headers
    lines = []
    for line in content.splitlines():
        line = line.rstrip() #keep left whitespaces, but remove right whitespaces
        line = re.sub(r'(?im)^\s*(<h\d+>)', r'\1', line) #remove left whitespaces when headers
        lines.append(line)
    content = '\n'.join(lines)
    for i in range(1, 10):
        content = re.sub(r'<h%d>(.*?)</h%d>' % (i, i), r'\n%s \1 %s\n' % ('='*i, '='*i), content)
    content = re.sub(r'(?im)^ *=', '=', content)
    content = re.sub(r'(?im)^=+ +=+\n', '', content) #remove empty headers == ==
    content = re.sub(r'(?im)\n', '\n\n', content)
    content = re.sub(r'(?im)\n\n\n+', r'\n\n', content)
    #links
    content = re.sub(r'\[([^\[\] ]+?) \1\]', r'\1', content)
    #html lists
    content = re.sub(r'(<ul class="bullet">|<ol class="number">|<li>|</ul>|</ol>)', r'\n\1', content)
    content2 = []
    tagchar = ''
    indent = 0
    for line in content.splitlines():
        if re.search(r'(?im)<ul[^<>]*?>', line):
            tagchar = '*'
            indent += 1
            line = re.sub('(?im)<ul[^<>]*?>', '', line)
        elif re.search(r'(?im)<ol[^<>]*?>', line):
            tagchar = '#'
            indent += 1
            line = re.sub('<ol[^<>]*?>', '', line)
        if re.search(r'(?im)</ul>', line): #separate
            indent -= 1
            line = re.sub(r'(?im)</ul>', r'', line)
        if re.search(r'(?im)</ol>', line): #separate
            indent -= 1
            line = re.sub(r'(?im)</ol>', r'', line)
        if indent > 1:
            line = re.sub(r'(?im)<li>(.*?)</li>', r'%s%s \1\n' % (tagchar*(indent-1), tagchar), line)
        else:
            line = re.sub(r'(?im)<li>(.*?)</li>', r'%s \1\n' % (tagchar*indent), line)
        line = re.sub(r'(?im)\n?<li>', r'%s ' % (tagchar*indent), line)
        line = re.sub(r'(?im)\n?</li>', r'', line)
        content2.append(line)
    content = '\n'.join(content2)
    content = re.sub(r'(?im)\n\n+([\*\#])', r'\n\1', content)
    content = re.sub(r'(?im)^([\*\#]) +', r'\1 ', content)
    content = re.sub(r'(?im)\n\n\n+', r'\n\n', content)
    #other lists
    content = re.sub(r'(?im)^\s*•\s*', '* ', content)
    #syntax colours
    content = re.sub(r'(?im)<([^<>]+?) style="color: *?\1;">(.*?)</\1>', r'\2', content)
    return content

def removeNoImport(content=''):
    tags = [
        ['<noimport>', '</noimport>'], 
        ['#noimport-on', '#noimport-off'], 
        ['<noinclude>', '</noinclude>'], 
        ['#noinclude-on', '#noinclude-off'], 
    ]
    for tagstart, tagend in tags: #converting to lowercase
        content = re.sub(r'(?im)%s' % (tagstart), tagstart, content)
        content = re.sub(r'(?im)%s' % (tagend), tagend, content)
    for tagstart, tagend in tags:
        content2 = []
        for x in content.split(tagstart):
            if not content2:
                content2.append(x)
            else:
                content2.append(x.split(tagend)[1])
        content = ''.join(content2)
    return content

def testImportPads():
    #url = 'https://pad.lamardebits.org/p/Sobtec2017rodona'
    #url = 'http://etherpad.guifi.net/p/ttn'
    #url = 'https://public.etherpad-mozilla.org/p/eradigital15f'
    #url = 'https://titanpad.com/democraciaDEcualquiera'
    #url = 'https://etherpad.wikimedia.org/p/vt26museus'
    #url = 'https://beta.etherpad.org/p/procomuns-pa1b'
    url = 'https://geoartivismes.titanpad.com/7'
    content = getPadContent(url=url)
    content = removeNoImport(content=content)
    print(content)
    
    pagetitle = 'User:%s/Sandbox' % (botname)
    page = pywikibot.Page(site, pagetitle)
    page.text = content
    page.save('BOT - Test edit')

def log(log=''):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log2 = "* '''%s''': %s" % (timestamp, log)
    print(log)
    logpage = pywikibot.Page(site, 'User:%s/Log' % (botname))
    newtext = logpage.text
    newtext = re.sub('<!-- log -->', '<!-- log -->\n%s' % (log2), newtext)
    logpage.text = newtext
    logpage.save('BOT - Actualitzant log')

def getPageHistoryAuthors(page=''):
    history = page.getVersionHistory()
    authors = [x[2] for x in history]
    authors = set(authors)
    authors = list(authors)
    return authors

def importPad(padurl='', content='', apuntspage=''):
    authors = getPadAuthors(url=padurl)
    apuntspage.text = """{{Notes
|content=
%s
|notes pad url=%s
|note-takers=%s
|anonymous-note-takers=%s
}}""" % (content, padurl, ', '.join(authors[0]), authors[1])
    apuntspage.save('BOT - Imported pad from %s' % (padurl))
    log(log='Imported [%s pad] into [[%s|apunts page]]' % (padurl, apuntspage.title()))

def importLabels(padurl='', page='', content=''):
    label2paramspage = pywikibot.Page(site, 'User:%s/Labels' % (botname))
    label2paramslist = []
    for line in label2paramspage.text.splitlines():
        if line.strip():
            label2paramslist.append(line)
    print(label2paramslist)
    label2params = {}
    for label, param in [re.sub(r'=+', '=', x).split('=') for x in label2paramslist]:
        label2params[label.strip()] = param.strip()
    newtext = page.text
    
    if re.search(r'resultsWO *= *{{Esdeveniment pr/resultsWO}}', newtext):
        newtext = re.sub(r'resultsWO *= *{{Esdeveniment pr/resultsWO}}', r'resultsWO={{Esdeveniment pr/resultsWO\n|weakness=\n|opportunity=\n}}', newtext)
    if re.search(r'resultsProposals *= *{{Esdeveniment pr/resultsProposals}}', newtext):
        newtext = re.sub(r'resultsProposals *= *{{Esdeveniment pr/resultsProposals}}', r'resultsProposals={{Esdeveniment pr/resultsProposals\n|proposal=\n}}', newtext)
    #print(newtext)
    #print(content)
    print(label2params.items())
    #labels == Style ==
    for label, param in label2params.items():
        section_r = '(?im)^=+[ #]*%s[ #]*=+' % (label)
        section = re.findall(section_r, content)
        if section:
            section = section[0]
            value = content.split(section)[1].split('\n=')[0]
            content = content.replace(section+value, '') #remove label from content
            value = value.strip()
            if value and not '<s>' in value.lower() and not '</s>' in value.lower():
                if re.search(r'%s *=[^\|\}]*' % (param), newtext):
                    newtext = re.sub(r'(%s *=)([^\|\}]*)' % (param), r'\1\2\n%s\n' % (value), newtext)
                else:
                    newtext = re.sub(r'({{Esdeveniment pr[^/])', r'\1\n|%s=%s' % (param, value), newtext) #fix mejorar orden dentro de la plantilla?
    #labels #style-on ... #style-off
    for label, param in label2params.items():
        tag_r = r'(?im)(#%s-on)([^#]*?)(#%s-off)' % (label, label)
        tags = re.findall(tag_r, content)
        for tagstart, value, tagend in tags:
            value = value.strip()
            if value:
                if re.search(r'%s *=[^\|\}]*' % (param), newtext):
                    newtext = re.sub(r'(%s *=)([^\|\}]*)' % (param), r'\1\2\n%s\n' % (value), newtext)
                else:
                    newtext = re.sub(r'({{Esdeveniment pr[^/])', r'\1\n|%s=%s' % (param, value), newtext) #fix mejorar orden dentro de la plantilla?
        #quitamos solo los label no el contenido que se rodea
        content = re.sub(r'(?im)(#%s-on)' % (label), r'', content)
        content = re.sub(r'(?im)(#%s-off)' % (label), r'', content)
    if newtext != page.text:
        pywikibot.showDiff(page.text, newtext)
        page.text = newtext
        page.save('BOT - Imported parameters from %s' % (padurl))
    return content

def switchCheckbox(oldvalue='', newvalue='', page='', apuntspage=''):
    newtext = re.sub('bot import=%s' % (oldvalue), 'bot import=%s' % (newvalue), page.text)
    if newtext != page.text:
        pywikibot.showDiff(page.text, newtext)
        page.text = newtext
        page.save('BOT - Imported pad in [[%s]]' % (apuntspage.title()))

def importKeywords(padurls=[], page='', content=''):
    keywordslimit = 20 # save only this number of keywords
    #load excluded keywords
    keywordsexcludedpage = pywikibot.Page(site, 'User:%s/Keywords excluded' % (botname))
    keywordsexcluded = list(set(keywordsexcludedpage.text.splitlines()))
    keywordsexcluded.sort()
    keywordsexcludedpage.text = '\n'.join(keywordsexcluded)
    keywordsexcludedpage.save('BOT - Sorting keywords')
    #calculate most frequent keywords in content
    keywords = content.split(' ')
    keywordsdic = {}
    for keyword in keywords:
        keyword = keyword.lower().strip()
        if len(keyword) > 2 and \
            keyword not in keywordsexcluded and \
            not re.search(r'(?im)[^a-z0-9áéíóúàèìòùäëïöüâêîôûñç·]', keyword):
            if keyword in keywordsdic:
                keywordsdic[keyword] += 1
            else:
                keywordsdic[keyword] = 1
    keywordslist = [[v, k] for k, v in keywordsdic.items()]
    keywordslist.sort(reverse=True)
    #save keywords
    keywordsplain = ', '.join([k for v, k in keywordslist[:keywordslimit]])
    newtext = page.text
    keywordsparamname = 'high frequency words'
    if re.search(r'\|\s*%s\s*=[^\|\}]*' % (keywordsparamname), newtext):
        newtext = re.sub(r'(?im)(\|\s*%s\s*=)[^\|\}]*' % (keywordsparamname), r'\1%s\n' % (keywordsplain), newtext)
    else:
        newtext = re.sub(r'({{Esdeveniment pr[^/])', r'\1|%s=%s\n' % (keywordsparamname, keywordsplain), newtext)
    if newtext != page.text:
        pywikibot.showDiff(page.text, newtext)
        page.text = newtext
        page.save('BOT - Imported keywords from %s' % (' '.join(padurls)))

def importPadsCheckbox():
    category = pywikibot.Category(site, catnameimport)
    gen = pagegenerators.CategorizedPageGenerator(category)
    print('Reading [[Category:%s]]' % (catnameimport))
    #pages = [pywikibot.Page(site, 'Usuari:TeixidoraBot/Sandbox3')]
    #for page in pages:
    for page in gen:
        print('\n== %s ==\n' % (page.title()))
        #get pads to import
        padnotes = page.text.split('{{Esdeveniment pr/padnotes')[1:]
        padnumber = 0
        pads = []
        for padnote in padnotes:
            padnote = padnote.split('}}')[0]
            try:
                padnumber += 1
                padurl = re.findall(r'(?im)notes pad url\s*=\s*(https?://[^\s\|]+)', padnote)[0]
                importornot = re.findall(r'(?im)bot import\s*=\s*Si', padnote) and True or False
                pads.append([padnumber, padurl, importornot])
            except:
                pass
        print('Pads found:\n%s' % (pads))
        contentall = ''
        padurls = []
        for padnumber, padurl, importornot in pads:
            print('Padurl: %s' % (padurl))
            if importornot:
                #get pad content
                padurls.append(padurl)
                content = getPadContent(url=padurl)
                content = removeNoImport(content=content)
                contentall += '\n' + content
                #create redirect from apunts to apunts/01
                """if padnumber == 1:
                    redapuntstitle = '%s/apunts' % (page.title())
                    redapuntspage = pywikibot.Page(site, redapuntstitle)
                    if not redapuntspage.exists():
                        redapuntspage.text = '#REDIRECT [[%s/apunts/01]]' % (page.title())
                        redapuntspage.save('BOT - Redirect')"""
                #save pad and params
                apuntstitle = '%s/apunts/%02d' % (page.title(), padnumber)
                apuntspage = pywikibot.Page(site, apuntstitle)
                if not apuntspage.exists() or \
                    (apuntspage.exists() and len(apuntspage.text) < 5) or \
                    '/Sandbox' in apuntstitle or \
                    getPageHistoryAuthors(page=apuntspage) == [botname]:
                    #import labels into template parameters and remove them from content
                    content = importLabels(padurl=padurl, page=page, content=content)
                    #import pad into apunts
                    importPad(padurl=padurl, content=content, apuntspage=apuntspage)
                    #remove checkbox
                    switchCheckbox(oldvalue='Si', newvalue='Fet', page=page, apuntspage=apuntspage)
                    print('Imported correctly')
                else:
                    log(log='[[%s|Apunts page]] exists, skiping. [%s Pad] not imported.' % (apuntstitle, padurl))
                    switchCheckbox(oldvalue='Si', newvalue='Fet', page=page, apuntspage=apuntspage)
            else:
                print('Not set to import, skiping...')
        #import keywords
        if padurls:
            importKeywords(padurls=padurls, page=page, content=contentall)

def main():
    #testEdit()
    #statsPadServices()
    #testImportPads()
    importPadsCheckbox()

if __name__ == '__main__':
    main()
