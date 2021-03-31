#!/usr/bin/python3
# -*- coding: utf-8 -*-

class tmdbapi():
	''' TMDB Details key obtainable from https://www.themoviedb.org/settings/api '''
	key=''
	username=''
	password=''


class youtubeapi():
	''' Youtube details https://developers.google.com/youtube/v3/getting-started '''
	apiKey = ''
	clientId = ''
	clientSecret = ''


class url():
	''' url path to your playlist files, film and tv required are on seperate files ''' 
	filmpath = 'https://raw.githubusercontent.com/bigyidbuilds/plugin.video.flixgui.example.basic/20842b0450692c75a9b9559d84ec34677800f4b2/_playlist_example/movies.json'
	tvpath   = 'https://raw.githubusercontent.com/bigyidbuilds/plugin.video.flixgui.example.basic/20842b0450692c75a9b9559d84ec34677800f4b2/_playlist_example/tvshows.json'