#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import os
import json
import traceback
import shutil
import langid
# import imghdr
from lxml import etree
from PIL import Image
from Getter import iqqtv_new, freejavbt, javbus, javdb, jav321, dmm, javlibrary_new, avsox, xcity, mgstage, fc2, fc2club, fc2hub, airav_new, avsex, airav_cc_new, mdtv, madouqu, mmtv, getchu, getchu_dmm, mywife, giga, hdouban, lulubar, love6, faleno, cnmdb, fantastica, theporndb, dahlia, kin8, official, prestige
import Function.config as cf
from Function.getHtml import get_html
from Function.getInfo import is_uncensored, get_number_letters

# ========================================================================判断是否清理文件


def need_clean(file_path, file_name, file_ext):
    config = cf.get_config()
    can_clean = config.get('can_clean')

    if not can_clean:
        return False

    clean_ext_list = config.get('clean_ext_list')
    clean_name_list = config.get('clean_name_list')
    clean_contains_list = config.get('clean_contains_list')
    clean_size_list = config.get('clean_size_list')
    clean_ignore_ext_list = config.get('clean_ignore_ext_list')
    clean_ignore_contains_list = config.get('clean_ignore_contains_list')

    # 不清理的扩展名
    if file_ext in clean_ignore_ext_list:
        return False

    # 不清理的文件名包含
    for each in clean_ignore_contains_list:
        if each in file_name:
            return False

    # 清理的扩展名
    if file_ext in clean_ext_list:
        return True

    # 清理的文件名等于
    if file_name in clean_name_list:
        return True

    # 清理的文件名包含
    for each in clean_contains_list:
        if each in file_name:
            return True

    # 清理的文件大小<=(KB)
    if os.path.islink(file_path):
        file_path = os.readlink(file_path)
    if clean_size_list != '':
        try:    # 路径太长时，此处会报错 FileNotFoundError: [WinError 3] 系统找不到指定的路径。
            if os.path.getsize(file_path) <= clean_size_list * 1024:
                return True
        except:
            pass
    return False


# ========================================================================删除文件


def delete_file(file_path):
    try:
        for _ in range(5):
            if os.path.islink(file_path):
                pass
            elif not os.path.exists(file_path):
                break
            os.remove(file_path)
        return True, ''
    except Exception as e:
        error_info = f' Delete File: {file_path}\n Error: {e}\n{traceback.format_exc()}'
        cf.add_log(error_info)
        print(error_info)
        return False, error_info


# ========================================================================移动文件


def move_file(old_path, new_path):
    try:
        if old_path.lower().replace('\\', '/') != new_path.lower().replace('\\', '/'):
            delete_file(new_path)
            shutil.move(old_path, new_path)
        return True, ''
    except Exception as e:
        error_info = f' Move File: {old_path}\n To: {new_path} \n Error: {e}\n{traceback.format_exc()}\n'
        cf.add_log(error_info)
        print(error_info)
        return False, error_info


# ========================================================================复制文件


def copy_file(old_path, new_path):
    for _ in range(3):
        try:
            if not os.path.exists(old_path):
                return False, f'不存在: {old_path}'
            elif old_path.lower() != new_path.lower():
                delete_file(new_path)
            shutil.copy(old_path, new_path)
            return True, ''
        except Exception as e:
            error_info = f' Copy File: {old_path}\n To: {new_path} \n Error: {e}\n{traceback.format_exc()}'
            cf.add_log(error_info)
            print(error_info)
    return False, error_info


# ========================================================================获取真实路径


def read_link(path):
    while os.path.islink(path):
        path = os.readlink(path)
    return path


# ========================================================================分离路径


def split_path(path):
    if '\\' in path:
        p, f = os.path.split(path.replace('\\', '/'))
        return p.replace('/', '\\'), f
    return os.path.split(path)


# ========================================================================打开图片


def open_image(pic_path):
    try:
        with Image.open(pic_path) as img:
            return True, img
    except Exception as e:
        error_info = f' Open: {pic_path}\n Error: {e}\n{traceback.format_exc()}'
        cf.add_log(error_info)
        print(error_info)
        return False, error_info


# ========================================================================根据番号获取数据


def get_new_website_list(field_website_list, number_website_list, file_number, short_number, field, all=False):
    config = cf.get_config()
    whole_fields = config.get('whole_fields')                                   # 继续补全的字段
    field_website_list = [i for i in field_website_list if i]                   # 去空
    number_website_list = [i for i in number_website_list if i]                 # 去空
    same_list = [i for i in field_website_list if i in number_website_list]     # 取交集
    if field in whole_fields or field == 'title' or all:                        # 取剩余未相交网站， trailer 不取未相交网站，title 默认取未相交网站
        if field != 'trailer':
            diff_list = [i for i in number_website_list if i not in field_website_list]
            same_list.extend(diff_list)
    dic_escape = {
        'title': config.get('title_website_exclude').split(','),
        'outline': config.get('outline_website_exclude').split(','),
        'actor': config.get('actor_website_exclude').split(','),
        'thumb': config.get('thumb_website_exclude').split(','),
        'poster': config.get('poster_website_exclude').split(','),
        'extrafanart': config.get('extrafanart_website_exclude').split(','),
        'trailer': config.get('trailer_website_exclude').split(','),
        'tag': config.get('tag_website_exclude').split(','),
        'release': config.get('release_website_exclude').split(','),
        'runtime': config.get('runtime_website_exclude').split(','),
        'score': config.get('score_website_exclude').split(','),
        'director': config.get('director_website_exclude').split(','),
        'series': config.get('series_website_exclude').split(','),
        'studio': config.get('studio_website_exclude').split(','),
        'publisher': config.get('publisher_website_exclude').split(','),
    }                                                                           # 根据字段排除的网站

    escape_list = dic_escape.get(field)
    if escape_list:
        same_list = [i for i in same_list if i not in escape_list]                  # 根据字段排除一些不含这些字段的网站

    # mgstage 素人番号检查
    if short_number:
        not_frist_field_list = ['title', 'actor']                               # 这些字段以外，素人把 mgstage 放在第一位
        if field not in not_frist_field_list and 'mgstage' in same_list:
            same_list.remove('mgstage')
            same_list.insert(0, 'mgstage')

    # faleno.jp 番号检查 dldss177 dhla009
    elif re.findall(r'F[A-Z]{2}SS', file_number):
        same_list = deal_some_list(field, 'faleno', same_list)

    # dahlia-av.jp 番号检查
    elif file_number.startswith('DLDSS') or file_number.startswith('DHLA'):
        same_list = deal_some_list(field, 'dahlia', same_list)

    # fantastica 番号检查 FAVI、FAAP、FAPL、FAKG、FAHO、FAVA、FAKY、FAMI、FAIT、FAKA、FAMO、FASO、FAIH、FASH、FAKS、FAAN
    elif re.search(r'FA[A-Z]{2}-?\d+', file_number.upper()) or file_number.upper().startswith('CLASS') or file_number.upper().startswith('FADRV') or file_number.upper().startswith('FAPRO') or file_number.upper().startswith('FAKWM') or file_number.upper().startswith('PDS'):
        same_list = deal_some_list(field, 'fantastica', same_list)

    return same_list


def deal_some_list(field, website, same_list):
    if website not in same_list:
        same_list.append(website)
    if field in ['title', 'outline', 'thumb', 'poster', 'trailer', 'extrafanart']:
        same_list.remove(website)
        same_list.insert(0, website)
    elif field in ['tag', 'score', 'director', 'series']:
        same_list.remove(website)
    return same_list


def get_web_data(json_data, website, language, file_number, short_number, mosaic, org_language):
    '''
    获取某个网站数据
    '''
    appoint_number = json_data['appoint_number']
    appoint_url = json_data['appoint_url']
    log_info = json_data['log_info']
    req_web = json_data['req_web']
    file_path = json_data['file_path']

    # 259LUXU-1111， mgstage 和 avsex 之外使用 LUXU-1111（素人番号时，short_number有值，不带前缀数字；反之，short_number为空)
    if short_number and website != 'mgstage' and website != 'avsex':
        file_number = short_number

    if website == 'official':
        json_data = json.loads(official.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'iqqtv':
        json_data = json.loads(iqqtv_new.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'avsex':
        json_data = json.loads(avsex.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'airav_cc':
        json_data = json.loads(airav_cc_new.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'airav':
        json_data = json.loads(airav_new.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'freejavbt':
        json_data = json.loads(freejavbt.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'javbus':
        json_data = json.loads(javbus.main(file_number, appoint_url, log_info, req_web, language, mosaic))
    elif website == 'javdb':
        json_data = json.loads(javdb.main(file_number, appoint_url, log_info, req_web, language, org_language))
    elif website == 'jav321':
        json_data = json.loads(jav321.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'dmm':
        json_data = json.loads(dmm.main(file_number, appoint_url, log_info, req_web, language, file_path))
    elif website == 'javlibrary':
        json_data = json.loads(javlibrary_new.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'xcity':
        json_data = json.loads(xcity.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'avsox':
        json_data = json.loads(avsox.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'mgstage':
        json_data = json.loads(mgstage.main(file_number, appoint_url, log_info, req_web, language, short_number))
    elif website == '7mmtv':
        json_data = json.loads(mmtv.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'fc2':
        json_data = json.loads(fc2.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'fc2hub':
        json_data = json.loads(fc2hub.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'fc2club':
        json_data = json.loads(fc2club.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'mdtv':
        json_data = json.loads(mdtv.main(file_number, appoint_url, log_info, req_web, language, file_path, appoint_number))
    elif website == 'madouqu':
        json_data = json.loads(madouqu.main(file_number, appoint_url, log_info, req_web, language, file_path, appoint_number))
    elif website == 'getchu':
        json_data = json.loads(getchu.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'getchu_dmm':
        json_data = json.loads(getchu_dmm.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'mywife':
        json_data = json.loads(mywife.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'giga':
        json_data = json.loads(giga.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'hdouban':
        json_data = json.loads(hdouban.main(file_number, appoint_url, log_info, req_web, language, file_path, appoint_number, mosaic))
    elif website == 'lulubar':
        json_data = json.loads(lulubar.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'love6':
        json_data = json.loads(love6.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'cnmdb':
        json_data = json.loads(cnmdb.main(file_number, appoint_url, log_info, req_web, language, file_path, appoint_number))
    elif website == 'faleno':
        json_data = json.loads(faleno.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'fantastica':
        json_data = json.loads(fantastica.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'theporndb':
        json_data = json.loads(theporndb.main(file_number, appoint_url, log_info, req_web, language, file_path))
    elif website == 'dahlia':
        json_data = json.loads(dahlia.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'prestige':
        json_data = json.loads(prestige.main(file_number, appoint_url, log_info, req_web, language))
    elif website == 'kin8':
        json_data = json.loads(kin8.main(file_number, appoint_url, log_info, req_web, language))
    else:
        json_data = json.loads(javdb.main(file_number, appoint_url, log_info, req_web, language))

    return json_data


def get_websites_data(json_data, number_website_list):
    '''
    获取一组网站的数据：按照设置的网站组，请求各字段数据，并返回最终的数据
    '''
    file_number = json_data['number']
    short_number = json_data['short_number']
    config = cf.get_config()
    scrape_like = config.get('scrape_like')
    none_fields = config.get('none_fields')                                     # 不刮削的字段

    # 获取使用的网站
    title_jp_website_list = config.get('title_website').split(',')
    title_zh_website_list = config.get('title_zh_website').split(',')
    outline_jp_website_list = config.get('outline_website').split(',')
    outline_zh_website_list = config.get('outline_zh_website').split(',')
    actor_website_list = config.get('actor_website').split(',')
    thumb_website_list = config.get('thumb_website').split(',')
    poster_website_list = config.get('poster_website').split(',')
    extrafanart_website_list = config.get('extrafanart_website').split(',')
    trailer_website_list = config.get('trailer_website').split(',')
    tag_website_list = config.get('tag_website').split(',')
    release_website_list = config.get('release_website').split(',')
    runtime_website_list = config.get('runtime_website').split(',')
    score_website_list = config.get('score_website').split(',')
    director_website_list = config.get('director_website').split(',')
    series_website_list = config.get('series_website').split(',')
    studio_website_list = config.get('studio_website').split(',')
    publisher_website_list = config.get('publisher_website').split(',')
    wanted_website_list = config.get('wanted_website').split(',')
    title_jp_website_new_list = get_new_website_list(title_jp_website_list, number_website_list, file_number, short_number, 'title')
    title_zh_website_new_list = get_new_website_list(title_zh_website_list, number_website_list, file_number, short_number, 'title_zh')
    outline_jp_website_new_list = get_new_website_list(outline_jp_website_list, number_website_list, file_number, short_number, 'outline')
    outline_zh_website_new_list = get_new_website_list(outline_zh_website_list, number_website_list, file_number, short_number, 'outline_zh')
    actor_website_new_list = get_new_website_list(actor_website_list, number_website_list, file_number, short_number, 'actor')
    thumb_website_new_list = get_new_website_list(thumb_website_list, number_website_list, file_number, short_number, 'thumb')
    poster_website_new_list = get_new_website_list(poster_website_list, number_website_list, file_number, short_number, 'poster')
    extrafanart_website_new_list = get_new_website_list(extrafanart_website_list, number_website_list, file_number, short_number, 'extrafanart')
    trailer_website_new_list = get_new_website_list(trailer_website_list, number_website_list, file_number, short_number, 'trailer')
    tag_website_new_list = get_new_website_list(tag_website_list, number_website_list, file_number, short_number, 'tag')
    release_website_new_list = get_new_website_list(release_website_list, number_website_list, file_number, short_number, 'release')
    runtime_website_new_list = get_new_website_list(runtime_website_list, number_website_list, file_number, short_number, 'runtime')
    score_website_new_list = get_new_website_list(score_website_list, number_website_list, file_number, short_number, 'score')
    director_website_new_list = get_new_website_list(director_website_list, number_website_list, file_number, short_number, 'director')
    series_website_new_list = get_new_website_list(series_website_list, number_website_list, file_number, short_number, 'series')
    studio_website_new_list = get_new_website_list(studio_website_list, number_website_list, file_number, short_number, 'studio')
    publisher_website_new_list = get_new_website_list(publisher_website_list, number_website_list, file_number, short_number, 'publisher')
    wanted_website_new_list = get_new_website_list(wanted_website_list, number_website_list, file_number, short_number, 'wanted')

    # 初始化变量
    all_json_data = {}

    # 生成各字段及请求网站列表，并请求数据
    if scrape_like == 'speed':
        request_field_list = [['title', '标题', 'title_language', number_website_list]]
    else:
        if 'official' in config.get('website_set'):
            title_jp_website_new_list.insert(0, 'official')
        request_field_list = [
            ['title', '标题', 'title_language', title_jp_website_new_list],
            ['title_zh', '中文标题', 'title_language', title_zh_website_new_list],
            ['outline', '简介', 'outline_language', outline_jp_website_new_list],
            ['outline_zh', '中文简介', 'outline_language', outline_zh_website_new_list],
            ['actor', '演员', 'actor_language', actor_website_new_list],
            ['cover', '背景图', 'title_language', thumb_website_new_list],
            ['poster', '封面图', 'title_language', poster_website_new_list],
            ['extrafanart', '剧照', 'title_language', extrafanart_website_new_list],
            ['tag', '标签', 'tag_language', tag_website_new_list],
            ['release', '发行日期', 'title_language', release_website_new_list],
            ['runtime', '时长', 'title_language', runtime_website_new_list],
            ['score', '评分', 'title_language', score_website_new_list],
            ['director', '导演', 'director_language', director_website_new_list],
            ['series', '系列', 'series_language', series_website_new_list],
            ['studio', '片商', 'studio_language', studio_website_new_list],
            ['publisher', '发行商', 'publisher_language', publisher_website_new_list],
            ['trailer', '预告片', 'title_language', trailer_website_new_list],
            ['wanted', '想看人数', 'title_language', wanted_website_new_list],
        ]
        if config.get('outline_language') == 'jp':
            request_field_list.pop(3)
        if config.get('title_language') == 'jp':
            request_field_list.pop(1)
        if not wanted_website_new_list:
            request_field_list.pop()

    for each_f in request_field_list:
        field_name, field_cnname, field_language, website_list = each_f
        if field_name in none_fields:
            continue
        get_each_field(all_json_data, json_data, website_list, field_name, field_cnname, field_language, config, file_number, short_number, json_data['mosaic'])
        if field_name == 'title' and not json_data['title']:
            return json_data

    # 处理字段字段：从已请求的网站中，按字段网站优先级取值
    title_website_list = title_jp_website_list
    outline_website_list = outline_jp_website_list
    number_website_list = [i for i in number_website_list if i in all_json_data.keys()]
    new_number_website_list = number_website_list
    if 'official' in all_json_data.keys() and all_json_data['official']['jp']['title']:
        official_website_name = all_json_data['official']['jp']['source']
        new_number_website_list = [official_website_name] + number_website_list
        title_jp_website_list = [official_website_name] + title_jp_website_list
        outline_jp_website_list = [official_website_name] + outline_jp_website_list
    if config.get('title_language') != 'jp':
        title_website_list = title_zh_website_list + title_jp_website_list
    if config.get('outline_language') != 'jp':
        outline_website_list = outline_zh_website_list + outline_jp_website_list
    title_website_new_list = get_new_website_list(title_website_list, new_number_website_list, file_number, short_number, 'title', all=True)
    title_jp_website_new_list = get_new_website_list(title_jp_website_list, new_number_website_list, file_number, short_number, 'title', all=True)
    outline_website_new_list = get_new_website_list(outline_website_list, new_number_website_list, file_number, short_number, 'outline', all=True)
    outline_jp_website_new_list = get_new_website_list(outline_jp_website_list, new_number_website_list, file_number, short_number, 'outline', all=True)
    actor_website_new_list = get_new_website_list(actor_website_list, number_website_list, file_number, short_number, 'actor', all=True)
    thumb_website_new_list = get_new_website_list(thumb_website_list, number_website_list, file_number, short_number, 'thumb', all=True)
    poster_website_new_list = get_new_website_list(poster_website_list, number_website_list, file_number, short_number, 'poster', all=True)
    extrafanart_website_new_list = get_new_website_list(extrafanart_website_list, number_website_list, file_number, short_number, 'extrafanart', all=True)
    tag_website_new_list = get_new_website_list(tag_website_list, number_website_list, file_number, short_number, 'tag', all=True)
    release_website_new_list = get_new_website_list(release_website_list, number_website_list, file_number, short_number, 'release', all=True)
    runtime_website_new_list = get_new_website_list(runtime_website_list, number_website_list, file_number, short_number, 'runtime', all=True)
    score_website_new_list = get_new_website_list(score_website_list, number_website_list, file_number, short_number, 'score', all=True)
    director_website_new_list = get_new_website_list(director_website_list, number_website_list, file_number, short_number, 'director', all=True)
    series_website_new_list = get_new_website_list(series_website_list, number_website_list, file_number, short_number, 'series', all=True)
    studio_website_new_list = get_new_website_list(studio_website_list, number_website_list, file_number, short_number, 'studio', all=True)
    publisher_website_new_list = get_new_website_list(publisher_website_list, number_website_list, file_number, short_number, 'publisher', all=True)
    trailer_website_new_list = get_new_website_list(trailer_website_list, number_website_list, file_number, short_number, 'trailer', all=True)
    wanted_website_new_list = get_new_website_list(wanted_website_list, number_website_list, file_number, short_number, 'wanted')
    deal_field_list = [
        ['title', '标题', 'title_language', title_website_new_list],
        ['originaltitle', '原标题', 'outline_language', title_jp_website_new_list],
        ['outline', '简介', 'outline_language', outline_website_new_list],
        ['originalplot', '原简介', 'outline_language', outline_jp_website_new_list],
        ['actor', '演员', 'actor_language', actor_website_new_list],
        ['cover', '背景图', 'title_language', thumb_website_new_list],
        ['poster', '封面图', 'title_language', poster_website_new_list],
        ['extrafanart', '剧照', 'title_language', extrafanart_website_new_list],
        ['tag', '标签', 'tag_language', tag_website_new_list],
        ['release', '发行日期', 'title_language', release_website_new_list],
        ['runtime', '时长', 'title_language', runtime_website_new_list],
        ['score', '评分', 'title_language', score_website_new_list],
        ['director', '导演', 'director_language', director_website_new_list],
        ['series', '系列', 'series_language', series_website_new_list],
        ['studio', '片商', 'studio_language', studio_website_new_list],
        ['publisher', '发行商', 'publisher_language', publisher_website_new_list],
        ['trailer', '预告片', 'title_language', trailer_website_new_list],
        ['wanted', '想看人数', 'title_language', wanted_website_list],
    ]
    if not wanted_website_new_list or (scrape_like == 'speed' and json_data['source'] not in wanted_website_new_list):
        deal_field_list.pop()

    for each_f in deal_field_list:
        field_name, field_cnname, field_language, website_list = each_f
        deal_each_field(all_json_data, json_data, website_list, field_name, field_cnname, field_language, config)

    # 把已刮削成功网站的 cover url 按照 cover 网站优先级，保存为一个列表，第一个图片下载失败时，可以使用其他图片下载
    cover_list = []
    for each_website in thumb_website_new_list:
        if each_website in all_json_data.keys() and all_json_data[each_website]['jp']['title']:
            temp_url = all_json_data[each_website]['jp']['cover']
            if temp_url not in cover_list:
                cover_list.append([each_website, temp_url])
    if not cover_list:
        json_data['cover'] = ''                                                 # GBBH-1041 背景图图挂了
    json_data['cover_list'] = cover_list

    # 把已刮削成功网站的 actor，保存为一个列表，用于 Amazon 搜图，因为有的网站 actor 不对，比如 MOPP-023 javbus错的
    actor_amazon_list = []
    actor_amazon_list_cn = []
    actor_amazon_list_tw = []
    actor_new_website = []
    [actor_new_website.append(i) for i in title_jp_website_new_list + title_website_new_list + actor_website_new_list if i not in actor_new_website]
    for each_website in actor_new_website:
        if each_website in all_json_data.keys() and all_json_data[each_website]['jp']['title']:
            temp_actor = all_json_data[each_website]['jp']['actor']
            if temp_actor:
                actor_amazon_list.extend(temp_actor.split(','))
                if all_json_data[each_website]['zh_cn']['title']:
                    actor_amazon_list_cn.extend(all_json_data[each_website]['zh_cn']['actor'].split(','))
                if all_json_data[each_website]['zh_tw']['title']:
                    actor_amazon_list_tw.extend(all_json_data[each_website]['zh_tw']['actor'].split(','))
    actor_amazon_list = actor_amazon_list + actor_amazon_list_cn + actor_amazon_list_tw
    actor_amazon = []
    [actor_amazon.append(i.strip()) for i in actor_amazon_list if i.strip() and i.strip() not in actor_amazon]
    if '素人' in actor_amazon:
        actor_amazon.remove('素人')
    json_data['actor_amazon'] = actor_amazon

    # 处理 year
    release = json_data['release']
    if release and re.search(r'\d{4}', release):
        json_data['year'] = str(re.search(r'\d{4}', release).group())

    # 处理 number：素人影片时使用有数字前缀的number
    if short_number:
        json_data['number'] = file_number

    json_data['fields_info'] = '\n 🌐 [website] %s' % json_data['req_web'].strip('-> ') + json_data['fields_info']
    return json_data


def deal_each_field(all_json_data, json_data, website_list, field_name, field_cnname, field_language, config):
    '''
    按照设置的网站顺序处理字段
    '''
    if config.get('scrape_like') == 'speed':
        website_list = [json_data['source']]

    elif 'official' in config.get('website_set'):
        if all_json_data['official']['jp']['title']:
            if field_name not in ['title', 'originaltitle', 'outline', 'originalplot', 'wanted', 'score']:
                website_list.insert(0, all_json_data['official']['jp']['source'])

    if not website_list:
        return

    backup_data = ''
    json_data['log_info'] += '\n\n    🙋🏻‍ %s \n    ====================================\n    🌐 来源优先级：%s' % (field_cnname, ' -> '.join(website_list))
    for website in website_list:
        title_language = config.get(field_language)
        if website not in ['airav_cc', 'iqqtv', 'airav', 'avsex', 'javlibrary', 'mdtv', 'madouqu', 'lulubar']:
            title_language = 'jp'
        elif field_name == 'originaltitle' or field_name == 'originalplot' or field_name == 'trailer' or field_name == 'wanted':
            title_language = 'jp'
        try:
            web_data_json = all_json_data[website][title_language]
        except:
            continue

        if web_data_json['title'] and web_data_json[field_name]:
            if not len(backup_data):
                backup_data = web_data_json[field_name]
                backup_website = website

            if config.get('scrape_like') != 'speed':
                if field_name in ['title', 'outline', 'originaltitle', 'originalplot']:
                    if website in ['airav_cc', 'iqqtv', 'airav', 'avsex', 'javlibrary', 'lulubar']:
                        if langid.classify(web_data_json[field_name])[0] != 'ja':
                            if title_language == 'jp':
                                json_data['log_info'] += f'\n    🔴 {website} (失败，检测为非日文，跳过！)'
                                continue
                        elif title_language != 'jp':
                            json_data['log_info'] += f'\n    🔴 {website} (失败，检测为日文，跳过！)'
                            continue
            if field_name == 'poster':
                json_data['poster_from'] = website
                json_data['image_download'] = web_data_json['image_download']
            elif field_name == 'cover':
                json_data['cover_from'] = website
            elif field_name == 'extrafanart':
                json_data['extrafanart_from'] = website
            elif field_name == 'trailer':
                json_data['trailer_from'] = website
            elif field_name == 'outline':
                json_data['outline_from'] = website
            elif field_name == 'actor':
                json_data['all_actor'] = json_data['all_actor'] if json_data.get('all_actor') else web_data_json['actor']
                json_data['all_actor_photo'] = json_data['all_actor_photo'] if json_data.get('all_actor_photo') else web_data_json['actor_photo']
            elif field_name == 'originaltitle':
                if web_data_json['actor']:
                    json_data['amazon_orginaltitle_actor'] = web_data_json['actor'].split(',')[0]
            json_data[field_name] = web_data_json[field_name]
            json_data['fields_info'] += '\n     ' + "%-13s" % field_name + ': %s (%s)' % (website, title_language)
            json_data['log_info'] += f'\n    🟢 {website} (成功)\n     ↳ {json_data[field_name]}'
            break
        else:
            json_data['log_info'] += f'\n    🔴 {website} (失败)'
    else:
        if len(backup_data):
            json_data[field_name] = backup_data
            json_data['fields_info'] += '\n     ' + "%-13s" % field_name + ': %s (%s)' % (backup_website, title_language)
            json_data['log_info'] += f'\n    🟢 {backup_website} (使用备用数据)\n     ↳ {backup_data}'
        else:
            json_data['fields_info'] += '\n     ' + "%-13s" % field_name + ': %s (%s)' % ('-----', 'not found')


def get_each_field(all_json_data, json_data, website_list, field_name, field_cnname, field_language, config, file_number, short_number, mosaic):
    '''
    按照设置的网站顺序获取各个字段信息
    '''
    if 'official' in config.get('website_set'):
        if field_name not in ['title', 'title_zh', 'outline_zh', 'wanted', 'score']:
            website_list.insert(0, 'official')

    backup_jsondata = {}
    for website in website_list:
        if (website in ['avsox', 'mdtv'] and mosaic in ['有码', '无码破解', '流出', '里番', '动漫']) or (website == 'mdtv' and mosaic == '无码'):
            if field_name != 'title':
                continue
        if field_name in ['title_zh', 'outline_zh']:
            title_language = 'zh_cn'
            field_name = field_name.replace('_zh', '')
        elif field_name in ['originaltitle', 'originalplot', 'trailer', 'wanted']:
            title_language = 'jp'
        elif website not in ['airav_cc', 'iqqtv', 'airav', 'avsex', 'javlibrary', 'mdtv', 'madouqu', 'lulubar']:
            title_language = 'jp'
        else:
            title_language = config.get(field_language)

        try:
            web_data_json = all_json_data[website][title_language]
        except:
            web_data = get_web_data(json_data, website, title_language, file_number, short_number, mosaic, config.get('title_language'))
            all_json_data.update(web_data)
            web_data_json = all_json_data.get(website).get(title_language)
            json_data['req_web'] = web_data_json['req_web']
            json_data['log_info'] = web_data_json['log_info']

        if field_cnname == '标题':
            json_data.update(web_data_json)
        if web_data_json['title'] and web_data_json[field_name]:
            if not len(backup_jsondata):
                backup_jsondata.update(web_data_json)
                backup_website = website
                backup_jsondata.pop('req_web')
                backup_jsondata.pop('log_info')
            if field_cnname == '标题':
                json_data['outline_from'] = website
                json_data['poster_from'] = website
                json_data['cover_from'] = website
                json_data['extrafanart_from'] = website
                json_data['trailer_from'] = website
            if config.get('scrape_like') != 'speed':
                if website in ['airav_cc', 'iqqtv', 'airav', 'avsex', 'javlibrary', 'lulubar']:
                    if field_name in ['title', 'outline', 'originaltitle', 'originalplot']:
                        if langid.classify(web_data_json[field_name])[0] != 'ja':
                            if title_language == 'jp':
                                json_data['log_info'] += f'\n    🔴 {field_cnname} 检测为非日文，跳过！({website})\n     ↳ {web_data_json[field_name]}'
                                continue
                        elif title_language != 'jp':
                            json_data['log_info'] += f'\n    🔴 {field_cnname} 检测为日文，跳过！({website})\n     ↳ {web_data_json[field_name]}'
                            continue
                elif website == 'official':
                    website = all_json_data['official']['jp']['source']
            json_data['log_info'] += f'\n    🟢 {field_cnname} 获取成功！({website})\n     ↳ {web_data_json[field_name]} '
            break
    else:
        if len(backup_jsondata):
            json_data['log_info'] += f'\n    🟢 {field_cnname} 使用备用数据！({backup_website})\n     ↳ {backup_jsondata[field_name]} '
            if field_cnname == '标题':
                json_data.update(backup_jsondata)
        else:
            json_data['log_info'] += f'\n    🔴 {field_cnname} 获取失败！'

# ================================================================================================= 单网站刮削


def get_single_website_data(json_data, website):
    file_number = json_data['number']
    short_number = json_data['short_number']
    mosaic = json_data['mosaic']
    json_data['fields_info'] = ''

    config = cf.get_config()
    title_language = config.get('title_language')
    org_language = title_language
    outline_language = config.get('outline_language')
    actor_language = config.get('actor_language')
    tag_language = config.get('tag_language')
    series_language = config.get('series_language')
    studio_language = config.get('studio_language')
    publisher_language = config.get('publisher_language')
    director_language = config.get('director_language')
    if website not in ['airav_cc', 'iqqtv', 'airav', 'avsex', 'javlibrary', 'mdtv', 'madouqu', 'lulubar']:
        title_language = 'jp'
        outline_language = 'jp'
        actor_language = 'jp'
        tag_language = 'jp'
        series_language = 'jp'
        studio_language = 'jp'
        publisher_language = 'jp'
        director_language = 'jp'
    elif website == 'mdtv':
        title_language = 'zh_cn'
        outline_language = 'zh_cn'
        actor_language = 'zh_cn'
        tag_language = 'zh_cn'
        series_language = 'zh_cn'
        studio_language = 'zh_cn'
        publisher_language = 'zh_cn'
        director_language = 'zh_cn'
    web_data = get_web_data(json_data, website, title_language, file_number, short_number, mosaic, org_language)
    web_data_json = web_data.get(website).get(title_language)
    json_data.update(web_data_json)
    if not json_data['title']:
        return json_data
    if outline_language != title_language:
        web_data_json = web_data[website][outline_language]
        if web_data_json['outline']:
            json_data['outline'] = web_data_json['outline']
    if actor_language != title_language:
        web_data_json = web_data[website][actor_language]
        if web_data_json['actor']:
            json_data['actor'] = web_data_json['actor']
    if tag_language != title_language:
        web_data_json = web_data[website][tag_language]
        if web_data_json['tag']:
            json_data['tag'] = web_data_json['tag']
    if series_language != title_language:
        web_data_json = web_data[website][series_language]
        if web_data_json['series']:
            json_data['series'] = web_data_json['series']
    if studio_language != title_language:
        web_data_json = web_data[website][studio_language]
        if web_data_json['studio']:
            json_data['studio'] = web_data_json['studio']
    if publisher_language != title_language:
        web_data_json = web_data[website][publisher_language]
        if web_data_json['publisher']:
            json_data['publisher'] = web_data_json['publisher']
    if director_language != title_language:
        web_data_json = web_data[website][director_language]
        if web_data_json['director']:
            json_data['director'] = web_data_json['director']
    if json_data['cover']:
        json_data['cover_list'] = [[website, json_data['cover']]]

    # 加入来源信息
    json_data['outline_from'] = website
    json_data['poster_from'] = website
    json_data['cover_from'] = website
    json_data['extrafanart_from'] = website
    json_data['trailer_from'] = website
    json_data['fields_info'] = '\n 🌐 [website] %s' % json_data['req_web'].strip('-> ')

    if short_number:
        json_data['number'] = file_number

    temp_actor = web_data[website]['jp']['actor'] + ',' + web_data[website]['zh_cn']['actor'] + ',' + web_data[website]['zh_tw']['actor']
    json_data['actor_amazon'] = []
    [json_data['actor_amazon'].append(i) for i in temp_actor.split(',') if i and i not in json_data['actor_amazon']]
    json_data['all_actor'] = json_data['all_actor'] if json_data.get('all_actor') else web_data_json['actor']
    json_data['all_actor_photo'] = json_data['all_actor_photo'] if json_data.get('all_actor_photo') else web_data_json['actor_photo']

    return json_data


# ========================================================================根据番号获取数据


def get_data_from_website(json_data, website_name):                             # 从JSON返回元数据
    file_number = json_data['number']
    file_path = json_data['file_path']
    short_number = json_data['short_number']
    appoint_number = json_data['appoint_number']
    appoint_url = json_data['appoint_url']
    logs = json_data['logs']
    has_sub = json_data['has_sub']
    c_word = json_data['c_word']
    leak = json_data['leak']
    wuma = json_data['wuma']
    youma = json_data['youma']
    cd_part = json_data['cd_part']
    destroyed = json_data['destroyed']
    mosaic = json_data['mosaic']
    version = json_data['version']
    config = cf.get_config()
    json_data['title'] = ''
    json_data['req_web'] = ''
    json_data['log_info'] = ''
    json_data['fields_info'] = ''
    json_data['all_actor'] = ''
    json_data['all_actor_photo'] = ''

    # ================================================网站规则添加开始================================================

    if website_name == 'all':                                                   # 从全部网站刮削

        # =======================================================================先判断是不是国产，避免浪费时间
        if mosaic == '国产' or mosaic == '國產' or (re.search(r'([^A-Z]|^)MD[A-Z-]*\d{4,}', file_number) and 'MDVR' not in file_number) or re.search(r'MKY-[A-Z]+-\d{3,}', file_number):
            json_data['mosaic'] = '国产'
            website_list = config.get('website_guochan').split(',')
            json_data = get_websites_data(json_data, website_list)

        # =======================================================================kin8
        elif file_number.startswith('KIN8'):
            website_name = 'kin8'
            json_data = get_single_website_data(json_data, website_name)

        # =======================================================================同人
        elif file_number.startswith('DLID'):
            website_name = 'getchu'
            json_data = get_single_website_data(json_data, website_name)

        # =======================================================================里番
        elif 'getchu' in file_path.lower() or '里番' in file_path or '裏番' in file_path:
            website_name = 'getchu_dmm'
            json_data = get_single_website_data(json_data, website_name)

        # =======================================================================Mywife No.1111
        elif 'mywife' in file_path.lower():
            website_name = 'mywife'
            json_data = get_single_website_data(json_data, website_name)

        # =======================================================================FC2-111111
        elif 'FC2' in file_number.upper():
            file_number_1 = re.search(r'\d{5,}', file_number)
            if file_number_1:
                file_number_1.group()
                website_list = config.get('website_fc2').split(',')
                json_data = get_websites_data(json_data, website_list)
            else:
                json_data['error_info'] = '未识别到FC2番号：%s' % file_number

        # =======================================================================sexart.15.06.14
        elif re.search(r'[^.]+\.\d{2}\.\d{2}\.\d{2}', file_number) or ('欧美' in file_path and '东欧美' not in file_path):
            website_list = config.get('website_oumei').split(',')
            json_data = get_websites_data(json_data, website_list)

        # =======================================================================无码抓取:111111-111,n1111,HEYZO-1111,SMD-115
        elif mosaic == '无码' or mosaic == '無碼':
            website_list = config.get('website_wuma').split(',')
            json_data = get_websites_data(json_data, website_list)

        # =======================================================================259LUXU-1111
        elif short_number or 'SIRO' in file_number.upper():
            website_list = config.get('website_suren').split(',')
            json_data = get_websites_data(json_data, website_list)

        # =======================================================================ssni00321
        elif re.match(r'\D{2,}00\d{3,}', file_number) and '-' not in file_number and '_' not in file_number:
            website_list = ['dmm']
            json_data = get_websites_data(json_data, website_list)

        # =======================================================================剩下的（含匹配不了）的按有码来刮削
        else:
            website_list = config.get('website_youma').split(',')
            json_data = get_websites_data(json_data, website_list)
    else:
        json_data = get_single_website_data(json_data, website_name)

    # ================================================网站请求结束================================================
    # ======================================超时或未找到返回
    if json_data['title'] == '':
        return json_data

    number = json_data['number']
    if appoint_number:
        number = appoint_number

    # 马赛克
    if leak:
        json_data['mosaic'] = '无码流出'
    elif destroyed:
        json_data['mosaic'] = '无码破解'
    elif wuma:
        json_data['mosaic'] = '无码'
    elif youma:
        json_data['mosaic'] = '有码'
    elif mosaic:
        json_data['mosaic'] = mosaic
    if not json_data.get('mosaic'):
        if is_uncensored(number):
            json_data['mosaic'] = '无码'
        else:
            json_data['mosaic'] = '有码'
    print(number, cd_part, json_data['mosaic'], json_data['req_web'].strip('-> '))

    # 车牌字母
    letters = get_number_letters(number)

    # 原标题，用于amazon搜索
    originaltitle = json_data.get('originaltitle') if json_data.get('originaltitle') else ''
    json_data['originaltitle_amazon'] = originaltitle
    for each in json_data['actor_amazon']:  # 去除演员名，避免搜索不到
        try:
            end_actor = re.compile(r' %s$' % each)
            json_data['originaltitle_amazon'] = re.sub(end_actor, '', json_data['originaltitle_amazon'])
        except:
            pass

    # VR 时下载小封面
    if 'VR' in number:
        json_data['image_download'] = True

    # 返回处理后的json_data
    json_data['number'] = number
    json_data['letters'] = letters
    json_data['has_sub'] = has_sub
    json_data['c_word'] = c_word
    json_data['leak'] = leak
    json_data['wuma'] = wuma
    json_data['youma'] = youma
    json_data['4k'] = ''
    json_data['cd_part'] = cd_part
    json_data['destroyed'] = destroyed
    json_data['actor_href'] = ''
    json_data['version'] = version
    json_data['logs'] = logs
    json_data['file_path'] = file_path
    json_data['appoint_number'] = appoint_number
    json_data['appoint_url'] = appoint_url
    json_data['poster_path'] = ''
    json_data['thumb_path'] = ''
    json_data['fanart_path'] = ''
    json_data['error_info'] = ''

    return json_data


# ========================================================================检查图片


def check_pic(path_pic):
    if os.path.exists(path_pic):
        try:
            with Image.open(path_pic) as img:                                   # 如果文件不是图片，报错
                img.load()                                                      # 如果图片不完整，报错OSError: image file is truncated
                return img.size
        except Exception as e:
            cf.add_log(f'文件损坏: {path_pic} \n Error: {e}')
            try:
                os.remove(path_pic)
                cf.add_log('删除成功！')
            except:
                cf.add_log('删除失败！')
    return False


# ========================================================================获取真实演员名字


def get_actorname(number):
    url = f'https://av-wiki.net/?s={number}'
    result, res = get_html(url)
    if not result:
        return False, f"Error: {res}"
    html_detail = etree.fromstring(res, etree.HTMLParser(encoding='utf-8'))
    actor_box = html_detail.xpath('//ul[@class="post-meta clearfix"]')
    for each in actor_box:
        actor_name = each.xpath('li[@class="actress-name"]/a/text()')
        actor_number = each.xpath('li[@class="actress-name"]/following-sibling::li[last()]/text()')
        if actor_number:
            if actor_number[0].upper().endswith(number.upper()) or number.upper().endswith(actor_number[0].upper()):
                return True, ','.join(actor_name)
    return False, 'No Result!'


# ========================================================================打印json_data


def print_js(json_data):
    js = json.dumps(
        json_data,
        ensure_ascii=False,
        sort_keys=False,
        indent=4,
        separators=(',', ': '),
    )
    print(js)
