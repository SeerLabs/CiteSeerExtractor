"""
This script can be used to test the CiteSeerExtractor
It takes as input a file containing a list of files and tries to submit each of them and get their metadata
It will print PASS if everything is successful or an appropriate error message
"""

import sys
import time
from citeseerextractor import CiteSeerExtractor

csex = CiteSeerExtractor('http://localhost:8081/extractor')

f = sys.argv[1]
passed, message = csex.postPDF(f)
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
            sys.exit()
    else:
        print 'Error getting header'
        print message
        sys.exit()
else:
    print 'Error posting'
    print message

