import redis
import subprocess
import sys
import itertools
import math

r = redis.StrictRedis(host='localhost', port=6379, db=0)

class CSExRedis:
	
	def simhash(self, path):
		""" Calculates the simhash of a text file """
		return str(subprocess.check_output(["../icde/simhashc/run_simhash.sh", path]))
		
	
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
	
	def add_token(self, token, simhash, subhashes):
		r.set(token, simhash)
		for subhash in subhashes:
			r.sadd(str(token+"-sh"), subhash)
	
	def check_matches(self, token):
		simhash = r.get(token)
		subhashes = r.smembers(str(token+"-sh"))
		candidates = set([])
		
		# Returns a list of candidate similar documents that share a subhash
		for subhash in subhashes:
			candidates = candidates.union(r.smembers(subhash))
		if len(candidates) == 0:
			return 0
		
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
			return 0
		# Best match
		return best
		
		
	def hamming(self, str1, str2):
		return sum(itertools.imap(str.__ne__, str1, str2))

	
if  __name__ =='__main__':
	
	CSExRedis = CSExRedis()
	#print str(sys.argv[1])
	simhash = CSExRedis.simhash(sys.argv[1])
	print simhash
	subhashes = CSExRedis.split_simhash(simhash, 3)
	token = sys.argv[2]
	CSExRedis.add_token(token, simhash, subhashes)
	print CSExRedis.check_matches(token)
	
	