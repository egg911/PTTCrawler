import time, requests, json
from bs4 import BeautifulSoup
from fbchat import Client
from fbchat.models import *

class PttSpider():
    def __init__(self, url = "https://www.ptt.cc//bbs/drama-ticket/index.html"):
        self.url = url

    def get_soup(self):
        time.sleep(1)
        resp = requests.get(url = self.url,cookies={'over18': '1'})

        #if resp.status_code != 200:
        #    print ('Invalid url:', resp.url)
        #    time.sleep(60)
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        return soup

class FileOperate():
    def __init__(self, filename = "text.json"):
        self.filename = filename

    def saveFile(self, articleLitst = []):
        with open(self.filename, 'w', encoding = 'utf-8') as f:
            json.dump(articleLitst, f, indent = 2, ensure_ascii = False)
        f.close()

    def loadFile(self):
        with open(self.filename, encoding = 'utf-8') as f:
            object_list = json.load(f)
        f.close()
        return object_list

class Article():
    def __init__(self):
        self.title = ""
        self.href = ""
        self.post_date = ""
        self.auther = ""
        self.blacklist = ""
    
    def filled_info_from_web(self, div):
        self.title = div.find('a').string
        self.href = div.find('a')['href']
        self.post_date = div.find('div', 'date').string
        self.auther = div.find('div', 'author').string
        self.blacklist = ""
    
    def filled_info_from_json(self, jsonDic):
        self.title = jsonDic['title']
        self.href = jsonDic['href']
        self.post_date = jsonDic['post_date']
        self.auther = jsonDic['auther']
        self.blacklist = jsonDic['blacklist']

    def get_title(self):
        return self.title
    
    def get_href(self):
        return self.href

    def get_content(self):
        soup = PttSpider("https://www.ptt.cc" + self.href).get_soup()
        content = soup.find(id = 'main-container').text
        return content
    
    def object2json(self):
        return {"title" : self.title,"href" : self.href, "post_date" : self.post_date, "auther" : self.auther, "blacklist" : self.blacklist}
        
    def isSameArticle(self, article):
        return (self.href == article.href)

class Articlelist():
    def __init__(self, url):
        self.article_list = []

        soup = PttSpider(url).get_soup()
        divs = soup.find_all('div', 'r-ent')
        for div in divs:
            if(div.find('a') != None):
                article = Article()
                article.filled_info_from_web(div)
                self.article_list.append(article)
    
    def get_all_articles(self):
        return self.article_list

    def get_all_articles_url(self):
        articles_url = []
        for i in self.article_list:
            articles_url.append(i.get_href())
        return articles_url

    def filt_article(self, keyWords):
        filted_articles = []
        for article in self.article_list:
            selected_flag = True
            for keyWord in keyWords:
                selected_flag = selected_flag and (keyWord in article.title)
            if(selected_flag):
                filted_articles.append(article)

        return filted_articles

    def saveArticleList(self):
        json_article_list = []
        for i in self.article_list:
            json_article_list.append(i.object2json())

        file = FileOperate()
        file.saveFile(json_article_list)

class OldArticlelist(Articlelist):
    def __init__(self):
        self.article_list = []

        jsonFile = FileOperate("text.json")
        jsonAricleList = jsonFile.loadFile()
        
        for i in jsonAricleList:
            article = Article()
            article.filled_info_from_json(i)
            self.article_list.append(article)
    
    def update_old_article_list(self, articlelist):
        self.article_list = self.article_list + articlelist
        self.saveArticleList()

class ArticleOperater():
    def __init__(self, url = "https://www.ptt.cc//bbs/drama-ticket/index.html"):
        self.article_list = Articlelist(url)
        self.old_article_list = OldArticlelist()

    def get_new_articles(self):
        new_article_list = []
        old_article_list_url = self.old_article_list.get_all_articles_url()
        for i in self.article_list.get_all_articles():
            if(i.get_href() not in old_article_list_url):
                new_article_list.append(i)
                #print(i.get_title())
        return new_article_list

    def update_old_article_list(self, new_articlelist):
        self.old_article_list.update_old_article_list(new_articlelist)

    def get_filted_articles(self, articlelist, people):
        filted_articles = []
        for article in articlelist:
            selected_flag = True
            for keyWord in people.get_request():
                selected_flag = selected_flag and (keyWord in article.title)
            if(selected_flag):
                filted_articles.append(article)
        return filted_articles

class People():
    def __init__(self, name = "", uid = "", request = []):
        self.name = name
        self.uid = uid
        self.request = request
    
    def get_name(self):
        return self.name

    def get_uid(self):
        return self.uid

    def get_request(self):
        return self.request

    def filled_info_from_json(self, jsonDic):
        self.name = jsonDic['name']
        self.uid = jsonDic['uid']
        self.request = jsonDic['request']

    def object2json(self):
        return {"name" : self.name,"uid" : self.uid ,"request" : self.request}

class PeopleList():
    def __init__(self):

        self.people_list = []
        jsonFile = FileOperate("people.json")
        jsonPeopleList = jsonFile.loadFile()
        
        for i in jsonPeopleList:
            people = People()
            people.filled_info_from_json(i)
            self.people_list.append(people)

    def get_people_list(self):
        return self.people_list
    
    def add_people(self, people):
        self.people_list.append(people)

    def savePeopleList(self):
        json_people_list = []
        for i in self.people_list:
            json_people_list.append(i.object2json())

        file = FileOperate("People.json")
        file.saveFile(json_people_list)

class FbBot():
    def __init__(self, account, password):
        self.client = Client(account, password)
        
    def send_msg(self, people, msg):
        self.client.send(Message(text=msg), thread_id=people.get_uid(), thread_type=ThreadType.USER)
        

class Server():
    def __init__(self):
        self.articleOperater = ArticleOperater()
        self.people_list = PeopleList()
        #self.fbbot = FbBot("account", "password")
        
    def main(self):
        new_article = self.articleOperater.get_new_articles()
        for i in self.people_list.get_people_list():
            sent_article_list = self.articleOperater.get_filted_articles(new_article, i)
            for j in sent_article_list:
                #self.fbbot.send_msg(i, j.get_content())
                print("For " + i.get_name() + " send " + j.get_title() + "/n" +  j.get_content())
        self.articleOperater.update_old_article_list(new_article)

if __name__ == '__main__':
    a = Server()
    a.main()
