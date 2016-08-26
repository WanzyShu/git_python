#!/usr/bin/env python

import time
import json
import urllib
import urllib2
import cookielib


ACTION = ['getToken','normalPowerOff','powerOn','getIpInfo']


class HUAWEI(object):
    def __init__(self,host,password):
        self.host = host
        self.password = password
        self.post_url = 'https://%s/bmc/php/processparameter.php' %host
        self.host_url = 'https://%s/login.html' %host
        self.cookie = self._get_cookie()[0].get('AddSession')[1]
        self.headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}
        self.getIpUrl =  'https://%s/bmc/php/getip.php' %self.host
        self.opreationUrl = 'https://%s/bmc/php/setpropertybymethod.php' %host
        self.tokenUrl = 'https://%s/bmc/php/gettoken.php' %host

    def _get_cookie(self):
        cj = cookielib.LWPCookieJar()
        cookie_support = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(cookie_support,urllib2.HTTPHandler)
        urllib2.install_opener(opener)

        h = urllib2.urlopen(self.host_url)
        headers = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
                    'Referer' : 'https://%s/login.html'%self.host
                   }
        postData = {
            'check_pwd': self.password,
            'logtype':0,
            'user_name':'root',
            'func':'AddSession',
        }

        postData = urllib.urlencode(postData)
        request = urllib2.Request(self.post_url,postData,headers)
        response = urllib2.urlopen(request)
        text = response.read()
        return json.loads(text.replace('%2522','"'))

    def _set_header(self):
        headers = {"Cookie": 'lang=zh; %s' %self._get_cookie()[0].get('AddSession')[1]}
        return headers

    def _get_token(self):
        headers = self.headers
        headers['Cookie'] = "opener=yes;lang=zh; SessionId3=%s; LoginCount3=1; Current=%%2Fbmc%%2Fpages%%2Finfo%%2Finfo.html" %self.cookie
        headers['Origin'] = "https://%s" %self.host
        request = urllib2.Request(self.tokenUrl,None,headers)
        response = urllib2.urlopen(request)
        return response.getcode(),response.read()

    def _do_request(self,action,params):
        if action not in ACTION:
            raise RuntimeError,'Action must in %s' %ACTION
        else:
            headers = self.headers
            cookie =  self.cookie

            if action == 'normalPowerOff' or action == "powerOn":
                url = self.opreationUrl
                headers['Cookie'] = "opener=yes;lang=zh; SessionId3=%s; LoginCount3=1; Current=%%2Fbmc%%2Fpages%%2Finfo%%2Finfo.html" %cookie
                headers['Origin'] = "https://%s" %self.host
                headers['Referer'] = "https://%s/bmc/pages/info/info.html?random_str=%s" %(self.host,int(time.time()*1000))
                headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
                headers['Host'] = self.host
                headers["X-Requested-With"] = "XMLHttpRequest"
            elif action == 'getIpInfo':
                url = self.getIpUrl
                headers['Cookie'] = "lang=zh; SessionId3=%s;" %cookie

            postData = urllib.urlencode(params)
            request = urllib2.Request(url,postData,headers)
            response = urllib2.urlopen(request)
            status_code = response.getcode()
            text = response.read()
            return status_code,text

    def normal_powerOff(self):
        action = 'normalPowerOff'
        status_code,token = self._get_token()
        if status_code == 200:
            params = {
                'token': '%s' %token,
                'str_input' : json.dumps({ "class_name":"Payload", "obj_name":"ChassisPayload", "method_list":[["PowerOff"]]} )
            }
            return self._do_request(action,params)
        else:
            raise RuntimeError,'GET TOKEN FAILED.....'

    def getip(self):
        action = 'getIpInfo'
        params = {
            'getip': 'getip'
        }
        return self._do_request(action,params)

    def powerOn(self):
        action = 'powerOn'
        status_code,token = self._get_token()
        if status_code == 200:
            params = {
                'token': '%s' %token,
                'str_input' : json.dumps({ "class_name":"Payload", "obj_name":"ChassisPayload", "method_list":[["PowerOn"]]} )
            }
            return self._do_request(action,params)
        else:
            raise RuntimeError,'GET TOKEN FAILED.....'


if __name__ == '__main__':
    pass
