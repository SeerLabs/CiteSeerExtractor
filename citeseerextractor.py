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
	
	def __init__(self, url):	
		self.url = url
		
	def postPDF(self, pdf):
		files = {'myfile': open(pdf, 'rb')}
		r = requests.post(str(self.url + '/file'), files=files)
		print r.status_code
		if r.status_code == 201:
			dom = xml.dom.minidom.parseString(r.content)
			token = dom.getElementsByTagName('token')[0].firstChild.nodeValue
			return True, token
		else:
			return False, r.content
	
	def getXMLTag(self, token, resource, tag):
		r = requests.get(self.url + '/' + token + '/' + resource)
		if r.status_code == 200:
			dom = xml.dom.minidom.parseString(smart_str(r.content))
			tagContents = dom.getElementsByTagName(tag)
			return True, tagContents
		else:
			return False, r.content
	
	def getHeaderAsString(self, token):
		passed, header = self.getHeaderTag(token, 'algorithm')
		if passed is False:
			return False, header
		ugly_xml = header[0].toprettyxml()
		text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)    
		prettyXml = text_re.sub('>\g<1></', ugly_xml)
		return True, prettyXml
	
	def getHeaderTag(self, token, tag):
		return self.getXMLTag(token, 'header', tag)
		
	def getAuthorNames(self, token):
		print token
		passed, authorsXML = self.getHeaderTag(token, 'name')
		if passed is False:
			return False, authorsXML
		authorList = ''
		authNo = 0
		for node in authorsXML:
			authNo += 1
			authorList += node.firstChild.nodeValue
			if authNo < len(authorsXML)-1:
				authorList += ", "
			elif authNo == len(authorsXML)-1:
				authorList += " and "
		return True, str(authorList)
		
	def getTitle(self, token):
		passed, titleXML = self.getHeaderTag(token, 'title')
		if passed is False:
			return False, titleXML
		return True, str(titleXML[0].firstChild.nodeValue)
		
	def getBodyText(self, token):
		passed, bodyXML = self.getXMLTag(token, 'body', 'body')
		if passed is False:
			return False, bodyXML
		return True, str(bodyXML[0].firstChild.nodeValue)

if  __name__ =='__main__':
	
	csex = CiteSeerExtractor(sys.argv[1])
	passed, message = csex.postPDF(sys.argv[2])
	print "Content-Type: text/html\n"
	if passed is False:
		print str(passed) + ' ' + message
	passed, message = csex.getAuthorNames(message)
	print type(message)
	passed, message = csex.getHeaderAsString('tmppn7vlO')
	print message
	print type(message)
		
	#"""
	#Here are some examples of how the code can be used
	#"""
	
	## To post a PDF use the postPDF method with a string containing the location of the PDF on the filesystem
	## A 'token' will be returned that can then be used to retrieve various aspects of the PDF, i.e. authors, title, body, etc.
	
	#token = csex.postPDF(filename)
	#print "Content-Type: text/html\n"
	#print csex.getAuthorNames(token)
	#print csex.getTitle(token)
	#print csex.getBodyText(token)
	