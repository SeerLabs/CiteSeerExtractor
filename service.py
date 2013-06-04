import web
import tempfile
import os
import subprocess

urls = ('/metadataparser', 'MetadataParser')
ROOT_FOLDER="./"# there must be a trailing /


class Extraction:
	def extractHeaders(self,path):
		"""extract headers from text file"""
		try:
			headers = subprocess.check_output([ROOT_FOLDER+"bin/getHeader.pl",path])
			web.debug(headers)
			return headers
		except Exception as ex:
			web.debug(ex)
	def extractCitations(self,path):
		"""extract citations from text file"""
		try:
			citations = subprocess.check_output([ROOT_FOLDER+"bin/getCitations.pl",path])
			web.debug(citations)
			return citations
		except Exception as ex:
			web.debug(ex)
	def extractBody(self,path):
                """extract body from text file"""
                try:
                        body = subprocess.check_output([ROOT_FOLDER+"bin/getBody.pl",path])
                        web.debug(body)
                        return body
                except Exception as ex:
                        web.debug(ex)
			
class Util:
	def handleUpload(self, inObject):
		"""
		Handles upload coming from web.input, write it to a temp file, and return the path to that temp file
		"""
		web.debug(inObject['myfile'].filename) # This is the filename
		handler, path = tempfile.mkstemp()
		f = open(path,'w')
		f.write(inObject['myfile'].file.read())
		f.close()
		web.debug(path)
		return path
	def pdf2text(self, path):
		"""
		calls pdfbox to convert a pdf file into text file. 
		returns the path of the text file
		"""
		try:
			subprocess.call(["java", "-jar", ROOT_FOLDER+"pdfbox/pdfbox-app-1.8.1.jar", "ExtractText", 
			path, path+".txt"])
			return path+".txt"
		except Exception as ex:
			web.debug(ex)


class MetadataParser:
	def GET(self):
		return """<html><head></head><body>
<form method="POST" enctype="multipart/form-data" action="">
<input type="file" name="myfile" />
<br/>
<input type="submit" />
</form>
</body></html>"""

	def POST(self):
		x = web.input(myfile={})
		utilities = Util()
		pdfpath = utilities.handleUpload(x)
		txtpath = utilities.pdf2text(pdfpath)
		try:
			extractor = Extraction()
			headers = extractor.extractHeaders(txtpath)
			citations = extractor.extractCitations(txtpath)
			text = extractor.extractBody(txtpath)
			merged = headers + citations + text
			response = """<?xml version="1.0" encoding="UTF-8"?>"""
			response = response + "<CSXAPIMetadata>"
			response = response + merged
			response = response + "</CSXAPIMetadata>"
			os.unlink(pdfpath)
			os.unlink(txtpath)
			return response
		except Exception as ex:
			web.debug(ex)
			
		raise web.seeother('/metadataparser')


if __name__ == "__main__":
   app = web.application(urls, globals()) 
   app.run()