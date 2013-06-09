import web
import tempfile
import os
import subprocess

urls = (

'/extractor/upload', 'Upload',
'/extractor/pdf', 'PDFHandler',
'/extractor/pdf/(.+)', 'PDFHandler',
'/extractor/header/(.+)', 'Extractor',
'/extractor/citations/(.+)', 'Extractor',

)

#,
#'/extractor/pdf/(.*)/(.*)', 'Extractor'
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
		#"""
		#calls pdfbox to convert a pdf file into text file. 
		#returns the path of the text file
		#"""
		try:
			subprocess.call(["java", "-jar", ROOT_FOLDER+"pdfbox/pdfbox-app-1.8.1.jar", "ExtractText", 
			path, path+".txt"])
			return path+".txt"
		except Exception as ex:
			web.debug(ex)


class Extractor:
	
	def GET(self, method, datafile):
		extractor = Extraction()
		data = ''
		txtfile = '/tmp/' + datafile + '.txt'
		if method == 'header':
			data = data + extractor.extractHeaders(txtfile)
		elif method == 'citations':
			data = data + extractor.extractCitations(txtfile)
		return data

class Upload:
	
	def GET(self):
		return """<html><head></head><body>
		<form method="POST" enctype="multipart/form-data" action="">
		<input type="file" name="myfile" />
		<br/>
		<input type="submit" />
		</form>
		</body></html>"""
		
	def POST(self):
		pdffile = web.input(myfile={})
		utilities = Util()
		
		try:
			pdfpath = utilities.handleUpload(pdffile)
			txtpath = utilities.pdf2text(pdfpath)
			location = web.ctx.homedomain + '/extractor/pdf/' + os.path.basename(pdfpath)
			web.ctx.status = '201 CREATED'
			web.header('Location', location)
			return location
		except Exception as ex:
			web.debug(ex)
			
class PDFHandler:

#Get the PDF
	def GET(self, pdf):
		pdffile = '/tmp/' + pdf
		web.header('Content-Type', 'application/pdf') # Set the Header
		return open(pdffile,"rb").read()
		
# Post the raw pdf data
	def POST(self):
		utilities = Util()
		data = web.data()
		try:
			handler, path = tempfile.mkstemp()
			f = open(path,'wb')
			f.write(data)
			f.close()
			web.debug(path)
			txtpath = utilities.pdf2text(path)
			location = web.ctx.homedomain + web.ctx.fullpath + "/" + os.path.basename(path)
			web.ctx.status = '201 CREATED'
			web.header('Location', location)
			return location
		except Exception as ex:
			web.debug(ex)


if __name__ == "__main__":
   app = web.application(urls, globals()) 
   app.run()