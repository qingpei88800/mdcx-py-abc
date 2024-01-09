#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random
import time
import os
import re
import platform
from configparser import RawConfigParser

config_global = {}
log_global = []
stop = False
data_global = {}

# ====================================================================================================================全局数据


def get_data():
    global data_global
    return data_global


def set_data(key, value):
    global data_global
    data_global[key] = value
    return data_global


# ====================================================================================================================全局日志


def get_current_time():
    return time.strftime("%H:%M:%S", time.localtime())


def add_log(*text):
    global log_global
    global stop
    if stop:
        raise '手动停止刮削'
    try:
        log_global.append(f" ⏰ {get_current_time()} {' '.join(text)}")
    except:
        pass


def get_log():
    global log_global
    text = ''
    if log_global:
        a = len(log_global)
        text = '\n'.join(log_global[:a])
        for _ in range(a):
            log_global.pop(0)
    return text


# ====================================================================================================================停止刮削
def set_stop(stop_flag):
    global config_global
    global stop
    if stop_flag:
        stop = True
        return ''
    stop = False
    config_global = get_config(True)
    return config_global


# ====================================================================================================================返回config_global


def get_config(force=False) -> dict:
    global config_global
    global stop
    if stop and not force:
        raise '手动停止刮削'
    if not config_global:
        mdcx_config = 'MDCx.config'
        if not os.path.exists(mdcx_config):
            mdcx_config = '../MDCx.config'
        if not os.path.exists(mdcx_config):
            # add_log('MDCx.config 未找到！')
            config_path = 'config.ini'
            if not os.path.exists(config_path):
                config_path = '../config.ini'
        else:
            with open(mdcx_config, 'r', encoding='UTF-8') as f:
                config_path = f.read()
        # add_log('读取 %s，生成config_global！' % config_path)
        read_config(config_path)
    return config_global


# ====================================================================================================================读取config.ini


def read_config(config_path) -> dict:
    config = RawConfigParser()
    config.read(config_path, encoding='UTF-8')
    json_config = {
        'config_path': config_path,
        'media_path': config.get('media', 'media_path'),
        'softlink_path': config.get('media', 'softlink_path'),
        'success_output_folder': config.get('media', 'success_output_folder'),
        'failed_output_folder': config.get('media', 'failed_output_folder'),
        'extrafanart_folder': config.get('media', 'extrafanart_folder'),
        'media_type': config.get('media', 'media_type'),
        'sub_type': config.get('media', 'sub_type'),
        'scrape_softlink_path': config.get('media', 'scrape_softlink_path'),
        'folders': config.get('escape', 'folders'),
        'string': config.get('escape', 'string'),
        'file_size': config.getfloat('escape', 'file_size'),
        'no_escape': config.get('escape', 'no_escape'),
        'clean_ext': config.get('clean', 'clean_ext'),
        'clean_name': config.get('clean', 'clean_name'),
        'clean_contains': config.get('clean', 'clean_contains'),
        'clean_size': config.getfloat('clean', 'clean_size'),
        'clean_ignore_ext': config.get('clean', 'clean_ignore_ext'),
        'clean_ignore_contains': config.get('clean', 'clean_ignore_contains'),
        'clean_enable': config.get('clean', 'clean_enable'),
        'website_single': config.get('website', 'website_single'),
        'website_youma': config.get('website', 'website_youma'),
        'website_wuma': config.get('website', 'website_wuma'),
        'website_suren': config.get('website', 'website_suren'),
        'website_fc2': config.get('website', 'website_fc2'),
        'website_oumei': config.get('website', 'website_oumei'),
        'website_guochan': config.get('website', 'website_guochan'),
        'scrape_like': config.get('website', 'scrape_like'),
        'website_set': config.get('website', 'website_set'),
        'title_website': config.get('website', 'title_website'),
        'title_zh_website': config.get('website', 'title_zh_website'),
        'title_website_exclude': config.get('website', 'title_website_exclude'),
        'title_language': config.get('website', 'title_language'),
        'title_sehua': config.get('website', 'title_sehua'),
        'title_yesjav': config.get('website', 'title_yesjav'),
        'title_translate': config.get('website', 'title_translate'),
        'title_sehua_zh': config.get('website', 'title_sehua_zh'),
        'outline_website': config.get('website', 'outline_website'),
        'outline_zh_website': config.get('website', 'outline_zh_website'),
        'outline_website_exclude': config.get('website', 'outline_website_exclude'),
        'outline_language': config.get('website', 'outline_language'),
        'outline_translate': config.get('website', 'outline_translate'),
        'outline_show': config.get('website', 'outline_show'),
        'actor_website': config.get('website', 'actor_website'),
        'actor_website_exclude': config.get('website', 'actor_website_exclude'),
        'actor_language': config.get('website', 'actor_language'),
        'actor_realname': config.get('website', 'actor_realname'),
        'actor_translate': config.get('website', 'actor_translate'),
        'tag_website': config.get('website', 'tag_website'),
        'tag_website_exclude': config.get('website', 'tag_website_exclude'),
        'tag_language': config.get('website', 'tag_language'),
        'tag_translate': config.get('website', 'tag_translate'),
        'tag_include': config.get('website', 'tag_include'),
        'series_website': config.get('website', 'series_website'),
        'series_website_exclude': config.get('website', 'series_website_exclude'),
        'series_language': config.get('website', 'series_language'),
        'series_translate': config.get('website', 'series_translate'),
        'studio_website': config.get('website', 'studio_website'),
        'studio_website_exclude': config.get('website', 'studio_website_exclude'),
        'studio_language': config.get('website', 'studio_language'),
        'studio_translate': config.get('website', 'studio_translate'),
        'publisher_website': config.get('website', 'publisher_website'),
        'publisher_website_exclude': config.get('website', 'publisher_website_exclude'),
        'publisher_language': config.get('website', 'publisher_language'),
        'publisher_translate': config.get('website', 'publisher_translate'),
        'director_website': config.get('website', 'director_website'),
        'director_website_exclude': config.get('website', 'director_website_exclude'),
        'director_language': config.get('website', 'director_language'),
        'director_translate': config.get('website', 'director_translate'),
        'poster_website': config.get('website', 'poster_website'),
        'poster_website_exclude': config.get('website', 'poster_website_exclude'),
        'thumb_website': config.get('website', 'thumb_website'),
        'thumb_website_exclude': config.get('website', 'thumb_website_exclude'),
        'extrafanart_website': config.get('website', 'extrafanart_website'),
        'extrafanart_website_exclude': config.get('website', 'extrafanart_website_exclude'),
        'score_website': config.get('website', 'score_website'),
        'score_website_exclude': config.get('website', 'score_website_exclude'),
        'release_website': config.get('website', 'release_website'),
        'release_website_exclude': config.get('website', 'release_website_exclude'),
        'runtime_website': config.get('website', 'runtime_website'),
        'runtime_website_exclude': config.get('website', 'runtime_website_exclude'),
        'trailer_website': config.get('website', 'trailer_website'),
        'trailer_website_exclude': config.get('website', 'trailer_website_exclude'),
        'wanted_website': config.get('website', 'wanted_website'),
        'whole_fields': config.get('website', 'whole_fields'),
        'none_fields': config.get('website', 'none_fields'),
        'nfo_include_new': config.get('website', 'nfo_include_new'),
        'nfo_tagline': config.get('website', 'nfo_tagline'),
        'nfo_tag_series': config.get('website', 'nfo_tag_series'),
        'nfo_tag_studio': config.get('website', 'nfo_tag_studio'),
        'nfo_tag_publisher': config.get('website', 'nfo_tag_publisher'),
        'translate_by': config.get('website', 'translate_by'),
        'deepl_key': config.get('website', 'deepl_key'),
        'thread_number': config.getint('common', 'thread_number'),
        'thread_time': config.getint('common', 'thread_time'),
        'javdb_time': config.getint('common', 'javdb_time'),
        'main_mode': config.getint('common', 'main_mode'),
        'read_mode': config.get('common', 'read_mode'),
        'update_mode': config.get('common', 'update_mode'),
        'update_a_folder': config.get('common', 'update_a_folder'),
        'update_b_folder': config.get('common', 'update_b_folder'),
        'update_d_folder': config.get('common', 'update_d_folder'),
        'soft_link': config.getint('common', 'soft_link'),
        'success_file_move': config.getint('common', 'success_file_move'),
        'failed_file_move': config.getint('common', 'failed_file_move'),
        'success_file_rename': config.getint('common', 'success_file_rename'),
        'del_empty_folder': config.getint('common', 'del_empty_folder'),
        'show_poster': config.getint('common', 'show_poster'),
        'download_files': config.get('file_download', 'download_files'),
        'keep_files': config.get('file_download', 'keep_files'),
        'download_hd_pics': config.get('file_download', 'download_hd_pics'),
        'google_used': config.get('file_download', 'google_used'),
        'google_exclude': config.get('file_download', 'google_exclude'),
        'folder_name': config.get('Name_Rule', 'folder_name'),
        'naming_file': config.get('Name_Rule', 'naming_file'),
        'naming_media': config.get('Name_Rule', 'naming_media'),
        'prevent_char': config.get('Name_Rule', 'prevent_char'),
        'fields_rule': config.get('Name_Rule', 'fields_rule'),
        'suffix_sort': config.get('Name_Rule', 'suffix_sort'),
        'actor_no_name': config.get('Name_Rule', 'actor_no_name'),
        'release_rule': config.get('Name_Rule', 'release_rule'),
        'folder_name_max': config.getint('Name_Rule', 'folder_name_max'),
        'file_name_max': config.getint('Name_Rule', 'folder_name_max'),
        'actor_name_max': config.getint('Name_Rule', 'actor_name_max'),
        'actor_name_more': config.get('Name_Rule', 'actor_name_more'),
        'umr_style': config.get('Name_Rule', 'umr_style'),
        'leak_style': config.get('Name_Rule', 'leak_style'),
        'wuma_style': config.get('Name_Rule', 'wuma_style'),
        'youma_style': config.get('Name_Rule', 'youma_style'),
        'show_moword': config.get('Name_Rule', 'show_moword'),
        'show_4k': config.get('Name_Rule', 'show_4k'),
        'cd_name': config.getint('Name_Rule', 'cd_name'),
        'cd_char': config.get('Name_Rule', 'cd_char'),
        'pic_name': config.getint('Name_Rule', 'pic_name'),
        'trailer_name': config.getint('Name_Rule', 'trailer_name'),
        'hd_name': config.get('Name_Rule', 'hd_name'),
        'hd_get': config.get('Name_Rule', 'hd_get'),
        'cnword_char': config.get('subtitle', 'cnword_char'),
        'cnword_style': config.get('subtitle', 'cnword_style').strip('^'),
        'folder_cnword': config.get('subtitle', 'folder_cnword'),
        'file_cnword': config.get('subtitle', 'file_cnword'),
        'subtitle_folder': config.get('subtitle', 'subtitle_folder'),
        'subtitle_add': config.get('subtitle', 'subtitle_add'),
        'subtitle_add_chs': config.get('subtitle', 'subtitle_add_chs'),
        'subtitle_add_rescrape': config.get('subtitle', 'subtitle_add_rescrape'),
        'server_type': config.get('emby', 'server_type'),
        'emby_url': config.get('emby', 'emby_url'),
        'api_key': config.get('emby', 'api_key'),
        'emby_on': config.get('emby', 'emby_on'),
        'gfriends_github': config.get('emby', 'gfriends_github'),
        'actor_photo_folder': config.get('emby', 'actor_photo_folder'),
        'poster_mark': config.getint('mark', 'poster_mark'),
        'thumb_mark': config.getint('mark', 'thumb_mark'),
        'fanart_mark': config.getint('mark', 'fanart_mark'),
        'mark_size': config.getint('mark', 'mark_size'),
        'mark_type': config.get('mark', 'mark_type'),
        'mark_fixed': config.get('mark', 'mark_fixed'),
        'mark_pos': config.get('mark', 'mark_pos'),
        'mark_pos_corner': config.get('mark', 'mark_pos_corner'),
        'mark_pos_sub': config.get('mark', 'mark_pos_sub'),
        'mark_pos_mosaic': config.get('mark', 'mark_pos_mosaic'),
        'mark_pos_hd': config.get('mark', 'mark_pos_hd'),
        'type': config.get('proxy', 'type'),
        'proxy': config.get('proxy', 'proxy'),
        'timeout': config.getint('proxy', 'timeout'),
        'retry': config.getint('proxy', 'retry'),
        'javbus_website': config.get('proxy', 'javbus_website'),
        'javdb_website': config.get('proxy', 'javdb_website'),
        'iqqtv_website': config.get('proxy', 'iqqtv_website'),
        'avsex_website': config.get('proxy', 'avsex_website'),
        'hdouban_website': config.get('proxy', 'hdouban_website'),
        'mdtv_website': config.get('proxy', 'mdtv_website'),
        'airavcc_website': config.get('proxy', 'airavcc_website'),
        'lulubar_website': config.get('proxy', 'lulubar_website'),
        'javlibrary_website': config.get('proxy', 'javlibrary_website'),
        'theporndb_api_token': config.get('proxy', 'theporndb_api_token'),
        'javdb': config.get('Cookies', 'javdb'),
        'javbus': config.get('Cookies', 'javbus'),
        'show_web_log': config.get('other', 'show_web_log'),
        'show_from_log': config.get('other', 'show_from_log'),
        'show_data_log': config.get('other', 'show_data_log'),
        'save_log': config.get('other', 'save_log'),
        'update_check': config.get('other', 'update_check'),
        'local_library': config.get('other', 'local_library'),
        'actors_name': config.get('other', 'actors_name'),
        'netdisk_path': config.get('other', 'netdisk_path'),
        'localdisk_path': config.get('other', 'localdisk_path'),
        'window_title': config.get('other', 'window_title'),
        'switch_on': config.get('other', 'switch_on'),
        'timed_interval': config.get('other', 'timed_interval'),
        'rest_count': config.get('other', 'rest_count'),
        'rest_time': config.get('other', 'rest_time'),
        'statement': config.getint('other', 'statement'),
    }
    # add_log('%s read done!' % config_path)
    # 更新config_global
    update_config(json_config)


# ====================================================================================================================更新config_global


def update_config(json_config) -> dict:
    global config_global

    # 获取proxies
    if json_config['type'] == 'http':
        json_config['proxies'] = {
            "http": "http://" + json_config['proxy'],
            "https": "http://" + json_config['proxy'],
        }
    elif json_config['type'] == 'socks5':
        json_config['proxies'] = {
            "http": "socks5h://" + json_config['proxy'],
            "https": "socks5h://" + json_config['proxy'],
        }
    else:
        json_config['proxies'] = None

    # IPv4
    if 'ipv4_only' in json_config['switch_on']:
        json_config['ipv4_only'] = True
    else:
        json_config['ipv4_only'] = False

    # theporndb_no_hash
    if 'theporndb_no_hash' in json_config['switch_on']:
        json_config['theporndb_no_hash'] = True
    else:
        json_config['theporndb_no_hash'] = False

    # 获取User-Agen
    temp_l = random.randint(110, 117)
    temp_m = random.randint(1, 5563)
    temp_n = random.randint(1, 180)
    json_config['headers'] = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/%s.0.%s.%s Safari/537.36' % (temp_l, temp_m, temp_n),
    }

    # 获取javdb_cookie
    cookies_javdb = json_config['javdb']
    if cookies_javdb:
        json_config['javdb_cookie'] = {'cookie': cookies_javdb}
    else:
        json_config['javdb_cookie'] = None
    cookies_javbus = json_config['javbus']
    if cookies_javbus:
        json_config['javbus_cookie'] = {'cookie': cookies_javbus}
    else:
        json_config['javbus_cookie'] = None

    # 要去掉^符号！！！
    json_config['cnword_style'] = json_config['cnword_style'].strip('^')

    # 获取 Google 下载关键词列表
    temp_list = re.split(r'[,，]', json_config['google_used'])
    json_config['google_keyused'] = [each for each in temp_list if each]           # 去空
    # 获取 Google 过滤关键词列表
    temp_list = re.split(r'[,，]', json_config['google_exclude'])
    json_config['google_keyword'] = [each for each in temp_list if each]        # 去空

    # 是否记录刮削成功列表
    json_config['record_success_file'] = bool('record_success_file' in json_config['no_escape'])

    # 是否清理文件以及清理列表
    clean_ext = json_config['clean_ext']
    clean_name = json_config['clean_name']
    clean_contains = json_config['clean_contains']
    clean_size = json_config['clean_size']
    clean_ignore_ext = json_config['clean_ignore_ext']
    clean_ignore_contains = json_config['clean_ignore_contains']
    clean_enable = json_config['clean_enable']
    can_clean = True if 'i_know' in clean_enable and 'i_agree' in clean_enable else False
    can_clean_auto = True if can_clean and 'clean_auto' in clean_enable else False
    clean_ext_list = re.split(r'[|｜，,]', clean_ext) if can_clean and clean_ext and 'clean_ext' in clean_enable else []
    clean_name_list = re.split(r'[|｜，,]', clean_name) if can_clean and clean_name and 'clean_name' in clean_enable else []
    clean_contains_list = re.split(r'[|｜，,]', clean_contains) if can_clean and clean_contains and 'clean_contains' in clean_enable else []
    clean_size_list = clean_size if can_clean and 'clean_size' in clean_enable else ''
    clean_ignore_ext_list = re.split(r'[|｜，,]', clean_ignore_ext) if can_clean and clean_ignore_ext and 'clean_ignore_ext' in clean_enable else []
    clean_ignore_contains_list = re.split(r'[|｜，,]', clean_ignore_contains) if can_clean and clean_ignore_contains and 'clean_ignore_contains' in clean_enable else []
    json_config['can_clean'] = can_clean
    json_config['can_clean_auto'] = can_clean_auto
    json_config['clean_ext_list'] = clean_ext_list
    json_config['clean_name_list'] = clean_name_list
    json_config['clean_contains_list'] = clean_contains_list
    json_config['clean_size_list'] = clean_size_list
    json_config['clean_ignore_ext_list'] = clean_ignore_ext_list
    json_config['clean_ignore_contains_list'] = clean_ignore_contains_list
    os_name = platform.system()
    json_config['is_docker'] = False
    if os_name == 'Linux' or os_name == 'Java':
        json_config['is_docker'] = True

    # 获取排除字符列表
    repl_list = [
        'HEYDOUGA',
        'CARIBBEANCOM',
        'CARIB',
        '1PONDO',
        '1PON',
        'PACOMA',
        'PACO',
        '10MUSUME',
        '-10MU',
        'Tokyo Hot',
        'Tokyo_Hot',
        'TOKYO-HOT',
        'TOKYOHOT',
        '(S1)',
        '[THZU.CC]',
        '「麻豆」',
        '(',
        ')',
        '.PRT',
        'MP4-KTR',
        'rarbg',
        'WEBDL',
        'x2160x',
        'x1080x',
        'x2160p',
        'x1080p',
        'x264 aac',
        'x264_aac',
        'x264-aac',
        'x265 aac',
        'x265_aac',
        'x265-aac',
        'H.264',
        'H.265',
        'DVDRIP',
        'DVD ',
        '2160P',
        '1440P',
        '1080P',
        '960P',
        '720P',
        '540P',
        '480P',
        '360P',
        '4096x2160',
        '1920x1080',
        '1280x720',
        '960x720',
        '640x480',
        '4096×2160',
        '1920×1080',
        '1280×720',
        '960×720',
        '640×480',
        '90fps'
        '60fps',
        '30fps',
        '.cht',
        '.chs',
    ]
    temp_list = re.split('[,，]', json_config['string']) + repl_list
    json_config['escape_string_list'] = []
    [json_config['escape_string_list'].append(i) for i in temp_list if i.strip() and i not in json_config['escape_string_list']]

    # 欧美系列长名字
    json_config['oumei_name'] = {
        'wgp': 'WhenGirlsPlay',
        '18og': '18OnlyGirls',
        '18yo': '18YearsOld',
        '1kf': '1000Facials',
        '21ea': '21EroticAnal',
        '21fa': '21FootArt',
        '21n': '21Naturals',
        '2cst': '2ChicksSameTime',
        'a1o1': 'Asian1on1',
        'aa': 'AmateurAllure',
        'ad': 'AmericanDaydreams',
        'add': 'ManualAddActors',
        'agm': 'AllGirlMassage',
        'am': 'AssMasterpiece',
        'analb': 'AnalBeauty',
        'baebz': 'Baeb',
        'bblib': 'BigButtsLikeItBig',
        'bcasting': 'BangCasting',
        'bconfessions': 'BangConfessions',
        'bglamkore': 'BangGlamkore',
        'bgonzo': 'BangGonzo',
        'brealteens': 'BangRealTeens',
        'bcb': 'BigCockBully',
        'bch': 'BigCockHero',
        'bdpov': 'BadDaddyPOV',
        'bex': 'BrazzersExxtra',
        'bgb': 'BabyGotBoobs',
        'bgbs': 'BoundGangbangs',
        'bin': 'BigNaturals',
        'bjf': 'BlowjobFridays',
        'bp': 'ButtPlays',
        'btas': 'BigTitsatSchool',
        'btaw': 'BigTitsatWork',
        'btc': 'BigTitCreampie',
        'btis': 'BigTitsinSports',
        'btiu': 'BigTitsinUniform',
        'btlbd': 'BigTitsLikeBigDicks',
        'btra': 'BigTitsRoundAsses',
        'burna': 'BurningAngel',
        'bwb': 'BigWetButts',
        'cfnm': 'ClothedFemaleNudeMale',
        'clip': 'LegalPorno',
        'cps': 'CherryPimps',
        'cuf': 'CumFiesta',
        'cws': 'CzechWifeSwap',
        'da': 'DoctorAdventures',
        'dbm': 'DontBreakMe',
        'dc': 'DorcelVision',
        'ddfb': 'DDFBusty',
        'ddfvr': 'DDFNetworkVR',
        'dm': 'DirtyMasseur',
        'dnj': 'DaneJones',
        'dpg': 'DigitalPlayground',
        'dwc': 'DirtyWivesClub',
        'dwp': 'DayWithAPornstar',
        'dsw': 'DaughterSwap',
        'esp': 'EuroSexParties',
        'ete': 'EuroTeenErotica',
        'ext': 'ExxxtraSmall',
        'fams': 'FamilyStrokes',
        'faq': 'FirstAnalQuest',
        'fds': 'FakeDrivingSchool',
        'fft': 'FemaleFakeTaxi',
        'fhd': 'FantasyHD',
        'fhl': 'FakeHostel',
        'fho': 'FakehubOriginals',
        'fka': 'FakeAgent',
        'fm': 'FuckingMachines',
        'fms': 'FantasyMassage',
        'frs': 'FitnessRooms',
        'ft': 'FastTimes',
        'ftx': 'FakeTaxi',
        'gft': 'GrandpasFuckTeens',
        'gbcp': 'GangbangCreampie',
        'gta': 'GirlsTryAnal',
        'gw': 'GirlsWay',
        'h1o1': 'Housewife1on1',
        'ham': 'HotAndMean',
        'hart': 'Hegre',
        'hcm': 'HotCrazyMess',
        'hegre-art': 'Hegre',
        'hoh': 'HandsOnHardcore',
        'hotab': 'HouseofTaboo',
        'ht': 'Hogtied',
        'ihaw': 'IHaveAWife',
        'iktg': 'IKnowThatGirl',
        'il': 'ImmoralLive',
        'kha': 'KarupsHA',
        'kow': 'KarupsOW',
        'kpc': 'KarupsPC',
        'la': 'LatinAdultery',
        'lcd': 'LittleCaprice-Dreams',
        'littlecaprice': 'LittleCaprice-Dreams',
        'lhf': 'LoveHerFeet',
        'lsb': 'Lesbea',
        'lst': 'LatinaSexTapes',
        'lta': 'LetsTryAnal',
        'maj': 'ManoJob',
        'mbb': 'MommyBlowsBest',
        'mbt': 'MomsBangTeens',
        'mc': 'MassageCreep',
        'mcu': 'MonsterCurves',
        'mdhf': 'MyDaughtersHotFriend',
        'mdhg': 'MyDadsHotGirlfriend',
        'mfa': 'ManuelFerrara',
        'mfhg': 'MyFriendsHotGirl',
        'mfhm': 'MyFriendsHotMom',
        'mfl': 'Mofos',
        'mfp': 'MyFamilyPies',
        'mfst': 'MyFirstSexTeacher',
        'mgbf': 'MyGirlfriendsBustyFriend',
        'mgb': 'MommyGotBoobs',
        'mic': 'MomsInControl',
        'mj': 'ManoJob',
        'mlib': 'MildsLikeItBig',
        'mlt': 'MomsLickTeens',
        'mmgs': 'MommysGirl',
        'mnm': 'MyNaughtyMassage',
        'mom': 'MomXXX',
        'mpov': 'MrPOV',
        'mrs': 'MassageRooms',
        'mshf': 'MySistersHotFriend',
        'mts': 'MomsTeachSex',
        'mvft': 'MyVeryFirstTime',
        'mwhf': 'MyWifesHotFriend',
        'naf': 'NeighborAffair',
        'nam': 'NaughtyAmerica',
        'na': 'NaughtyAthletics',
        'naughtyamericavr': 'NaughtyAmerica',
        'nb': 'NaughtyBookworms',
        'news': 'NewSensations',
        'nf': 'NubileFilms',
        'no': 'NaughtyOffice',
        'nrg': 'NaughtyRichGirls',
        'nubilef': 'NubileFilms',
        'num': 'NuruMassage',
        'nw': 'NaughtyWeddings',
        'obj': 'OnlyBlowjob',
        'otb': 'OnlyTeenBlowjobs',
        'pav': 'PixAndVideo',
        'pba': 'PublicAgent',
        'pf': 'PornFidelity',
        'phd': 'PassionHD',
        'plib': 'PornstarsLikeitBig',
        'pop': 'PervsOnPatrol',
        'ppu': 'PublicPickups',
        'prdi': 'PrettyDirty',
        'ps': 'PropertySex',
        'pud': 'PublicDisgrace',
        'reg': 'RealExGirlfriends',
        'rkp': 'RKPrime',
        'rws': 'RealWifeStories',
        'saf': 'ShesAFreak',
        'sart': 'SexArt',
        'sbj': 'StreetBlowjobs',
        'sislove': 'SisLovesMe',
        'smb': 'ShareMyBF',
        'ssc': 'StepSiblingsCaught',
        'ssn': 'ShesNew',
        'sts': 'StrandedTeens',
        'swsn': 'SwallowSalon',
        'tdp': 'TeensDoPorn',
        'tds': 'TheDickSuckers',
        'ted': 'Throated',
        'tf': 'TeenFidelity',
        'tgs': 'ThisGirlSucks',
        'these': 'TheStripperExperience',
        'tla': 'TeensLoveAnal',
        'tlc': 'TeensLoveCream',
        'tle': 'TheLifeErotic',
        'tlhc': 'TeensLoveHugeCocks',
        'tlib': 'TeensLikeItBig',
        'tlm': 'TeensLoveMoney',
        'togc': 'TonightsGirlfriendClassic',
        'tog': 'TonightsGirlfriend',
        'tspa': 'TrickySpa',
        'tss': 'ThatSitcomShow',
        'tuf': 'TheUpperFloor',
        'wa': 'WhippedAss',
        'wfbg': 'WeFuckBlackGirls',
        'wkp': 'Wicked',
        'wlt': 'WeLiveTogether',
        'woc': 'WildOnCam',
        'wov': 'WivesOnVacation',
        'wowg': 'WowGirls',
        'wy': 'WebYoung',
        'zzs': 'ZZseries',
        'ztod': 'ZeroTolerance',
        'itc': 'InTheCrack',
        'abbw': 'AbbyWinters',
        'abme': 'AbuseMe',
        'ana': 'AnalAngels',
        'atke': 'ATKExotics',
        'atkg': 'ATKGalleria',
        'atkgfs': 'ATKGirlfriends',
        'atkh': 'ATKHairy',
        'aktp': 'ATKPetites',
        'btp': 'BadTeensPunished',
        'brealmilfs': 'Bang.RealMilfs',
        'byngr': 'bang.YNGR',
        'ba': 'Beauty-Angels',
        'bgfs': 'BlackGFS',
        'bna': 'BrandNew',
        'bam': 'BruceAndMorgan',
        'bcast': 'BrutalCastings',
        'bd': 'BrutalDildos',
        'bpu': 'BrutalPickups',
        'clubseventeen': 'ClubSweethearts',
        'cfnmt': 'CFNMTeens',
        'cfnms': 'FNMSecret',
        'cza': 'CzhecAmateurs',
        'czbb': 'CzechBangBus',
        'czb': 'CzechBitch',
        'cc': 'CzechCasting',
        'czc': 'CzechCouples',
        'czestro': 'CzechEstrogenolit',
        'czf': 'CzechFantasy',
        'czgb': 'CzechGangBang',
        'cgfs': 'CzechGFS',
        'czharem': 'CzechHarem',
        'czm': 'CzechMassage',
        'czo': 'CzechOrgasm',
        'czps': 'CzechPawnShop',
        'css': 'CzechStreets',
        'cztaxi': 'CzechTaxi',
        'czt': 'CzechTwins',
        'dlla': 'DadysLilAngel',
        'dts': 'DeepThroatSirens',
        'deb': 'DeviceBondage',
        'doan': 'DiaryOfANanny',
        'dpf': 'DPFanatics',
        'ds': 'DungeonSex',
        'ffr': 'FacialsForever',
        'ff': 'FilthyFamily',
        'fbbg': 'FirstBGG',
        'fab': 'FuckedAndBound',
        'fum': 'FuckingMachines',
        'fs': 'FuckStudies',
        'tfcp': 'FullyClothedPissing',
        'gfr': 'GFRevenge',
        'gdp': 'GirlsDoPorn',
        'hletee': 'HelplessTeens',
        'hotb': 'HouseOfTaboo',
        'Infr': 'InfernalRestraints',
        'inh': 'InnocentHigh',
        'jlmf': 'JessieLoadsMonsterFacials',
        'university': 'KinkUniversity',
        'lang': 'LANewGirl',
        'mmp': 'MMPNetwork',
        'mot': 'MoneyTalks',
        'mbc': 'MyBabysittersClub',
        'mdm': 'MyDirtyMaid',
        'nvg': 'NetVideoGirls',
        'nubp': 'Nubiles-Porn',
        'oo': 'Only-Opaques',
        'os': 'Only-Secretaries',
        'oss': 'OnlySilAndSatin',
        'psus': 'PascalsSubSluts',
        'pbf': 'PetiteBallerinasFucked',
        'phdp': 'PetiteHDPoorn',
        'psp': 'PorsntarsPunishment',
        'pc': 'PrincessCum',
        'pdmqfo': 'QuestForOrgasm',
        'rtb': 'RealTimeBondage',
        'rab': 'RoundAndBrown',
        'sr': 'SadisticRope',
        'sas': 'SexAndSubmission',
        'sed': 'SexualDisgrace',
        'seb': 'SexuallyBroken',
        'sislov': 'SisLovesMe',
        'tslw': 'SlimeWave',
        'steps': 'StepSiblings',
        'stre': 'StrictRestraint',
        't18': 'Taboo18',
        'tft': 'TeacherFucksTeens',
        'tmf': 'TeachMeFisting',
        'tsma': 'TeenSexMania',
        'tsm': 'TeenSexMovs',
        'ttw': 'TeensInTheWoods',
        'tgw': 'ThaiGirlsWild',
        'taob': 'TheArtOfBlowJob',
        'trwo': 'TheRealWorkout',
        'tto': 'TheTrainingOfO',
        'tg': 'TopGrl',
        'tt': 'TryTeens',
        'th': 'TwistysHard',
        'vp': 'VIPissy',
        'wrh': 'WeAreHairy',
        'wpa': 'WhippedAss',
        'yt': 'YoungThroats',
        'zb': 'ZoliBoy',
    }
    official_websites_dic = {}
    official_websites = {
        'https://s1s1s1.com': 'sivr|ssis|ssni|snis|soe|oned|one|onsd|ofje|sps|tksoe',     # https://s1s1s1.com/search/list?keyword=soe
        'https://moodyz.com': 'mdvr|midv|mide|midd|mibd|mimk|miid|migd|mifd|miae|miad|miaa|mdl|mdj|mdi|mdg|mdf|mde|mdld|mded|mizd|mird|mdjd|rmid|mdid|mdmd|mimu|mdpd|mivd|mdud|mdgd|mdvd|mias|miqd|mint|rmpd|mdrd|tkmide|tkmidd|kmide|tkmigd|mdfd|rmwd',
        'https://www.madonna-av.com': 'juvr|jusd|juq|juy|jux|jul|juk|juc|jukd|jusd|oba|jufd|roeb|roe|ure|mdon|jfb|obe|jums',
        'https://www.wanz-factory.com': 'wavr|waaa|bmw|wanz',
        'https://ideapocket.com': 'ipvr|ipx|ipz|iptd|ipsd|idbd|supd|ipit|and|hpd|tkipz|ipzz|cosd|anpd|dan|alad|kipx',
        'https://kirakira-av.com': 'kivr|blk|kibd|kifd|kird|kisd|set',
        'https://www.av-e-body.com': 'ebvr|ebod|mkck|eyan',
        'https://bi-av.com': 'cjvr|cjod|bbi|bib|cjob|beb|bid|bist|bwb',
        'https://premium-beauty.com': 'prvr|pgd|pred|pbd|pjd|prtd|pxd|pid|ptv',
        'https://miman.jp': 'mmvr|mmnd|mmxd|aom',
        'https://tameikegoro.jp': 'mevr|meyd|mbyd|mdyd|mnyd',
        'https://fitch-av.com': 'fcvr|jufe|jufd|jfb|juny|nyb|finh|gcf|nima',
        'https://kawaiikawaii.jp': 'kavr|cawd|kwbd|kawd|kwsr|kwsd|kane',
        'https://befreebe.com': 'bf',
        'https://muku.tv': 'mucd|mudr|mukd|smcd|mukc',
        'https://attackers.net': 'atvr|rbk|rbd|same|shkd|atid|adn|atkd|jbd|sspd|atad|azsd',
        'https://mko-labo.net': 'mvr|mism|emlb',
        'https://dasdas.jp': 'dsvr|dass|dazd|dasd|pla',
        'https://mvg.jp': 'mvsd|mvbd',
        'https://av-opera.jp': 'opvr|opbd|opud',
        'https://oppai-av.com': 'ppvr|pppe|ppbd|pppd|ppsd|ppfd',
        'https://v-av.com': 'vvvd|vicd|vizd|vspd',
        'https://to-satsu.com': 'clvr|stol|club',
        'https://bibian-av.com': 'bbvr|bban',
        'https://honnaka.jp': 'hnvr|hmn|hndb|hnd|krnd|hnky|hnjc|hnse',
        'https://rookie-av.jp': 'rvr|rbb|rki',
        'https://nanpa-japan.jp': 'njvr|nnpj|npjb',
        'https://hajimekikaku.com': 'hjbb|hjmo|avgl',
        'https://hhh-av.com': 'huntb|hunta|hunt|hunbl|royd|tysf',
        'https://www.prestige-av.com': 'abp|mbm|ezd|docp|onez|yrh|abw|abs|chn|mgt|tre|edd|ult|cmi|mbd|dnw|sga|rdd|dcx|evo|rdt|ppt|gets|sim|kil|tus|dtt|gnab|man|mas|tbl|rtp|ctd|fiv|dic|esk|kbi|tem|ama|kfne|trd|har|yrz|srs|mzq|zzr|gzap|tgav|rix|aka|bgn|lxv|afs|goal|giro|cpde|nmp|mct|abc|inu|shl|mbms|pxh|nrs|ftn|prdvr|fst|blo|shs|kum|gsx|ndx|atd|dld|kbh|bcv|raw|soud|job|chs|yok|bsd|fsb|nnn|hyk|sor|hsp|jbs|xnd|mei|day|mmy|kzd|jan|gyan|tdt|tok|dms|fnd|cdc|jcn|pvrbst|sdvr|docvr|fcp',
    }
    for key, value in official_websites.items():
        temp_list = value.upper().split('|')
        for each in temp_list:
            official_websites_dic[each] = key
    json_config['official_websites'] = official_websites_dic

    # 素人
    json_config['suren_dic'] = {
        'SHN-': '116',                                                          # 116SHN-045
        'GANA': '200',                                                          # 200GANA-2556
        'CUTE-': '229',                                                         # 229SCUTE-953
        'LUXU': '259',                                                          # 200LUXU-2556
        'ARA-': '261',                                                          # 261ARA-094
        'DCV-': '277',                                                          # 277DCV-102
        'EWDX': '299',                                                          # 299EWDX-400
        'MAAN': '300',                                                          # 300MAAN-673
        'MIUM': '300',                                                          # 300MIUM-745
        'NTK-': '300',                                                          # 300NTK-635
        'KIRAY-': '314',                                                        # 314KIRAY-128
        'KJO-': '326',                                                          # 326KJO-002
        'NAMA-': '332',                                                         # 332NAMA-077
        'KNB-': '336',                                                          # 336KNB-172
        'SIMM-': '345',                                                         # 345SIMM-662
        'NTR-': '348',                                                          # 348NTR-001
        'JAC-': '390',                                                          # 390JAC-034
        'KIWVR': '408',                                                         # 408KIWVR-254
        'INST': '413',                                                          # 413INST-202
        'SRYA': '417',                                                          # 417SRYA-015
        'SUKE-': '428',                                                         # 428SUKE-086
        'MFC-': '435',                                                          # 435MFC-142
        'HHH-': '451',                                                          # 451HHH-027
        'TEN-': '459',                                                          # 459TEN-024
        'MLA-': '476',                                                          # 476MLA-043
        'SGK-': '483',                                                          # 483SGK-054
        'GCB-': '485',                                                          # 485GCB-015
        'SEI-': '502',                                                          # 502SEI-001
        'STCV': '529',                                                          # 529STCV-009
        'MY-': '292',                                                           # 292MY-425
        'DANDY': '104',                                                         # 104DANDY-852A
        'ICHK': '368',                                                          # 368ICHK-018
    }

    config_global = json_config
    # add_log('%s update done!' % json_config['config_path'])


# ====================================================================================================================恢复默认配置


def init_config(config_path='', version=''):
    json_config = {
        'version': version,
        'config_path': config_path,
        'media_path': '',
        'softlink_path': 'softlink',
        'success_output_folder': 'JAV_output',
        'failed_output_folder': 'failed',
        'extrafanart_folder': 'extrafanart_copy',
        'media_type': '.mp4|.avi|.rmvb|.wmv|.mov|.mkv|.flv|.ts|.webm|.iso|.mpg',
        'sub_type': '.smi|.srt|.idx|.sub|.sup|.psb|.ssa|.ass|.usf|.xss|.ssf|.rt|.lrc|.sbv|.vtt|.ttml',
        'scrape_softlink_path': '',
        'folders': 'JAV_output,examples',
        'string': 'h_720,2048论坛@fun2048.com,1080p,720p,22-sht.me,-HD,bbs2048.org@,hhd800.com@,icao.me@,hhb_000,[456k.me],[ThZu.Cc]',
        'file_size': '100.0',
        'no_escape': 'record_success_file',
        'clean_ext': '.html|.url',
        'clean_name': 'uur76.mp4|uur9 3.com.mp4',
        'clean_contains': '直 播 盒 子|最 新 情 報|最 新 位 址|注册免费送|房间火爆|美女荷官|妹妹直播|精彩直播',
        'clean_size': 0,
        'clean_ignore_ext': '',
        'clean_ignore_contains': 'skip|ignore',
        'clean_enable': 'clean_ext,clean_name,clean_contains,clean_size,clean_ignore_ext,clean_ignore_contains,',
        'scrape_like': 'info',
        'website_single': 'airav_cc',
        'website_youma': 'airav_cc,iqqtv,javbus,freejavbt,jav321,dmm,javlibrary,7mmtv,hdouban,javdb,avsex,lulubar,airav,xcity,avsox',
        'website_wuma': 'iqqtv,javbus,freejavbt,jav321,avsox,7mmtv,hdouban,javdb,airav',
        'website_suren': 'mgstage,avsex,jav321,freejavbt,7mmtv,javbus,javdb',
        'website_fc2': 'fc2,fc2club,fc2hub,freejavbt,7mmtv,hdouban,javdb,avsox,airav',
        'website_oumei': 'theporndb,javdb,javbus,hdouban',
        'website_guochan': 'madouqu,mdtv,hdouban,cnmdb',
        'whole_fields': 'outline,actor,thumb,tag,release,',
        'none_fields': 'wanted,',
        'website_set': 'official,',
        'title_website': 'theporndb,mgstage,dmm,javbus,jav321,javlibrary',
        'title_zh_website': 'airav_cc,iqqtv,avsex,lulubar',
        'title_website_exclude': '',
        'outline_website': 'theporndb,dmm,jav321',
        'outline_zh_website': 'airav_cc,avsex,iqqtv,lulubar',
        'outline_website_exclude': 'avsox,fc2club,javbus,javdb,javlibrary,freejavbt,hdouban',
        'actor_website': 'theporndb,javbus,javlibrary,javdb',
        'actor_website_exclude': '',
        'thumb_website': 'theporndb,javbus',
        'thumb_website_exclude': 'javdb',
        'poster_website': 'theporndb,avsex,javbus',
        'poster_website_exclude': 'airav,fc2club,fc2hub,iqqtv,7mmtv,javlibrary,lulubar',
        'extrafanart_website': 'javbus,freejavbt',
        'extrafanart_website_exclude': 'airav,airav_cc,avsex,avsox,iqqtv,javlibrary,lulubar',
        'trailer_website': 'freejavbt,mgstage,dmm',
        'trailer_website_exclude': '7mmtv,lulubar',
        'tag_website': 'javbus,freejavbt',
        'tag_website_exclude': '',
        'release_website': 'javbus,freejavbt,7mmtv',
        'release_website_exclude': 'fc2club,fc2hub',
        'runtime_website': 'javbus,freejavbt',
        'runtime_website_exclude': 'airav,airav_cc,fc2,fc2club,fc2hub,lulubar',
        'score_website': 'jav321,javlibrary,javdb',
        'score_website_exclude': 'airav,airav_cc,avsex,avsox,7mmtv,fc2,fc2hub,iqqtv,javbus,xcity,lulubar',
        'director_website': 'javbus,freejavbt',
        'director_website_exclude': 'airav,airav_cc,avsex,avsox,fc2,fc2hub,iqqtv,jav321,mgstage,lulubar',
        'series_website': 'javbus,freejavbt',
        'series_website_exclude': 'airav,airav_cc,avsex,iqqtv,7mmtv,javlibrary,lulubar',
        'studio_website': 'javbus,freejavbt',
        'studio_website_exclude': 'avsex',
        'publisher_website': 'javbus',
        'publisher_website_exclude': 'airav,airav_cc,avsex,iqqtv,lulubar',
        'wanted_website': 'javlibrary,javdb',
        'thread_number': 10,
        'thread_time': 0,
        'javdb_time': 10,
        'main_mode': 1,
        'read_mode': '',
        'update_mode': 'c',
        'update_a_folder': 'actor',
        'update_b_folder': 'number actor',
        'update_d_folder': 'number actor',
        'soft_link': 0,
        'success_file_move': 1,
        'failed_file_move': 1,
        'success_file_rename': 1,
        'del_empty_folder': 1,
        'show_poster': 1,
        'translate_by': 'youdao,google,deepl,',
        'deepl_key': '',
        'title_language': 'zh_cn',
        'title_sehua': 'on',
        'title_yesjav': 'off',
        'title_translate': 'on',
        'title_sehua_zh': 'on',
        'outline_language': 'zh_cn',
        'outline_translate': 'on',
        'outline_show': '',
        'actor_language': 'zh_cn',
        'actor_realname': 'on',
        'actor_translate': 'on',
        'tag_language': 'zh_cn',
        'tag_translate': 'on',
        'tag_include': 'actor,letters,series,studio,publisher,cnword,mosaic,definition',
        'director_language': 'zh_cn',
        'director_translate': 'on',
        'series_language': 'zh_cn',
        'series_translate': 'on',
        'studio_language': 'zh_cn',
        'studio_translate': 'on',
        'publisher_language': 'zh_cn',
        'publisher_translate': 'on',
        'nfo_include_new': 'sorttitle,originaltitle,title_cd,outline,plot_,originalplot,release_,releasedate,premiered,country,mpaa,customrating,year,runtime,wanted,score,criticrating,actor,director,series,tag,genre,series_set,studio,maker,publisher,label,poster,cover,trailer,website,',
        'nfo_tagline': '发行日期 release',
        'nfo_tag_series': '系列: series',
        'nfo_tag_studio': '片商: studio',
        'nfo_tag_publisher': '发行: publisher',
        'download_files': ',poster,thumb,fanart,nfo,ignore_wuma,ignore_fc2,ignore_guochan',
        'keep_files': ',extrafanart,trailer,theme_videos,',
        'download_hd_pics': 'poster,thumb,amazon,official,google,',
        'google_used': 'm.media-amazon.com,',
        'google_exclude': 'fake,javfree,idoljp.com,qqimg.top,u9a9,picturedata,abpic,pbs.twimg.com,naiwarp',
        'folder_name': 'actor/number actor',
        'naming_file': 'number',
        'naming_media': 'number title',
        'prevent_char': '',
        'fields_rule': 'del_actor,del_char',
        'suffix_sort': 'mosaic,cnword',
        'actor_no_name': '未知演员',
        'release_rule': 'YYYY-MM-DD',
        'folder_name_max': 60,
        'file_name_max': 60,
        'actor_name_max': 3,
        'actor_name_more': '等演员',
        'umr_style': '-破解',
        'leak_style': '-流出',
        'wuma_style': '',
        'youma_style': '',
        'show_moword': 'file,',
        'show_4k': 'folder,file,',
        'cd_name': 0,
        'cd_char': 'letter,underline,',
        'pic_name': 0,
        'trailer_name': 1,
        'hd_name': 'height',
        'hd_get': 'video',
        'cnword_char': '-C.,-C-,ch.,字幕',
        'cnword_style': '-C',
        'folder_cnword': 'on',
        'file_cnword': 'on',
        'subtitle_folder': '',
        'subtitle_add': 'off',
        'subtitle_add_chs': 'on',
        'subtitle_add_rescrape': 'on',
        'server_type': 'emby',
        'emby_url': 'http://192.168.5.191:8096',
        'api_key': 'ee9a2f2419704257b1dd60b975f2d64e',
        'emby_on': 'actor_info_zh_cn,actor_info_miss,actor_photo_net,actor_photo_miss,',
        'gfriends_github': 'https://github.com/gfriends/gfriends',
        'actor_photo_folder': '',
        'poster_mark': 1,
        'thumb_mark': 1,
        'fanart_mark': 0,
        'mark_size': 5,
        'mark_type': 'sub,umr,leak,uncensored,hd',
        'mark_fixed': 'off',
        'mark_pos': 'top_left',
        'mark_pos_corner': 'top_left',
        'mark_pos_sub': 'top_left',
        'mark_pos_mosaic': 'top_right',
        'mark_pos_hd': 'bottom_right',
        'type': 'no',
        'proxy': '127.0.0.1:7890',
        'timeout': 10,
        'retry': 3,
        'javbus_website': '',
        'javdb_website': '',
        'iqqtv_website': '',
        'avsex_website': '',
        'hdouban_website': '',
        'mdtv_website': '',
        'airavcc_website': '',
        'lulubar_website': '',
        'javlibrary_website': '',
        'javdb': '',
        'javbus': '',
        'theporndb_api_token': '',
        'show_web_log': 'off',
        'show_from_log': 'on',
        'show_data_log': 'on',
        'save_log': 'on',
        'update_check': 'on',
        'local_library': '',
        'actors_name': '',
        'netdisk_path': '',
        'localdisk_path': '',
        'window_title': 'hide',
        'switch_on': 'rest_scrape,show_dialog_exit,show_dialog_stop_scrape,remain_task,show_logs,ipv4_only,',
        'timed_interval': '00:30:00',
        'rest_count': '20',
        'rest_time': '00:01:02',
        'statement': 3,
    }

    # add_log('%s restore done!' % config_path)
    if config_path:
        save_config(json_config)
    else:                                                                       # 返回默认设置
        return json_config


# ====================================================================================================================保存配置到config.ini


def save_config(json_config):
    config_path = json_config['config_path']
    with open('MDCx.config', 'w', encoding='UTF-8') as f:
        f.write(config_path)
    with open(config_path, "wt", encoding='UTF-8') as code:
        print("[modified_time]", file=code)
        print("modified_time = " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), file=code)
        print("version = " + str(json_config['version']), file=code)
        print("", file=code)

        print("[media]", file=code)
        print("media_path = " + str(json_config['media_path']), file=code)
        print("softlink_path = " + str(json_config['softlink_path']), file=code)
        print("success_output_folder = " + str(json_config['success_output_folder']), file=code)
        print("failed_output_folder = " + str(json_config['failed_output_folder']), file=code)
        print("extrafanart_folder = " + str(json_config['extrafanart_folder']), file=code)
        print("media_type = " + str(json_config['media_type']), file=code)
        print("sub_type = " + str(json_config['sub_type']), file=code)
        print("scrape_softlink_path = " + str(json_config['scrape_softlink_path']), file=code)
        print("", file=code)

        print("[escape]", file=code)
        print("folders = " + str(json_config['folders']), file=code)
        print("string = " + str(json_config['string']), file=code)
        print("file_size = " + str(json_config['file_size']), file=code)
        print("no_escape = " + str(json_config['no_escape']), file=code)
        print("", file=code)

        print("[clean]", file=code)
        print("clean_ext = " + str(json_config['clean_ext']), file=code)
        print("clean_name = " + str(json_config['clean_name']), file=code)
        print("clean_contains = " + str(json_config['clean_contains']), file=code)
        print("clean_size = " + str(json_config['clean_size']), file=code)
        print("clean_ignore_ext = " + str(json_config['clean_ignore_ext']), file=code)
        print("clean_ignore_contains = " + str(json_config['clean_ignore_contains']), file=code)
        print("clean_enable = " + str(json_config['clean_enable']), file=code)
        print("", file=code)

        print("[common]", file=code)
        print("thread_number = " + str(json_config['thread_number']), file=code)
        print("thread_time = " + str(json_config['thread_time']), file=code)
        print("javdb_time = " + str(json_config['javdb_time']), file=code)
        print("main_mode = " + str(json_config['main_mode']), file=code)
        print("read_mode = " + str(json_config['read_mode']), file=code)
        print("update_mode = " + str(json_config['update_mode']), file=code)
        print("update_a_folder = " + str(json_config['update_a_folder']), file=code)
        print("update_b_folder = " + str(json_config['update_b_folder']), file=code)
        print("update_d_folder = " + str(json_config['update_d_folder']), file=code)
        print("soft_link = " + str(json_config['soft_link']), file=code)
        print("success_file_move = " + str(json_config['success_file_move']), file=code)
        print("failed_file_move = " + str(json_config['failed_file_move']), file=code)
        print("success_file_rename = " + str(json_config['success_file_rename']), file=code)
        print("del_empty_folder = " + str(json_config['del_empty_folder']), file=code)
        print("show_poster = " + str(json_config['show_poster']), file=code)
        print("", file=code)

        print("[file_download]", file=code)
        print("download_files = " + str(json_config['download_files']), file=code)
        print("keep_files = " + str(json_config['keep_files']), file=code)
        print("download_hd_pics = " + str(json_config['download_hd_pics']), file=code)
        print("google_used = " + str(json_config['google_used']), file=code)
        print("google_exclude = " + str(json_config['google_exclude']), file=code)
        print("", file=code)

        print("[website]", file=code)
        print("scrape_like = " + str(json_config['scrape_like']), file=code)
        print("website_single = " + str(json_config['website_single']), file=code)
        print("website_youma = " + str(json_config['website_youma']), file=code)
        print("website_wuma = " + str(json_config['website_wuma']), file=code)
        print("website_suren = " + str(json_config['website_suren']), file=code)
        print("website_fc2 = " + str(json_config['website_fc2']), file=code)
        print("website_oumei = " + str(json_config['website_oumei']), file=code)
        print("website_guochan = " + str(json_config['website_guochan']), file=code)
        print("whole_fields = " + str(json_config['whole_fields']), file=code)
        print("none_fields = " + str(json_config['none_fields']), file=code)
        print("website_set = " + str(json_config['website_set']), file=code)
        print("title_website = " + str(json_config['title_website']), file=code)
        print("title_zh_website = " + str(json_config['title_zh_website']), file=code)
        print("title_website_exclude = " + str(json_config['title_website_exclude']), file=code)
        print("outline_website = " + str(json_config['outline_website']), file=code)
        print("outline_zh_website = " + str(json_config['outline_zh_website']), file=code)
        print("outline_website_exclude = " + str(json_config['outline_website_exclude']), file=code)
        print("actor_website = " + str(json_config['actor_website']), file=code)
        print("actor_website_exclude = " + str(json_config['actor_website_exclude']), file=code)
        print("thumb_website = " + str(json_config['thumb_website']), file=code)
        print("thumb_website_exclude = " + str(json_config['thumb_website_exclude']), file=code)
        print("poster_website = " + str(json_config['poster_website']), file=code)
        print("poster_website_exclude = " + str(json_config['poster_website_exclude']), file=code)
        print("extrafanart_website = " + str(json_config['extrafanart_website']), file=code)
        print("extrafanart_website_exclude = " + str(json_config['extrafanart_website_exclude']), file=code)
        print("trailer_website = " + str(json_config['trailer_website']), file=code)
        print("trailer_website_exclude = " + str(json_config['trailer_website_exclude']), file=code)
        print("tag_website = " + str(json_config['tag_website']), file=code)
        print("tag_website_exclude = " + str(json_config['tag_website_exclude']), file=code)
        print("release_website = " + str(json_config['release_website']), file=code)
        print("release_website_exclude = " + str(json_config['release_website_exclude']), file=code)
        print("runtime_website = " + str(json_config['runtime_website']), file=code)
        print("runtime_website_exclude = " + str(json_config['runtime_website_exclude']), file=code)
        print("score_website = " + str(json_config['score_website']), file=code)
        print("score_website_exclude = " + str(json_config['score_website_exclude']), file=code)
        print("director_website = " + str(json_config['director_website']), file=code)
        print("director_website_exclude = " + str(json_config['director_website_exclude']), file=code)
        print("series_website = " + str(json_config['series_website']), file=code)
        print("series_website_exclude = " + str(json_config['series_website_exclude']), file=code)
        print("studio_website = " + str(json_config['studio_website']), file=code)
        print("studio_website_exclude = " + str(json_config['studio_website_exclude']), file=code)
        print("publisher_website = " + str(json_config['publisher_website']), file=code)
        print("publisher_website_exclude = " + str(json_config['publisher_website_exclude']), file=code)
        print("wanted_website = " + str(json_config['wanted_website']), file=code)
        print("translate_by = " + str(json_config['translate_by']), file=code)
        print("deepl_key = " + str(json_config['deepl_key']), file=code)
        print("title_language = " + str(json_config['title_language']), file=code)
        print("title_sehua = " + str(json_config['title_sehua']), file=code)
        print("title_yesjav = " + str(json_config['title_yesjav']), file=code)
        print("title_translate = " + str(json_config['title_translate']), file=code)
        print("title_sehua_zh = " + str(json_config['title_sehua_zh']), file=code)
        print("outline_language = " + str(json_config['outline_language']), file=code)
        print("outline_translate = " + str(json_config['outline_translate']), file=code)
        print("outline_show = " + str(json_config['outline_show']), file=code)
        print("actor_language = " + str(json_config['actor_language']), file=code)
        print("actor_realname = " + str(json_config['actor_realname']), file=code)
        print("actor_translate = " + str(json_config['actor_translate']), file=code)
        print("tag_language = " + str(json_config['tag_language']), file=code)
        print("tag_translate = " + str(json_config['tag_translate']), file=code)
        print("tag_include = " + str(json_config['tag_include']), file=code)
        print("director_language = " + str(json_config['director_language']), file=code)
        print("director_translate = " + str(json_config['director_translate']), file=code)
        print("series_language = " + str(json_config['series_language']), file=code)
        print("series_translate = " + str(json_config['series_translate']), file=code)
        print("studio_language = " + str(json_config['studio_language']), file=code)
        print("studio_translate = " + str(json_config['studio_translate']), file=code)
        print("publisher_language = " + str(json_config['publisher_language']), file=code)
        print("publisher_translate = " + str(json_config['publisher_translate']), file=code)
        print("nfo_include_new = " + str(json_config['nfo_include_new']), file=code)
        print("nfo_tagline = " + str(json_config['nfo_tagline']), file=code)
        print("nfo_tag_series = " + str(json_config['nfo_tag_series']), file=code)
        print("nfo_tag_studio = " + str(json_config['nfo_tag_studio']), file=code)
        print("nfo_tag_publisher = " + str(json_config['nfo_tag_publisher']), file=code)
        print("# website: iqqtv, javbus, javdb, freejavbt, jav321, dmm, avsox, xcity, mgstage, fc2, fc2club, fc2hub, airav, javlibrary, mdtv", file=code)
        print("", file=code)

        print("[Name_Rule]", file=code)
        print("folder_name = " + str(json_config['folder_name']), file=code)
        print("naming_file = " + str(json_config['naming_file']), file=code)
        print("naming_media = " + str(json_config['naming_media']), file=code)
        print("prevent_char = " + str(json_config['prevent_char']), file=code)
        print("fields_rule = " + str(json_config['fields_rule']), file=code)
        print("suffix_sort = " + str(json_config['suffix_sort']), file=code)
        print("actor_no_name = " + str(json_config['actor_no_name']), file=code)
        print("release_rule = " + str(json_config['release_rule']), file=code)
        print("folder_name_max = " + str(json_config['folder_name_max']), file=code)
        print("file_name_max = " + str(json_config['file_name_max']), file=code)
        print("actor_name_max = " + str(json_config['actor_name_max']), file=code)
        print("actor_name_more = " + str(json_config['actor_name_more']), file=code)
        print("umr_style = " + str(json_config['umr_style']), file=code)
        print("leak_style = " + str(json_config['leak_style']), file=code)
        print("wuma_style = " + str(json_config['wuma_style']), file=code)
        print("youma_style = " + str(json_config['youma_style']), file=code)
        print("show_moword = " + str(json_config['show_moword']), file=code)
        print("show_4k = " + str(json_config['show_4k']), file=code)
        print("cd_name = " + str(json_config['cd_name']), file=code)
        print("cd_char = " + str(json_config['cd_char']), file=code)
        print("pic_name = " + str(json_config['pic_name']), file=code)
        print("trailer_name = " + str(json_config['trailer_name']), file=code)
        print("hd_name = " + str(json_config['hd_name']), file=code)
        print("hd_get = " + str(json_config['hd_get']), file=code)
        print("# 命名字段有：title, originaltitle, actor, number, studio, publisher, year, mosaic, runtime, director, release, series, definition, cnword", file=code)
        print("", file=code)

        print("[subtitle]", file=code)
        print("cnword_char = " + str(json_config['cnword_char']), file=code)
        print("cnword_style = " + str(json_config['cnword_style']), file=code)
        print("folder_cnword = " + str(json_config['folder_cnword']), file=code)
        print("file_cnword = " + str(json_config['file_cnword']), file=code)
        print("subtitle_folder = " + str(json_config['subtitle_folder']), file=code)
        print("subtitle_add = " + str(json_config['subtitle_add']), file=code)
        print("subtitle_add_chs = " + str(json_config['subtitle_add_chs']), file=code)
        print("subtitle_add_rescrape = " + str(json_config['subtitle_add_rescrape']), file=code)
        print("", file=code)

        print("[emby]", file=code)
        print("server_type = " + str(json_config['server_type']), file=code)
        print("emby_url = " + str(json_config['emby_url']), file=code)
        print("api_key = " + str(json_config['api_key']), file=code)
        print("emby_on = " + str(json_config['emby_on']), file=code)
        print("gfriends_github = " + str(json_config['gfriends_github']), file=code)
        print("actor_photo_folder = " + str(json_config['actor_photo_folder']), file=code)
        print("", file=code)

        print("[mark]", file=code)
        print("poster_mark = " + str(json_config['poster_mark']), file=code)
        print("thumb_mark = " + str(json_config['thumb_mark']), file=code)
        print("fanart_mark = " + str(json_config['fanart_mark']), file=code)
        print("mark_size = " + str(json_config['mark_size']), file=code)
        print("mark_type = " + str(json_config['mark_type']), file=code)
        print("mark_fixed = " + str(json_config['mark_fixed']), file=code)
        print("mark_pos = " + str(json_config['mark_pos']), file=code)
        print("mark_pos_corner = " + str(json_config['mark_pos_corner']), file=code)
        print("mark_pos_sub = " + str(json_config['mark_pos_sub']), file=code)
        print("mark_pos_mosaic = " + str(json_config['mark_pos_mosaic']), file=code)
        print("mark_pos_hd = " + str(json_config['mark_pos_hd']), file=code)
        print("# mark_size: range 1-40", file=code)
        print("# mark_type: sub, youma, umr, leak, uncensored, hd", file=code)
        print("# mark_pos: top_left, top_right, bottom_left, bottom_right", file=code)
        print("", file=code)

        print("[proxy]", file=code)
        print("type = " + json_config['type'], file=code)
        print("proxy = " + str(json_config['proxy']), file=code)
        print("timeout = " + str(json_config['timeout']), file=code)
        print("retry = " + str(json_config['retry']), file=code)
        print("javbus_website = " + str(json_config['javbus_website']), file=code)
        print("javdb_website = " + str(json_config['javdb_website']), file=code)
        print("iqqtv_website = " + str(json_config['iqqtv_website']), file=code)
        print("avsex_website = " + str(json_config['avsex_website']), file=code)
        print("hdouban_website = " + str(json_config['hdouban_website']), file=code)
        print("mdtv_website = " + str(json_config['mdtv_website']), file=code)
        print("airavcc_website = " + str(json_config['airavcc_website']), file=code)
        print("lulubar_website = " + str(json_config['lulubar_website']), file=code)
        print("javlibrary_website = " + str(json_config['javlibrary_website']), file=code)
        print("theporndb_api_token = " + str(json_config['theporndb_api_token']), file=code)
        print("# type: no, http, socks5", file=code)
        print("", file=code)

        print("[Cookies]", file=code)
        print("javdb = " + str(json_config['javdb']), file=code)
        print("javbus = " + str(json_config['javbus']), file=code)
        print("# cookies存在有效期，记得更新", file=code)
        print("", file=code)

        print("[other]", file=code)
        print("show_web_log = " + str(json_config['show_web_log']), file=code)
        print("show_from_log = " + str(json_config['show_from_log']), file=code)
        print("show_data_log = " + str(json_config['show_data_log']), file=code)
        print("save_log = " + str(json_config['save_log']), file=code)
        print("update_check = " + str(json_config['update_check']), file=code)
        print("local_library = " + str(json_config['local_library']), file=code)
        print("actors_name = " + str(json_config['actors_name']), file=code)
        print("netdisk_path = " + str(json_config['netdisk_path']), file=code)
        print("localdisk_path = " + str(json_config['localdisk_path']), file=code)
        print("window_title = " + str(json_config['window_title']), file=code)
        print("switch_on = " + str(json_config['switch_on']), file=code)
        print("timed_interval = " + str(json_config['timed_interval']), file=code)
        print("rest_count = " + str(json_config['rest_count']), file=code)
        print("rest_time = " + str(json_config['rest_time']), file=code)
        print("statement = " + str(json_config['statement']), file=code)

    code.close()
    # add_log('%s save done!' % config_path)
    # 更新config_global
    update_config(json_config)
