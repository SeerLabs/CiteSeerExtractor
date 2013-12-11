"""
This script can be used to test the CiteSeerExtractor
It takes as input a file containing a list of files and tries to submit each of them and get their metadata
It will print PASS if everything is successful or an appropriate error message
"""

import sys
import time
from citeseerextractor import CiteSeerExtractor

csex = CiteSeerExtractor('http://localhost:8081/extractor')

number=1
text_file = open(sys.argv[1], "r")
lines = text_file.readlines()
for line in lines:
    line = line.rstrip()
    print str(number) + ' ' + line
    number = number+1
    passed, message = csex.postPDF(line)
    if passed is True:
        token = message
        passed, message = csex.getHeaderAsXMLString(token)
        if passed is True:
            passed, message = csex.getCitationsAsXMLString(token)
            if passed is True:
                print 'PASS'
            else:
                print 'Error getting citations'
                print message
                continue
        else:
            print 'Error getting header'
            print message
            continue
    else:
        print 'Error posting'
        print message
        continue
    sys.stdout.flush()

text_file.close()
