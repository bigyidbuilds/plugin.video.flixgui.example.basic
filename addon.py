#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import FlixGui
import json
import os
import requests
import uservar
import xbmc
import xbmcaddon
import xbmcvfs
import youtube_registration

#addon var
__addon__   = xbmcaddon.Addon()
__addonID__ = __addon__.getAddonInfo('id')


filmUrl = uservar.url.filmpath
tvUrl   = uservar.url.tvpath


#DatabaseConnection
# path to database
dbpath = os.path.join(xbmcvfs.translatePath('special://database'),'{}.db'.format(__addonID__))
# connection to database
dbconn = FlixGui.DatabaseConnection(dbpath)
# create/update database 
dbconn.Create() 
#register Youtube api
youtube_registration.register_api_keys(addon_id=__addonID__,api_key=uservar.youtubeapi.apiKey,client_id=uservar.youtubeapi.clientId,client_secret=uservar.youtubeapi.clientSecret)
#connection to caller utils in script.gui.flixgui
meta_cache = FlixGui.MetaCache(dbconn,uservar.tmdbapi.key,__addonID__)

def main():
	cachemovies()
	cachetv()
	CacheTmdbMovie()
	CacheTmdbTv()
	SetDbData()
	# in Kodi 18 was bug that stopped custom gui opening while DialogBusy was visible so it was closed to allow gui to run
	if float(xbmc.getInfoLabel("System.BuildVersion")[:4]) >= 18:
		xbmc.executebuiltin('Dialog.Close(busydialog)')
	#run script
	d=FlixGui.WindowHome(dbconn)
	d.doModal()
	del d 


def cachemovies():
	'''
		Cache Movies
		opens file and reads data
		init database cursor
		Caches movies from file to database, 
		removes movies no longer in list if present in database
		commits changes to database
	''' 
	movies = []
	a=[]
	r = requests.get(filmUrl)
	if r.ok:
		movies = json.loads(r.content).get('movies')
		with dbconn.conn:
			c = dbconn.conn.cursor()
			for movie in movies:
				tmdb_id = movie.get('tmdbid')
				a.append(tmdb_id)
				c.execute("INSERT OR IGNORE INTO movie_list(title,tmdb_id,genre, overview, poster_path,backdrop_path,release_date,stream,date_added) VALUES(?,?,?,?,?,?,?,?,?)",(movie.get('title'),tmdb_id,str(movie.get('genre')),movie.get('overview'),movie.get('poster'),movie.get('backdrop'),movie.get('releasedate'),str(movie.get('stream')),datetime.datetime.now()))	
			c.execute("SELECT tmdb_id FROM movie_list")
			b = [i[0] for i in c.fetchall() if i[0] not in a]
			for d in b:
				c.execute("DELETE FROM movie_list WHERE tmdb_id=?",(d,))
		dbconn.conn.commit()
	c.close()


def cachetv():
	'''
		Cache TV shows and episodes
		opens file and reads data
		init database cursor
		Checks if episodes in list match episodes in cache and deleting those that don't
		Adds tv shows to cache
		Adds tv episodes to cache
		Delete any not in list
	'''
	tvshows= []
	r = requests.get(tvUrl)
	if r.ok:
		tvshows = json.loads(r.content).get('tvshows')
		total = len(tvshows)
		a=[]
		with dbconn.conn:
			c = dbconn.conn.cursor()
			for tvs in tvshows:
				tmdbid = tvs.get('tmdbid')
				episodes = tvs.get('episodes')
				a.append(tmdbid)
				c.execute("DELETE FROM tv_list WHERE tmdb_id =? AND episodes !=? ",(tmdbid,str(episodes)))
				c.execute("INSERT OR IGNORE INTO tv_list(title ,tmdb_id ,genre , overview,poster_path,backdrop_path,release_date,episodes,date_added) VALUES(?,?,?,?,?,?,?,?,?)",(tvs.get('title'),tmdbid,str(tvs.get('genre')),tvs.get('overview'),tvs.get('poster'),tvs.get('backdrop'),tvs.get('releasedate'),str(episodes),datetime.datetime.now()))
				for episode in episodes:
					c.execute("INSERT OR IGNORE INTO tv_episode_list(tmdb_id,season,episode,stream) VALUES(?,?,?,?)",(tmdbid,episode.get('season'),episode.get('episode'),str(episode.get('stream'))))
					c.execute("INSERT OR IGNORE INTO user_watched_tv(tmdb_id,season,episode) VALUES(?,?,?)",(tmdbid,episode.get('season'),episode.get('episode')))
			c.execute("SELECT tmdb_id FROM tv_list")
			b = [i[0] for i in c.fetchall() if i[0] not in a]
			for d in b:
				c.execute("DELETE FROM tv_list WHERE tmdb_id=?",(d,))
				c.execute("DELETE FROM user_viewed_tv WHERE tmdb_id=?",(d,))
			dbconn.conn.commit()
	c.close()


def CacheTmdbMovie():
	''' checks to see if flixgui already has meta data from tmdb in cache if not is added'''
	with dbconn.conn:
		c = dbconn.conn.cursor()
		c.execute("SELECT tmdb_id FROM movie_list EXCEPT SELECT tmdb_id FROM master.tmdb_movie_details")
		tmdbids=  [x[0] for x in c.fetchall()]
		total = len(tmdbids)
		if total >0:
			for tmdbid in tmdbids:
				meta_cache.MovieMeta(tmdbid)
		c.close()

def CacheTmdbTv():
	''' checks to see if flixgui already has meta data from tmdb in cache if not is added'''
	with dbconn.conn:
		c = dbconn.conn.cursor()
		c.execute("SELECT tmdb_id FROM tv_list EXCEPT SELECT tmdb_id FROM master.tmdb_tv_details")
		tmdbids=  [x[0] for x in c.fetchall()]
		total = len(tmdbids)
		if total >0:
			for tmdbid in tmdbids:
				meta_cache.TvMeta(tmdbid)
		c.close()


def SetDbData():
	'''
		Update other tables with required info
		temp.caller table deletes upon closing of database connection
	'''
	with dbconn.conn:
		c=dbconn.conn.cursor()
		c.execute("INSERT OR IGNORE INTO user_watched_movie(tmdb_id) SELECT tmdb_id FROM movie_list")
		c.execute("INSERT OR IGNORE INTO user_list(tmdb_id,media_type) SELECT tmdb_id,media_type FROM movie_list")
		c.execute("INSERT OR IGNORE INTO user_watched_tv(tmdb_id,season,episode) SELECT tmdb_id,season,episode FROM tv_episode_list")
		c.execute("INSERT OR IGNORE INTO user_list(tmdb_id,media_type) SELECT tmdb_id,media_type FROM tv_list")
		c.execute("INSERT OR IGNORE INTO temp.caller(addon_id,tmdb_key,tmdb_user,tmdb_password,youtubeapi_key,youtubeapi_clientid,youtubeapi_clientsecret) VALUES(?,?,?,?,?,?,?)",(__addonID__,uservar.tmdbapi.key,uservar.tmdbapi.username,uservar.tmdbapi.password,uservar.youtubeapi.apiKey,uservar.youtubeapi.clientId,uservar.youtubeapi.clientSecret))
		dbconn.conn.commit()



if __name__ == '__main__':
	main()