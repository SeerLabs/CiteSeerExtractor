import web
import tempfile
import os
import subprocess

urls = ('/metadataparser', 'MetadataParser')
ROOT_FOLDER="../seersuite-extract/CiteSeerExtractor/"

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
		web.debug(x['myfile'].filename) # This is the filename
		handler, path = tempfile.mkstemp()
		f = open(path,'w')
		f.write(x['myfile'].file.read())
		f.close()
		web.debug(path)
		try:
			headers = subprocess.check_output([ROOT_FOLDER+"bin/getHeader.pl",path])
			web.debug(headers)
			citations = subprocess.check_output([ROOT_FOLDER+"bin/getCitations.pl",path])
			web.debug(citations)
			merged = headers + citations
			response = """<?xml version="1.0" encoding="UTF-8"?>"""
			response = response + "<CSXAPIMetadata>"
			response = response + merged
			response = response + "</CSXAPIMetadata>"
			return response
		except ex as Exception:
			web.debug(ex)
			
		raise web.seeother('/metadataparser')


if __name__ == "__main__":
   app = web.application(urls, globals()) 
   app.run()