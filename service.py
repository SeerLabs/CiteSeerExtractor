import web
import tempfile
import os
import subprocess
import xmltodict
import json
import cgi
import shutil
import magic

urls = (

'/', 'Index',
'/extractor', 'FileHandler', # For uploading a file
'/extractor/pdf', 'PDFStreamHandler', # For uploading a PDF data stream
'/extractor/(.+)/(header|citations|body|text|pdf)', 'Extractor', # For retrieving file information
'/extractor/(.+)', 'FileHandler', # For deleting a file

)

ROOT_FOLDER="./" # there must be a trailing /
TMP_FOLDER=tempfile.gettempdir()+"/citeseerextractor/" #Specifies temp folder - useful for cleaning up afterwards

cgi.maxlen = 5 * 1024 * 1024 # 5MB file size limit for uploads

allowedTypes = set(['application/pdf', 'text/plain','application/postscript']) # Allowed file types

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
			
class Util:
	"""
	Some utility methods for handling uploads and printing output
	Errors are caught in the calling classes
	"""

	def handleUpload(self, inObject):
		"""
		Handles upload coming from web.input, write it to a temp file, and return the path to that temp file
		"""
		web.debug(inObject['myfile'].filename) # This is the filename
		handler, path = tempfile.mkstemp(dir=TMP_FOLDER)
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
		ret = subprocess.call(["java", "-jar", ROOT_FOLDER+"pdfbox/pdfbox-app-1.8.1.jar", "ExtractText", path, path+".txt"])
		""" Raise an error if text extraction failed"""
		if ret > 0: 
			raise IOError
		return path+".txt"
			
	def doFilter(self, path): 
		"""
		Pass in the pdfpath here, only tells if file type is allowed or not
		"""
		docFilter = 0		
		fileTypeString = magic.from_file(path, mime=True) # Stores the MIME string that describes the file type
		web.debug(fileTypeString)
		if fileTypeString in allowedTypes:
			docFilter = 1  # Condition of right file Type                 	   
		else: 
			docFilter = 2  # Condition of wrong file type 
		web.debug(docFilter)
		return docFilter

	def academicFilter(self, path): 
		"""
		Pass in txtpath here, only tells if document is academic or not
		"""
		acaFilter = 0
		acaFilter = subprocess.check_output([ROOT_FOLDER+"bin/doFilter.pl",path]) # This is typically either 0 or 1
		web.debug(acaFilter)
		return acaFilter
		
	def printXML(self, xml):
		"""Returns XMl with the proper headers"""
		response = """<?xml version="1.0" encoding="UTF-8"?>\n"""
		response = response + "<CSXAPIMetadata>\n"
		response = response + xml
		response = response + "</CSXAPIMetadata>\n"
		return response
	
	def printXMLLocations(self, fileid):
		"""Returns the URIs for different types of metadata"""
		response = '<token>' + fileid + '</token>'
		response = response + '<pdf>' + web.ctx.homedomain + '/extractor/' + fileid + '/pdf</pdf>\n'
		response = response + '<header>' + web.ctx.homedomain + '/extractor/' + fileid + '/header</header>\n'
		response = response + '<citations>' + web.ctx.homedomain + '/extractor/' + fileid + '/citations</citations>\n'
		response = response + '<body>' + web.ctx.homedomain + '/extractor/' + fileid + '/body</body>\n'
		response = response + '<text>' + web.ctx.homedomain + '/extractor/' + fileid + '/text</text>\n'
		return self.printXML(response)

class Index:
	"""Loads the index page from the static dir"""
	def GET(self):
		web.header('Content-Type','text/html; charset=utf-8') 	
		raise web.seeother('/static/index.html')
		
class Extractor:
	
	def GET(self, datafile, method):
		
		params = web.input(output="xml")
		"""Returns some extracted information from a file"""
		extractor = Extraction()
		utilities = Util()
		data = ''
		txtfile = TMP_FOLDER + datafile + '.txt'
		
		"""Check if the file exists, if not return a 404"""
		if not os.path.exists(txtfile):
			return web.notfound()
		
		try:
			if method == 'text':
				txtfile = TMP_FOLDER + datafile + '.txt'
				web.header('Content-Type', 'text/text') # Set the Header
				return open(txtfile,"rb").read()
			elif method == 'pdf':
				pdffile = TMP_FOLDER + datafile
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
		
		except (IOError, OSError) as er: #Internal error, i.e. during extraction
			web.debug(er)
			return web.internalerror()
		

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
		try:
			# Here we handle the file upload first, and do the following:
			# I. Check if the file type is allowed: PDF, TXT or PostScript. This returns:
			#	1 - Allowed File Type -> Proceed to next step
			#	2 - Unallowed File Type -> Value error & Display error message
			# II. Extract the document -> proceed to next step
			# III. Check if the document is an academic document and returns:
			#	"1" - Document is academic -> Proceed to next step
			#	"0" - Document is not academic -> Value error & Display error message
			#	"-1" - OS error
			# IV. Form and return XML response
			
			pdffile = web.input(myfile={})
			utilities = Util()
			pdfpath = utilities.handleUpload(pdffile)
			
			try:
				typeFilterStatus = utilities.doFilter(pdfpath)
				web.debug(typeFilterStatus)
				if typeFilterStatus == 2:
					raise ValueError
				txtpath = utilities.pdf2text(pdfpath)
				acaFilterStatus = utilities.academicFilter(txtpath)
				web.debug(acaFilterStatus)
				if acaFilterStatus == "-1":
					raise OSError
				elif acaFilterStatus == "0":
					raise ValueError
			except OSError as ex:
				web.debug(ex)
				return web.internalerror()
			except ValueError as ex:
				web.debug(ex)
				if typeFilterStatus == 2:
					return "Your document failed our academic document filter due to invalid file type"
				elif acaFilterStatus == "0":
					return "Your document failed our academic document filter due to not being academic"
							
			fileid = os.path.basename(pdfpath)
			location = web.ctx.homedomain + '/extractor/pdf/' + fileid
			web.ctx.status = '201 CREATED'
			web.header('Location', location)
			web.header('Content-Type','text/xml; charset=utf-8') 
			web.header('Access-Control-Allow-Origin', '*')
			response = utilities.printXMLLocations(fileid)
			return response
		except (IOError, OSError) as ex:
			web.debug(ex)
			return web.internalerror()
		except ValueError as ex: 
			web.debug(ex)
			return "File too large. Limit is ", cgi.maxlen              

	def DELETE(self,fileid):
		
		""" 404 when txt file doesn't exist """
		if not os.path.exists(TMP_FOLDER + fileid + '.txt'): 
			return web.notfound()
		
		try:
			os.unlink(TMP_FOLDER + fileid)
			os.unlink(TMP_FOLDER + fileid + '.txt')
			return 'DELETED ' + fileid
		except (IOError, OSError) as ex:
			web.debug(ex)
			return web.internalerror()
				

class PDFStreamHandler:
	def POST(self):
		"""Posts a PDF bytestream"""
		utilities = Util()
		content_size = -1
		
		# Check for Content-Length header
		try:
			content_size = int(web.ctx.env.get('CONTENT_LENGTH'))
		except (TypeError, ValueError):
			content_size = 0
		try: #Max file size
			if content_size > cgi.maxlen:
				raise ValueError
		except ValueError as ex:
			web.debug(ex)
			return "File too large. Limit is ", cgi.maxlen              
		try:
			if content_size == 0: #No Content-Length header
				raise ValueError
		except ValueError as ex:
			web.debug(ex)
			return "Please set Content-Length header for bytestream upload"
		
		try:
			data = web.data()
			handler, path = tempfile.mkstemp(dir=TMP_FOLDER)
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
		except (IOError, OSError) as ex:
			web.debug(ex)
			return web.internalerror()
		except ValueError as ex: 
			web.debug(ex)
			return "File too large. Limit is ", cgi.maxlen              

if __name__ == "__main__":

	if os.path.isdir(TMP_FOLDER): #Create the temp folder
		shutil.rmtree(TMP_FOLDER)
		
	os.mkdir(TMP_FOLDER, 0o700)
		
	app = web.application(urls, globals()) 
	app.run()
	
