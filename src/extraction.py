import web
import tempfile
import os
import subprocess
import shutil

ROOT_FOLDER="../" # there must be a trailing /

class Extraction:
	"""
	This class does the actual extraction by calling the relevant perl methods
	Errors are caught in the calling class
	"""
	def extractHeaders(self,path):
		"""extract headers from text file"""
		headers = subprocess.check_output([ROOT_FOLDER+"bin/getHeader.pl",path])
		web.debug(headers)
		return headers
	def extractCitations(self,path):
		"""extract citations from text file"""
		citations = subprocess.check_output([ROOT_FOLDER+"bin/getCitations.pl",path])
		web.debug(citations)
		return citations
	def extractBody(self,path):
		"""extract body from text file"""
		body = subprocess.check_output([ROOT_FOLDER+"bin/getBody.pl",path])
		web.debug(body)
		return body
