'''
模块名: chd_bulletin_spider
定义的类：chdParser(MyParser),chdArchiver(MyArchiver),chdSpider(MySpider)
简介：爬取长安大学信息门户公告，并存到数据库
目前已知的bug或者缺陷：
- 新闻链接混杂着绝对链接和相对链接，遇到绝对链接时会出错，正在修复
- 需要已经创建好的数据库和表，正在修改为能自动检测并创建相应的表
- 很多函数还没有完整的错误处理
'''

from my_spider import MySpider
from my_parser import MyParser
from my_database import MyDatabase
from my_archiver import MyArchiver
import decorator

from bs4 import BeautifulSoup
import requests
import pymysql
import json

class chdParser(MyParser):

    @decorator.report
    def login_data_parser(self,login_url):
        '''
        长安大学登录表单数据解析
        :param login_url: 登录页面的url
        :return (登录信息字典,获取时得到的cookies)
        '''
        

        response=requests.get(login_url)
        html=response.text
        # parse the html
        soup=BeautifulSoup(html,'lxml')
        
        lt=soup.find('input',{'name':'lt'})['value']
        dllt=soup.find('input',{'name':'dllt'})['value']
        execution = soup.find('input', {'name': 'execution'})['value']
        _eventId = soup.find('input', {'name': '_eventId'})['value']
        rmShown = soup.find('input', {'name': 'rmShown'})['value']
        login_data={
            'username': input('input account:'),
            'password': input('input passwd:'),
            'btn':'',
            'lt': lt,
            'dllt': dllt,
            'execution': execution,
            '_eventId': _eventId,
            'rmShown': rmShown
        }


        

        return login_data,response.cookies

    @decorator.report
    def get_urls(self,catalogue_url,**kwargs):
        '''
        获取目录页的url
        :param catalogue_url:目录页的url
        :param **kwargs:cookies和headers可以从这里传入
        '''
        #prepare
        base_url='http://portal.chd.edu.cn/'
        index_url='http://portal.chd.edu.cn/index.portal?.pn=p167'
        cata_base_url=catalogue_url.split('?')[0]
        para = {
            'pageIndex': 1,
            'pageSize': '',
            '.pmn': 'view',
            '.ia': 'false',
            'action': 'bulletinsMoreView',
            'search': 'true',
            'groupid': 'all',
            '.pen': 'pe65'
        }
        requests.post(index_url,**kwargs)
        
        #get page number
        xpath='//*[@id="bulletin_content"]/div[2]/div/span/text()'
        num=self.uni_parser(cata_base_url,xpath,params=para,**kwargs)
        num=num[0].strip().split("/")
        total=int(num[0])
        page_num=int(num[1])
        
        #repeat get single catalogue's urls
        xpath='//*[@id="bulletin_content"]//ul[contains(@class,"rss-container")]//a[@class="rss-title"]/@href'
        url_list=[]
        
        
        for i in range(1,10+1):
            para['pageIndex'] = i
            #report
            print("[@parser]:get urls({}%): {}/{}".format(round((i/page_num)*100,1),i,page_num))
            #get single catalogue's urls
            urls=self.uni_parser(cata_base_url,xpath,params=para,**kwargs)
            for url in urls:
                url_list.append(base_url+str(url))

        return url_list
    
    def get_content(self,url,**kwargs):
        '''
        获取内容
        :param url:需要解析的网页的url
        :return: 用于传给存档器的 记录字典，键为字段名，值为值
        '''
        try:
            html=requests.post(url,**kwargs).text
            soup=BeautifulSoup(html,'lxml')
            html=str(soup.find('div',id='content'))
            title=str(soup.find('div',class_='bulletin-title').text).strip()
            
            record_dict={
                'url':url,
                'title':title,
                'html':pymysql.escape_string(html)
            }
        except:
            print('There is an exception when parser "{}"'.format(url))
            record_dict={
                'url':url,
                'title':'There is an exception when parser "{}"'.format(url),
                'html':'error'
            }
            return 

        return record_dict

    
class chdArchiver(MyArchiver):
    pass

class chdSpider(MySpider):
    pass


if __name__ == '__main__':
    
    #读取json配置文件
    with open('config.json','r') as f:
        config=json.load(f)
    
    connect_config={
        'host':config['host'],
        'user':config['user'],
        'passwd':config['passwd'],
        'port':config['port'],
        'charset':config['charset'],
    }

    #创建解析器和存档器
    parser=chdParser()
    archiver=chdArchiver(config['database_name'],config['table_name'],**connect_config)
    #召唤小蜘蛛:D
    sp=chdSpider(parser,archiver)
    sp.crawl(config['login_url'],config['home_page_url'],config['catalogue_url'])
    