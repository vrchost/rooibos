#import urllib, urllib2, time
#import cookielib
#from xml.etree.ElementTree import ElementTree
#from rooibos.settings import ARTSTOR_GATEWAY
#from models import SmartRedirectHandler
#import unittest

# TODO: rework test since it depends on a working ARTstor connection

#class Test(unittest.TestCase):
#
#
#    def setUp(self):
#        self.searchString = "Rome"
#
#
#    def tearDown(self):
#        pass
#
#
#    def testConnection(self):
#        urlopen = urllib2.urlopen
#        Request = urllib2.Request
#        cj = cookielib.CookieJar()
#
#        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj), SmartRedirectHandler())
#        urllib2.install_opener(opener)
#
#        max_recs = 0
#
#        params = {'query': self.searchString,
#                  'version': '1.1',
#                  'operation': 'searchRetrieve',
#                  'startRecord': 1,
#                  'maximumRecords': max_recs}
#
#        txdata = urllib.urlencode(params)
#        txheaders =  {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
#        req = Request(ARTSTOR_GATEWAY, txdata, txheaders)
#        handle = urlopen(req)
#
#        results = ElementTree(file=handle)
#        total = results.findtext('{http://www.loc.gov/zing/srw/}numberOfRecords')
#        self.assertTrue(total)
#
#
#if __name__ == "__main__":
#    #import sys;sys.argv = ['', 'Test.testConnection']
#    unittest.main()
