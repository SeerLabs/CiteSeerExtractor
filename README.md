# CiteSeerExtractor

This code provides a RESTful API to the extraction code that is currently in use in the [CiteSeerX academic digital library](http://citeseerx.ist.psu.edu).

*The code is still in development and is not feature complete yet and does not fail gracefully*

The code is runnable as a stand-alone Web server.

### Dependencies
* Python 2.7
* web.py python module
* String::Approx perl module

### Installation
1. Get the code
2. Install web.py `easy_install web.py`
3. Install String::Approx  `cpan String::Approx`

### Run
`python service.py [port]` and navigate to http://localhost:port

Upload a PDF and let us know if you have any problems!
