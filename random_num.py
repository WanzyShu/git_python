#!/usr/bin/env python

import requests
from PIL import Image
from StringIO import StringIO

class graphite_api(object):
        def __init__(self):
                self.find_url = "http://graphite.elenet.me/metrics/find?" 
                self.data_url = "http://graphite.elenet.me/render?"
                self.png_dir = "/opt/monitor"


        def get_list_from_node(self,args={}):
                node = args.get("node_name","")


                if node:
                        payload = {'query' : node }
                        data = requests.get(self.find_url,params=payload)
                        return data.text

        def get_png_from_node(self,args={}):
                node = args.get("node_name")

                headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0', 'Content-type' : 'application/x-www-form-urlencoded'}
                login_data={'auto_login': 1, 'name': 'monitor','password':'OCYXkBKHx9l9','enter':'login'}
                
                graph_req = requests.session()
                login_url = "http://graphite.elenet.me/"
                verify = False

                if node:
                        session.post(login_url, params=login_data, headers=headers, verify=verify)
                        graph_url = self.data_url + 'target'= + str(node)
                        
                        graph_req = session.get(graph_url,verify=verify)
                        graph_png = Image.open(StringIO(graph_req.content))
                        png_name = os.path.join(self.png_dir,node)
                        graph_png.save(png_name)

                        return png_name

        def main(self,opr,args={}):
                opr_dic = {
                'get_list' : self.get_list_from_node,
                'get_png' : self.get_png_from_node,
                }
                if opr in opr_dic:
                        opr_dic[opr](args)
                else:
                        return


