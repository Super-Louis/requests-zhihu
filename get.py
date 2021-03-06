import random, json
# from ip_acquire import get_ips
import time
user_agents = [
	"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
	]
with open('ip_pool.txt', 'r') as f:
	ip_list = json.load(f)

def get_response(s, url, data=None, timeout=5, proxy=False, num_retries=6):
	# s.headers['User-Agent'] = random.choice(user_agents)
	if not proxy:
		# print("不使用代理")
		try:
			if data == None:
				return s.get(url, timeout=timeout)
			else:
				return s.post(url, data=data, timeout=timeout)
		except:
			if num_retries > 0:
				print("连接失败，重试中...")
				time.sleep(1)
				return get_response(s, url, data, timeout=5, proxy=False, num_retries=num_retries-1)
			else:
				print("已失败6次，尝试切换IP...")
				time.sleep(1)
				return get_response(s, url, data, timeout=5, proxy=True, num_retries=6)
	else:
		print("使用代理连接")
		try:
			proxy = random.choice(ip_list)
			if data == None:
				return s.get(url, timeout=timeout, proxies=proxy)
			else:
				return s.post(url, data=data, timeout=timeout, proxies=proxy)
		except:
			if num_retries > 0:
				print("更换代理连接")
				# ip_list.remove(proxy)
				# if ip_list == []:
				# ip_list = get_ips()
				time.sleep(1)
				return get_response(s, url, data, timeout=timeout, proxy=True)
			else:
				print("已失败6次，切换回本地IP")
				return get_response(s, url, data, timeout=3, proxy=False, num_retries=6)


