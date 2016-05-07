#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# By Fred John (https://github.com/fredjohnd) - 2016-04-16

#########################################################################

import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmc,xbmcaddon,HTMLParser,sys,json,base64

from xbmcgui import ListItem
from BeautifulSoup import BeautifulSoup

addon_id    = 'plugin.video.telenovelasPT'
selfAddon   = xbmcaddon.Addon(id=addon_id)
addonfolder = selfAddon.getAddonInfo('path')
artfolder   = addonfolder + '/resources/img/'
fanart      = addonfolder + '/fanart.jpg'
base 		= 'http://tvstoryoficialportugaltv.blogspot.co.uk/'

# All these shows are on an external website so we don't want to display them
def isExternal(title):
		externalShows = ["ACHAS QUE SABES DANÇAR?", "A QUINTA", "CASA DOS SEGREDOS 5", 
		"COOK OFF", "CRISTINA", "DANÇA COM AS ESTRELAS 3", "DESAFIO FINAL 3", "FACTOR X", 
		"GOT TALENT", "GOT TALENT PORTUGAL 2016", "LOVE ON TOP", "LUTA PELO PODER", 
		"MAR SALGADO", "MASTERCHEF", "PEQUENOS GIGANTES", "PEQUENOS GIGANTES 2", 
		"PESO PESADO TEEN", "SOM DE CRISTAL", "SHARK TANK", "TEMOS NEGÓCIO",
		"ÍDOLOS", "THE VOICE PORTUGAL"]
		return title in externalShows

# Convert a value into a slug
def slugify(value):
	value = cleanHtml(value.encode('ascii', 'ignore'))
	value = value.replace(' ', '-')
	return value.lower()

def mainMenu():

		link = openURL(base)
		link = unicode(link, 'latin-1', errors='replace')
		soup = BeautifulSoup(link)
		novelasElements = soup.find('div',{ "id" : "PageList3" }).findAll('a')

		novelas = []
		i = 0;

		# Loop each element and get valid shows
		for novela in novelasElements:
			i 		+= 10
			url 	= novela["href"]
			title 	= cleanHtml(novela.text.encode('latin-1', 'replace'))
			slugTitle = slugify(novela.text)
			artImage= artfolder + slugTitle + '.jpg'

			isShowExternal = isExternal(title)
			if isShowExternal: 	continue
			if not title: 		continue
			novelas.append([title, url, i ,artImage])

		# Sort shows by title
		novelas.sort(key=lambda elem: elem[0])

		# Add them to the UI
		for title, url, i, artImage in novelas:
			addDir(title, url, i, artImage)
		
		xbmcplugin.setContent(int(sys.argv[1]), 'movies')
		xbmc.executebuiltin('Container.SetViewMode(500)')

def getEpisodes(url, iconimage):
		link = openURL(url)
		link = unicode(link, 'latin-1', errors='replace')
		soup = BeautifulSoup(link)

		possibleEpisodes = soup.find('div',{ "id" : "main" }).findAll('h3')
		episodes = []
		imgTemp = ""

		try:
			imgTemp = soup.find('div', {"class" : "separator"}).find('img')
			imgTemp = imgTemp['src']
		except:
			imgTemp = iconimage

		for ep in possibleEpisodes:
				try:
						titTemp = cleanHtml(ep.a.text.encode('latin-1', 'replace'))
						urlTemp = ep.a['href']
						temp = [titTemp, urlTemp ,imgTemp, ''] 
						episodes.append(temp)
				except:
						pass
				
		total = len(episodes)

		for title, url2, img, plot in episodes:
				title = cleanHtml(title)
				addDir(title, url2, 1000, img, False, total, plot)
				
		xbmcplugin.setContent(int(sys.argv[1]), 'movies')
		xbmc.executebuiltin('Container.SetViewMode(500)')

def getAvailableStreams(url):

		link = openURL(url)
		soup = BeautifulSoup(link)
		possibleSources = soup.findAll(re.compile("frame"))

		sources = []
		for possibleSource in possibleSources:
			url = possibleSource['src']
			
			# Check for vimeo
			if url.find("vimeo") != -1:
				vimeoSources = getStreamVimeo(url)
				for source in vimeoSources:
					sources.append(source)

			elif url.find("youtube") != -1:
				youtubeSources = getStreamYoutube(url)
				sources.append(youtubeSources)

			elif url.find("dailymotion") != -1:
				dailySources = getStreamDailyMotion(url)
				for source in dailySources:
					sources.append(source)

		return sources

def getStreamDailyMotion(url):

	videoId = url.split('video/')[1].split('?')[0]
	configURL = "http://www.dailymotion.com/player/metadata/video/" + videoId;
	response = openURL(configURL)
	data = json.loads(response)

	sources = []

	try:
		if data['error']['message']:
			xbmcgui.Dialog().ok("Erro", data['error']['message'])
			return []
	except:
		pass

	if not data['qualities']: return []

	for q in data['qualities']:
		
		for source in data['qualities'][q]:
			tmp = ["DailyMotion (" + q + ")", source['url']]
			sources.append(tmp)

	return sources


def getStreamYoutube(url):
		videoId = url.split('embed/')[1].split('?')[0]
		stream = ["Youtube", "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + videoId]
		return stream

def getStreamVimeo(url):

		videoId = url.split('video/')[1].split('?')[0]
		configURL = "http://player.vimeo.com/video/" + videoId + "/config"
		sources = []

		try:
			response = openURL(configURL)
			data = json.loads(response)

		except: return sources

		if not data: return

		availableStreams = data['request']['files']['progressive']
		for availableStream in availableStreams:
			tmp = ["Vimeo " + availableStream['quality'], availableStream['url']]
			sources.append(tmp)

		return sources

def doPlay(url, name, iconimage):

		streams = getAvailableStreams(url)
		urls = []
		labels = []
		i = 0

		for quality, url in streams:
			urls.append(url)
			labels.append(quality)

		if not streams:
			xbmcgui.Dialog().ok("Stream indisponivel", "Não existe nenhum vídeo disponível")
			return

		index = xbmcgui.Dialog().select("Selecione a resolução desejada :", labels)

		if index == -1 : return
		
		urlVideo = urls[index]
		playlist = xbmc.PlayList(1)
		playlist.clear()
		
		listitem = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
		listitem.setInfo("Video", {"Title":name})
		listitem.setProperty('mimetype', 'video/mp4')
		listitem.setProperty('IsPlayable', 'true')

		playlist.add(urlVideo,listitem)
		xbmcPlayer = xbmc.Player(xbmc.PLAYER_CORE_AUTO)
		xbmc.executebuiltin('Container.SetViewMode(500)')
		xbmcPlayer.play(playlist)

###################################################################################

def addDir(name,url,mode,iconimage,pasta=True,total=1,plot=''):
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
		liz.setProperty('fanart_image', iconimage)
		liz.setInfo( type="video", infoLabels={ "title": name, "plot": plot } )
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=pasta,totalItems=total)
		return ok
	
def openURL(url):
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		req.add_header('Cookie', 'ff=off')
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		return link


def cleanHtml(dirty):
    clean = re.sub('&quot;', '\"', dirty)
    clean = re.sub('&#039;', '\'', clean)
    clean = re.sub('&#215;', 'x', clean)
    clean = re.sub('&#038;', '&', clean)
    clean = re.sub('&#8216;', '\'', clean)
    clean = re.sub('&#8217;', '\'', clean)
    clean = re.sub('&#8211;', '-', clean)
    clean = re.sub('&#8220;', '\"', clean)
    clean = re.sub('&#8221;', '\"', clean)
    clean = re.sub('&#8212;', '-', clean)
    clean = re.sub('&#180;', '\'', clean)
    clean = re.sub('&amp;', '&', clean)
    clean = re.sub("`", '', clean)
    clean = re.sub('<em>', '[I]', clean)
    clean = re.sub('</em>', '[/I]', clean)
    return clean	

###################################################################################

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

params    = get_params()
url       = None
name      = None
mode      = None
iconimage = None

try    : url=urllib.unquote_plus(params["url"])
except : pass

try    : name=urllib.unquote_plus(params["name"])
except : pass

try    : mode=int(params["mode"])
except : pass

try    : iconimage=urllib.unquote_plus(params["iconimage"])
except : pass

print "Mode     : " + str(mode)
print "URL      : " + str(url)
print "Name     : " + str(name)
print "Iconimage: " + str(iconimage)

if   mode == None : mainMenu()
elif mode < 1000  :	getEpisodes(url, iconimage)
elif mode == 1000 :	doPlay(url, name, iconimage)
	
xbmcplugin.endOfDirectory(int(sys.argv[1]))