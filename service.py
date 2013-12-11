import web
import tempfile
import os
import subprocess
import xmltodict
import json
import cgi
import shutil
from extraction import Extraction
from utilities import Util
from csexredis import CSExRedis

urls = (

'/', 'Index',
'/extractor', 'FileHandler', # For uploading a file
'/extractor/file', 'PDFStreamHandler', # For uploading any binary data stream
'/extractor/(.+)/(header|citations|body|text|file)', 'Extractor', # For retrieving file information
'/extractor/(.+)', 'FileHandler', # For deleting a file

)

ROOT_FOLDER="./" # there must be a trailing /
TMP_FOLDER=tempfile.gettempdir()+"/citeseerextractor/" #Specifies temp folder - useful for cleaning up afterwards

cgi.maxlen = 5 * 1024 * 1024 # 5MB file size limit for uploads

global utilities
utilities = Util()

global csexredis
csexredis = CSExRedis()
	
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
			elif method == 'file':
				pdffile = TMP_FOLDER + datafile
				typeFilterStatus = utilities.typeFilter(pdffile)
				web.header('Content-Type', typeFilterStatus) # Set the Header
				return open(pdffile,"rb").read()
			else:
				""" Looks for near duplicates in redis database
				First check if we have exact metadata. If not, do the following
				1. Check if near dupe exists
				2. If one does, check if we have already extracted the metadata and return if we have
				3. If not, extract the metadata and store """
				
				simhash = csexredis.simhash(txtfile)
				exact_metadata = csexredis.get_metadata(simhash, method)
				if exact_metadata is not None: #Check if we have the exact thing stored already
					print "I have the exact metadata, returning!"
					data = exact_metadata
				else:
					web.debug("Checking redis database for near duplicates")
					match = csexredis.lookup_add(datafile, simhash) # Look for near duplicate and add if one doesn't exist
					have_metadata = None
					if match is not None: # Near dupe exists
						print "Found! Now checking for " + method + " metadata"
						have_metadata = csexredis.get_metadata(match, method)
					if have_metadata is not None:
						print "Found...no need to extract"
						data = have_metadata # Have metadata, return!
					else: # Either no dupes or don't have metadata
						print "Not found...extracting"
						if method == 'header':
							data = data + extractor.extractHeaders(txtfile)
						elif method == 'citations':
							data = data + extractor.extractCitations(txtfile)
						elif method == 'body':
							data = data + extractor.extractBody(txtfile)
						csexredis.add_metadata(datafile, method, data) # Add the newly extracted metadata
				#Print XML or JSON
				if params.output == 'xml' or params.output == '':
					web.header('Content-Type','text/xml; charset=utf-8')
					return utilities.printXML(data)
				elif params.output == 'json':
					jsondata = xmltodict.parse(data)
					web.header('Content-Type','text/json; charset=utf-8') 	
					return json.dumps(jsondata)
				else:
					web.ctx.status = '400'
					return 'Unsupported output format. Options are: "xml" (default) and "json"'
		
		except (IOError, OSError) as er: #Internal error, i.e. during extraction
			web.debug(er)
			return web.internalerror()

class Handler(object):	# Super-class for the two handlers
	
	def fileCheck(self, pdfpath):
			
		try:
			# After we handle the file upload, we do the following:
			# I. Check the uploaded file's type -> proceed to next step
			# II. Extract the full text from the document, where if the file type is:
			#	PDF -> extract text using pdf2text -> proceed to next step
			#	PostScript -> extract text using ps2text -> proceed to next step
			#	Text File -> skip full text extraction, proceed to next step
			#	Type NOT from the above -> Value error & Display error message
			# III. Check if the document is an academic document and returns:
			#	"1" - Document is academic -> Proceed to next step
			#	"0" - Document is not academic -> Value error & Display error message
			#	"-1" - OS error
			# IV. Form and return XML response
			
			typeFilterStatus = utilities.typeFilter(pdfpath)
			web.debug(typeFilterStatus)
			if typeFilterStatus == "application/pdf":
				txtpath = utilities.pdf2text(pdfpath)
			elif typeFilterStatus == "application/postscript":
				os.rename(pdfpath, pdfpath + ".ps")
				txtpath = utilities.ps2text(pdfpath)
				os.rename(pdfpath + ".ps", pdfpath)
			elif "text" in typeFilterStatus:
				shutil.copy(pdfpath, pdfpath + ".txt")
				txtpath = pdfpath + ".txt"
			else:
				typeFilterStatus = "falsetype"
				raise ValueError
			web.debug(txtpath)
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
			if typeFilterStatus == "falsetype":
				return False, "Your document failed our academic document filter due to invalid file type. Supported types are PDF, PS, and TXT."
			elif acaFilterStatus == "0":
				return False, "Your document failed our academic document filter."
		return True, typeFilterStatus
		
	def printLocations(self, fileid):
		location = web.ctx.homedomain + '/extractor/pdf/' + fileid
		web.ctx.status = '201 CREATED'
		web.header('Location', location)
		web.header('Content-Type','text/xml; charset=utf-8') 
		web.header('Access-Control-Allow-Origin', '*')
		response = utilities.printXMLLocations(fileid)
		return response
	
					
class FileHandler(Handler):
	
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
			pdffile = web.input(myfile={})
			pdfpath = utilities.handleUpload(pdffile)
			passed, message = super(FileHandler, self).fileCheck(pdfpath)
			if passed is False:
				web.ctx.status = '400'
				return message
			else:
				fileid = os.path.basename(pdfpath)
				return super(FileHandler, self).printLocations(fileid)
		except (IOError, OSError) as ex:
			web.debug(ex)
			web.ctx.status = '500'
			return web.internalerror()
		except ValueError as ex:
			web.debug(ex)
			web.ctx.status = '400'
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


class PDFStreamHandler(Handler):

	def POST(self):
		"""Posts a PDF bytestream"""
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
			web.ctx.status = '400'
			return "File too large. Limit is ", cgi.maxlen              
		try:
			if content_size == 0: #No Content-Length header
				raise ValueError
		except ValueError as ex:
			web.debug(ex)
			web.ctx.status = '400'
			return "Please set Content-Length header for bytestream upload"
		
		try:
			data = web.data()
			with tempfile.NamedTemporaryFile('wb',dir=TMP_FOLDER,delete=False) as f:
				f.write(data)
				pdfpath = os.path.abspath(f.name)
			web.debug(pdfpath)
			passed, message = super(PDFStreamHandler, self).fileCheck(pdfpath)
			if passed is False:
				web.ctx.status = '400'
				return message
			else:
				fileid = os.path.basename(pdfpath)
				return super(PDFStreamHandler, self).printLocations(fileid)
		except (IOError, OSError) as ex:
			web.debug(ex)
			web.ctx.status = '500'
			return web.internalerror()
		
if __name__ == "__main__":

	if os.path.isdir(TMP_FOLDER): #Create the temp folder
		shutil.rmtree(TMP_FOLDER)
		
	os.mkdir(TMP_FOLDER, 0o700)
		
	app = web.application(urls, globals()) 
	app.run()
	
