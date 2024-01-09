from curl_cffi import requests
import Function.config as cf
from urllib.parse import quote

s = requests.Session()

# ========================================================================curl请求(模拟浏览器指纹)


def curl_html(url, headers=None, proxies=True, cookies=None):
    global s

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

    cf.add_log(f'🔎 请求 {url}')
    if not proxies:
        cf.add_log(f'🔴 注意：你未设置代理，当前请求不会使用系统代理！需要你在「设置」-「网络」中设置 http 或 socks5 后才会走代理！（如路由器已科学或使用 Surge 增强模式，可忽略） 当前请求：{url}')
    for i in range(int(retry_times)):
        try:
            response = s.get(url_encode(url), headers=headers, cookies=cookies, proxies=proxies, impersonate="edge99")
            if 'amazon' in url:
                response.encoding = 'Shift_JIS'
            else:
                response.encoding = 'UFT-8'
            if response.status_code == 200:
                cf.add_log(f'✅ 成功 {url}')
                return response.headers, response.text
            else:
                error_info = f"{response.status_code} {url}"
                cf.add_log('🔴 重试 [%s/%s] %s' % (i + 1, retry_times, error_info))
                continue
        except Exception as e:
            error_info = '%s\nError: %s' % (url, e)
            cf.add_log('[%s/%s] %s' % (i + 1, retry_times, error_info))
    cf.add_log(f"🔴 请求失败！{error_info}")
    return False, error_info


def url_encode(url):
    new_url = ''
    for i in url:
        if i not in [':', '/', '&', '?', '=', '%']:
            i = quote(i)
        new_url += i
    return new_url


if "__main__" == __name__:
    url = "https://www.amazon.co.jp/black-curtain/save-eligibility/black-curtain?returnUrl=/s?k=%25E3%2582%25B8%25E3%2583%25A3%25E3%2582%25A4%25E3%2582%25A2%25E3%2583%25B3%25E3%2583%2588%25E5%25AE%25B6%25E6%2597%258F%25E3%2581%25AB%25E7%258A%25AF%25E3%2581%2595%25E3%2582%258C%25E3%2581%259F%25E5%25B0%258F%25E3%2581%25A3%25E3%2581%25A1%25E3%2582%2583%25E3%2581%25AA%25E5%25A7%2589%25E5%25A6%25B9%2B%25E5%25A4%25A2%25E4%25B9%2583%25E3%2581%2582%25E3%2581%2584%25E3%2581%258B%2B%255BDVD%255D&ref=nb_sb_noss"
    curl_html(url)
