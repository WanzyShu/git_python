#!/bin/env python
#coding:utf8

'''
[global]
key = RmVk2zDpY5kpBW0M
[qszg]
key = haha
'''


import tornado.ioloop,tornado.web,tornado.httpclient
import urllib,re,datetime,os
import hashlib, time, commands, ConfigParser, json
import salt.client
from salt import key  as salt_key
from salt import runner as salt_runner
from jinja2 import Template

SALT_DIR='/srv/salt'


class serverConfigInit():
    def __init__(self,project=None):
        self.project = project
        self.conf_file = '/tmp/eleme_salt.conf'
        self.conf_tmp = ConfigParser.ConfigParser()
        self.conf_tmp.read(self.conf_file)
        self.cmd = self.conf_tmp.get(project, 'cmd')

    def command(self):
        return commands.getstatusoutput(self.cmd)


#获取指定项目名可执行的命令
def get_command(project):
    module_name = project+'_commands'
    conf_file = '/tmp/eleme_salt.conf'
    conf_tmp=ConfigParser.ConfigParser()
    conf_tmp.read(conf_file)
    try:
        return dict(conf_tmp.items(module_name))
    except:
        return False

#获取指定配置段的key值
def get_config(sec,key):
    conf_file = '/tmp/eleme_salt.conf'
    conf_tmp=ConfigParser.ConfigParser()
    conf_tmp.read(conf_file)
    return conf_tmp.get(sec,key)


#http请求基类
class MainHandler(tornado.web.RequestHandler):
    opts = salt.config.master_config('/etc/salt/master')
    local = salt.client.LocalClient()
    runner = salt_runner.RunnerClient(opts)
    key = salt_key.Key(opts)
    result = {}

    def auth(self,project,tgt):
        project_key = get_config(project,'key')
        print project_key
        token = self.get_argument('token')
        now_time = datetime.datetime.now()
        hours = [now_time.strftime("%Y-%m-%d-%H"),(now_time + datetime.timedelta(hours = 1)).strftime("%Y-%m-%d-%H"),(now_time + datetime.timedelta(hours = -1)).strftime("%Y-%m-%d-%H")]
        token_list = []
        for hour in hours:
            token_list.append(hashlib.new("md5", project_key+hour).hexdigest())
            token_list.append(hashlib.new("md5", hour+project_key).hexdigest())

        print hours
        print token_list

        if token in token_list:
            return True
        else:
            return False

#excute salt 
class ConfigState(MainHandler):
    def post(self):
        result={}
        project = self.get_argument('project')
        if self.auth(project,tgt=False):
            tgt = self.get_argument('tgt')
            sls = self.get_argument('sls')
            timeout = self.get_argument('timeout')
            result['data'] = self.local.cmd_async(tgt,'state.sls',[sls],expr_form='list',timeout=timeout)
            result['state'] = True
        else:
            result['data'] = 'auth wrong'
            result['state'] = False

        self.write(json.dumps(result))


#Grains
class GrainsItems(MainHandler):
    def post(self):
        result={}
        project = self.get_argument('project')
        tgt = self.get_argument('tgt')
        if self.auth(project,tgt=False):
            self.local.cmd(tgt,
                          'saltutil.sync_grains',
                           expr_form='list'
                          )
            result['data'] = self.local.cmd(tgt,
                                          'grains.items',
                                          expr_form='list',
                                           )
            result['state'] = True
        else:
            result['data'] = 'auth wrong'
            result['state'] = False
        self.write(json.dumps(result))


#Pillar
class PillarData(MainHandler):
    def post(self):
        result={}
        project = self.get_argument('project')
        tgt = self.get_argument('tgt')
        if self.auth(project,tgt=False):
            self.local.cmd(tgt,
                          'saltutil.sync_all',
                           expr_form='list'
                          )
            result['data'] = self.local.cmd(tgt,
                                          'pillar.data',
                                          expr_form='list',
                                          )
            result['state'] = True
        else:
            result['data'] = 'auth wrong'
            result['state'] = False
        self.write(json.dumps(result))

#class Command(MainHandler):
#    def post(self):
#        result={}
#        project = self.get_argument('project')
#        tgt = self.get_argument('tgt')
#        cmd_args = self.get_argument('args',None)
#        timeout = self.get_argument('timeout')
#        if self.auth(project,tgt=False):
#            cmds = get_command(project)
#            cmd_k = self.get_argument('cmd')
#            if cmd_k in cmds.keys():
#                cmd_str = cmds[cmd_k]
#                if cmd_args:
#                    cmd_args = json.loads(cmd_args)
#                    t = Template(cmd_str)
#                    instances=cmd_args['args']
#                    cmd_str = t.render(instances=cmd_args['args'])
#                try:
#                    result['data'] = self.local.cmd_async(tgt,
#                                              'cmd.run_all',
#                                              [str(cmd_str)],
#                                              expr_form='list',
#                                              timeout=timeout)
#                    if result['data']:
#                        result['state'] = True
#                    else:
#                        result['state'] = False
#                except:
#                        result['data']='exec wrong'
#                        result['state'] = False
#            else:
#                result['data'] = "Not support the command"
#                result['state'] = False
#        else:
#            result['data'] = 'auth wrong'
#            result['state'] = False
#
#        self.write(json.dumps(result))


#get host status
class HostState(MainHandler):
    def post(self):
        result={}
        if self.auth('global',tgt=False):
            lister = self.get_argument('list')
            minions = self.local.cmd('*', 'test.ping', timeout=120)
            keys = self.key.list_keys()
            ret = {}
            ret['up'] = sorted(minions)
            ret['down'] = sorted(set(keys['minions']) - set(minions))
            if lister == 'up':
                result['data'] = ret['up']
                result['state'] = True
            elif lister == 'down':
                result['data'] = ret['down']
                result['state'] = True
            else:
                result['data'] = 'Not support the command'
                result['state'] = False
        else:
            result['data'] = 'auth wrong'
            result['state'] = False

        self.write(json.dumps(result))

#通过JID返回执行状态
class ShowReturn(MainHandler):
    def post(self):
        result={}
        jid_type = self.get_argument('jid_type')
        project = self.get_argument('project')
        if self.auth(project,tgt=False):
            jid = self.get_argument('jid')
            if jid == 'all':
                result['data'] = self.runner.cmd('jobs.list_jobs', [])
                result['state'] = True
            elif jid and jid_type == 'normal':
                result['data'] = self.runner.cmd('jobs.lookup_jid',[jid])
                result['state'] = True
            elif jid and jid_type == 'sls':
                result['data'] = {}
                result['data']['error'] = {}
                result['data']['correct'] = {}
                host_ret = {}
                job_ret = self.runner.cmd('jobs.lookup_jid',[jid]).items()
                for hostname,v in job_ret:
                    host_ret[hostname] = {}
                    host_state = 'correct'
                    for i,j in v.items():
                        job_name = re.sub(r'-u(.+?) -p(.+?) ','-uxxx -pxxx ',i)
                        if j['result']:
                            host_ret[hostname][job_name] = j['comment']
                        else:
                            host_ret[hostname][job_name] = j['comment']
                            host_state = 'error'

                    result['data'][host_state][hostname] = host_ret[hostname]
                result['state'] = True
            else:
                result['data'] = 'Not support the command'
                result['state'] = False
        else:
            result['data'] = 'auth wrong'
            result['state'] = False

        self.write(json.dumps(result))

#key相关操作
class Key(MainHandler):
    def post(self):
        result={}
        #project = self.get_argument('project')
        if self.auth('global',tgt=False):
            operation = self.get_argument('operation')
            if operation == 'list':
                    result['data'] = self.key.list_keys()['minions']
                    result['state'] = True
            elif operation == 'delete':
                tgt = self.get_argument('tgt')
                key_list = tgt.split(',')
                try:
                    for i in key_list:
                        self.key.delete_key(i)
                    result['state'] = True
                    result['data'] = None
                except:
                    result['state'] = False
                    result['data'] = None
            else:
                result['data'] = 'Not support the operation'
                result['state'] = False
        else:
            result['data'] = 'auth wrong'
            result['state'] = False
        self.write(json.dumps(result))


#查看文件
class ShowSlsContent(MainHandler):
    def post(self):
        result={'state':False}
        project = self.get_argument('project')
        file = self.get_argument('file')
        if self.auth(project,tgt=False):
            if file.endswith('.sls'):
                abs_file = os.path.join(SALT_DIR,file)
                if os.path.isfile(abs_file):
                    with open(abs_file,'r') as f:
                        result['data'] = f.read()
                        result['state'] = True
                else:
                    result['data'] = 'no such sls file!'
            else:
                result['data'] = 'only sls file can show!'
        else:
            result['data'] = 'auth wrong'
        self.write(json.dumps(result))


settings = {'debug' : True}
#URL路由
application = tornado.web.Application([
    (r"/api/v1.1/config_state/", ConfigState),
#    (r"/api/v1.1/command/", Command),
    (r"/api/v1.1/key/", Key),
    (r"/api/v1.1/host_state/", HostState),
    (r"/api/v1.1/show_return/", ShowReturn),
    (r"/api/v1.1/grains_items/", GrainsItems),
    (r"/api/v1.1/pillar_data/", PillarData),
    (r"/api/v1.1/showslscontext/", ShowSlsContent),
],**settings)

if __name__ == "__main__":
    application.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
