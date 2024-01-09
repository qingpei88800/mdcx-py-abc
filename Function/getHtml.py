#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from threading import Lock
import threading
from PIL import Image
from io import BytesIO
import requests
import cloudscraper
import re
import random
import Function.config as cf
from Function.curl_request import curl_html
from requests.exceptions import HTTPError, ProxyError, SSLError, ConnectionError, Timeout, ConnectTimeout, ReadTimeout, URLRequired, TooManyRedirects, InvalidURL, InvalidHeader, InvalidProxyURL, ChunkedEncodingError, ContentDecodingError, StreamConsumedError
from concurrent.futures import ThreadPoolExecutor
import traceback
import socket
import requests.packages.urllib3.util.connection as urllib3_cn


def allowed_gai_family():
    """
     https://github.com/shazow/urllib3/blob/master/urllib3/util/connection.py
    """
    family = socket.AF_INET
    return family


try:
    if cf.get_config().get('ipv4_only'):
        urllib3_cn.allowed_gai_family = allowed_gai_family
except:
    urllib3_cn.allowed_gai_family = allowed_gai_family

session_g = requests.Session()
session_g.mount('https://', requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100))
session_g.mount('http://', requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100))
scraper = cloudscraper.create_scraper(browser={'browser': 'firefox', 'platform': 'windows', 'mobile': False}) # returns a CloudScraper instance
lock = Lock()
pool = ThreadPoolExecutor(32)

# ========================================================================get请求


def get_html(url: str, headers=None, cookies=None, proxies=True, allow_redirects=True, json_data=False, content=False, res=False, keep=True, timeout=False, encoding='utf-8', back_cookie=False):
    global session_g

    # 获取代理信息
    config = cf.get_config()
    retry_times = config.get('retry')
    if proxies:
        proxies = config['proxies']
    else:
        proxies = {
            "http": None,
            "https": None,
        }

    if not headers:
        headers = config.get('headers')
    if not timeout:
        timeout = config.get('timeout')
    if 'getchu' in url:
        headers_o = {
            'Referer': 'http://www.getchu.com/top.html',
        }
        headers.update(headers_o)
    elif 'xcity' in url:
        headers_o = {
            'referer': 'https://xcity.jp/result_published/?genre=%2Fresult_published%2F&q=2&sg=main&num=60',
        }
        headers.update(headers_o)

    cf.add_log(f'🔎 请求 {url}')
    for i in range(int(retry_times)):
        try:
            if keep:
                response = session_g.get(url, headers=headers, cookies=cookies, proxies=proxies, timeout=timeout, verify=False, allow_redirects=allow_redirects)
            else:
                response = requests.get(url, headers=headers, cookies=cookies, proxies=proxies, timeout=timeout, verify=False, allow_redirects=allow_redirects)
            # print(response.headers.items())
            # print(response.status_code, url)
            _header = response.headers
            if back_cookie:
                _header = response.cookies if response.cookies else _header
            if response.status_code > 299:
                if response.status_code == 302 and allow_redirects:
                    pass
                else:
                    error_info = f"{response.status_code} {url}"
                    cf.add_log('🔴 重试 [%s/%s] %s' % (i + 1, retry_times, error_info))
                    continue
            else:
                cf.add_log(f'✅ 成功 {url}')
            if res:
                return _header, response
            if content:
                return _header, response.content
            response.encoding = encoding
            if json_data:
                return _header, response.json()
            return _header, response.text
        except Exception as e:
            error_info = '%s\nError: %s' % (url, e)
            cf.add_log('[%s/%s] %s' % (i + 1, retry_times, error_info))
    cf.add_log(f"🔴 请求失败！{error_info}")
    return False, error_info


# ========================================================================post请求


def post_html(url: str, data=None, json=None, headers=None, cookies=None, proxies=True, json_data=False, keep=True):
    global session_g

    # 获取代理信息
    config = cf.get_config()
    timeout = config.get('timeout')
    retry_times = config.get('retry')
    if not headers:
        headers = config.get('headers')
    if proxies:
        proxies = config['proxies']
    else:
        proxies = {
            "http": None,
            "https": None,
        }

    cf.add_log(f'🔎 POST请求 {url}')
    for i in range(int(retry_times)):
        try:
            if keep:
                response = session_g.post(url=url, data=data, json=json, headers=headers, cookies=cookies, proxies=proxies, timeout=timeout, verify=False)
            else:
                response = requests.post(url=url, data=data, json=json, headers=headers, cookies=cookies, proxies=proxies, timeout=timeout, verify=False)
            if response.status_code > 299:
                error_info = f"{response.status_code} {url}"
                cf.add_log('🔴 重试 [%s/%s] %s' % (i + 1, retry_times, error_info))
                continue
            else:
                cf.add_log(f'✅ POST成功 {url}')
            response.encoding = 'utf-8'
            if json_data:
                return True, response.json()
            return True, response.text
        except Exception as e:
            error_info = '%s\nError: %s' % (url, e)
            cf.add_log('[%s/%s] %s' % (i + 1, retry_times, error_info))
    cf.add_log(f"🔴 请求失败！{error_info}")
    return False, error_info


# ========================================================================scraper请求(绕过5s盾)


def scraper_html(url: str, proxies=True, cookies=None, headers=None):
    global scraper

    # 获取代理信息
    config = cf.get_config()
    is_docker = config.get('is_docker')
    timeout = config.get('timeout')
    retry_times = config.get('retry')
    if is_docker:
        return get_html(url, proxies=proxies, cookies=cookies)
    if proxies:
        proxies = config['proxies']
    else:
        proxies = {
            "http": None,
            "https": None,
        }

    cf.add_log(f'🔎 Scraper请求 {url}')
    for i in range(retry_times):
        try:
            with scraper.get(url, headers=headers, proxies=proxies, cookies=cookies, timeout=timeout) as f:
                response = f

            if response.status_code > 299:
                error_info = f"{response.status_code} {url} {str(f.cookies).replace('<RequestsCookieJar[', '').replace(']>', '')}"
                return False, error_info
            else:
                cf.add_log(f'✅ Scraper成功 {url}')
            response.encoding = 'utf-8'
            return True, f.text
        except Exception as e:
            error_info = '%s\nError: %s' % (url, e)
            cf.add_log('🔴 重试 [%s/%s] %s' % (i + 1, retry_times, error_info))
    cf.add_log(f"🔴 请求失败！{error_info}")
    return False, error_info


# ========================================================================检测链接


def check_url(url, length=False, real_url=False):
    config = cf.get_config()
    proxies = config.get('proxies')
    timeout = config.get('timeout')
    retry_times = config.get('retry')
    headers = config.get('headers')

    if not url:
        return 0

    cf.add_log(f'⛑️ 检测链接 {url}')
    if 'http' not in url:
        cf.add_log(f'🔴 检测未通过！链接格式错误！ {url}')
        return 0

    if 'getchu' in url:
        headers_o = {
            'Referer': 'http://www.getchu.com/top.html',
        }
        headers.update(headers_o)

    for j in range(retry_times):
        try:
            r = requests.head(url, headers=headers, proxies=proxies, timeout=timeout, verify=False, allow_redirects=True)

            # 状态码 > 299，表示请求失败，视为不可用
            if r.status_code > 299:
                error_info = f"{r.status_code} {url}"
                cf.add_log('🔴 请求失败！ 重试: [%s/%s] %s' % (j + 1, retry_times, error_info))
                continue

            # 返回重定向的url
            true_url = r.url
            if real_url:
                return true_url

            # 检查是否需要登录 https://lookaside.fbsbx.com/lookaside/crawler/media/?media_id=637921621668064
            if 'login' in true_url:
                cf.add_log(f'🔴 检测未通过！需要登录查看 {true_url}')
                return 0

            # 检查是否带有图片不存在的关键词
            '''
            如果跳转后的真实链接存在删图标识，视为不可用
            https://pics.dmm.co.jp/mono/movie/n/now_printing/now_printing.jpg dmm 删图的标识，javbus、javlib 用的是 dmm 图
            https://static.mgstage.com/mgs/img/common/actress/nowprinting.jpg mgstage 删图的标识
            https://jdbimgs.com/images/noimage_600x404.jpg javdb删除的图 WANZ-921
            https://www.javbus.com/imgs/cover/nopic.jpg
            https://assets.tumblr.com/images/media_violation/community_guidelines_v1_1280.png tumblr删除的图
            '''
            bad_url_keys = ['now_printing', 'nowprinting', 'noimage', 'nopic', 'media_violation']
            for each_key in bad_url_keys:
                if each_key in true_url:
                    cf.add_log(f'🔴 检测未通过！当前图片已被网站删除 {url}')
                    return 0

            # 获取文件大小。如果没有获取到文件大小，尝试下载15k数据，如果失败，视为不可用
            content_length = r.headers.get('Content-Length')
            if not content_length:
                response = requests.get(true_url, headers=headers, proxies=proxies, timeout=timeout, verify=False, stream=True)
                i = 0
                chunk_size = 5120
                for _ in response.iter_content(chunk_size):
                    i += 1
                    if i == 3:
                        response.close()
                        cf.add_log(f'✅ 检测通过！未返回大小，预下载15k通过 {true_url}')
                        return 10240 if length else true_url
                cf.add_log(f'🔴 检测未通过！未返回大小，预下载15k失败 {true_url}')
                return 0

            # 如果返回内容的文件大小 < 8k，视为不可用
            elif int(content_length) < 8192:
                cf.add_log(f'🔴 检测未通过！返回大小({content_length}) < 8k {true_url}')
                return 0
            cf.add_log(f'✅ 检测通过！返回大小({content_length}) {true_url}')
            return int(content_length) if length else true_url
        except InvalidProxyURL as e:
            error_info = f' 无效的代理链接 ({e}) {url}'
        except ProxyError as e:
            error_info = f' 代理错误 {e} {url}'
        except SSLError as e:
            error_info = f' SSL错误 ({e}) {url}'
        except ConnectTimeout as e:
            error_info = f' 尝试连接到远程服务器时超时 ({e}) {url}'
        except ReadTimeout as e:
            error_info = f' 服务器未在分配的时间内发送任何数据 ({e}) {url}'
        except Timeout as e:
            error_info = f' 请求超时错误 ({e}) {url}'
        except ConnectionError as e:
            error_info = f' 连接错误 {e} {url}'
        except URLRequired as e:
            error_info = f' URL格式错误 ({e}) {url}'
        except TooManyRedirects as e:
            error_info = f' 过多的重定向 ({e}) {url}'
        except InvalidURL as e:
            error_info = f' 无效的url ({e}) {url}'
        except InvalidHeader as e:
            error_info = f' 无效的请求头 ({e}) {url}'
        except HTTPError as e:
            error_info = f' HTTP错误 {e} {url}'
        except ChunkedEncodingError as e:
            error_info = f' 服务器声明了分块编码，但发送了无效的分块 ({e}) {url}'
        except ContentDecodingError as e:
            error_info = f' 解码响应内容失败 ({e}) {url}'
        except StreamConsumedError as e:
            error_info = f' 该响应的内容已被占用 ({e}) {url}'
        except Exception as e:
            error_info = f' Error ({e}) {url}'
        cf.add_log('🔴 重试 [%s/%s] %s' % (j + 1, retry_times, error_info))
    cf.add_log(f'🔴 检测未通过！ {url}')
    return 0


def split_parts(start, end, step):
    parts = [(start, min(start + step, end)) for start in range(0, end, step)]
    return parts


def get_filesize(url):
    global session_g
    config = cf.get_config()
    proxies = config.get('proxies')
    timeout = config.get('timeout')
    retry_times = config.get('retry')
    headers = config.get('headers')

    for _ in range(int(retry_times)):
        try:
            response = session_g.head(url, headers=headers, proxies=proxies, timeout=timeout, verify=False)
            file_size = response.headers.get('Content-Length')
            return file_size
        except:
            pass
    return False


def multi_download(url, file_path) -> None:
    # 获取文件大小
    file_size = get_filesize(url)

    # 判断是不是webp文件
    webp = False
    if file_path.endswith('jpg') and '.webp' in url:
        webp = True

    # 没有大小时，不支持分段下载，直接下载；< 2 MB 的直接下载
    MB = 1024**2
    if not file_size or int(file_size) <= 2 * MB or webp:
        result, response = get_html(url, content=True)
        if result:
            if webp:
                byte_stream = BytesIO(response)
                img = Image.open(byte_stream)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(file_path, quality=95, subsampling=0)
                img.close()
            else:
                with open(file_path, "wb") as f:
                    f.write(response)
            return True
        return False

    return multi_download2(url, file_path, int(file_size))


def multi_download2(url, file_path, file_size) -> None:
    global pool

    # 分块，每块 1 MB
    MB = 1024**2
    file_size = int(file_size)
    each_size = int(1 * MB)
    each_size = min(int(each_size), int(file_size))
    parts = split_parts(0, int(file_size), int(each_size))
    # print(f'分块数：{len(parts)} \n')

    # 先写入一个文件
    f = open(file_path, 'wb')
    f.truncate(file_size)
    f.close()

    # 开始下载
    i = 0
    task_list = []
    for part in parts:
        i += 1
        start, end = part
        task_list.append([start, end, i, url, file_path])
    result = pool.map(start_download, task_list)
    for res in result:
        if not res:
            # bar.close()
            return False
    # bar.close()
    return True


def start_download(task) -> None:
    global session_g
    global lock
    start, end, i, url, file_path = task
    config = cf.get_config()
    proxies = config.get('proxies')
    timeout = config.get('timeout')
    retry_times = config.get('retry')
    headers = config.get('headers')
    _headers = headers.copy()
    _headers['Range'] = f'bytes={start}-{end}'
    for _ in range(int(retry_times)):
        try:
            response = session_g.get(url, headers=_headers, proxies=proxies, timeout=timeout, verify=False, stream=True)
            chunk_size = 128
            chunks = []
            for chunk in response.iter_content(chunk_size=chunk_size):
                chunks.append(chunk)
                # bar.update(chunk_size)
            lock.acquire()
            with open(file_path, "rb+") as fp:
                fp.seek(start)
                for chunk in chunks:
                    fp.write(chunk)
                lock.release()
                # 释放锁
            del chunks
            return True
        except:
            pass
    return False


def get_website_url():
    url = 'https://tellme.pw/avsox'
    result, response = get_html(url)

    if not result:
        return ''
    res = re.findall(r'(https://[^"]+)', response)
    for each in res:
        if 'https://avsox.com' not in each or 'api.qrserver.com' not in each:
            return each
    return ''


def get_avsox_domain():
    try:
        avsox_domain = cf.get_data()['avsox_domain']
    except:
        avsox_domain = get_website_url()
        if avsox_domain:
            cf.set_data('avsox_domain', avsox_domain)
        else:
            avsox_domain = 'https://avsox.click'
    return avsox_domain


def get_imgsize(url):
    config = cf.get_config()
    proxies = config.get('proxies')
    timeout = config.get('timeout')
    retry_times = config.get('retry')
    headers = config.get('headers')

    for _ in range(int(retry_times)):
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout, verify=False, stream=True)
            if response.status_code == 200:
                file_head = BytesIO()
                chunk_size = 1024 * 10
                for chunk in response.iter_content(chunk_size):
                    file_head.write(chunk)
                    response.close()
                    try:
                        img = Image.open(file_head)
                        return img.size
                    except:
                        return (0, 0)
        except:
            return (0, 0)
    return (0, 0)


def get_dmm_trailer(trailer_url):                                               # 获取预览片
    if '.dmm.co' not in trailer_url:
        return trailer_url
    if trailer_url.startswith('//'):
        trailer_url = 'https:' + trailer_url
    '''
    '_sm_w.mp4': 320*180, 3.8MB
    '_dm_w.mp4': 560*316, 10.1MB
    '_dmb_w.mp4': 720*404, 14.6MB
    '_mhb_w.mp4': 720*404, 27.9MB
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_sm_w.mp4
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_dm_w.mp4
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_dmb_w.mp4
    https://cc3001.dmm.co.jp/litevideo/freepv/s/ssi/ssis00090/ssis00090_mhb_w.mp4
    '''

    # keylist = ['_sm_w.mp4', '_dm_w.mp4', '_dmb_w.mp4', '_mhb_w.mp4']
    if '_mhb_w.mp4' not in trailer_url:
        t = re.findall(r'(.+)(_[sd]mb?_w.mp4)', trailer_url)
        if t:
            s, e = t[0]
            mhb_w = s + '_mhb_w.mp4'
            dmb_w = s + '_dmb_w.mp4'
            dm_w = s + '_dm_w.mp4'
            if e == '_dmb_w.mp4':
                if check_url(mhb_w):
                    trailer_url = mhb_w
            elif e == '_dm_w.mp4':
                if check_url(mhb_w):
                    trailer_url = mhb_w
                elif check_url(dmb_w):
                    trailer_url = dmb_w
            elif e == '_sm_w.mp4':
                if check_url(mhb_w):
                    trailer_url = mhb_w
                elif check_url(dmb_w):
                    trailer_url = dmb_w
                elif check_url(dm_w):
                    trailer_url = dm_w
    return trailer_url


def get_amazon_data(req_url):
    '''
    获取 Amazon 数据，修改地区为540-0002
    '''
    try:
        headers = cf.get_data()['amazon_header']
        result, html_info = curl_html(req_url)
    except:
        headers = {
            "accept-encoding": "gzip, deflate, br",
            'Host': 'www.amazon.co.jp',
            'User-Agent': get_user_agent(),
        }
        cf.set_data('amazon_header', headers)
        result, html_info = curl_html(req_url, headers=headers)
        try:
            sessionId = re.findall(r'sessionId: "([^"]+)', html_info)[0]
        except:
            sessionId = ''
        try:
            ubid_acbjp = re.findall(r'ubid-acbjp=([^ ]+)', str(result))[0]
        except:
            ubid_acbjp = ''
        headers = cf.get_data()['amazon_header'].copy()
        headers_o = {
            'cookie': f'session-id={sessionId}; ubid_acbjp={ubid_acbjp}',
        }
        headers.update(headers_o)
        result, html_info = curl_html(req_url, headers=headers)
    return result, html_info

    if not result:
        if '503 http' in html_info:
            headers = {
                'Host': 'www.amazon.co.jp',
                'User-Agent': get_user_agent(),
            }
            cf.set_data('amazon_header', headers)
            result, html_info = get_html(req_url, headers=headers, keep=False, back_cookie=True)

        if not result:
            return False, html_info

    if '540-0002' not in html_info:
        try:
            # 获取 anti_csrftoken_a2z
            anti_csrftoken_a2z = re.findall(r'anti-csrftoken-a2z([^}]+)', html_info)[0].replace('&quot;', '').strip(':')
            sessionId = re.findall(r'sessionId: "([^"]+)', html_info)[0]
            ubid_acbjp = ''
            if 'ubid-acbjp' in str(result):
                try:
                    ubid_acbjp = result['set-cookie']
                except:
                    try:
                        ubid_acbjp = re.findall(r'ubid-acbjp=([^ ]+)', str(result))[0]
                    except:
                        pass
            headers = cf.get_data()['amazon_header'].copy()
            headers_o = {
                'Anti-csrftoken-a2z': anti_csrftoken_a2z,
                'cookie': f'session-id={sessionId}; ubid_acbjp={ubid_acbjp}',
            }
            headers.update(headers_o)
            mid_url = 'https://www.amazon.co.jp/portal-migration/hz/glow/get-rendered-toaster?pageType=Search&aisTransitionState=in&rancorLocationSource=REALM_DEFAULT&_='
            result, html = curl_html(mid_url, headers=headers)
            anti_csrftoken_a2z = re.findall(r'csrfToken="([^"]+)', html)[0]
            try:
                ubid_acbjp = re.findall(r'ubid-acbjp=([^ ]+)', str(result))[0]
            except:
                pass

            # 修改配送地址为日本，这样结果多一些
            headers_o = {
                'Anti-csrftoken-a2z': anti_csrftoken_a2z,
                'Content-length': '140',
                'Content-Type': 'application/json',
                'cookie': f'session-id={sessionId}; ubid_acbjp={ubid_acbjp}',
            }
            headers.update(headers_o)
            post_url = 'https://www.amazon.co.jp/portal-migration/hz/glow/address-change?actionSource=glow'
            data = {"locationType": "LOCATION_INPUT", "zipCode": "540-0002", "storeContext": "generic", "deviceType": "web", "pageType": "Search", "actionSource": "glow"}
            result, html = post_html(post_url, json=data, headers=headers)

            if result:
                if '540-0002' in str(html):
                    headers = cf.get_data()['amazon_header']
                    result, html_info = curl_html(req_url, headers=headers)
                else:
                    print('Amazon 修改地区失败: ', req_url, str(result), str(html))
            else:
                print('Amazon 修改地区异常: ', req_url, str(result), str(html))

        except Exception as e:
            print('Amazon 修改地区出错: ', req_url, str(e))
            print(traceback.format_exc())

    return result, html_info


def get_user_agent():
    temp_l = random.randint(109, 111)
    temp_m = random.randint(1, 5563)
    temp_n = random.randint(1, 180)
    return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/%s.0.%s.%s Safari/537.36' % (temp_l, temp_m, temp_n)


if "__main__" == __name__:
    # 测试下载文件
    list1 = [
        'https://issuecdn.baidupcs.com/issue/netdisk/yunguanjia/BaiduNetdisk_7.2.8.9.exe',
        'https://cc3001.dmm.co.jp/litevideo/freepv/1/118/118abw015/118abw015_mhb_w.mp4',
        'https://cc3001.dmm.co.jp/litevideo/freepv/1/118/118abw00016/118abw00016_mhb_w.mp4',
        'https://cc3001.dmm.co.jp/litevideo/freepv/1/118/118abw00017/118abw00017_mhb_w.mp4',
        'https://cc3001.dmm.co.jp/litevideo/freepv/1/118/118abw00018/118abw00018_mhb_w.mp4',
        'https://cc3001.dmm.co.jp/litevideo/freepv/1/118/118abw00019/118abw00019_mhb_w.mp4',
        'https://www.prestige-av.com/images/corner/goods/prestige/tktabw/018/pb_tktabw-018.jpg',
        'https://iqq1.one/preview/80/b/3SBqI8OjheI-800.jpg?v=1636404497',
    ]
    for each in list1:
        url = each
        file_path = each.split('/')[-1]
        t = threading.Thread(target=multi_download, args=(url, file_path))
        t.start()

    # 死循环，避免程序程序完后，pool自动关闭
    while True:
        pass
