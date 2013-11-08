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
	
	
if  __name__ =='__main__':
	
	CSExRedis = CSExRedis()
	#print str(sys.argv[1])
	simhash = CSExRedis.simhash(sys.argv[1])
	print simhash
	subhashes = CSExRedis.split_simhash(simhash, 3)
	