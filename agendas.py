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
import hashlib
import html
import random
import re
import time
import urllib
import urllib.parse
import urllib.request
import http.client
from urllib.parse import urlparse

import pwb
import pywikibot
from pywikibot import pagegenerators

#config
site = pywikibot.Site('ca', 'teixidora')
botname = 'TeixidoraBot'

def getURL(url=''):
    raw = ''
    req = urllib.request.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
    resource = urllib.request.urlopen(req)
    raw = resource.read()
    try:
        raw = raw.decode(resource.headers.get_content_charset())
    except:
        try:
            raw = raw.decode('utf-8')
        except:
            try:
                raw = raw.decode('iso-8859-1')
            except:
                try:
                    raw = raw.decode('latin-1')
                except:
                    print('CODIFICATION ERROR')
                    raw = ''
    return raw

def unshorturl(url=''):
    parsed = urlparse(url)
    h = http.client.HTTPConnection(parsed.netloc)
    h.request('HEAD', parsed.path)
    response = h.getresponse()
    if response.status//100 == 3 and response.getheader('Location'):
        return response.getheader('Location')
    else:
        return url

def unshorturls(s=''):
    urls = re.findall(r'(?im)(https?://[^\'\"\[\]\(\)\n\r\s ]+)', s)
    urls = list(set(urls))
    for url in urls:
        try:
            s = s.replace(url, unshorturl(url=url))
        except:
            pass
    return s

def cleanIcal2(s=''):
    s = re.sub(r'(?im)\\', '', s)
    s = re.sub(r'(?im)(<p[^<>]*?>|</p>)', '', s)
    s = re.sub(r'(?im)(<span[^<>]*?>|</span>)', '', s)
    s = re.sub(r'(?im)<img[^<>]*?>', '', s)
    s = re.sub(r'(?im)</?strong>', "'''", s)
    s = re.sub(r'(?im)</?em>', "''", s)
    s = re.sub(r'(?im)</?br */*>', "\n", s)
    s = re.sub(r'(?im)<a href="([^<>"]+?)"[^<>]*?>([^<>]*?)</a>', r'[\1 \2] ', s)
    s = re.sub(r'(?im)\[([^ \[\]]*?) \1\]', r'\1 ', s)
    s = re.sub(r'(?im)\[([^ \[\]]*?) *?]', r'\1 ', s)
    s = re.sub(r'(?im) *\n *', '', s.strip()).strip()
    s = re.sub(r'  *', ' ', s)
    s = unshorturls(s=s)
    return s

def getEventsFromIcal2(url=''):
    events = []
    calendarurl = url
    url = ''
    raw = getURL(url=calendarurl)
    if not re.search(r'(?m)BEGIN:VCALENDAR\s*VERSION:2.0', raw):
        print('Error, iCal version incorrect')
        return events
    eventsical2 = raw.split('BEGIN:VEVENT')
    for event in eventsical2:
        if not re.search(r'END:VEVENT', event):
            continue
        event = event.split('END:VEVENT')[0]
        #print(event)
        errors = []
        try:
            dtstart = ''
            dtend = ''
            url = ''
            summary = ''
            description = ''
            
            dtstart = 'DTSTART;' in event and re.findall(r'(?im)^DTSTART;[^:]*?:([\dT]+)', event)[0].strip() or ''
            if 'T' in dtstart:
                dtstart = datetime.datetime.strptime(dtstart, "%Y%m%dT%H%M%S")
            else:
                dtstart = datetime.datetime.strptime(dtstart, "%Y%m%d")
            dtend = 'DTEND;' in event and re.findall(r'(?im)^DTEND;[^:]*?:([\dT]+)', event)[0].strip() or ''
            if 'T' in dtend:
                dtend = datetime.datetime.strptime(dtend, "%Y%m%dT%H%M%S")
            else:
                dtend = datetime.datetime.strptime(dtend, "%Y%m%d")
            errors.append('dates ok')
            
            #summary = 'SUMMARY:' in event and re.findall(r'(?im)^SUMMARY:(.*)', event)[0].strip() or ''
            if 'SUMMARY:' in event:
                summary = 'SUMMARY:' in event and event.split('SUMMARY:')[1].strip() or ''
                summary2 = summary.splitlines()[0]
                for line in summary.splitlines()[1:]:
                    if line.startswith(' '):
                        summary2 += line.lstrip()
                    else:
                        break
                summary = cleanIcal2(summary2).strip('.')
            errors.append('summary ok')
            
            #url = 'URL:' in event and re.findall(r'(?im)^URL:(.*)', event)[0].strip() or ''
            url = ''
            if 'URL:' in event:
                url = 'URL:' in event and event.split('URL:')[1].strip() or ''
                url2 = url.splitlines()[0]
                for line in url.splitlines()[1:]:
                    if line.startswith(' '):
                        url2 += line.lstrip()
                    else:
                        break
                url = url2
            errors.append('url ok')
            
            if not url:
                #url = 'URL;VALUE=URI:' in event and re.findall(r'(?im)^URL;VALUE=URI:(.*)', event)[0].strip() or ''
                if 'URL;VALUE=URI:' in event:
                    url = 'URL;VALUE=URI:' in event and event.split('URL;VALUE=URI:')[1].strip() or ''
                    url2 = url.splitlines()[0]
                    for line in url.splitlines()[1:]:
                        if line.startswith(' '):
                            url2 += line.lstrip()
                        else:
                            break
                    url = url2
            errors.append('uri ok')
            
            if not url:
                #create dummy url for events without url
                m = hashlib.md5()
                dummyurl = "%s%s%s" % (calendarurl, dtstart, summary)
                m.update(dummyurl.encode('utf-8'))
                url = '%s#%s' % (calendarurl, m.hexdigest())
            
            if 'DESCRIPTION:' in event:
                description = 'DESCRIPTION:' in event and event.split('DESCRIPTION:')[1].strip() or ''
                description2 = description.splitlines()[0]
                for line in description.splitlines()[1:]:
                    if line.startswith(' '):
                        description2 += line.lstrip()
                    else:
                        break
                description = cleanIcal2(description2)
            errors.append('description ok')
            
            events.append([url, {'start': dtstart, 'end': dtend, 'url': url, 'summary': summary, 'description': description}])
        except:
            print('Error while parsing event:\n%s\n\n%s\n\n' % (', '.join(errors), event))
        #events.sort()
    return events

def loadCalendars():
    calendars = []
    page = pywikibot.Page(site, 'teixidora:Agendes')
    for line in page.text.splitlines():
        #if not 'Harmo' in line:
        #    continue #fix
        m = re.findall(r'(?im)^\* *\[\[ *teixidora:Agendes/([^\[\]]+?)\]\]', line)
        for i in m:
            i = i.strip()
            calendarpage = pywikibot.Page(site, 'teixidora:Agendes/%s/Calendars' % (i))
            print('Reading %s' % (calendarpage.title()))
            if calendarpage.exists():
                calendarurls = []
                for line2 in calendarpage.text.strip().splitlines():
                    line2 = line2.strip()
                    if line2.lower().startswith('http'):
                        calendarurls.append(line2)
                    elif line2.lower().startswith('webcal'):
                        line2 = re.sub(r'(?im)^webcal:', 'http:', line2)
                        calendarurls.append(line2)
                calendars.append([i, calendarurls])
                print('Found %d calendars' % (len(calendarurls)))
    return calendars

def loadEventActionPages(sitetitle='', action=''):
    events = []
    page = pywikibot.Page(site, 'teixidora:Agendes/%s/%s' % (sitetitle, action))
    for line in page.text.splitlines():
        if '=' in line:
            for event in line.split('=')[1].split(','):
                event = event.strip()
                if event:
                    events.append(event)
    return events

def saveEventActionPages(sitetitle='', action='', events=[]):
    page = pywikibot.Page(site, 'teixidora:Agendes/%s/%s' % (sitetitle, action))
    newtext = []
    for line in page.text.splitlines():
        if '=' in line:
            line2 = line.split('=')[0] + '=' + ', '.join(events)
            newtext.append(line2)
        else:
            newtext.append(line)
    newtext = '\n'.join(newtext)
    if page.text != newtext:
        pywikibot.showDiff(page.text, newtext)
        page.text = newtext
        page.save('BOT - Updating events')

def createEvent(sitetitle='', eventurl=''):
    page = pywikibot.Page(site, 'teixidora:Agendes/%s' % (sitetitle))
    for event in page.text.split('{{Import event'):
        event = event.split('}}')[0].strip()
        esite, etitle, eweblink = ['', '', '']
        estart, eend, edescription = ['', '', '']
        for line in event.splitlines():
            if line.startswith('|site='):
                esite = line.split('|site=')[1].strip()
            elif line.startswith('|title='):
                etitle = line.split('|title=')[1].strip()
            elif line.startswith('|web link='):
                eweblink = line.split('|web link=')[1].strip()
            elif line.startswith('|start='):
                estart = line.split('|start=')[1].strip()
            elif line.startswith('|end='):
                eend = line.split('|end=')[1].strip()
            elif line.startswith('|description='):
                edescription = line.split('|description=')[1].strip()
        
        if eventurl.strip().lower() != eweblink.strip().lower():
            continue
        
        if etitle and estart:
            estarthour = ' ' in estart and estart.split(' ')[1].strip() or ''
            estarthour = len(estarthour) > 5 and ':'.join(estarthour.split(':')[:2]) or estarthour
            etext = """{{Esdeveniment pr
|event=%s
|web link=%s
|start=%s%s
|resultsWO={{Esdeveniment pr/resultsWO}}
|resultsProposals={{Esdeveniment pr/resultsProposals}}
}}""" % (etitle, eweblink, estart.split(' ')[0], estarthour and '\n|start hour=%s' % (estarthour) or '')
            etitle_ = '%s %s' % (etitle, re.sub('-', '/', estart.split(' ')[0]))
            epage = pywikibot.Page(site, etitle_)
            if not epage.exists():
                print('Creating page [[%s]]\n' % (etitle_))
                print(etext)
                epage.text = etext
                epage.save('BOT - Creating event %s' % (eweblink))
                log(log='Created page [[%s]]' % (etitle_))

def log(log=''):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log2 = "* '''%s''': %s" % (timestamp, log)
    print(log)
    logpage = pywikibot.Page(site, 'User:%s/Log' % (botname))
    newtext = logpage.text
    newtext = re.sub('<!-- log -->', '<!-- log -->\n%s' % (log2), newtext)
    logpage.text = newtext
    logpage.save('BOT - Actualitzant log')

def main():
    #load agendas
    agendas = loadCalendars()
    
    #create events if approved
    for sitetitle, urls in agendas:
        importevents = loadEventActionPages(sitetitle=sitetitle, action='Import')
        print('Loaded %d events to import for %s' % (len(importevents), sitetitle))
        importedevents = loadEventActionPages(sitetitle=sitetitle, action='Imported')
        print('Loaded %d imported events for %s' % (len(importedevents), sitetitle))
        excludedevents = loadEventActionPages(sitetitle=sitetitle, action='Excluded')
        print('Loaded %d excluded events for %s' % (len(excludedevents), sitetitle))
        for event in importevents:
            if event not in importedevents and event not in excludedevents:
                print('Importing event %s from %s' % (event, sitetitle))
                createEvent(sitetitle=sitetitle, eventurl=event)
                importevents.remove(event)
                importedevents.append(event)
        saveEventActionPages(sitetitle=sitetitle, action='Import', events=importevents)
        saveEventActionPages(sitetitle=sitetitle, action='Imported', events=importedevents)
    
    #paste more events
    for sitetitle, urls in agendas:
        importedevents = loadEventActionPages(sitetitle=sitetitle, action='Imported')
        excludedevents = loadEventActionPages(sitetitle=sitetitle, action='Excluded')
        
        events_plain = ''
        for url in urls:
            print('Getting events from %s' % (url))
            time.sleep(1)
            events = getEventsFromIcal2(url=url)
            for k2, v2 in events:
                #imported previously?
                if v2['url'] in importedevents:
                    continue
                #excluded event?
                if v2['url'] in excludedevents:
                    continue
                
                event = """{{Import event
|site=%s
|title=%s
|web link=%s
|start=%s
|end=%s
|description=%s
}}""" % (sitetitle, v2['summary'], v2['url'], v2['start'], v2['end'], v2['description'])
                events_plain += event
        newtext = '{{teixidora:Agendes/%s/header}}\n%s\n{{teixidora:Agendes/%s/footer}}' % (sitetitle, events_plain, sitetitle)
        page = pywikibot.Page(site, 'teixidora:Agendes/%s' % (sitetitle))
        if page.text != newtext:
            pywikibot.showDiff(page.text, newtext)
            page.text = newtext
            page.save('BOT - Updating events')

if __name__ == '__main__':
    main()
