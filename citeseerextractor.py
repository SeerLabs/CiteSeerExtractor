#!/usr/bin/python2.7

"""
    Copyright (C) 2013  Kyle Williams <kwilliams@psu.edu>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
	This is a wrapper around the CiteSeerExtractor. 
	It can easily be used to retrieve various parts of a PDF without needing to worry about HTTP and XML handling.
"""

import cgi, cgitb
import sys
import requests
import xml.dom.minidom
import re
import subprocess
from django.utils.encoding import smart_str, smart_unicode

class CiteSeerExtractor:
	
	global url
	url = 'http://citeseerextractor.ist.psu.edu:8080/extractor'
		
	def postPDF(self, pdf):
		files = {'myfile': open(pdf, 'rb')}
		r = requests.post(url, files=files)
		if r.status_code == 201:
			dom = xml.dom.minidom.parseString(r.content)
			tokenXML = dom.getElementsByTagName('pdf')[0].firstChild.nodeValue
			m = re.search('(?<=extractor\/)\w+',tokenXML)
			return m.group()
		else:
			return -1;
	
	def getXMLTag(self, token, resource, tag):
		r = requests.get(url + '/' + token + '/' + resource)
		dom = xml.dom.minidom.parseString(smart_str(r.content))
		tagContents = dom.getElementsByTagName(tag)
		return tagContents
	
	def getHeaderTag(self, token, tag):
		return self.getXMLTag(token, 'header', tag)
		
	def getAuthorNames(self, token):
		authorsXML = self.getHeaderTag(token, 'name')
		authorList = ''
		authNo = 0
		for node in authorsXML:
			authNo += 1
			authorList += node.firstChild.nodeValue
			if authNo < len(authorsXML)-1:
				authorList += ", "
			elif authNo == len(authorsXML)-1:
				authorList += " and "
		return authorList
		
	def getTitle(self, token):
		titleXML = self.getHeaderTag(token, 'title')
		return titleXML[0].firstChild.nodeValue
		
	def getBodyText(self, token):
		bodyXML = self.getXMLTag(token, 'body', 'body')
		return bodyXML[0].firstChild.nodeValue

if  __name__ =='__main__':
	
	csex = CiteSeerExtractor()
	form = cgi.FieldStorage()
	filename = form.getvalue('filename')
		
	"""
	Here are some examples of how the code can be used
	"""
	
	# To post a PDF use the postPDF method with a string containing the location of the PDF on the filesystem
	# A 'token' will be returned that can then be used to retrieve various aspects of the PDF, i.e. authors, title, body, etc.
	
	token = csex.postPDF(filename)
	print "Content-Type: text/html\n"
	print csex.getAuthorNames(token)
	print csex.getTitle(token)
	print csex.getBodyText(token)
	