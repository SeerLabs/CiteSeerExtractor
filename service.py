import web
import tempfile
import os
import subprocess
import xmltodict
import json

urls = (

'/', 'Index',
'/extractor', 'FileHandler', # For uploading a file
'/extractor/pdf', 'PDFStreamHandler', # For uploading a PDF data stream
'/extractor/(.+)/(header|citations|body|text|pdf)', 'Extractor', # For retrieving file information
'/extractor/(.+)', 'FileHandler', # For deleting a file

)

ROOT_FOLDER="./" # there must be a trailing /

# This class does the actual extraction by calling the relevant perl methods
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
			
	def printXML(self, xml):
		"""Returns XMl with the proper headers"""
		response = """<?xml version="1.0" encoding="UTF-8"?>\n"""
		response = response + "<CSXAPIMetadata>\n"
		response = response + xml
		response = response + "</CSXAPIMetadata>\n"
		return response
	
	def printXMLLocations(self, fileid):
		"""Returns the URIs for different types of metadata"""
		response = '<pdf>' + web.ctx.homedomain + '/extractor/' + fileid + '/pdf</pdf>\n'
		response = response + '<header>' + web.ctx.homedomain + '/extractor/' + fileid + '/header</header>\n'
		response = response + '<citations>' + web.ctx.homedomain + '/extractor/' + fileid + '/citations</citations>\n'
		response = response + '<body>' + web.ctx.homedomain + '/extractor/' + fileid + '/body</body>\n'
		response = response + '<text>' + web.ctx.homedomain + '/extractor/' + fileid + '/text</text>\n'
		return self.printXML(response)

class Index:
	
	def GET(self):
		web.header('Content-Type','text/html; charset=utf-8') 	
		render = web.template.render('www/')
		return render.index()
		
class Extractor:
	
	def GET(self, datafile, method):
		
		params = web.input(output="xml")
		"""Returns some extracted information from a file"""
		extractor = Extraction()
		utilities = Util()
		data = ''
		txtfile = '/tmp/' + datafile + '.txt'
		if method == 'text':
			txtfile = '/tmp/' + datafile + '.txt'
			web.header('Content-Type', 'text/text') # Set the Header
			return open(txtfile,"rb").read()
		elif method == 'pdf':
			pdffile = '/tmp/' + datafile
			web.header('Content-Type', 'application/pdf') # Set the Header
			return open(pdffile,"rb").read()
		else:
			if method == 'header':
				data = data + extractor.extractHeaders(txtfile)
			elif method == 'citations':
				data = data + extractor.extractCitations(txtfile)
			elif method == 'body':
				data = data + extractor.extractBody(txtfile)
			#Print XML or JSON
			if params.output == 'xml' or params.output == '':
				web.header('Content-Type','text/xml; charset=utf-8')
				return utilities.printXML(data)
			elif params.output == 'json':
				jsondata = xmltodict.parse(data)
				web.header('Content-Type','text/json; charset=utf-8') 	
				return json.dumps(jsondata)
			else:
				return 'Unsupported output format. Options are: "xml" (default) and "json"'
			

class FileHandler:
	
	def GET(self):
		"""A form for submitting a pdf"""
		return """<html><head></head><body>
		<form method="POST" enctype="multipart/form-data" action="">
		<input type="file" name="myfile" />
		<br/>
		<input type="submit" />
		</form>
		</body></html>"""
		
	def POST(self):
		"""Actually submits the file"""
		pdffile = web.input(myfile={})
		utilities = Util()
		try:
			pdfpath = utilities.handleUpload(pdffile)
			txtpath = utilities.pdf2text(pdfpath)
			fileid = os.path.basename(pdfpath)
			location = web.ctx.homedomain + '/extractor/pdf/' + fileid
			web.ctx.status = '201 CREATED'
			web.header('Location', location)
			web.header('Content-Type','text/xml; charset=utf-8') 
			response = utilities.printXMLLocations(fileid)
			return response
		except Exception as ex:
			web.debug(ex)
			
	def DELETE(self,fileid):
		
		os.unlink('/tmp/' + fileid)
		os.unlink('/tmp/' + fileid + '.txt')
		return 'DELETED ' + fileid
		
		
class PDFStreamHandler:

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
			fileid = os.path.basename(path)
			location = web.ctx.homedomain + '/extractor/' + fileid + '/pdf'
			web.ctx.status = '201 CREATED'
			web.header('Location', location)
			web.header('Content-Type','text/xml; charset=utf-8') 
			response = utilities.printXMLLocations(fileid)
			return response
		except Exception as ex:
			web.debug(ex)


if __name__ == "__main__":
   app = web.application(urls, globals()) 
   app.run()