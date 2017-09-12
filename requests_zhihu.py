import requests
from lxml import etree
from PIL import Image
import http.cookiejar
import json, time, re
import get
from get import get_response
from multiprocessing import Process, Queue
import threading

s = requests.Session()
s.headers = {
			'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
			'Accept-Encoding':'gzip, deflate, br',
			'Accept-Language':'zh-CN,zh;q=0.8',
			'Cache-Control':'no-cache',
 			'Connection':'keep-alive',
 			"Host": "www.zhihu.com",
 			'Pragma':'no-cache',
 			"Referer": "https://www.zhihu.com/",
 			'Upgrade-Insecure-Requests':'1',
 			'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 '
 			'(KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
 			}
s.cookies = http.cookiejar.LWPCookieJar("cookie")

def load_cookies():
	try:
		s.cookies.load(ignore_discard=True)
		print("cookies 已加载")
		return True
	except IOError:
		print("cookies 未加载")
		return False

def get_captcha():
	t = str(time.time()*1000)
	captcha_url = 'http://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
	with open('captcha.jpg', 'wb') as p:
		p.write(get_response(s, captcha_url, proxy=False).content)
	im = Image.open('captcha.jpg')
	im.show()
	captcha = input("请输入验证码：")
	return captcha

def get_xsrf():
	url = 'http://www.zhihu.com/'
	response = get_response(s, url, proxy=False).text
	page = etree.HTML(response)
	_xsrf = page.xpath('//form[@method="POST"]/input[@name="_xsrf"]/@value')[0]
	return _xsrf

def login(account, password):
	_xsrf = get_xsrf()
	captcha = get_captcha()
	if re.match(r'.+@.+', account):
		login_url = 'https://www.zhihu.com/login/email'
		form_data = {
					'_xsrf': _xsrf,
		 			'password': password,
		 			'email': account,
					'captcha': captcha
					}
	else:
		login_url = 'https://www.zhihu.com/login/phone_num'
		form_data = {
					'_xsrf': _xsrf,
		 			'password': password,
		 			'phone_num': account,
					'captcha': captcha
					}
	response = get_response(s, url=login_url, data=form_data, proxy=False).text
	print(json.loads(response)['msg'])
	s.cookies.save(ignore_discard=True, ignore_expires=True)
	return int(json.loads(response)['r'])

def get_topic_urls():
	head_url = 'https://www.zhihu.com/topic/'
	tail_url = '/top-answers'
	my_topic_url = 'https://www.zhihu.com/followed_topics?offset=0&limit=80' # offse，limit表示1-80个项目
	res = get_response(s, my_topic_url, proxy=False).text
	time.sleep(3)
	print(json.loads(res))
	topic_lists = json.loads(res)['payload']
	topic_urls = []
	for topic in topic_lists:
		topic_url = head_url + topic['url_token'] + tail_url
		# print(topic_url)
		topic_urls.append(topic_url)
		q_url.put(topic_url)

def get_topic_info():
	topics = []
	while True:
		url = q_url.get()
		topic = {} #放在循环内部！！！
		response = get_response(s, url, proxy=False).text
		time.sleep(3)
		page = etree.HTML(response)
		title = page.xpath('//div[@id="zh-topic-title"]/h1/text()')[0]
		followers = page.xpath('//div[@class="zm-topic-side-followers-info"]/a/strong/text()')[0] #text只能得到直接子节点的文本，string可得全部；与bs4相反
		topic['title'] = title
		topic['url'] = url
		topic['followers'] = followers
		active_answerers_list = []
		active_answerers = page.xpath('//div[@class="zm-topic-side-person-item"]')
		for answerer in active_answerers:
			active_answerer = {}
			active_answerer['name'] = answerer.xpath('div[@class="zm-topic-side-person-item-content"]/a/text()')[0] #最好不要对子元素再进行xpath,if so,需从该element的直接子节点直接往下写，前往不要用\\也不要用\！！
			active_answerer['url'] = 'http://www.zhihu.com' + answerer.xpath('div[@class="zm-topic-side-person-item-content"]/a/@href')[0]
			active_answerer['description'] = answerer.xpath('div[@class="zm-topic-side-person-item-content"]/div[2]/a/text()')[0]
			active_answerers_list.append(active_answerer)
		topic['active_answerers'] = active_answerers_list
		print("话题:" + topic['title'] + " 加载完毕")
		topics.append(topic)
		q_topic.put(topic)
		if len(topics) == 42:
			break
	print("全部话题加载完毕，等待爬取热门问题...")
	with open('zhihu_topics.json', 'w') as f:
		json.dump(topics, f)

def get_question_threads():
	top_questions = []
	while True:
		topic_question_list = []
		topic = q_topic.get()
		url = topic['url']
		for n in range(1, 6):
			url1 = url + '?page=' + str(n) #n转化为字符！！
			response = get_response(s, url1, proxy=False).text
			time.sleep(3)
			page = etree.HTML(response)
			issues = page.xpath('//div[@itemprop="question"]')
			threads = []
			for issue in issues:
				thread = threading.Thread(target=get_question_details, args=(issue, topic))
				threads.append(thread)
			for thread in threads:
				thread.start()
				time.sleep(5)
			for thread in threads:
				thread.join()
				top_question = q_question.get()
				topic_question_list.append(top_question)
		top_questions.append(topic_question_list)
		if len(top_questions) == 42:
			break
	with open('top_questions.json', 'w') as f:
		json.dump(top_questions, f)

def get_question_details(issue, topic):
	top_question = {}
	top_question['category'] = topic['title']
	top_question['question_title'] = issue.xpath('div[@class="feed-main"]/div/h2/a/text()')[0].strip()
	top_question['question_url'] = 'http://www.zhihu.com' + issue.xpath('div[@class="feed-main"]/div/h2/a/@href')[0] 
	print(top_question['question_title'])
	response = get_response(s, top_question['question_url'], proxy=False).text
	page = etree.HTML(response)
	top_question['question_followers'] = page.xpath('//button[@class="Button NumberBoard-item Button--plain"]/div[2]/text()')[0]
	top_question['question_watchers'] = page.xpath('//div[@class="NumberBoard-item"]/div[2]/text()')[0]
	question_answers = etree.tostring(page.xpath('//h4[@class="List-headerText"]')[0]).decode('utf-8')
	# print(question_answers)
	top_question['question_answers'] = re.findall(r'>(\d+)\s', question_answers)[0] #有问题的地方要看下源网页，看是不是有这个元素，是否与之相同
	best_answer = {}
	best_answer['author'] = page.xpath('//div[@data-zop-feedlist="true"]/div[1]//div[@class="AuthorInfo"]/meta[1]/@content')[0]
	best_answer['author_link'] = page.xpath('//div[@data-zop-feedlist="true"]/div[1]//div[@class="AuthorInfo"]/meta[3]/@content')[0]
	answer_content = page.xpath('//div[@data-zop-feedlist="true"]/div[1]//div[@class="RichContent RichContent--unescapable"]//span[@class="RichText CopyrightRichText-richText"]//text()')
	best_answer['content'] = ''.join(answer_content)
	print(best_answer['content'])
	top_question['best_answer'] = best_answer
	lock.acquire()
	q_question.put(top_question)
	lock.release()

if __name__=='__main__':
	if load_cookies():
		lock = threading.Lock()
		q_url = Queue()
		q_topic = Queue()
		q_question = Queue()
		funcs = [get_topic_urls, get_topic_info, get_question_threads]
		process = []
		for fun in funcs:
			p = Process(target=fun, args=())
			process.append(p)
		for p in process:
			p.start()
		for p in process:
			p.join()
	else:
		while True:
			account = input("请输入账号: ")
			password = input("请输入密码：")
			status = login(account, password)
			if status == 0:
				break
		lock = threading.Lock()
		q_url = Queue()
		q_topic = Queue()
		q_question = Queue()
		funcs = [get_topic_urls, get_topic_info, get_question_threads]
		process = []
		for fun in funcs:
			p = Process(target=fun, args=())
			process.append(p)
		for p in process:
			p.start()
		for p in process:
			p.join()




