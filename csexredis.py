import redis
import subprocess
import sys
import itertools
import math

r = redis.StrictRedis(host='localhost', port=6379, db=0)

class CSExRedis:
	
	def lookup_add(self, token, simhash):
		""" When a new document is added, first look up if a similar hash exists and add it if one doesn't """
		subhashes = self.split_simhash(simhash, 3)
		r.set(token, simhash)
		# Look for a match
		match = self.check_matches(simhash, subhashes)
		# No match, so add as new record
		if match is None:
			for subhash in subhashes:
				r.sadd(subhash, simhash)
			return None
		else:
			if len(match) is 64:
				return match
			else:
				return None
	
	def get_metadata(self, simhash, field):
		""" Returns the metadata for a given hash value """
		metadata = r.get(str(simhash+"-"+field))
		return metadata
	
	def add_metadata(self, token, field, metadata, expire=None):
		""" Adds metadata for a given hash value """
		key = r.get(token) # Add by hash value, not token
		if expire is None:
			r.set(str(key+"-"+field), metadata)
		else:
			r.setex(str(key+"-"+field), expire, metadata)
			
	def check_matches(self, simhash, subhashes):
		""" Performs a lookup to see if a similar looking file has been encountered before
		Method based on (Mankue et al, 2007; Williams & Giles, 2013) """
		
		candidates = set([])
		
		# Returns a list of candidate similar documents that share a subhash
		for subhash in subhashes:
			candidates = candidates.union(r.smembers(subhash))
		if len(candidates) == 0:
			return None
		
		# Check Hamming distance with each candidate and keep track of the best
		first = 64
		best = ""
		for candidate in candidates:
			hamming = self.hamming(simhash, candidate)
			if hamming < first:
				first = hamming
				best = candidate
		# No good match
		if (first > 3):
			return None
		# Best match
		return best
		
	###
	# This section of code is relevant to simhash calculation
	###
	
	def simhash(self, path):
		""" Calculates the simhash of a text file """
		return str(subprocess.check_output(["simhashc/run_simhash.sh", path]))
		
	def split_simhash(self, simhash, k):
		""" Takes a simhash and splits it into k substrings """
		subhashes = []
		
		hashlen = len(simhash)
		# Want relatively equal size substrings so split into k partitions and round partition size up
		# Prevents subhashes like "11111" "110101" "1"
		length = int(math.ceil(hashlen/float(k)))
		for i in range(0, hashlen, length):
			lastPoint = i+length if (i+length <= hashlen) else hashlen
			subhashes.append(simhash[i:lastPoint])
		
		return subhashes
	
	def hamming(self, str1, str2):
		""" Returns the hamming distance between two bit strings """
		return sum(itertools.imap(str.__ne__, str1, str2))

	
if  __name__ =='__main__':
	
	CSExRedis = CSExRedis()
	print CSExRedis.lookup(sys.argv[2], sys.argv[1])
	simhash = CSExRedis.simhash(sys.argv[1])
	print simhash
	subhashes = CSExRedis.split_simhash(simhash, 3)
	print subhashes
	
