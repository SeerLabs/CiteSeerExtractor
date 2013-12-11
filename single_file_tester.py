"""
This script can be used to test the CiteSeerExtractor
It takes as input a file containing a list of files and tries to submit each of them and get their metadata
It will print PASS if everything is successful or an appropriate error message
"""

import sys
import time
from citeseerextractor import CiteSeerExtractor

csex = CiteSeerExtractor('http://localhost:8081/extractor')

API_HEADER_TAG='CSXAPIMetadata'

f = sys.argv[1]
passed, message = csex.postPDF(f)
if passed is True:
    token = message
    passed, message = csex.getHeaderAsXMLString(token)
    if passed is True:
        if API_HEADER_TAG not in message:
            print f + ' Error in header validation'
            sys.exit()
        passed, message = csex.getCitationsAsXMLString(token)
        if passed is True:
            if API_HEADER_TAG not in message:
                print f + ' Error in citation validation'
                sys.exit()
            print sys.argv[2] + ' ' + f + ' PASS'
        else:
            print f + ' Error getting citations'
            print message
            sys.exit()
    else:
        print f + ' Error getting header'
        print message
        sys.exit()
else:
    print f + ' Error posting'
    print message

