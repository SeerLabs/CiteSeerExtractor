"""
This script can be used to test the CiteSeerExtractor
It takes as input a file containing a list of files and tries to submit each of them and get their metadata
It will print PASS if everything is successful or an appropriate error message
"""

import sys
import time
from citeseerextractor import CiteSeerExtractor

if int(sys.argv[2])%1000 == 0 or int(sys.argv[2]) == 1:
    with open('times.txt', 'a') as f:
        f.write(sys.argv[2] + ' ' + str(time.time()))
        f.write('\n')

csex = CiteSeerExtractor('http://localhost:8081/extractor')

API_HEADER_TAG='SVM HeaderParse'
API_CITATION_TAG='citationList'

f = sys.argv[1]
print f
passed, message = csex.postPDF(f)
if passed is True:
    token = message
    passed, message = csex.getHeaderAsXMLString(token)
    if passed is True:
        if API_HEADER_TAG not in message:
            print 'Error in header validation'
            sys.exit()
        passed, message = csex.getCitationsAsXMLString(token)
        if passed is True:
            if API_CITATION_TAG not in message:
                print 'Error in citation validation'
                sys.exit()
            print sys.argv[2] + ' PASS'
            csex.delete(token)
        else:
            print 'Error getting citations'
            print message
            sys.exit()
    else:
        print 'Error getting header'
        print message
        sys.exit()
else:
    print 'Error posting'
    print message

