#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import ctypes
import traceback
import cv2
import platform
import langid
import zhconv
import hashlib
import random
from lxml import etree
import bs4
import threading
import json
from PyQt5.QtGui import QCursor, QPixmap, QIcon, QImageReader, QHoverEvent, QKeySequence, QFontDatabase
from PyQt5.QtWidgets import QMainWindow, QTreeWidgetItem, QApplication, QPushButton, QDialog, QFileDialog, QMessageBox, QInputDialog, QMenu, QAction, QShortcut, QSystemTrayIcon
from PyQt5.QtCore import pyqtSignal, Qt, QCoreApplication, QPoint, QRect, QEvent, QTimer
import sys
import subprocess
import time
import os.path
import requests
import shutil
import base64
import re
from PIL import Image, ImageFilter, ImageFile
import os
import webbrowser
from configparser import RawConfigParser
from ping3 import ping
from Ui.MDCx import Ui_MDCx
from Ui.posterCutTool import Ui_Dialog_cut_poster
from Function.Function import get_data_from_website, check_pic, need_clean, delete_file, move_file, copy_file, get_actorname, split_path, read_link, print_js
from Function.getHtml import get_html, post_html, scraper_html, check_url, multi_download, get_avsox_domain, get_imgsize, get_amazon_data, get_user_agent
from Function.getInfo import get_file_number, get_number_letters, get_info, is_uncensored, remove_escape_string, get_number_first_letter
import Function.config as cf
import unicodedata
import urllib
import urllib3  # yapf: disable # NOQA: E402
from concurrent.futures import ThreadPoolExecutor
import queue
import deepl
# import faulthandler
# faulthandler.enable()
urllib3.disable_warnings()  # yapf: disable # NOQA: E402
ImageFile.LOAD_TRUNCATED_IMAGES = True


class Pool(ThreadPoolExecutor):

    def shutdown39(self, wait=True, *, cancel_futures=False):
        with self._shutdown_lock:
            self._shutdown = True
            if cancel_futures:
                # Drain all work items from the queue, and then cancel their
                # associated futures.
                while True:
                    try:
                        work_item = self._work_queue.get_nowait()
                    except queue.Empty:
                        break
                    if work_item is not None:
                        work_item.future.cancel()

            # Send a wake-up to prevent threads calling
            # _work_queue.get(block=True) from permanently blocking.
            self._work_queue.put(None)
        if wait:
            for t in self._threads:
                t.join()


class MyMAinWindow(QMainWindow, Ui_MDCx):
    progressBarValue = pyqtSignal(int)                                          # 进度条信号量
    main_logs_show = pyqtSignal(str)                                            # 显示刮削日志信号
    main_logs_clear = pyqtSignal(str)                                           # 清空刮削日志信号
    req_logs_clear = pyqtSignal(str)                                            # 清空请求日志信号
    main_req_logs_show = pyqtSignal(str)                                        # 显示刮削后台日志信号
    logs_failed_show = pyqtSignal(str)                                          # 失败面板添加信息日志信号
    logs_failed_settext = pyqtSignal(str)                                       # 失败面板添加信息日志信号
    net_logs_show = pyqtSignal(str)                                             # 显示网络检测日志信号
    set_javdb_cookie = pyqtSignal(str)                                          # 加载javdb cookie文本内容到设置页面
    set_javbus_cookie = pyqtSignal(str)                                         # 加载javbus cookie文本内容到设置页面
    set_javbus_status = pyqtSignal(str)                                         # javbus 检查状态更新
    set_label_file_path = pyqtSignal(str)                                       # 主界面更新路径信息显示
    set_tree_child = pyqtSignal(str, str)                                       # 主界面更新结果列表
    set_main_info = pyqtSignal(object)                                          # 主界面更新番号信息
    set_pic_pixmap = pyqtSignal(list, list)                                     # 主界面显示封面、缩略图
    set_pic_text = pyqtSignal(str)                                              # 主界面显示封面信息
    change_to_mainpage = pyqtSignal(str)                                        # 切换到主界面
    label_result = pyqtSignal(str)
    pushButton_start_cap = pyqtSignal(str)
    pushButton_start_cap2 = pyqtSignal(str)
    pushButton_start_single_file = pyqtSignal(str)
    pushButton_add_sub_for_all_video = pyqtSignal(str)
    pushButton_show_pic_actor = pyqtSignal(str)
    pushButton_add_actor_info = pyqtSignal(str)
    pushButton_add_actor_pic = pyqtSignal(str)
    pushButton_add_actor_pic_kodi = pyqtSignal(str)
    pushButton_del_actor_folder = pyqtSignal(str)
    pushButton_check_and_clean_files = pyqtSignal(str)
    pushButton_move_mp4 = pyqtSignal(str)
    pushButton_find_missing_number = pyqtSignal(str)
    label_show_version = pyqtSignal(str)

    def __init__(self, parent=None):
        super(MyMAinWindow, self).__init__(parent)

        # 初始化需要的变量
        self.localversion = '20231014'                                          # 当前版本号
        self.new_version = ''                                                   # 有版本更新时在左下角显示的新版本信息
        self.main_path = self.get_main_path()                                   # 获取主程序路径
        self.json_data = {}                                                     # 当前树状图选中文件的json_data
        self.img_path = ''                                                      # 当前树状图选中文件的图片地址
        self.actor_mapping_data = ''                                            # 演员映射表数据
        self.info_mapping_data = ''                                             # 信息映射表数据
        self.m_drag = False                                                     # 允许鼠标拖动的标识
        self.m_DragPosition = 0                                                 # 鼠标拖动位置
        self.logs_counts = 0                                                    # 日志次数（每1w次清屏）
        self.req_logs_counts = 0                                                # 日志次数（每1w次清屏）
        self.count_claw = 0                                                     # 批量刮削次数
        self.single_file_path = ''                                              # 工具单文件刮削的文件路径
        self.file_main_open_path = ''                                           # 主界面打开的文件路径
        self.json_array = {}                                                    # 主界面右侧结果树状数据
        self.local_number_flag = ''                                             # 启动后本地数据库是否扫描过
        self.actor_numbers_dic = {}                                             # 每个演员所有番号的字典
        self.local_number_set = set()                                           # 本地所有番号的集合
        self.local_number_cnword_set = set()                                    # 本地所有有字幕的番号的集合
        self.current_proxy = ''                                                 # 代理信息
        self.youdaokey = "Ygy_4c=r#e#4EX^NUGUc5"                                # 有道key，可以不要这个
        self.window_radius = 0                                                  # 窗口四角弧度，为0时表示显示窗口标题栏
        self.window_border = 0                                                  # 窗口描边，为0时表示显示窗口标题栏
        self.threads_list = []                                                  # 开启的线程列表
        self.dark_mode = False                                                  # 暗黑模式标识
        self.again_dic = {}                                                     # 待重新刮削的字典
        self.check_mac = True                                                   # 检测配置目录

        # self.window_marjin = 0 窗口外边距，为0时不往里缩
        self.show_flag = True                                                   # 是否加载刷新样式
        self.file_mode = 'default_folder'                                       # 默认刮削待刮削目录
        self.stop_other = True                                                  # 非刮削线程停止标识

        # 获取资源文件路径
        self.sehua_title_path = self.resource_path(self.get_c_number_path())    # 内置色花数据的文件路径
        self.actor_map_backup_path = self.resource_path(self.get_actor_path())  # 内置演员映射表的文件路径
        self.info_map_backup_path = self.resource_path(self.get_info_path())    # 内置信息映射表的文件路径
        self.icon_ico = self.resource_path('Img/MDCx.ico')                      # 任务栏图标
        self.right_menu = self.resource_path('Img/menu.svg')                    # 主界面菜单按钮
        self.play_icon = self.resource_path('Img/play.svg')                     # 主界面播放按钮
        self.open_folder_icon = self.resource_path('Img/folder.svg')            # 主界面打开文件夹按钮
        self.open_nfo_icon = self.resource_path('Img/nfo.svg')                  # 主界面打开nfo按钮
        self.input_number_icon = self.resource_path('Img/number.svg')           # 主界面输入番号按钮
        self.input_website_icon = self.resource_path('Img/website.svg')         # 主界面输入网址按钮
        self.del_file_icon = self.resource_path('Img/delfile.svg')              # 主界面删除文件按钮
        self.del_folder_icon = self.resource_path('Img/delfolder.svg')          # 主界面删除文件夹按钮
        self.start_icon = self.resource_path('Img/start.svg')                   # 主界面开始按钮
        self.stop_icon = self.resource_path('Img/stop.svg')                     # 主界面开始按钮
        self.show_logs_icon = self.resource_path('Img/show.svg')                # 日志界面显示日志按钮
        self.hide_logs_icon = self.resource_path('Img/hide.svg')                # 日志界面隐藏日志按钮
        self.hide_boss_icon = self.resource_path('Img/hide_boss.svg')           # 隐藏界面按钮
        self.save_failed_list_icon = self.resource_path('Img/save.svg')         # 保存失败列表按钮
        self.clear_tree_icon = self.resource_path('Img/clear.svg')              # 主界面清空结果列表按钮
        self.can_save_remain = False                                            # 保存剩余任务
        self.timer = QTimer()                                                   # 初始化一个定时器，用于显示日志
        self.timer.timeout.connect(self.show_detail_log)
        self.timer.start(100)                                                   # 设置间隔100毫秒
        self.timer_scrape = QTimer()                                            # 初始化一个定时器，用于间隔刮削
        self.timer_scrape.timeout.connect(self.auto_scrape)
        self.scrape_start_time = ''
        self.timer_update = QTimer()                                            # 初始化一个定时器，用于检查更新
        self.timer_update.timeout.connect(self.check_version)
        self.timer_update.start(43200000)                                       # 设置检查间隔12小时
        self.timer_remain_task = QTimer()                                       # 初始化一个定时器，用于显示保存剩余任务
        self.timer_remain_task.timeout.connect(self.save_remain_list)
        self.timer_remain_task.start(1500)                                      # 设置间隔1.5秒
        self.atuo_scrape_count = 0                                              # 循环刮削次数
        self.label_number_url = ''
        self.label_actor_url = ''
        self.failed_list = []                                                   # 失败文件和错误原因记录
        self.failed_file_list = []                                              # 失败文件记录

        self.get_platform_info()                                                # 获取平台信息

        # 加载字体
        self.get_fonts()

        # 加载Ui、配置
        self.Ui = Ui_MDCx()                                                     # 实例化 Ui
        self.Ui.setupUi(self)                                                   # 初始化 Ui
        self.Init_Singal()                                                      # 信号连接
        self.Init_Ui()                                                          # 设置Ui初始状态
        self.load_config()                                                      # 加载配置
        self.success_list = set()
        self.get_success_list()                                                 # 获取历史成功刮削列表

        # 启动后一些文案提示和后台检查更新
        self.set_some_data()                                                    # 设置一些全局变量
        self.show_scrape_info()                                                 # 主界面左下角显示一些配置信息
        self.show_net_info('\n🏠 代理设置在:【设置】 - 【网络】 - 【代理设置】。\n')                 # 检查网络界面显示提示信息
        self.show_netstatus(self.new_proxy)                                     # 检查网络界面显示当前网络代理信息
        self.show_net_info('\n💡 说明：\n 任意代理：javbus、jav321、javlibrary、mgstage、mywife、giga、freejavbt、mdtv、madouqu、7mmtv、faleno、dahlia、prestige、theporndb、cnmdb、fantastica、kin8\n 非日本代理：javdb、airav-cc、avsex（日本代理会报错）\n 日本代理：seesaawiki\n 无需代理：avsex、hdouban、iqqtv、airav-wiki、love6、lulubar、fc2、fc2club、fc2hub\n\n▶️ 点击右上角 【开始检测】按钮以测试网络连通性。')                            # 检查网络界面显示提示信息
        cf.add_log("🍯 你可以点击左下角的图标来 显示 / 隐藏 请求信息面板！")
        # self.get_youdao_key()                                                 # 获取有道key
        self.show_version()                                                     # 日志页面显示版本信息
        self.creat_right_menu()                                                 # 加载右键菜单
        self.extrafanart_pool = Pool(20)                                        # 剧照下载线程池
        self.get_local_data()                                                   # 载入本地数据（sehua_title, actor_map， info_map）
        self.pushButton_main_clicked()                                          # 切换到主界面
        # self.pushButton_show_log_clicked()
        self.show_statement()
        self.auto_start()                                                       # 自动开始刮削

        # self.load_langid()# 后台加载langid，第一次加载需要时间，预加载避免卡住

    # ======================================================================================设置Ui的一些参数

    def Init_Ui(self):
        self.setWindowTitle("MDCx")                                             # 设置任务栏标题
        self.setWindowIcon(QIcon(self.icon_ico))                                # 设置任务栏图标
        self.setWindowOpacity(1.0)                                              # 设置窗口透明度
        if self.is_windows:
            self.setFixedSize(self.width(), self.height())                      # 禁止调整窗口大小(mac 平台禁止后最小化没反应，恢复时顶部会残留标题栏)
        self.setAttribute(Qt.WA_TranslucentBackground)                          # 设置窗口背景透明
        self.Ui.progressBar_scrape.setValue(0)                                  # 进度条清0
        self.Ui.progressBar_scrape.setTextVisible(False)                        # 不显示进度条文字
        self.Ui.pushButton_start_cap.setCheckable(True)                         # 主界面开始按钮可点状态
        self.init_QTreeWidget()                                                 # 初始化树状图
        self.Ui.label_poster.setScaledContents(True)                            # 图片自适应窗口
        self.Ui.label_thumb.setScaledContents(True)                             # 图片自适应窗口
        self.Ui.pushButton_right_menu.setIcon(QIcon(self.right_menu))
        self.Ui.pushButton_right_menu.setToolTip(' 右键菜单 ')
        self.Ui.pushButton_play.setIcon(QIcon(self.play_icon))
        self.Ui.pushButton_play.setToolTip(' 播放 ')
        self.Ui.pushButton_open_folder.setIcon(QIcon(self.open_folder_icon))
        self.Ui.pushButton_open_folder.setToolTip(' 打开文件夹 ')
        self.Ui.pushButton_open_nfo.setIcon(QIcon(self.open_nfo_icon))
        self.Ui.pushButton_open_nfo.setToolTip(' 编辑 NFO ')
        self.Ui.pushButton_tree_clear.setIcon(QIcon(self.clear_tree_icon))
        self.Ui.pushButton_tree_clear.setToolTip(' 清空结果列表 ')
        self.Ui.pushButton_close.setToolTip(' 关闭 ')
        self.Ui.pushButton_min.setToolTip(' 最小化 ')
        self.Ui.pushButton_main.setIcon(QIcon(self.resource_path('Img/home.svg')))
        self.Ui.pushButton_log.setIcon(QIcon(self.resource_path('Img/log.svg')))
        self.Ui.pushButton_tool.setIcon(QIcon(self.resource_path('Img/tool.svg')))
        self.Ui.pushButton_setting.setIcon(QIcon(self.resource_path('Img/setting.svg')))
        self.Ui.pushButton_net.setIcon(QIcon(self.resource_path('Img/net.svg')))
        help_icon = QIcon(self.resource_path('Img/help.svg'))
        self.Ui.pushButton_about.setIcon(help_icon)
        self.Ui.pushButton_tips_normal_mode.setIcon(help_icon)
        self.Ui.pushButton_tips_normal_mode.setToolTip('''<html><head/><body><p><b>正常模式：</b><br/>1）适合海报墙用户。正常模式将联网刮削视频字段信息，并执行翻译字段信息，移动和重命名视频文件及文件夹，下载图片、剧照、预告片，添加字幕、4K水印等一系列自动化操作<br/>2）刮削目录请在「设置」-「刮削目录」-「待刮削目录」中设置<br/>3）刮削网站请在「设置」-「刮削网站」中设置。部分网站需要代理访问，可在「设置」-「代理」中设置代理和免翻网址。你可以点击左侧的「检测网络」查看网络连通性<br/>\
            4）字段翻译请在「设置」-「翻译」中设置<br/>5）图片、剧照、预告片请在「设置」-「下载」中设置<br/>6）视频文件命名请在「设置」-「命名」中设置<br/>7）如果刮削后不需要重命名，请在下面的「刮削成功后重命名文件」设置为「关」<br/>8）如果刮削后不需要移动文件，请在下面的「刮削成功后移动文件」设置为「关」<br/>9）如果想自动刮削，请在「设置」-「高级」中勾选「自动刮削」<br/>10）其他设置项和功能玩法可自行研究</p></body></html>''')
        self.Ui.pushButton_tips_sort_mode.setIcon(help_icon)
        self.Ui.pushButton_tips_sort_mode.setToolTip('''<html><head/><body><p><b>视频模式：</b><br/>1，适合不需要图片墙的情况。视频模式将联网刮削视频相关字段信息，然后根据「设置」-「命名」中设置的命名规则重命名、移动视频文件<br/>2，仅整理视频，不会下载和重命名图片、nfo 文件<br/>3，如果是海报墙用户，请不要使用视频模式。</p></body></html>''')
        self.Ui.pushButton_tips_update_mode.setIcon(help_icon)
        self.Ui.pushButton_tips_update_mode.setToolTip('''<html><head/><body><p><b>更新模式：</b><br/>1，适合视频已经归类好的情况。更新模式将在不改动文件位置结构的前提下重新刮削更新一些信息<br/>2，更新规则在下面的「更新模式规则中」定义：<br/>-1）如果只更新视频文件名，请选择「只更新C」，视频文件名命名规则请到「设置-」「命名规则」中设置<br/>-2）如果要更新视频所在的目录名，请选择「更新B和C」；如果要更新视频目录的上层目录，请勾选「同时更新A目录」<br/>-3），如果要在视频目录为视频再创建一级目录，请选择「创建D目录」<br/>\
            3，更新模式将会对「待刮削目录」下的所有视频进行联网刮削和更新。<br/>4，当有部分内容没有更新成功，下次想只刮削这些内容时，请选择「读取模式」，同时勾选「不存在 nfo 时，刮削并执行更新模式规则」，它将查询并读取所有视频本地的 nfo 文件（不联网），当没有 nfo 文件时，则会自动进行联网刮削<br/>5，当部分内容确实无法刮削时，你可以到「日志」页面，点击「失败」按钮，点击左下角的保存按钮，就可以把失败列表保存到本地，然后可以手动查看和处理这些视频信息。</p></body></html>''')
        self.Ui.pushButton_tips_read_mode.setIcon(help_icon)
        self.Ui.pushButton_tips_read_mode.setToolTip('''<html><head/><body><p><b>读取模式：</b><br/>\
            1，读取模式通过读取本地的 nfo 文件中的字段信息，可以无需联网，实现查看或更新视频命名等操作<br/>\
            2，如果仅想查看和检查已刮削的视频信息和图片是否存在问题，可以：<br/>\
            -1）不勾选「本地已刮削成功的文件，重新整理分类」；<br/>\
            -2）不勾选「本地自取刮削失败的文件，重新刮削」。<br/>\
            3，如果想要快速重新整理分类(不联网)，可以：<br/>\
            -1）勾选「本地已刮削成功的文件，重新整理分类」；<br/>\
            -2）在下面的「更新模式规则」中自定义更新规则。<br/>\
            软件将按照「更新模式规则」，和「设置」-「命名」中的设置项，进行重命名等操作。<br/>\
            4，如果想要重新翻译映射字段，可以：<br/>\
            -1）勾选「本地已刮削成功的文件，重新整理分类」；<br/>\
            -2）勾选「重新翻译映射 nfo 的信息」。<br/>\
            软件将按照「设置」-「翻译」中的设置项，重新翻译映射各字段。<br/>\
            6，如果想要重新下载图片等文件（需联网），可以：<br/>\
            -1）勾选「本地已刮削成功的文件，重新整理分类」；<br/>\
            -2）勾选「重新下载图片等文件」。<br/>\
            软件将按照「设置」-「下载」中的设置项，进行下载、保留等操作。</p></body></html>''')
        self.Ui.pushButton_tips_soft.setIcon(help_icon)
        self.Ui.pushButton_tips_soft.setToolTip('''<html><head/><body><p><b>创建软链接：</b><br/>\
            1，软链接适合网盘用户。软链接类似快捷方式，是指向真实文件的一个符号链接。它体积小，支持跨盘指向，删除后不影响原文件（当原文件删除后，软链接会失效）。<br/>\
            <span style=" font-weight:700; color:red;">注意：\
            <br/>Windows版：软链接保存位置必须是本地磁盘（平台限制），真实文件则网盘或本地盘都可以。<br/>\
            macOS版：没有问题。<br/>\
            Docker版：挂载目录的完整路径需要和实际目录完整路径一样，这样软链接才能指向实际位置，Emby 才能播放。</span><br/>\

            2，网盘受网络等因素影响，读写慢，限制多。选择创建软链接时，将在本地盘创建指向网盘视频文件的软链接文件，同时刮削下载的图片同样放在本地磁盘，使用 Emby、Jellyfin 加载速度快！<br/>\
            3，刮削不会移动、修改、重命名原文件，仅读取原文件的路径位置，用来创建软链接<br/>\
            4，刮削成功后，将按照刮削设置创建和重命名软链接文件<br/>\
            5，刮削失败时，不会创建软链接，如果你想要把全部文件都创建软链接，可以到 【工具】-【软链接助手】-【一键创建软链接】）<br/>\
            6，如果网盘里已经有刮削好的内容，想要把刮削信息转移到本地磁盘，同样使用上述工具，勾选【复制已刮削的图片和NFO文件】即可<br/>\
            7，网盘挂载和刮削方法：<br/>\
            -1）使用 CloudDriver、Alist、RaiDrive 等第三方工具挂载网盘<br/>\
            -2）MDCx 设置待刮削目录为网盘视频目录，输出目录为本地磁盘文件夹<br/>\
            -3）设置中选择「创建软链接」，其他配置设置好后保存配置，点击开始刮削<br/>\
            -4）Emby、Jellyfin 媒体库路径设置为本地刮削后保存的磁盘文件夹扫描即可</p></body></html>''')
        self.Ui.pushButton_tips_hard.setIcon(help_icon)
        self.Ui.pushButton_tips_hard.setToolTip('''<html><head/><body><p><b>创建硬链接：</b><br/>1，硬链接适合 PT 用户。PT 用户视频文件一般存放在 NAS 中，为保证上传分享率，不能修改原文件信息。<br/>2，硬链接指向和原文件相同的硬盘索引，和原文件必须同盘。使用硬链接，可以在同盘单独存放刮削资料，不影响原文件信息。<br/>3，删除硬链接，原文件还在；删除原文件，硬链接还在。两个都删除，文件才会被删除。<br/><span style=" font-weight:700; color:#ff2600;">注意：Mac 平台仅支持本地磁盘创建硬链接（权限问题），非本地磁盘请选择创建软链接。Windows 平台没有这个问题。</span></p></body></html>''')
        self.Ui.textBrowser_log_main_3.hide()   # 失败列表隐藏
        self.Ui.pushButton_scraper_failed_list.hide()
        self.Ui.pushButton_save_failed_list.hide()
        # self.Ui.textBrowser_log_main.document().setMaximumBlockCount(100000)     # 限制日志页最大行数rowCount
        # self.Ui.textBrowser_log_main_2.document().setMaximumBlockCount(30000)     # 限制日志页最大行数rowCount
        self.Ui.textBrowser_log_main.viewport().installEventFilter(self)            # 注册事件用于识别点击控件时隐藏失败列表面板
        self.Ui.textBrowser_log_main_2.viewport().installEventFilter(self)
        self.Ui.pushButton_save_failed_list.setIcon(QIcon(self.save_failed_list_icon))
        self.Ui.widget_show_success.resize(811, 511)
        self.Ui.widget_show_success.hide()
        self.Ui.widget_show_tips.resize(811, 511)
        self.Ui.widget_show_tips.hide()
        self.Ui.widget_nfo.resize(791, 681)
        self.Ui.widget_nfo.hide()

    # ======================================================================================初始化树状控件

    def init_QTreeWidget(self):
        try:
            self.set_label_file_path.emit('🎈 当前刮削路径: \n %s' % self.get_movie_path_setting()[0]) # 主界面右上角显示提示信息
        except:
            pass
        self.add_label_info('')
        self.count_claw = 0                                                     # 批量刮削次数
        if self.Ui.pushButton_start_cap.text() != '开始':
            self.count_claw = 1                                                 # 批量刮削次数
        else:
            self.label_result.emit(' 刮削中：0 成功：0 失败：0')
        self.Ui.treeWidget_number.clear()
        self.item_succ = QTreeWidgetItem(self.Ui.treeWidget_number)
        self.item_succ.setText(0, '成功')
        self.item_fail = QTreeWidgetItem(self.Ui.treeWidget_number)
        self.item_fail.setText(0, '失败')
        self.Ui.treeWidget_number.expandAll()                                   # 展开主界面树状内容

    # ======================================================================================设置按钮、鼠标点击、消息事件信号

    def Init_Singal(self):
        # 控件点击
        # self.Ui.treeWidget_number.clicked.connect(self.treeWidget_number_clicked)
        self.Ui.treeWidget_number.selectionModel().selectionChanged.connect(self.treeWidget_number_clicked)
        self.Ui.pushButton_close.clicked.connect(self.pushButton_close_clicked)
        self.Ui.pushButton_min.clicked.connect(self.pushButton_min_clicked)
        self.Ui.pushButton_main.clicked.connect(self.pushButton_main_clicked)
        self.Ui.pushButton_log.clicked.connect(self.pushButton_show_log_clicked)
        self.Ui.pushButton_net.clicked.connect(self.pushButton_show_net_clicked)
        self.Ui.pushButton_tool.clicked.connect(self.pushButton_tool_clicked)
        self.Ui.pushButton_setting.clicked.connect(self.pushButton_setting_clicked)
        self.Ui.pushButton_about.clicked.connect(self.pushButton_about_clicked)
        self.Ui.pushButton_select_local_library.clicked.connect(self.pushButton_select_local_library_clicked)
        self.Ui.pushButton_select_netdisk_path.clicked.connect(self.pushButton_select_netdisk_path_clicked)
        self.Ui.pushButton_select_localdisk_path.clicked.connect(self.pushButton_select_localdisk_path_clicked)
        self.Ui.pushButton_select_media_folder.clicked.connect(self.pushButton_select_media_folder_clicked)
        self.Ui.pushButton_select_media_folder_setting_page.clicked.connect(self.pushButton_select_media_folder_clicked)
        self.Ui.pushButton_select_softlink_folder.clicked.connect(self.pushButton_select_softlink_folder_clicked)
        self.Ui.pushButton_select_sucess_folder.clicked.connect(self.pushButton_select_sucess_folder_clicked)
        self.Ui.pushButton_select_failed_folder.clicked.connect(self.pushButton_select_failed_folder_clicked)
        self.Ui.pushButton_view_success_file.clicked.connect(self.show_success_list)
        self.Ui.pushButton_select_subtitle_folder.clicked.connect(self.pushButton_select_subtitle_folder_clicked)
        self.Ui.pushButton_select_actor_photo_folder.clicked.connect(self.pushButton_select_actor_photo_folder_clicked)
        self.Ui.pushButton_select_config_folder.clicked.connect(self.pushButton_select_config_folder_clicked)
        self.Ui.pushButton_select_file.clicked.connect(self.pushButton_select_file_clicked)
        self.Ui.pushButton_start_cap.clicked.connect(self.pushButton_start_cap_clicked)
        self.Ui.pushButton_start_cap2.clicked.connect(self.pushButton_start_cap_clicked)
        self.Ui.pushButton_show_hide_logs.clicked.connect(self.pushButton_show_hide_logs_clicked)
        self.Ui.pushButton_view_failed_list.clicked.connect(self.pushButton_show_hide_failed_list_clicked)
        self.Ui.pushButton_save_new_config.clicked.connect(self.pushButton_save_new_config_clicked)
        self.Ui.pushButton_save_config.clicked.connect(self.pushButton_save_config_clicked)
        self.Ui.pushButton_init_config.clicked.connect(self.pushButton_init_config_clicked)
        self.Ui.pushButton_move_mp4.clicked.connect(self.pushButton_move_mp4_clicked)
        self.Ui.pushButton_check_net.clicked.connect(self.pushButton_check_net_clicked)
        self.Ui.pushButton_check_javdb_cookie.clicked.connect(self.pushButton_check_javdb_cookie_clicked)
        self.Ui.pushButton_check_javbus_cookie.clicked.connect(self.pushButton_check_javbus_cookie_clicked)
        self.Ui.pushButton_check_and_clean_files.clicked.connect(self.pushButton_check_and_clean_files_clicked)
        self.Ui.pushButton_add_all_extras.clicked.connect(self.pushButton_add_all_extras_clicked)
        self.Ui.pushButton_del_all_extras.clicked.connect(self.pushButton_del_all_extras_clicked)
        self.Ui.pushButton_add_all_extrafanart_copy.clicked.connect(self.pushButton_add_all_extrafanart_copy_clicked)
        self.Ui.pushButton_del_all_extrafanart_copy.clicked.connect(self.pushButton_del_all_extrafanart_copy_clicked)
        self.Ui.pushButton_add_all_theme_videos.clicked.connect(self.pushButton_add_all_theme_videos_clicked)
        self.Ui.pushButton_del_all_theme_videos.clicked.connect(self.pushButton_del_all_theme_videos_clicked)
        self.Ui.pushButton_add_sub_for_all_video.clicked.connect(self.pushButton_add_sub_for_all_video_clicked)
        self.Ui.pushButton_add_actor_info.clicked.connect(self.pushButton_add_actor_info_clicked)
        self.Ui.pushButton_add_actor_pic.clicked.connect(self.pushButton_add_actor_pic_clicked)
        self.Ui.pushButton_add_actor_pic_kodi.clicked.connect(self.pushButton_add_actor_pic_kodi_clicked)
        self.Ui.pushButton_del_actor_folder.clicked.connect(self.pushButton_del_actor_folder_clicked)
        self.Ui.pushButton_show_pic_actor.clicked.connect(self.pushButton_show_pic_actor_clicked)
        self.Ui.pushButton_select_thumb.clicked.connect(self.pushButton_select_thumb_clicked)
        self.Ui.pushButton_find_missing_number.clicked.connect(self.pushButton_find_missing_number_clicked)
        self.Ui.pushButton_creat_symlink.clicked.connect(self.pushButton_creat_symlink_clicked)
        self.Ui.pushButton_start_single_file.clicked.connect(self.pushButton_start_single_file_clicked)
        self.Ui.pushButton_select_file_clear_info.clicked.connect(self.pushButton_select_file_clear_info_clicked)
        self.Ui.pushButton_scrape_note.clicked.connect(self.pushButton_scrape_note_clicked)
        self.Ui.pushButton_field_tips_website.clicked.connect(self.pushButton_field_tips_website_clicked)
        self.Ui.pushButton_field_tips_nfo.clicked.connect(self.pushButton_field_tips_nfo_clicked)
        self.Ui.pushButton_tips_normal_mode.clicked.connect(self.pushButton_tips_normal_mode_clicked)
        self.Ui.pushButton_tips_sort_mode.clicked.connect(self.pushButton_tips_sort_mode_clicked)
        self.Ui.pushButton_tips_update_mode.clicked.connect(self.pushButton_tips_update_mode_clicked)
        self.Ui.pushButton_tips_read_mode.clicked.connect(self.pushButton_tips_read_mode_clicked)
        self.Ui.pushButton_tips_soft.clicked.connect(self.pushButton_tips_soft_clicked)
        self.Ui.pushButton_tips_hard.clicked.connect(self.pushButton_tips_hard_clicked)
        self.Ui.checkBox_cover.stateChanged.connect(self.checkBox_cover_clicked)
        self.Ui.checkBox_i_agree_clean.stateChanged.connect(self.checkBox_i_agree_clean_clicked)
        self.Ui.checkBox_cd_part_a.stateChanged.connect(self.checkBox_cd_part_a_clicked)
        self.Ui.checkBox_i_understand_clean.stateChanged.connect(self.checkBox_i_agree_clean_clicked)
        self.Ui.horizontalSlider_timeout.valueChanged.connect(self.lcdNumber_timeout_change)
        self.Ui.horizontalSlider_retry.valueChanged.connect(self.lcdNumber_retry_change)
        self.Ui.horizontalSlider_mark_size.valueChanged.connect(self.lcdNumber_mark_size_change)
        self.Ui.horizontalSlider_thread.valueChanged.connect(self.lcdNumber_thread_change)
        self.Ui.horizontalSlider_javdb_time.valueChanged.connect(self.lcdNumber_javdb_time_change)
        self.Ui.horizontalSlider_thread_time.valueChanged.connect(self.lcdNumber_thread_time_change)
        self.Ui.comboBox_change_config.activated[str].connect(self.config_file_change)
        self.Ui.pushButton_right_menu.clicked.connect(self.main_open_right_menu)
        self.Ui.pushButton_play.clicked.connect(self.main_play_click)
        self.Ui.pushButton_open_folder.clicked.connect(self.main_open_folder_click)
        self.Ui.pushButton_open_nfo.clicked.connect(self.main_open_nfo_click)
        self.Ui.pushButton_tree_clear.clicked.connect(self.init_QTreeWidget)
        self.Ui.pushButton_scraper_failed_list.clicked.connect(self.pushButton_scraper_failed_list_clicked)
        self.Ui.pushButton_save_failed_list.clicked.connect(self.pushButton_save_failed_list_clicked)
        self.Ui.pushButton_success_list_close.clicked.connect(self.Ui.widget_show_success.hide)
        self.Ui.pushButton_success_list_save.clicked.connect(self.pushButton_success_list_save_clicked)
        self.Ui.pushButton_success_list_clear.clicked.connect(self.pushButton_success_list_clear_clicked)
        self.Ui.pushButton_show_tips_close.clicked.connect(self.Ui.widget_show_tips.hide)
        self.Ui.pushButton_nfo_close.clicked.connect(self.Ui.widget_nfo.hide)
        self.Ui.pushButton_nfo_save.clicked.connect(self.save_nfo_info)

        # 鼠标点击
        self.Ui.label_number.mousePressEvent = self.label_number_clicked
        self.Ui.label_source.mousePressEvent = self.label_number_clicked
        self.Ui.label_actor.mousePressEvent = self.label_actor_clicked
        self.Ui.label_show_version.mousePressEvent = self.label_version_clicked
        self.Ui.label_local_number.mousePressEvent = self.label_local_number_clicked
        self.Ui.label_download_actor_zip.mousePressEvent = self.download_actor_zip_clicked
        self.Ui.label_download_sub_zip.mousePressEvent = self.download_zip_clicked
        self.Ui.label_download_mark_zip.mousePressEvent = self.download_zip_clicked
        self.Ui.label_get_cookie_url.mousePressEvent = self.get_cookie_url_clicked

        # 控件更新
        self.main_logs_show.connect(self.Ui.textBrowser_log_main.append)
        self.main_logs_clear.connect(self.Ui.textBrowser_log_main.clear)
        self.req_logs_clear.connect(self.Ui.textBrowser_log_main_2.clear)
        self.main_req_logs_show.connect(self.Ui.textBrowser_log_main_2.append)
        self.logs_failed_show.connect(self.Ui.textBrowser_log_main_3.append)
        self.logs_failed_settext.connect(self.Ui.textBrowser_log_main_3.setText)
        self.net_logs_show.connect(self.Ui.textBrowser_net_main.append)
        self.set_javdb_cookie.connect(self.Ui.plainTextEdit_cookie_javdb.setPlainText)
        self.set_javbus_cookie.connect(self.Ui.plainTextEdit_cookie_javbus.setPlainText)
        self.set_javbus_status.connect(self.Ui.label_javbus_cookie_result.setText)
        self.set_tree_child.connect(self.addTreeChild)
        self.set_main_info.connect(self.add_label_info_Thread)
        self.progressBarValue.connect(self.set_processbar)
        self.set_pic_pixmap.connect(self.resize_label_and_setpixmap)
        self.set_pic_text.connect(self.Ui.label_poster_size.setText)
        self.change_to_mainpage.connect(self.change_mainpage)

        # 文本更新
        self.set_label_file_path.connect(self.Ui.label_file_path.setText)
        self.pushButton_start_cap.connect(self.Ui.pushButton_start_cap.setText)
        self.pushButton_start_cap2.connect(self.Ui.pushButton_start_cap2.setText)
        self.pushButton_start_single_file.connect(self.Ui.pushButton_start_single_file.setText)
        self.pushButton_add_sub_for_all_video.connect(self.Ui.pushButton_add_sub_for_all_video.setText)
        self.pushButton_show_pic_actor.connect(self.Ui.pushButton_show_pic_actor.setText)
        self.pushButton_add_actor_info.connect(self.Ui.pushButton_add_actor_info.setText)
        self.pushButton_add_actor_pic.connect(self.Ui.pushButton_add_actor_pic.setText)
        self.pushButton_add_actor_pic_kodi.connect(self.Ui.pushButton_add_actor_pic_kodi.setText)
        self.pushButton_del_actor_folder.connect(self.Ui.pushButton_del_actor_folder.setText)
        self.pushButton_check_and_clean_files.connect(self.Ui.pushButton_check_and_clean_files.setText)
        self.pushButton_move_mp4.connect(self.Ui.pushButton_move_mp4.setText)
        self.pushButton_find_missing_number.connect(self.Ui.pushButton_find_missing_number.setText)
        self.label_result.connect(self.Ui.label_result.setText)
        self.label_show_version.connect(self.Ui.label_show_version.setText)

    def tray_icon_click(self, e):
        if int(e) == 3:
            if self.is_windows:
                if self.isVisible():
                    self.hide()
                else:
                    self.activateWindow()
                    self.raise_()
                    self.show()

    def tray_icon_show(self):
        if int(self.windowState()) == 1:                                        # 最小化时恢复
            self.showNormal()
        self.recover_windowflags()                                              # 恢复焦点
        self.activateWindow()
        self.raise_()
        self.show()

    def Init_QSystemTrayIcon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(self.icon_ico))
        self.tray_icon.activated.connect(self.tray_icon_click)
        self.tray_icon.setToolTip(f'MDCx {self.localversion}（左键显示/隐藏 | 右键退出）')
        show_action = QAction(u"显示", self)
        hide_action = QAction(u"隐藏\tQ", self)
        quit_action = QAction(u"退出 MDCx", self)
        show_action.triggered.connect(self.tray_icon_show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(self.ready_to_exit)
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.showMessage(f"MDCx {self.localversion}", u'已启动！欢迎使用!', QIcon(self.icon_ico), 3000) # icon的值  0没有图标  1是提示  2是警告  3是错误

    def change_mainpage(self, t):
        self.pushButton_main_clicked()

    def creat_right_menu(self):
        self.menu_start = QAction(QIcon(self.start_icon), u'  开始刮削\tS', self)
        self.menu_stop = QAction(QIcon(self.stop_icon), u'  停止刮削\tS', self)
        self.menu_number = QAction(QIcon(self.input_number_icon), u'  重新刮削\tN', self)
        self.menu_website = QAction(QIcon(self.input_website_icon), u'  输入网址重新刮削\tU', self)
        self.menu_del_file = QAction(QIcon(self.del_file_icon), u'  删除文件\tD', self)
        self.menu_del_folder = QAction(QIcon(self.del_folder_icon), u'  删除文件和文件夹\tA', self)
        self.menu_folder = QAction(QIcon(self.open_folder_icon), u'  打开文件夹\tF', self)
        self.menu_nfo = QAction(QIcon(self.open_nfo_icon), u'  编辑 NFO\tE', self)
        self.menu_play = QAction(QIcon(self.play_icon), u'  播放\tP', self)
        self.menu_hide = QAction(QIcon(self.hide_boss_icon), u'  隐藏\tQ', self)

        self.menu_start.triggered.connect(self.pushButton_start_cap_clicked)
        self.menu_stop.triggered.connect(self.pushButton_start_cap_clicked)
        self.menu_number.triggered.connect(self.search_by_number_clicked)
        self.menu_website.triggered.connect(self.search_by_url_clicked)
        self.menu_del_file.triggered.connect(self.main_del_file_click)
        self.menu_del_folder.triggered.connect(self.main_del_folder_click)
        self.menu_folder.triggered.connect(self.main_open_folder_click)
        self.menu_nfo.triggered.connect(self.main_open_nfo_click)
        self.menu_play.triggered.connect(self.main_play_click)
        self.menu_hide.triggered.connect(self.hide)

        QShortcut(QKeySequence(self.tr("N")), self, self.search_by_number_clicked)
        QShortcut(QKeySequence(self.tr("U")), self, self.search_by_url_clicked)
        QShortcut(QKeySequence(self.tr("D")), self, self.main_del_file_click)
        QShortcut(QKeySequence(self.tr("A")), self, self.main_del_folder_click)
        QShortcut(QKeySequence(self.tr("F")), self, self.main_open_folder_click)
        QShortcut(QKeySequence(self.tr("E")), self, self.main_open_nfo_click)
        QShortcut(QKeySequence(self.tr("P")), self, self.main_play_click)
        QShortcut(QKeySequence(self.tr("S")), self, self.pushButton_start_cap_clicked)
        QShortcut(QKeySequence(self.tr("Q")), self, self.hide)
        # QShortcut(QKeySequence(self.tr("Esc")), self, self.hide)
        QShortcut(QKeySequence(self.tr("Ctrl+M")), self, self.pushButton_min_clicked2)
        QShortcut(QKeySequence(self.tr("Ctrl+W")), self, self.ready_to_exit)

        self.Ui.page_main.setContextMenuPolicy(Qt.CustomContextMenu)
        self.Ui.page_main.customContextMenuRequested.connect(self.menu)

    def menu(self, pos=''):
        if not pos:
            pos = self.Ui.pushButton_right_menu.pos() + QPoint(40, 10)
            # pos = QCursor().pos()
        menu = QMenu()
        if self.file_main_open_path:
            file_name = split_path(self.file_main_open_path)[1]
            menu.addAction(QAction(file_name, self))
            menu.addSeparator()
        else:
            menu.addAction(QAction('请刮削后使用！', self))
            menu.addSeparator()
            if self.Ui.pushButton_start_cap.text() != '开始':
                menu.addAction(self.menu_stop)
            else:
                menu.addAction(self.menu_start)
        menu.addAction(self.menu_number)
        menu.addAction(self.menu_website)
        menu.addSeparator()
        menu.addAction(self.menu_del_file)
        menu.addAction(self.menu_del_folder)
        menu.addSeparator()
        menu.addAction(self.menu_folder)
        menu.addAction(self.menu_nfo)
        menu.addAction(self.menu_play)
        menu.addAction(self.menu_hide)
        menu.exec_(self.Ui.page_main.mapToGlobal(pos))
        # menu.move(pos)
        # menu.show()

    def eventFilter(self, object, event):
        # print(event.type())

        if event.type() == 3:                                                   # 松开鼠标，检查是否在前台
            self.recover_windowflags()
        if event.type() == 121:
            if not self.isVisible():
                self.show()
        if object.objectName() == 'label_poster' or object.objectName() == 'label_thumb':
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.start_click_time = time.time()
                self.start_click_pos = event.globalPos()
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                if not (event.globalPos() - self.start_click_pos) or (time.time() - self.start_click_time < 0.05):
                    self.pic_main_clicked()
        if object is self.Ui.textBrowser_log_main.viewport() or object is self.Ui.textBrowser_log_main_2.viewport():
            if not self.Ui.textBrowser_log_main_3.isHidden() and event.type() == QEvent.MouseButtonPress:
                self.Ui.textBrowser_log_main_3.hide()
                self.Ui.pushButton_scraper_failed_list.hide()
                self.Ui.pushButton_save_failed_list.hide()
        return super().eventFilter(object, event)

    def showEvent(self, event):
        self.resize(1030, 700)                                                  # 调整窗口大小

    # 当隐藏边框时，最小化后，点击任务栏时，需要监听事件，在恢复窗口时隐藏边框
    def changeEvent(self, event):
        # self.show_traceback_log(QEvent.WindowStateChange)
        # WindowState （WindowNoState=0 正常窗口; WindowMinimized= 1 最小化; WindowMaximized= 2 最大化; WindowFullScreen= 3 全屏;WindowActive= 8 可编辑。）
        # windows平台无问题，仅mac平台python版有问题
        if not self.is_windows:
            if self.window_radius and event.type() == QEvent.WindowStateChange and not int(self.windowState()):
                self.setWindowFlag(Qt.FramelessWindowHint, True)                # 隐藏边框
                self.show()

        # activeAppName = AppKit.NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName'] # 活动窗口的标题

    def closeEvent(self, event):
        self.ready_to_exit()
        event.ignore()

    # 显示与隐藏窗口标题栏
    def windows_auto_adjust(self):
        if self.config.get('window_title') == 'hide':                           # 隐藏标题栏
            if self.window_radius == 0:
                self.show_flag = True
            self.window_radius = 5
            if self.is_windows:
                self.window_border = 1
            else:
                self.window_border = 0
            self.setWindowFlag(Qt.FramelessWindowHint, True)                    # 隐藏标题栏
            self.Ui.pushButton_close.setVisible(True)
            self.Ui.pushButton_min.setVisible(True)
            self.Ui.widget_buttons.move(0, 50)

        else:                                                                   # 显示标题栏
            if self.window_radius == 5:
                self.show_flag = True
            self.window_radius = 0
            self.window_border = 0
            self.window_marjin = 0
            self.setWindowFlag(Qt.FramelessWindowHint, False)                   # 显示标题栏
            self.Ui.pushButton_close.setVisible(False)
            self.Ui.pushButton_min.setVisible(False)
            self.Ui.widget_buttons.move(0, 20)

        if bool(self.dark_mode != self.Ui.checkBox_dark_mode.isChecked()):
            self.show_flag = True
            self.dark_mode = self.Ui.checkBox_dark_mode.isChecked()

        if self.show_flag:
            self.show_flag = False
            self.set_style()                                                    # 样式美化

            # self.setWindowState(Qt.WindowNoState)                               # 恢复正常窗口
            self.show()
            self.change_page()

    # ======================================================================================样式美化

    def set_style(self):
        if self.dark_mode:
            self.set_dark_style()
            return

        # 控件美化 左侧栏样式
        self.Ui.widget_setting.setStyleSheet(
            '''
            QWidget#widget_setting{
                background: #F5F5F6;
                border-top-left-radius: %spx;
                border-bottom-left-radius: %spx;
            }
            QPushButton#pushButton_main,#pushButton_log,#pushButton_tool,#pushButton_setting,#pushButton_net,#pushButton_about{
                font-size: 14px;
                color: black;
                border-width: 9px;
                border-color: gray;
                border-radius: 10px;
                text-align : left;
                qproperty-iconSize: 20px 20px;
                padding-left: 20px;
            }
            QLabel#label_show_version{
                font-size: 13px;
                color: rgba(20, 20, 20, 250);
                border: 0px solid rgba(255, 255, 255, 80);
            }
            ''' % (self.window_radius, self.window_radius)
        )
        # 主界面
        self.Ui.page_main.setStyleSheet(
            '''
            QLabel#label_number1,#label_actor1,#label_title1,#label_poster1,#label_number,#label_actor,#label_title,#label_poster1{
                font-size: 16px;
                font-weight: bold;
                background-color: rgba(246, 246, 246, 0);
                border: 0px solid rgba(0, 0, 0, 80);
            }
            QLabel#label_file_path{
                font-size: 16px;
                color: black;
                background-color: rgba(246, 246, 246, 0);
                font-weight: bold;
                border: 0px solid rgba(0, 0, 0, 80);
            }
            QLabel#label_poster_size{
                color: rgba(0, 0, 0, 200);
            }
            QLabel#label_poster,#label_thumb{
                border: 1px solid rgba(60, 60, 60, 100);
            }
            QGroupBox{
                background-color: rgba(246, 246, 246, 0);
            }
            ''')
        # 工具页
        self.Ui.page_tool.setStyleSheet(
            '''
            * {
                font-size: 13px;
            }
            QScrollArea{
                background-color: rgba(246, 246, 246, 0);
                border-color: rgba(246, 246, 246, 0);
            }
            QWidget#scrollAreaWidgetContents_9{
                background-color: rgba(246, 246, 246, 0);
                border-color: rgba(246, 246, 246, 255);
            }

            QLabel{
                font-size:13px;
                border: 0px solid rgba(0, 0, 0, 80);
            }
            QLineEdit{
                font-size:13px;
                border:0px solid rgba(130, 30, 30, 20);
                border-radius: 15px;
            }
            QComboBox{
                font-size: 13px;
                color: black;
            }
            QGroupBox{
                background-color: rgba(245,245,246,220);
                border-radius: 10px;
            }
            '''
        )
        # 使用帮助页
        self.Ui.page_about.setStyleSheet(
            '''
            * {
                font-size: 13px;
            }
            QTextBrowser{
                font-family: Consolas, 'PingFang SC', 'Microsoft YaHei UI', 'Noto Color Emoji', 'Segoe UI Emoji';
                font-size: 13px;
                border: 0px solid #BEBEBE;
                background-color: rgba(246,246,246,0);
                padding: 2px, 2px;
            }
            ''')
        # 设置页
        self.Ui.page_setting.setStyleSheet(
            '''
            * {
                font-size:13px;
            }
            QScrollArea{
                background-color: rgba(246, 246, 246, 0);
                border-color: rgba(246, 246, 246, 255);
            }
            QTabWidget{
                background-color: rgba(246, 246, 246, 0);
                border-color: rgba(246, 246, 246, 255);
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab{
                color: black;
                border:1px solid #E8E8E8;
                min-height: 3ex;
                min-width: 6ex;
                padding: 2px;
                background-color:#FFFFFF;
                border-radius: 1px;
            }
            QTabBar::tab:selected{
                color: white;
                font-weight:bold;
                border-bottom: 2px solid #2080F7;
                background-color:#2080F7;
                border-radius: 1px;
            }
            QWidget#tab1,#scrollAreaWidgetContents,#tab2,#scrollAreaWidgetContents_2,#tab3,#scrollAreaWidgetContents_3,#tab4,#scrollAreaWidgetContents_4,#tab5,#scrollAreaWidgetContents_5,#tab,#tab_2,#tab_3,#tab_4,#tab_5,#tab_6,#tab_7,#scrollAreaWidgetContents_6,#scrollAreaWidgetContents_7,#scrollAreaWidgetContents_8,#scrollAreaWidgetContents_10,#scrollAreaWidgetContents_11,#scrollAreaWidgetContents_12,#scrollAreaWidgetContents_13{
                background-color: rgba(255, 255, 255, 255);
                border-color: rgba(246, 246, 246, 255);
            }
            QLabel{
                font-size:13px;
                border:0px solid rgba(0, 0, 0, 80);
            }
            QLabel#label_config{
                font-size:13px;
                border:0px solid rgba(230, 230, 230, 80);
                background: rgba(246, 246, 246, 220);
            }

            QLineEdit{
                font-size:13px;
                border:0px solid rgba(130, 30, 30, 20);
                border-radius: 15px;
            }
            QRadioButton{
                font-size:13px;
            }
            QComboBox{
                font-size:13px;
            }
            QCheckBox{
                font-size:13px;
            }
            QPlainTextEdit{
                font-size:13px;
            }
            QGroupBox{
                background-color: rgba(245,245,246,220);
                border-radius: 10px;
            }
            '''
        )
        # 整个页面
        self.Ui.centralwidget.setStyleSheet(
            '''
            * {
                font-family: Consolas, 'PingFang SC', 'Microsoft YaHei UI', 'Noto Color Emoji', 'Segoe UI Emoji';
                font-size:13px;
                color: black;
            }
            QTreeWidget
            {
                background-color: rgba(246, 246, 246, 0);
                font-size: 12px;
                border:0px solid rgb(120,120,120);
            }
            QWidget#centralwidget{
                background: #FFFFFF;
                border: %spx solid rgba(20,20,20,50);
                border-radius: %spx;
           }
            QTextBrowser#textBrowser_log_main,#textBrowser_net_main{
                font-size:13px;
                border: 0px solid #BEBEBE;
                background-color: rgba(246,246,246,0);
                padding: 2px, 2px;
            }
            QTextBrowser#textBrowser_log_main_2{
                font-size:13px;
                border-radius: 0px;
                border-top: 1px solid #BEBEBE;
                background-color: rgba(238,245,245,60);
                padding: 2px, 2px;
            }
            QTextBrowser#textBrowser_log_main_3{
                font-size:13px;
                border-radius: 0px;
                border-right: 1px solid #EDEDED;
                background-color: rgba(239,255,252,240);
                padding: 2px, 2px;
            }
            QTextBrowser#textBrowser_show_success_list,#textBrowser_show_tips{
                font-size: 13px;
                background-color: rgba(240, 245, 240, 240);
                border: 1px solid #BEBEBE;
                padding: 2px;
            }
            QWidget#widget_show_success,#widget_show_tips,#widget_nfo{
                background-color: rgba(246,246,246,255);
                border: 1px solid rgba(20,20,20,50);
                border-radius: 10px;
           }
            QWidget#scrollAreaWidgetContents_nfo{
                background-color: rgba(240, 245, 240, 240);
                border: 0px solid rgba(0,0,0,150);
            }
            QLineEdit{
                font-size:14px;
                background:white;
                border-radius:10px;
                border: 1px solid rgba(20,20,20,200);
                padding: 2px;
            }
            QTextEdit#textEdit_nfo_outline,#textEdit_nfo_originalplot,#textEdit_nfo_tag{
                font-size:14px;
                background:white;
                border: 1px solid rgba(20,20,20,200);
                padding: 2px;
            }
            QToolTip{border: 1px solid;border-radius: 8px;border-color: gray;background:white;color:black;padding: 4px 8px;}
            QPushButton#pushButton_right_menu,#pushButton_play,#pushButton_open_folder,#pushButton_open_nfo,#pushButton_show_hide_logs,#pushButton_save_failed_list,#pushButton_tree_clear{
                background-color: rgba(181, 181, 181, 0);
                border-radius:10px;
                border: 0px solid rgba(0, 0, 0, 80);
            }
            QPushButton:hover#pushButton_right_menu,:hover#pushButton_play,:hover#pushButton_open_folder,:hover#pushButton_open_nfo,:hover#pushButton_show_hide_logs,:hover#pushButton_save_failed_list,:hover#pushButton_tree_clear{
                background-color: rgba(181, 181, 181, 120);
            }
            QPushButton:pressed#pushButton_right_menu,:pressed#pushButton_play,:pressed#pushButton_open_folder,:pressed#pushButton_open_nfo,:pressed#pushButton_show_hide_logs,:pressed#pushButton_save_failed_list,:pressed#pushButton_tree_clear{
                background-color: rgba(150, 150, 150, 120);
            }
            QPushButton#pushButton_save_new_config,#pushButton_init_config,#pushButton_success_list_close,#pushButton_success_list_save,#pushButton_success_list_clear,#pushButton_show_tips_close,#pushButton_nfo_close,#pushButton_nfo_save,#pushButton_show_pic_actor,#pushButton_add_actor_pic,#pushButton_add_actor_info,#pushButton_add_actor_pic_kodi,#pushButton_del_actor_folder,#pushButton_move_mp4,#pushButton_select_file,#pushButton_select_local_library,#pushButton_select_netdisk_path,#pushButton_select_localdisk_path,#pushButton_creat_symlink,#pushButton_find_missing_number,#pushButton_select_thumb,#pushButton_start_single_file,#pushButton_select_file_clear_info,#pushButton_add_sub_for_all_video,#pushButton_view_failed_list,#pushButton_select_media_folder,#pushButton_select_media_folder_setting_page,#pushButton_select_softlink_folder,#pushButton_select_sucess_folder,#pushButton_select_failed_folder,#pushButton_view_success_file,#pushButton_select_subtitle_folder,#pushButton_select_actor_photo_folder,#pushButton_select_config_folder,#pushButton_add_all_extrafanart_copy,#pushButton_del_all_extrafanart_copy,#pushButton_add_all_extras,#pushButton_del_all_extras,#pushButton_add_all_theme_videos,#pushButton_del_all_theme_videos,#pushButton_check_and_clean_files,#pushButton_search_by_number,#pushButton_search_by_url{
                font-size:14px;
                background-color: rgba(220, 220,220, 255);
                border-color:black;
                border-width:8px;
                border-radius:20px;
                padding: 2px, 2px;
            }
            QPushButton:hover#pushButton_show_pic_actor,:hover#pushButton_add_actor_pic,:hover#pushButton_add_actor_info,:hover#pushButton_add_actor_pic_kodi,:hover#pushButton_del_actor_folder,:hover#pushButton_add_sub_for_all_video,:hover#pushButton_view_failed_list,:hover#pushButton_select_media_folder,:hover#pushButton_select_media_folder_setting_page,:hover#pushButton_select_softlink_folder,:hover#pushButton_select_sucess_folder,:hover#pushButton_select_failed_folder,:hover#pushButton_view_success_file,:hover#pushButton_select_subtitle_folder,:hover#pushButton_select_actor_photo_folder,:hover#pushButton_select_config_folder,:hover#pushButton_add_all_extrafanart_copy,:hover#pushButton_del_all_extrafanart_copy,:hover#pushButton_add_all_extras,:hover#pushButton_del_all_extras,:hover#pushButton_add_all_theme_videos,:hover#pushButton_del_all_theme_videos,:hover#pushButton_check_and_clean_files,:hover#pushButton_search_by_number,:hover#pushButton_search_by_url{
                color: white;
                background-color: rgba(76,110,255,240);
                font-weight:bold;
            }
            QPushButton:pressed#pushButton_show_pic_actor,:pressed#pushButton_add_actor_pic,:pressed#pushButton_add_actor_info,:pressed#pushButton_add_actor_pic_kodi,:pressed#pushButton_del_actor_folder,:pressed#pushButton_add_sub_for_all_video,:pressed#pushButton_view_failed_list,:pressed#pushButton_select_media_folder,:pressed#pushButton_select_media_folder_setting_page,:pressed#pushButton_select_softlink_folder,:pressed#pushButton_select_sucess_folder,:pressed#pushButton_select_failed_folder,:pressed#pushButton_view_success_file,:pressed#pushButton_select_subtitle_folder,:pressed#pushButton_select_actor_photo_folder,:pressed#pushButton_select_config_folder,:pressed#pushButton_add_all_extrafanart_copy,:pressed#pushButton_del_all_extrafanart_copy,:pressed#pushButton_add_all_extras,:pressed#pushButton_del_all_extras,:pressed#pushButton_add_all_theme_videos,:pressed#pushButton_del_all_theme_videos,:pressed#pushButton_check_and_clean_files,:pressed#pushButton_search_by_number,:pressed#pushButton_search_by_url{
                background-color:#4C6EE0;
                border-color:black;
                border-width:14px;
                font-weight:bold;
            }
            QPushButton#pushButton_save_config{
                color: white;
                font-size:14px;
                background-color:#4C6EFF;
                border-radius:25px;
                padding: 2px, 2px;
            }
            QPushButton:hover#pushButton_save_config,:hover#pushButton_save_new_config,:hover#pushButton_init_config,:hover#pushButton_success_list_close,:hover#pushButton_success_list_save,:hover#pushButton_success_list_clear,:hover#pushButton_show_tips_close,:hover#pushButton_nfo_close,:hover#pushButton_nfo_save,:hover#pushButton_scraper_failed_list{
                color: white;
                background-color: rgba(76,110,255,240);
                font-weight:bold;
                }
            QPushButton:pressed#pushButton_save_config,:pressed#pushButton_save_new_config,:pressed#pushButton_init_config,:pressed#pushButton_success_list_close,:pressed#pushButton_success_list_save,:pressed#pushButton_success_list_clear,:pressed#pushButton_show_tips_close,:pressed#pushButton_nfo_close,:pressed#pushButton_nfo_save,:pressed#pushButton_scraper_failed_list{
                background-color:#4C6EE0;
                border-color:black;
                border-width:14px;
                font-weight:bold;
            }
            QPushButton#pushButton_start_cap,#pushButton_start_cap2,#pushButton_check_net,#pushButton_scraper_failed_list{
                color: white;
                font-size:14px;
                background-color:#4C6EFF;
                border-radius:20px;
                padding: 2px, 2px;
                font-weight:bold;
            }
            QPushButton:hover#pushButton_start_cap,:hover#pushButton_start_cap2,:hover#pushButton_check_net,:hover#pushButton_move_mp4,:hover#pushButton_select_file,:hover#pushButton_select_local_library,:hover#pushButton_select_netdisk_path,:hover#pushButton_select_localdisk_path,:hover#pushButton_creat_symlink,:hover#pushButton_find_missing_number,:hover#pushButton_select_thumb,:hover#pushButton_start_single_file,:hover#pushButton_select_file_clear_info{
                color: white;
                background-color: rgba(76,110,255,240);
                font-weight:bold;
                }
            QPushButton:pressed#pushButton_start_cap,:pressed#pushButton_start_cap2,:pressed#pushButton_check_net,:pressed#pushButton_move_mp4,:pressed#pushButton_select_file,:pressed#pushButton_select_local_library,:pressed#pushButton_select_netdisk_path,:pressed#pushButton_select_localdisk_path,:pressed#pushButton_creat_symlink,:pressed#pushButton_find_missing_number,:pressed#pushButton_select_thumb,:pressed#pushButton_start_single_file,:press#pushButton_select_file_clear_info{
                background-color:#4C6EE0;
                border-color:black;
                border-width:12px;
                font-weight:bold;
            }
            QProgressBar::chunk{
                background-color: #5777FF;
                width: 3px; /*区块宽度*/
                margin: 0px;
            }
            ''' % (self.window_border, self.window_radius)
        )

    def set_dark_style(self):
        # 控件美化 左侧栏样式 暗黑模式
        self.Ui.widget_setting.setStyleSheet(
            '''
            QWidget#widget_setting{
                background: #1F272F;
                border-top-left-radius: %spx;
                border-bottom-left-radius: %spx;
            }
            QPushButton#pushButton_main,#pushButton_log,#pushButton_tool,#pushButton_setting,#pushButton_net,#pushButton_about{
                font-size: 14px;
                color: white;
                border-width: 9px;
                border-color: gray;
                border-radius: 10px;
                text-align : left;
                qproperty-iconSize: 20px 20px;
                padding-left: 20px;
            }
            QLabel#label_show_version{
                font-size: 13px;
                color: rgba(210, 210, 210, 250);
                border: 0px solid rgba(255, 255, 255, 80);
            }
            ''' % (self.window_radius, self.window_radius)
        )
        # 主界面
        self.Ui.page_main.setStyleSheet(
            '''
            QLabel#label_number1,#label_actor1,#label_title1,#label_poster1,#label_number,#label_actor,#label_title,#label_poster1{
                font-size: 16px;
                font-weight: bold;
                background-color: rgba(246, 246, 246, 0);
                border: 0px solid rgba(0, 0, 0, 80);
            }
            QLabel#label_file_path{
                font-size: 16px;
                color: white;
                background-color: rgba(246, 246, 246, 0);
                font-weight: bold;
                border: 0px solid rgba(0, 0, 0, 80);
            }
            QLabel#label_poster_size{
                color: rgba(255, 255, 255, 200);
            }
            QLabel#label_poster,#label_thumb{
                border: 1px solid rgba(255, 255, 255, 200);
            }
            QGroupBox{
                background-color: rgba(246, 246, 246, 0);
            }
            ''')
        # 工具页
        self.Ui.page_tool.setStyleSheet(
            '''
            * {
                font-size: 13px;
            }
            QScrollArea{
                background-color: rgba(246, 246, 246, 0);
                border-color: rgba(246, 246, 246, 0);
            }
            QWidget#scrollAreaWidgetContents_9{
                background-color: rgba(246, 246, 246, 0);
                border-color: rgba(246, 246, 246, 255);
            }

            QLabel{
                font-size:13px;
                border: 0px solid rgba(0, 0, 0, 80);
            }

            QGroupBox{
                background-color: rgba(180, 180, 180, 20);
                border-radius: 10px;
            }
            '''
        )
        # 使用帮助页
        self.Ui.page_about.setStyleSheet(
            '''
            * {
                font-size: 13px;
            }
            QTextBrowser{
                font-family: Consolas, 'PingFang SC', 'Microsoft YaHei UI', 'Noto Color Emoji', 'Segoe UI Emoji';
                font-size: 13px;
                border: 0px solid #BEBEBE;
                background-color: rgba(246,246,246,0);
                padding: 2px, 2px;
            }
            ''')
        # 设置页
        self.Ui.page_setting.setStyleSheet(
            '''
            * {
                font-size:13px;
            }
            QScrollArea{
                background-color: rgba(246, 246, 246, 0);
                border-color: rgba(246, 246, 246, 0);
            }
            QTabWidget{
                background-color: rgba(246, 246, 246, 0);
                border-color: rgba(246, 246, 246, 0);
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab{
                border:1px solid #1F272F;
                min-height: 3ex;
                min-width: 6ex;
                padding: 2px;
                background-color:#242D37;
                border-radius: 2px;
            }
            QTabBar::tab:selected{
                font-weight:bold;
                border-bottom: 2px solid #2080F7;
                background-color:#2080F7;
                border-radius: 1px;
            }
            QWidget#tab1,#scrollAreaWidgetContents,#tab2,#scrollAreaWidgetContents_2,#tab3,#scrollAreaWidgetContents_3,#tab4,#scrollAreaWidgetContents_4,#tab5,#scrollAreaWidgetContents_5,#tab,#tab_2,#tab_3,#tab_4,#tab_5,#tab_6,#tab_7,#scrollAreaWidgetContents_6,#scrollAreaWidgetContents_7,#scrollAreaWidgetContents_8,#scrollAreaWidgetContents_10,#scrollAreaWidgetContents_11,#scrollAreaWidgetContents_12,#scrollAreaWidgetContents_13{
                background-color: #18222D;
                border-color: rgba(246, 246, 246, 0);
            }
            QLabel{
                font-size:13px;
                border:0px solid rgba(0, 0, 0, 80);
            }
            QLabel#label_config{
                font-size:13px;
                border:0px solid rgba(0, 0, 0, 80);
                background: rgba(31,39,47,230);
            }
            QLineEdit{
                font-size:13px;
                border:0px solid rgba(130, 30, 30, 20);
                border-radius: 15px;
            }
            QRadioButton{
                font-size:13px;
            }
            QCheckBox{
                font-size:13px;
            }
            QPlainTextEdit{
                font-size:13px;
                background:#18222D;
                border-radius: 4px;
            }
            QGroupBox{
                background-color: rgba(180, 180, 180, 20);
                border-radius: 10px;
            }
            QPushButton#pushButton_scrape_note,#pushButton_field_tips_website,#pushButton_field_tips_nfo,#pushButton_check_javdb_cookie{
                color: black;
            }
            '''
        )
        # 整个页面
        self.Ui.centralwidget.setStyleSheet(
            '''
            * {
                font-family: Consolas, 'PingFang SC', 'Microsoft YaHei UI', 'Noto Color Emoji', 'Segoe UI Emoji';
                font-size:13px;
                color: white;
            }
            QTreeWidget
            {
                background-color: rgba(246, 246, 246, 0);
                font-size: 12px;
                border:0px solid rgb(120,120,120);
            }
            QWidget#centralwidget{
                background: #18222D;
                border: %spx solid rgba(20,20,20,50);
                border-radius: %spx;
           }
            QTextBrowser#textBrowser_log_main,#textBrowser_net_main{
                font-size:13px;
                border: 0px solid #BEBEBE;
                background-color: rgba(246,246,246,0);
                padding: 2px, 2px;
            }
            QTextBrowser#textBrowser_log_main_2{
                font-size:13px;
                border-radius: 0px;
                border-top: 1px solid #BEBEBE;
                background-color: #18222D;
                padding: 2px, 2px;
            }
            QTextBrowser#textBrowser_log_main_3{
                font-size:13px;
                border-radius: 0px;
                border-right: 1px solid #20303F;
                background-color: #1F272F;
                padding: 2px, 2px;
            }
            QTextBrowser#textBrowser_show_success_list,#textBrowser_show_tips{
                font-size: 13px;
                border: 1px solid #BEBEBE;
                background-color: #18222D;
                padding: 2px;
            }
            QWidget#widget_show_success,#widget_show_tips,#widget_nfo{
                background-color: #1F272F;
                border: 1px solid rgba(240,240,240,150);
                border-radius: 10px;
           }
            QWidget#scrollAreaWidgetContents_nfo{
                background-color: #18222D;
                border: 0px solid rgba(0,0,0,150);
            }
            QLineEdit{
                font-size:13px;
                background:#18222D;
                border-radius:20px;
                border: 1px solid rgba(240,240,240,200);
                padding: 2px;
            }
            QTextEdit#textEdit_nfo_outline,#textEdit_nfo_originalplot,#textEdit_nfo_tag{
                font-size:13px;
                background:#18222D;
                border: 1px solid rgba(240,240,240,200);
                padding: 2px;
            }
            QToolTip{border: 1px solid;border-radius: 8px;border-color: gray;background:white;color:black;padding: 4px 8px;}
            QPushButton#pushButton_right_menu,#pushButton_play,#pushButton_open_folder,#pushButton_open_nfo,#pushButton_show_hide_logs,#pushButton_save_failed_list,#pushButton_tree_clear{
                background-color: rgba(181, 181, 181, 0);
                border-radius:10px;
                border: 0px solid rgba(0, 0, 0, 80);
            }
            QPushButton:hover#pushButton_right_menu,:hover#pushButton_play,:hover#pushButton_open_folder,:hover#pushButton_open_nfo,:hover#pushButton_show_hide_logs,:hover#pushButton_save_failed_list,:hover#pushButton_tree_clear{
                background-color: rgba(181, 181, 181, 120);
            }
            QPushButton:pressed#pushButton_right_menu,:pressed#pushButton_play,:pressed#pushButton_open_folder,:pressed#pushButton_open_nfo,:pressed#pushButton_show_hide_logs,:pressed#pushButton_save_failed_list,:pressed#pushButton_tree_clear{
                background-color: rgba(150, 150, 150, 120);
            }
            QPushButton#pushButton_save_new_config,#pushButton_init_config,#pushButton_success_list_close,#pushButton_success_list_save,#pushButton_success_list_clear,#pushButton_show_tips_close,#pushButton_nfo_close,#pushButton_nfo_save,#pushButton_show_pic_actor,#pushButton_add_actor_pic,#pushButton_add_actor_info,#pushButton_add_actor_pic_kodi,#pushButton_del_actor_folder,#pushButton_move_mp4,#pushButton_select_file,#pushButton_select_local_library,#pushButton_select_netdisk_path,#pushButton_select_localdisk_path,#pushButton_creat_symlink,#pushButton_find_missing_number,#pushButton_select_thumb,#pushButton_start_single_file,#pushButton_select_file_clear_info,#pushButton_add_sub_for_all_video,#pushButton_view_failed_list,#pushButton_select_media_folder,#pushButton_select_media_folder_setting_page,#pushButton_select_softlink_folder,#pushButton_select_sucess_folder,#pushButton_select_failed_folder,#pushButton_view_success_file,#pushButton_select_subtitle_folder,#pushButton_select_actor_photo_folder,#pushButton_select_config_folder,#pushButton_add_all_extrafanart_copy,#pushButton_del_all_extrafanart_copy,#pushButton_add_all_extras,#pushButton_del_all_extras,#pushButton_add_all_theme_videos,#pushButton_del_all_theme_videos,#pushButton_check_and_clean_files,#pushButton_search_by_number,#pushButton_search_by_url{
                font-size:14px;
                background-color: rgba(220, 220,220, 50);
                border-color:black;
                border-width:8px;
                border-radius:20px;
                padding: 2px, 2px;
            }
            QPushButton:hover#pushButton_show_pic_actor,:hover#pushButton_add_actor_pic,:hover#pushButton_add_actor_info,:hover#pushButton_add_actor_pic_kodi,:hover#pushButton_del_actor_folder,:hover#pushButton_add_sub_for_all_video,:hover#pushButton_view_failed_list,:hover#pushButton_scraper_failed_list,:hover#pushButton_select_media_folder,:hover#pushButton_select_media_folder_setting_page,:hover#pushButton_select_softlink_folder,:hover#pushButton_select_sucess_folder,:hover#pushButton_select_failed_folder,:hover#pushButton_view_success_file,:hover#pushButton_select_subtitle_folder,:hover#pushButton_select_actor_photo_folder,:hover#pushButton_select_config_folder,:hover#pushButton_add_all_extrafanart_copy,:hover#pushButton_del_all_extrafanart_copy,:hover#pushButton_add_all_extras,:hover#pushButton_del_all_extras,:hover#pushButton_add_all_theme_videos,:hover#pushButton_del_all_theme_videos,:hover#pushButton_check_and_clean_files,:hover#pushButton_search_by_number,:hover#pushButton_search_by_url{
                color: white;
                background-color: rgba(76,110,255,240);
                font-weight:bold;
            }
            QPushButton:pressed#pushButton_show_pic_actor,:pressed#pushButton_add_actor_pic,:pressed#pushButton_add_actor_info,:pressed#pushButton_add_actor_pic_kodi,:pressed#pushButton_del_actor_folder,:pressed#pushButton_add_sub_for_all_video,:pressed#pushButton_view_failed_list,:pressed#pushButton_scraper_failed_list,:pressed#pushButton_select_media_folder,:pressed#pushButton_select_media_folder_setting_page,:pressed#pushButton_select_softlink_folder,:pressed#pushButton_select_sucess_folder,:pressed#pushButton_select_failed_folder,:pressed#pushButton_view_success_file,:pressed#pushButton_select_subtitle_folder,:pressed#pushButton_select_actor_photo_folder,:pressed#pushButton_select_config_folder,:pressed#pushButton_add_all_extrafanart_copy,:pressed#pushButton_del_all_extrafanart_copy,:pressed#pushButton_add_all_extras,:pressed#pushButton_del_all_extras,:pressed#pushButton_add_all_theme_videos,:pressed#pushButton_del_all_theme_videos,:pressed#pushButton_check_and_clean_files,:pressed#pushButton_search_by_number,:pressed#pushButton_search_by_url{
                background-color:#4C6EE0;
                border-color:black;
                border-width:14px;
                font-weight:bold;
            }
            QPushButton#pushButton_save_config{
                color: white;
                font-size:14px;
                background-color:#4C6EFF;
                border-radius:25px;
                padding: 2px, 2px;
            }
            QPushButton:hover#pushButton_save_config,:hover#pushButton_save_new_config,:hover#pushButton_init_config,:hover#pushButton_success_list_close,:hover#pushButton_success_list_save,:hover#pushButton_success_list_clear,:hover#pushButton_show_tips_close,:hover#pushButton_nfo_close,:hover#pushButton_nfo_save{
                color: white;
                background-color: rgba(76,110,255,240);
                font-weight:bold;
            }
            QPushButton:pressed#pushButton_save_config,:pressed#pushButton_save_new_config,:pressed#pushButton_init_config,:pressed#pushButton_success_list_close,:pressed#pushButton_success_list_save,:pressed#pushButton_success_list_clear,pressed#pushButton_show_tips_close,:pressed#pushButton_nfo_close,:pressed#pushButton_nfo_save{
                background-color:#4C6EE0;
                border-color:black;
                border-width:14px;
                font-weight:bold;
            }
            QPushButton#pushButton_start_cap,#pushButton_start_cap2,#pushButton_check_net,#pushButton_scraper_failed_list{
                color: white;
                font-size:14px;
                background-color:#4C6EFF;
                border-radius:20px;
                padding: 2px, 2px;
                font-weight:bold;
            }
            QPushButton:hover#pushButton_start_cap,:hover#pushButton_start_cap2,:hover#pushButton_check_net,:hover#pushButton_move_mp4,:hover#pushButton_select_file,:hover#pushButton_select_local_library,:hover#pushButton_select_netdisk_path,:hover#pushButton_select_localdisk_path,:hover#pushButton_creat_symlink,:hover#pushButton_find_missing_number,:hover#pushButton_select_thumb,:hover#pushButton_start_single_file,:hover#pushButton_select_file_clear_info{
                color: white;
                background-color: rgba(76,110,255,240);
                font-weight:bold;
                }
            QPushButton:pressed#pushButton_start_cap,:pressed#pushButton_start_cap2,:pressed#pushButton_check_net,:pressed#pushButton_move_mp4,:pressed#pushButton_select_file,:pressed#pushButton_select_local_library,:pressed#pushButton_select_netdisk_path,:pressed#pushButton_select_localdisk_path,:pressed#pushButton_creat_symlink,:pressed#pushButton_find_missing_number,:pressed#pushButton_select_thumb,:pressed#pushButton_start_single_file,:press#pushButton_select_file_clear_info{
                background-color:#4C6EE0;
                border-color:black;
                border-width:12px;
                font-weight:bold;
            }
            QComboBox{
                font-size:13px;
                color: white;
                background:#18222D;
                border-radius: 15px;
            }
            QComboBox::drop-down:!editable {
                subcontrol-position: right;
                margin: 10px;
                height: 10px;
                width: 10px;
                border-radius: 5px;
                background: lightgreen;
            }
            QComboBox::drop-down:!editable:on {
                background: lightgreen;
            }

            QComboBox QAbstractItemView {
                color:white;
                background: #1F272F;
                selection-color:white;
                selection-background-color: #18222D;
            }
            QScrollBar:vertical{
                border-radius:2px;
                background:#242D37;
                padding-top:16px;
                padding-bottom:16px
            }
            QScrollBar::handle:vertical{
                border-radius:2px;
                background:#484F57;
            }
            QScrollBar::add-page:vertical{
                background:#242D37;
            }
            QScrollBar::sub-page:vertical{
                border-radius:2px;
                background:#242D37;
            }
            QProgressBar::chunk{
                background-color: #5777FF;
                width: 3px; /*区块宽度*/
                margin: 0px;
            }
            ''' % (self.window_border, self.window_radius)
        )

    # ======================================================================================获取各种路径
    # 主程序路径
    def get_main_path(self):
        try:
            main_path = os.path.split(os.path.realpath(__file__))[0]            # 取的是__file__所在文件xx.py的所在目录
        except Exception as e:
            self.show_traceback_log('get_main_path ERROR: ' + str(e) + traceback.format_exc())
            main_path = os.path.abspath(sys.path[0])

            # 或sys.argv[0],取的是被初始执行的脚本的所在目录，打包后路径会变成\base_libarary.zip
            # base_path = os.path.abspath(".") 取的是起始执行目录，和os.getcwd()结果一样，不太准
        if getattr(sys, 'frozen', False):                                       # 是否Bundle Resource，是否打包成exe运行
            main_path = os.path.abspath(".")                                    # 打包后，路径是准的
        return main_path

    # 资源文件路径
    def resource_path(self, relative_path):
        base_path = self.main_path
        if os.path.exists(os.path.join(base_path, relative_path)):
            pass
        elif getattr(sys, 'frozen', False):                                     # 是否Bundle Resource，是否打包成exe运行
            try:
                base_path = sys._MEIPASS
            except:
                self.show_traceback_log(base_path)
                self.show_traceback_log(relative_path)
                self.show_traceback_log(traceback.format_exc())
                print(base_path, relative_path, traceback.format_exc())
        return os.path.join(base_path, relative_path).replace('\\', '/')

    # 数据资源文件路径
    def update_userdata_path(self):
        userdata_folder = os.path.join(self.config_folder, 'userdata')
        self.userdata_folder = userdata_folder
        if not os.path.isdir(userdata_folder):
            os.makedirs(userdata_folder)
        self.actor_map_local_path = os.path.join(userdata_folder, 'mapping_actor.xml')
        self.info_map_local_path = os.path.join(userdata_folder, 'mapping_info.xml')
        self.local_number_list_path = os.path.join(userdata_folder, 'number_list.json')
        self.gfriends_json_path = os.path.join(userdata_folder, 'gfriends.json')
        self.remain_list_path = os.path.join(userdata_folder, 'remain.txt')
        self.success_list_path = os.path.join(userdata_folder, 'success.txt')

    # 水印图片资源文件路径
    def update_mark_icon_path(self):
        mark_4k = self.resource_path('Img/4k.png')
        mark_8k = self.resource_path('Img/8k.png')
        mark_sub = self.resource_path('Img/sub.png')
        mark_youma = self.resource_path('Img/youma.png')
        mark_umr = self.resource_path('Img/umr.png')
        mark_leak = self.resource_path('Img/leak.png')
        mark_wuma = self.resource_path('Img/wuma.png')
        mark_folder = os.path.join(self.userdata_folder, 'watermark')
        self.icon_4k_path = os.path.join(mark_folder, '4k.png')
        self.icon_8k_path = os.path.join(mark_folder, '8k.png')
        self.icon_sub_path = os.path.join(mark_folder, 'sub.png')
        self.icon_youma_path = os.path.join(mark_folder, 'youma.png')
        self.icon_umr_path = os.path.join(mark_folder, 'umr.png')
        self.icon_leak_path = os.path.join(mark_folder, 'leak.png')
        self.icon_wuma_path = os.path.join(mark_folder, 'wuma.png')
        if not os.path.isdir(mark_folder):
            os.makedirs(mark_folder)
        if not os.path.isfile(self.icon_4k_path):
            copy_file(mark_4k, self.icon_4k_path)
        if not os.path.isfile(self.icon_8k_path):
            copy_file(mark_8k, self.icon_8k_path)
        if not os.path.isfile(self.icon_sub_path):
            copy_file(mark_sub, self.icon_sub_path)
        if not os.path.isfile(self.icon_youma_path):
            copy_file(mark_youma, self.icon_youma_path)
        if not os.path.isfile(self.icon_umr_path):
            copy_file(mark_umr, self.icon_umr_path)
        if not os.path.isfile(self.icon_leak_path):
            copy_file(mark_leak, self.icon_leak_path)
        if not os.path.isfile(self.icon_wuma_path):
            copy_file(mark_wuma, self.icon_wuma_path)

    # 根据平台转换路径
    def convert_path(self, path):
        if self.is_windows:
            path = path.replace('/', '\\')
        else:
            path = path.replace('\\', '/')
        return path

    # 加载字体
    def get_fonts(self):
        fontDb = QFontDatabase()
        if getattr(sys, 'frozen', False):                                       # 是否Bundle Resource，是否打包成exe运行
            font_folder_path = self.resource_path('fonts')
        else:
            font_folder_path = self.resource_path('Data/fonts')
        for f in os.listdir(font_folder_path):
            fontDb.addApplicationFont(os.path.join(font_folder_path, f))  # 字体路径

    # c_number.json位置
    def get_c_number_path(self):
        if getattr(sys, 'frozen', False):                                       # 是否Bundle Resource，是否打包成exe运行
            c_number_path = 'c_number/c_number.json'
        else:
            c_number_path = 'Data/c_number/c_number.json'
        return c_number_path

    # mapping_info.xml位置
    def get_info_path(self):
        if getattr(sys, 'frozen', False):                                       # 是否Bundle Resource，是否打包成exe运行
            info_path = 'mapping_table/mapping_info.xml'
        else:
            info_path = 'Data/mapping_table/mapping_info.xml'
        return info_path

    # mapping_actor.xml位置
    def get_actor_path(self):
        if getattr(sys, 'frozen', False):                                       # 是否Bundle Resource，是否打包成exe运行
            actor_path = 'mapping_table/mapping_actor.xml'
        else:
            actor_path = 'Data/mapping_table/mapping_actor.xml'
        return actor_path

    # ======================================================================================显示版本号

    def check_version(self):
        latest_version = 0
        res = ''
        if self.config.get('update_check') == 'on':
            url = 'https://api.github.com/repos/anyabc/something/releases/latest'
            result, res = get_html(url)
            if result:

                # 显示版本信息
                if self.is_windows:
                    latest_version = re.findall(r'-win-(\d+)', res)
                elif self.is_mac:
                    latest_version = re.findall(r'-mac-(\d+)', res)
                else:
                    latest_version = re.findall(r'-py-(\d+)', res)
                latest_version = latest_version[0] if latest_version else 1
                if int(self.localversion) < int(latest_version):
                    self.new_version = f'\n🍉 有新版本了！（{latest_version}）'
                    self.show_scrape_info()
                    self.Ui.label_show_version.setCursor(Qt.OpenHandCursor)  # 设置鼠标形状为十字形
        return latest_version, res

    def show_version(self):
        try:
            t = threading.Thread(target=self.show_version_thread)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())

    def show_version_thread(self):
        version_info = f'基于 MDC-GUI 修改 当前版本: {self.localversion}'
        feedback_email = ''
        download_link = ''
        latest_version, res = self.check_version()
        if latest_version:
            if int(self.localversion) < int(latest_version):
                version_info = f'基于 MDC-GUI 修改 · 当前版本: {self.localversion} （ <font color=\"red\" >最新版本是: {latest_version}，请及时更新！🚀 </font>）'
            else:
                version_info = f'基于 MDC-GUI 修改 · 当前版本: {self.localversion} （ <font color=\"green\">你使用的是最新版本！🎉 </font>）'

            if '@gmail.com' in res:
                feedback_email = f' 💌 <a href="mailto:anyabcx@gmail.com?subject=Feedback&body=\n\nVersion: {self.localversion}\nSystem: {platform.platform()}">问题反馈</a>: anyabcx@gmail.com'
            if '-py-' in res:
                download_link = ' ⬇️ <a href="https://github.com/anyabc/something/releases">下载新版本</a>'

        # 显示版本信息和反馈入口
        self.show_log_text(version_info)
        if feedback_email or download_link:
            self.main_logs_show.emit(f'{feedback_email}{download_link}')
        self.show_log_text('================================================================================')
        self.pushButton_check_javdb_cookie_clicked()                            # 检测javdb cookie
        self.pushButton_check_javbus_cookie_clicked()                           # 检测javbus cookie
        self.check_theporndb_api_token_thread()                                 # 检查 theporndb api token

    # ======================================================================================各种点击跳转浏览器
    # 主界面点番号或数据来源
    def label_number_clicked(self, test):
        try:
            if self.label_number_url:
                javdb_website = self.config.get('javdb_website')
                if javdb_website:
                    self.label_number_url = self.label_number_url.replace('https://javdb.com', javdb_website)
                webbrowser.open(self.label_number_url)
        except:
            self.show_traceback_log(traceback.format_exc())

    # 主界面点演员名
    def label_actor_clicked(self, test):
        try:
            if self.label_actor_url:
                javdb_website = self.config.get('javdb_website')
                if javdb_website:
                    self.label_actor_url = self.label_actor_url.replace('https://javdb.com', javdb_website)
                webbrowser.open(self.label_actor_url)
        except:
            self.show_traceback_log(traceback.format_exc())

    # 主界面点演员名
    def label_version_clicked(self, test):
        try:
            if self.new_version:
                webbrowser.open('https://github.com/anyabc/something/releases')
        except:
            self.show_traceback_log(traceback.format_exc())

    # 主界面打开文件
    def open_file(self, file_path, is_dir=False):
        file_path = self.convert_path(file_path)

        # mac需要改为无焦点状态，不然弹窗失去焦点后，再切换回来会有找不到焦点的问题（windows无此问题）
        # if not self.is_windows:
        #     self.setWindowFlags(self.windowFlags() | Qt.WindowDoesNotAcceptFocus)
        #     self.show()

        # 启动线程打开文件
        t = threading.Thread(target=self.open_file_thread, args=(file_path, is_dir))
        t.start()

    def open_file_thread(self, file_path, is_dir):
        if self.is_windows:
            if is_dir:
                # os.system(f'explorer /select,"{file_path}"')  pyinstall打包后打开文件时会闪现cmd窗口。
                # file_path路径必须转换为windows样式，并且加上引号（不加引号，文件名过长会截断）。select,后面不能有空格！！！
                subprocess.Popen(f'explorer /select,"{file_path}"')
            else:
                subprocess.Popen(f'explorer "{file_path}"')
        elif self.is_mac:
            if is_dir:
                if os.path.islink(file_path):
                    file_path = split_path(file_path)[0]
                subprocess.Popen(['open', '-R', file_path])
            else:
                subprocess.Popen(['open', file_path])
        else:
            if is_dir:
                if os.path.islink(file_path):
                    file_path = split_path(file_path)[0]
                try:
                    subprocess.Popen(['dolphin', '--select', file_path])
                except:
                    subprocess.Popen(['xdg-open', '-R', file_path])
            else:
                subprocess.Popen(['xdg-open', file_path])

    # 改回接受焦点状态
    def recover_windowflags(self):
        return
        if not self.is_windows and not self.window().isActiveWindow(): # 不在前台，有点击事件，即切换回前台
            if (self.windowFlags() | Qt.WindowDoesNotAcceptFocus) == self.windowFlags():
                self.setWindowFlags(self.windowFlags() & ~Qt.WindowDoesNotAcceptFocus)
                self.show()

    # ======================================================================================显示右键菜单

    def check_main_file_path(self):
        if not self.file_main_open_path:
            QMessageBox.about(self, '没有目标文件', '请刮削后再使用！！')
            self.show_scrape_info('💡 请刮削后使用！%s' % self.get_current_time())
            return False
        return True

    # 主界面点播放
    def main_play_click(self):
        # 发送hover事件，清除hover状态（因为弹窗后，失去焦点，状态不会变化）
        self.Ui.pushButton_play.setAttribute(Qt.WA_UnderMouse, False)
        event = QHoverEvent(QEvent.HoverLeave, QPoint(40, 40), QPoint(0, 0))
        QApplication.sendEvent(self.Ui.pushButton_play, event)
        if self.check_main_file_path():
            self.open_file(self.file_main_open_path)

    # 主界面点打开文件夹
    def main_open_folder_click(self):
        self.Ui.pushButton_open_folder.setAttribute(Qt.WA_UnderMouse, False)
        event = QHoverEvent(QEvent.HoverLeave, QPoint(40, 40), QPoint(0, 0))
        QApplication.sendEvent(self.Ui.pushButton_open_folder, event)
        if self.check_main_file_path():
            self.open_file(self.file_main_open_path, True)

    # 主界面点打开nfo
    def main_open_nfo_click(self):
        self.Ui.pushButton_open_nfo.setAttribute(Qt.WA_UnderMouse, False)
        event = QHoverEvent(QEvent.HoverLeave, QPoint(40, 40), QPoint(0, 0))
        QApplication.sendEvent(self.Ui.pushButton_open_nfo, event)
        if self.check_main_file_path():
            self.Ui.widget_nfo.show()
            self.show_nfo_info()

    # 主界面点打开右键菜单
    def main_open_right_menu(self):
        # 发送hover事件，清除hover状态（因为弹窗后，失去焦点，状态不会变化）
        self.Ui.pushButton_right_menu.setAttribute(Qt.WA_UnderMouse, False)
        event = QHoverEvent(QEvent.HoverLeave, QPoint(40, 40), QPoint(0, 0))
        QApplication.sendEvent(self.Ui.pushButton_right_menu, event)
        self.menu()

    # 主界面点输入番号
    def search_by_number_clicked(self):
        if self.check_main_file_path():
            file_path = self.file_main_open_path
            main_file_name = split_path(file_path)[1]
            default_text = os.path.splitext(main_file_name)[0].upper()
            text, ok = QInputDialog.getText(self, '输入番号重新刮削', f'文件名: {main_file_name}\n请输入番号:', text=default_text)
            if ok and text:
                self.again_dic[file_path] = [text, '', '']
                self.show_scrape_info('💡 已添加刮削！%s' % self.get_current_time())
                if self.Ui.pushButton_start_cap.text() == '开始':
                    self.again_search()

    # 主界面点输入网址
    def search_by_url_clicked(self):
        if self.check_main_file_path():
            file_path = self.file_main_open_path
            main_file_name = split_path(file_path)[1]
            text, ok = QInputDialog.getText(self, '输入网址重新刮削', f'文件名: {main_file_name}\n支持网站:airav_cc、airav、avsex、avsox、dmm、getchu、fc2、fc2club、fc2hub、iqqtv、jav321、javbus、javdb、freejavbt、javlibrary、mdtv、madouqu、mgstage、7mmtv、xcity、mywife、giga、faleno、dahlia、fantastica、prestige、hdouban、lulubar、love6、cnmdb、theporndb、kin8\n请输入番号对应的网址（不是网站首页地址！！！是番号页面地址！！！）:')
            if ok and text:
                website, url = self.deal_url(text)
                if website:
                    self.again_dic[file_path] = ['', url, website]
                    self.show_scrape_info('💡 已添加刮削！%s' % self.get_current_time())
                    if self.Ui.pushButton_start_cap.text() == '开始':
                        self.again_search()
                else:
                    self.show_scrape_info('💡 不支持的网站！%s' % self.get_current_time())

    # 主界面点删除文件
    def main_del_file_click(self):
        if self.check_main_file_path():
            file_path = self.file_main_open_path
            box = QMessageBox(QMessageBox.Warning, '删除文件', f'将要删除文件: \n{file_path}\n\n 你确定要删除吗？')
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.button(QMessageBox.Yes).setText('删除文件')
            box.button(QMessageBox.No).setText('取消')
            box.setDefaultButton(QMessageBox.No)
            reply = box.exec()
            if reply != QMessageBox.Yes:
                return
            delete_file(file_path)
            self.show_scrape_info('💡 已删除文件！%s' % self.get_current_time())

    # 主界面点删除文件夹
    def main_del_folder_click(self):
        if self.check_main_file_path():
            folder_path = split_path(self.file_main_open_path)[0]
            box = QMessageBox(QMessageBox.Warning, '删除文件', f'将要删除文件夹: \n{folder_path}\n\n 你确定要删除吗？')
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.button(QMessageBox.Yes).setText('删除文件和文件夹')
            box.button(QMessageBox.No).setText('取消')
            box.setDefaultButton(QMessageBox.No)
            reply = box.exec()
            if reply != QMessageBox.Yes:
                return
            shutil.rmtree(folder_path, ignore_errors=True)
            self.show_scrape_info('💡 已删除文件夹！%s' % self.get_current_time())

    # 主界面点图片
    def pic_main_clicked(self):
        newWin2.showimage(self.img_path, self.json_data)
        newWin2.show()

    # 日志页点展开折叠日志
    def pushButton_show_hide_logs_clicked(self):
        if self.Ui.textBrowser_log_main_2.isHidden():
            self.show_hide_logs(True)
        else:
            self.show_hide_logs(False)

    # 日志页点展开折叠日志
    def show_hide_logs(self, show):
        if show:
            self.Ui.pushButton_show_hide_logs.setIcon(QIcon(self.hide_logs_icon))
            self.Ui.textBrowser_log_main_2.show()
            self.Ui.textBrowser_log_main.resize(790, 418)
            self.Ui.textBrowser_log_main.verticalScrollBar().setValue(self.Ui.textBrowser_log_main.verticalScrollBar().maximum())
            self.Ui.textBrowser_log_main_2.verticalScrollBar().setValue(self.Ui.textBrowser_log_main_2.verticalScrollBar().maximum())

            # self.Ui.textBrowser_log_main_2.moveCursor(self.Ui.textBrowser_log_main_2.textCursor().End)

        else:
            self.Ui.pushButton_show_hide_logs.setIcon(QIcon(self.show_logs_icon))
            self.Ui.textBrowser_log_main_2.hide()
            self.Ui.textBrowser_log_main.resize(790, 689)
            self.Ui.textBrowser_log_main.verticalScrollBar().setValue(self.Ui.textBrowser_log_main.verticalScrollBar().maximum())

    # 日志页点展开折叠失败列表
    def pushButton_show_hide_failed_list_clicked(self):
        if self.Ui.textBrowser_log_main_3.isHidden():
            self.show_hide_failed_list(True)
        else:
            self.show_hide_failed_list(False)

    # 日志页点展开折叠失败列表
    def show_hide_failed_list(self, show):
        if show:
            self.Ui.textBrowser_log_main_3.show()
            self.Ui.pushButton_scraper_failed_list.show()
            self.Ui.pushButton_save_failed_list.show()
            self.Ui.textBrowser_log_main_3.verticalScrollBar().setValue(self.Ui.textBrowser_log_main_3.verticalScrollBar().maximum())

        else:
            self.Ui.pushButton_save_failed_list.hide()
            self.Ui.textBrowser_log_main_3.hide()
            self.Ui.pushButton_scraper_failed_list.hide()

    # 日志页点一键刮削失败列表
    def pushButton_scraper_failed_list_clicked(self):
        if len(self.failed_file_list) and self.Ui.pushButton_start_cap.text() == '开始':
            self.start_new_scrape('default_folder', movie_list=self.failed_file_list)
            self.show_hide_failed_list(False)

    # 日志页点另存失败列表
    def pushButton_save_failed_list_clicked(self):
        if len(self.failed_file_list) or True:
            log_name = 'failed_' + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + '.txt'
            log_name = self.convert_path(os.path.join(self.get_movie_path_setting()[0], log_name))
            filename, filetype = QFileDialog.getSaveFileName(None, "保存失败文件列表", log_name, "Text Files (*.txt)", options=self.options)
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.Ui.textBrowser_log_main_3.toPlainText().strip())

    # 工具点查看本地番号
    def label_local_number_clicked(self, test):
        if self.Ui.pushButton_find_missing_number.isEnabled():
            self.pushButton_show_log_clicked()                                        # 点击按钮后跳转到日志页面
            if self.Ui.lineEdit_actors_name.text() != self.config.get('actors_name'): # 保存配置
                self.pushButton_save_config_clicked()
            try:
                t = threading.Thread(target=self.check_missing_number, args=(False, ))
                t.start()                                                             # 启动线程,即让线程开始执行
            except:
                self.show_traceback_log(traceback.format_exc())
                self.show_log_text(traceback.format_exc())

    # 设置-头像，点下载头像包
    def download_actor_zip_clicked(self, test):
        webbrowser.open('https://github.com/moyy996/AVDC/releases/tag/%E5%A4%B4%E5%83%8F%E5%8C%85-2')

    # 设置，点下载各种资源包
    def download_zip_clicked(self, test):
        webbrowser.open('https://www.dropbox.com/sh/vkbxawm6mwmwswr/AADqZiF8aUHmK6qIc7JSlURIa')

    # 设置-网络-cookie，点链接
    def get_cookie_url_clicked(self, test):
        webbrowser.open('https://tieba.baidu.com/p/5492736764')

    # ======================================================================================鼠标拖动窗口
    # 按下鼠标
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.m_drag = True
            self.m_DragPosition = e.globalPos() - self.pos()
            self.setCursor(QCursor(Qt.OpenHandCursor))                          # 按下左键改变鼠标指针样式为手掌

    # 松开鼠标
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.m_drag = False
            self.setCursor(QCursor(Qt.ArrowCursor))                             # 释放左键改变鼠标指针样式为箭头

    # 拖动鼠标
    def mouseMoveEvent(self, e):
        if Qt.LeftButton and self.m_drag:
            self.move(e.globalPos() - self.m_DragPosition)
            e.accept()

    # ======================================================================================切换配置
    def config_file_change(self, new_config_file):
        if new_config_file != self.config_file:
            new_config_path = os.path.join(self.config_folder, new_config_file)
            self.show_log_text('\n================================================================================\n切换配置：%s' % new_config_path)
            with open('MDCx.config', 'w', encoding='UTF-8') as f:
                f.write(new_config_path)
            temp_dark = self.dark_mode
            temp_window_radius = self.window_radius
            self.load_config()
            if temp_dark != self.dark_mode and temp_window_radius == self.window_radius:
                self.show_flag = True
                self.windows_auto_adjust()
            self.show_scrape_info('💡 配置已切换！%s' % self.get_current_time())

    # ======================================================================================更新进度条
    # 设置-线程数量
    def lcdNumber_thread_change(self):
        thread_number = self.Ui.horizontalSlider_thread.value()
        self.Ui.lcdNumber_thread.display(thread_number)

    # 设置-javdb延时
    def lcdNumber_javdb_time_change(self):
        javdb_time = self.Ui.horizontalSlider_javdb_time.value()
        self.Ui.lcdNumber_javdb_time.display(javdb_time)

    # 设置-其他网站延时
    def lcdNumber_thread_time_change(self):
        thread_time = self.Ui.horizontalSlider_thread_time.value()
        self.Ui.lcdNumber_thread_time.display(thread_time)

    # 设置-超时时间
    def lcdNumber_timeout_change(self):
        timeout = self.Ui.horizontalSlider_timeout.value()
        self.Ui.lcdNumber_timeout.display(timeout)

    # 设置-重试次数
    def lcdNumber_retry_change(self):
        retry = self.Ui.horizontalSlider_retry.value()
        self.Ui.lcdNumber_retry.display(retry)

    # 设置-水印大小
    def lcdNumber_mark_size_change(self):
        mark_size = self.Ui.horizontalSlider_mark_size.value()
        self.Ui.lcdNumber_mark_size.display(mark_size)

    # 主界面-开关封面显示
    def checkBox_cover_clicked(self):
        if not self.Ui.checkBox_cover.isChecked():
            self.Ui.label_poster.setText("封面图")
            self.Ui.label_thumb.setText("缩略图")
            self.Ui.label_poster.resize(156, 220)
            self.Ui.label_thumb.resize(328, 220)
            self.Ui.label_poster_size.setText("")
            self.Ui.label_thumb_size.setText("")
        else:
            self.add_label_info(self.json_data)

    # 设置-命名-分集-字母
    def checkBox_cd_part_a_clicked(self):
        if self.Ui.checkBox_cd_part_a.isChecked():
            self.Ui.checkBox_cd_part_c.setEnabled(True)
        else:
            self.Ui.checkBox_cd_part_c.setEnabled(False)

    # 设置-刮削目录-同意清理
    def checkBox_i_agree_clean_clicked(self):
        if self.Ui.checkBox_i_understand_clean.isChecked() and self.Ui.checkBox_i_agree_clean.isChecked():
            self.Ui.pushButton_check_and_clean_files.setEnabled(True)
            self.Ui.checkBox_auto_clean.setEnabled(True)
        else:
            self.Ui.pushButton_check_and_clean_files.setEnabled(False)
            self.Ui.checkBox_auto_clean.setEnabled(False)

    # 主界面-点击树状条目
    def treeWidget_number_clicked(self, qmodeLindex):
        item = self.Ui.treeWidget_number.currentItem()
        if item.text(0) != '成功' and item.text(0) != '失败':
            try:
                index_json = str(item.text(0))
                self.add_label_info(self.json_array[str(index_json)])
                if not self.Ui.widget_nfo.isHidden():
                    self.show_nfo_info()
            except:
                self.show_traceback_log(item.text(0) + ': No info!')

    # ======================================================================================左侧按钮点击事件响应函数
    def pushButton_close_clicked(self):
        if 'hide_close' in cf.get_config(True).get('switch_on'):
            self.hide()
        else:
            self.ready_to_exit()

    def ready_to_exit(self):
        if 'show_dialog_exit' in cf.get_config(True).get('switch_on'):
            if not self.isVisible():
                self.show()
            if int(self.windowState()) == 1:
                self.showNormal()

            # print(self.window().isActiveWindow()) # 是否为活动窗口
            self.raise_()
            box = QMessageBox(QMessageBox.Warning, '退出', '确定要退出吗？')
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.button(QMessageBox.Yes).setText('退出 MDCx')
            box.button(QMessageBox.No).setText('取消')
            box.setDefaultButton(QMessageBox.No)
            reply = box.exec()
            if reply != QMessageBox.Yes:
                self.raise_()
                self.show()
                return
        self.exit_app()

    # 关闭窗口
    def exit_app(self):
        self.config = cf.get_config(True)
        show_poster = self.config.get('show_poster')
        switch_on = self.config.get('switch_on')
        need_save_config = False

        if bool(self.Ui.checkBox_cover.isChecked()) != bool(show_poster):
            if self.Ui.checkBox_cover.isChecked():
                self.config['show_poster'] = 1
            else:
                self.config['show_poster'] = 0
            need_save_config = True
        if self.Ui.textBrowser_log_main_2.isHidden() == bool('show_logs' in switch_on):
            if self.Ui.textBrowser_log_main_2.isHidden():
                self.config['switch_on'] = switch_on.replace('show_logs,', '')
            else:
                self.config['switch_on'] = switch_on + 'show_logs,'
            need_save_config = True
        if need_save_config:
            try:
                cf.save_config(self.config)
            except:
                self.show_traceback_log(traceback.format_exc())
        try:
            self.tray_icon.hide()
        except:
            pass
        self.show_traceback_log('\n\n\n\n************ 程序正常退出！************\n')
        os._exit(0)

    # 最小化窗口
    def pushButton_min_clicked(self):
        if 'hide_mini' in cf.get_config(True).get('switch_on'):
            self.hide()
            return
        # mac 平台 python 版本 最小化有问题，此处就是为了兼容它，需要先设置为显示窗口标题栏才能最小化
        if not self.is_windows:
            self.setWindowFlag(Qt.FramelessWindowHint, False)                   # 不隐藏边框

        # self.setWindowState(Qt.WindowMinimized)
        # self.show_traceback_log(self.isMinimized())
        self.showMinimized()

    def pushButton_min_clicked2(self):
        if not self.is_windows:
            self.setWindowFlag(Qt.FramelessWindowHint, False)                   # 不隐藏边框
            # self.show()                                                         # 加上后可以显示缩小动画
        self.showMinimized()

    # 重置左侧按钮样式
    def set_left_button_style(self):
        try:
            if self.dark_mode:
                self.Ui.left_backgroud_widget.setStyleSheet('background: #1F272F;border-right: 1px solid #20303F;border-top-left-radius: %spx;border-bottom-left-radius: %spx;' % (self.window_radius, self.window_radius))
                self.Ui.pushButton_main.setStyleSheet('QPushButton:hover#pushButton_main{color: white;background-color: rgba(160,160,165,40);}')
                self.Ui.pushButton_log.setStyleSheet('QPushButton:hover#pushButton_log{color: white;background-color: rgba(160,160,165,40);}')
                self.Ui.pushButton_net.setStyleSheet('QPushButton:hover#pushButton_net{color: white;background-color: rgba(160,160,165,40);}')
                self.Ui.pushButton_tool.setStyleSheet('QPushButton:hover#pushButton_tool{color: white;background-color: rgba(160,160,165,40);}')
                self.Ui.pushButton_setting.setStyleSheet('QPushButton:hover#pushButton_setting{color: white;background-color: rgba(160,160,165,40);}')
                self.Ui.pushButton_about.setStyleSheet('QPushButton:hover#pushButton_about{color: white;background-color: rgba(160,160,165,40);}')
            else:
                self.Ui.pushButton_main.setStyleSheet('QPushButton:hover#pushButton_main{color: black;background-color: rgba(160,160,165,40);}')
                self.Ui.pushButton_log.setStyleSheet('QPushButton:hover#pushButton_log{color: black;background-color: rgba(160,160,165,40);}')
                self.Ui.pushButton_net.setStyleSheet('QPushButton:hover#pushButton_net{color: black;background-color: rgba(160,160,165,40);}')
                self.Ui.pushButton_tool.setStyleSheet('QPushButton:hover#pushButton_tool{color: black;background-color: rgba(160,160,165,40);}')
                self.Ui.pushButton_setting.setStyleSheet('QPushButton:hover#pushButton_setting{color: black;background-color: rgba(160,160,165,40);}')
                self.Ui.pushButton_about.setStyleSheet('QPushButton:hover#pushButton_about{color: black;background-color: rgba(160,160,165,40);}')
        except:
            pass

    # ====================================================================================== 设置左侧入口按钮的样式
    # 点左侧的主界面按钮
    def pushButton_main_clicked(self):
        self.Ui.left_backgroud_widget.setStyleSheet('background: #F5F5F6;border-right: 1px solid #EDEDED;border-top-left-radius: %spx;border-bottom-left-radius: %spx;' % (self.window_radius, self.window_radius))
        self.Ui.stackedWidget.setCurrentIndex(0)
        self.set_left_button_style()
        self.Ui.pushButton_main.setStyleSheet('font-weight: bold; background-color: rgba(160,160,165,60);')

    # 点左侧的日志按钮
    def pushButton_show_log_clicked(self):
        self.Ui.left_backgroud_widget.setStyleSheet('background: #EFFFFC;border-right: 1px solid #EDEDED;border-top-left-radius: %spx;border-bottom-left-radius: %spx;' % (self.window_radius, self.window_radius))
        self.Ui.stackedWidget.setCurrentIndex(1)
        self.set_left_button_style()
        self.Ui.pushButton_log.setStyleSheet('font-weight: bold; background-color: rgba(160,160,165,60);')
        self.Ui.textBrowser_log_main.verticalScrollBar().setValue(self.Ui.textBrowser_log_main.verticalScrollBar().maximum())
        self.Ui.textBrowser_log_main_2.verticalScrollBar().setValue(self.Ui.textBrowser_log_main_2.verticalScrollBar().maximum())

    # 点左侧的工具按钮
    def pushButton_tool_clicked(self):
        self.Ui.left_backgroud_widget.setStyleSheet('background: #FFEFF6;border-right: 1px solid #EDEDED;border-top-left-radius: %spx;border-bottom-left-radius: %spx;' % (self.window_radius, self.window_radius))
        self.Ui.stackedWidget.setCurrentIndex(3)
        self.set_left_button_style()
        self.Ui.pushButton_tool.setStyleSheet('font-weight: bold; background-color: rgba(160,160,165,60);')

    # 点左侧的设置按钮
    def pushButton_setting_clicked(self):
        self.Ui.left_backgroud_widget.setStyleSheet('background: #84CE9A;border-right: 1px solid #EDEDED;border-top-left-radius: %spx;border-bottom-left-radius: %spx;' % (self.window_radius, self.window_radius))
        self.Ui.stackedWidget.setCurrentIndex(4)
        self.set_left_button_style()
        try:
            if self.dark_mode:
                self.Ui.pushButton_setting.setStyleSheet('font-weight: bold; background-color: rgba(160,160,165,60);')
            else:
                self.Ui.pushButton_setting.setStyleSheet('font-weight: bold; background-color: rgba(160,160,165,100);')
            self.check_mac_config_folder()
        except:
            pass

    # 点击左侧【检测网络】按钮，切换到检测网络页面
    def pushButton_show_net_clicked(self):
        self.Ui.left_backgroud_widget.setStyleSheet('background: #E1F2FF;border-right: 1px solid #EDEDED;border-top-left-radius: %spx;border-bottom-left-radius: %spx;' % (self.window_radius, self.window_radius))
        self.Ui.stackedWidget.setCurrentIndex(2)
        self.set_left_button_style()
        self.Ui.pushButton_net.setStyleSheet('font-weight: bold; background-color: rgba(160,160,165,60);')

    # 点左侧的关于按钮
    def pushButton_about_clicked(self):
        self.Ui.left_backgroud_widget.setStyleSheet('background: #FFEFEF;border-right: 1px solid #EDEDED;border-top-left-radius: %spx;border-bottom-left-radius: %spx;' % (self.window_radius, self.window_radius))
        self.Ui.stackedWidget.setCurrentIndex(5)
        self.set_left_button_style()
        self.Ui.pushButton_about.setStyleSheet('font-weight: bold; background-color: rgba(160,160,165,60);')

    def change_page(self):
        page = int(self.Ui.stackedWidget.currentIndex())
        if page == 0:
            self.pushButton_main_clicked()
        elif page == 1:
            self.pushButton_show_log_clicked()
        elif page == 2:
            self.pushButton_show_net_clicked()
        elif page == 3:
            self.pushButton_tool_clicked()
        elif page == 4:
            self.pushButton_setting_clicked()
        elif page == 5:
            self.pushButton_about_clicked()

    # ======================================================================================点开始按钮

    def pushButton_start_cap_clicked(self):
        if self.Ui.pushButton_start_cap.text() == '开始':
            if not self.get_remain_list():
                self.start_new_scrape('default_folder')
        elif self.Ui.pushButton_start_cap.text() == '■ 停止':
            self.pushButton_stop_scrape_clicked()

    def start_new_scrape(self, file_mode, movie_list=[]):
        self.change_buttons_status()
        self.progressBarValue.emit(int(0))
        try:
            self.start_time = time.time()
            t = threading.Thread(target=self.MDCx_main, name='MDCx-Scrape-Thread', args=(file_mode, movie_list))
            self.threads_list.append(t)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())

    # ======================================================================================停止确认弹窗

    def pushButton_stop_scrape_clicked(self):
        if 'show_dialog_stop_scrape' in self.config.get('switch_on'):
            box = QMessageBox(QMessageBox.Warning, '停止刮削', '确定要停止刮削吗？')
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.button(QMessageBox.Yes).setText('停止刮削')
            box.button(QMessageBox.No).setText('取消')
            box.setDefaultButton(QMessageBox.No)
            reply = box.exec()
            if reply != QMessageBox.Yes:
                return
        if self.Ui.pushButton_start_cap.text() == '■ 停止':
            self.save_success_list()                                            # 保存成功列表
            self.stop_flag = True                                               # 在pool启动前，点停止按钮时，需要用这个来停止启动pool
            self.rest_time_convert_ = self.rest_time_convert
            self.rest_time_convert = 0
            self.rest_sleepping = False
            self.Ui.pushButton_start_cap.setText(' ■ 停止中 ')
            self.Ui.pushButton_start_cap2.setText(' ■ 停止中 ')
            self.show_scrape_info('⛔️ 刮削停止中...')
            try:                                                                # pool可能还没启动
                self.pool.shutdown39(wait=False, cancel_futures=True)
            except:
                pass
            t = threading.Thread(target=self.kill_threads)                      # 关闭线程池和扫描线程
            t.start()

    # ======================================================================================加载时去除错误字段

    def get_new_str(self, a, field=''):
        all_website_list = ['airav_cc', 'iqqtv', 'avsex', 'freejavbt', 'javbus', 'javdb', 'jav321', 'dmm', 'getchu', 'getchu_dmm', '7mmtv', 'avsox', 'xcity', 'mgstage', 'fc2', 'fc2club', 'fc2hub', 'airav', 'javlibrary', 'mdtv', 'madouqu', 'mywife', 'giga', 'faleno', 'dahlia', 'lulubar', 'love6', 'cnmdb', 'fantastica', 'theporndb', 'kin8', 'prestige']
        if field == 'wanted':
            all_website_list = ['javlibrary', 'javdb']
        read_web_list = re.split(r'[,，]', a)
        new_website_list1 = [i for i in read_web_list if i in all_website_list]              # 去除错误网站
        new_website_list = []
        [new_website_list.append(i) for i in new_website_list1 if i not in new_website_list] # 去重
        new_str = ','.join(new_website_list)
        return new_str

    def get_new_str_2(self, a):
        all_str_list = ['mosaic', 'cnword']
        read_str_list = re.split(r'[,，]', a)
        new_str_list1 = [i for i in read_str_list if i in all_str_list]          # 去除不在list中的字符
        new_str_list = []
        [new_str_list.append(i) for i in new_str_list1 if i not in new_str_list] # 去重
        [new_str_list.append(i) for i in all_str_list if i not in new_str_list]  # 补全
        new_str = ','.join(new_str_list)
        return new_str

    # ======================================================================================设置点恢复默认

    def pushButton_init_config_clicked(self):
        self.Ui.pushButton_init_config.setEnabled(False)
        cf.init_config(self.config_path, self.localversion)
        temp_dark = self.dark_mode
        temp_window_radius = self.window_radius
        self.load_config()
        if temp_dark and temp_window_radius:
            self.show_flag = True
            self.windows_auto_adjust()
        self.Ui.pushButton_init_config.setEnabled(True)
        self.show_scrape_info('💡 配置已重置！%s' % self.get_current_time())

    # ======================================================================================加载config

    def load_config(self):
        config_folder = self.main_path
        config_file = 'config.ini'

        # 读取 MDCx.config 配置
        mdc_config_file = 'MDCx.config'
        mdcx_config = True
        if os.path.exists(mdc_config_file):
            with open(mdc_config_file, 'r', encoding='UTF-8') as f:
                config_path = f.read().strip()
                config_folder, config_file = split_path(config_path)
        else:
            try:
                with open(mdc_config_file, 'w', encoding='UTF-8') as f:
                    f.write('')
            except:
                mdcx_config = False

        # 判断 配置文件夹和配置文件名
        if not config_file:
            config_file = 'config.ini'
        if not config_folder or not os.path.isdir(config_folder):
            config_folder = self.main_path
        config_path = self.convert_path(os.path.join(config_folder, config_file))
        self.config_file = config_file
        self.config_folder = self.convert_path(config_folder)
        self.config_path = config_path
        self.Ui.lineEdit_config_folder.setText(config_folder)

        # 检测配置目录权限
        if not os.access(config_folder, os.W_OK) or not os.access(config_folder, os.R_OK):
            mdcx_config = False

        if os.path.exists(config_path):
            config = RawConfigParser()
            # ======================================================================================当配置读取失败时重置
            try:
                config.read(config_path, encoding='UTF-8')
            except Exception as e:
                # ini损坏，重新创建
                self.show_traceback_log('ini损坏，重新创建。错误信息：\n %s' % e)
                self.show_traceback_log(traceback.format_exc())
                self.show_log_text('%s 读取失败！错误信息：\n%s \n%s 将重置为初始值！\n' % (config_path, str(e), config_path))
                self.pushButton_init_config_clicked()
                return

            # ======================================================================================获取默认配置
            default_config = cf.init_config()

            # ======================================================================================获取配置文件夹中的配置文件列表
            all_files = os.listdir(config_folder)
            all_config_files = [i for i in all_files if '.ini' in i]
            all_config_files.sort()
            self.Ui.comboBox_change_config.clear()
            self.Ui.comboBox_change_config.addItems(all_config_files)
            if config_file in all_config_files:
                self.Ui.comboBox_change_config.setCurrentIndex(all_config_files.index(config_file))
            else:
                self.Ui.comboBox_change_config.setCurrentIndex(all_config_files.index('config.ini'))

            # ======================================================================================modified_time
            if not config.has_section("modified_time"):
                config.add_section("modified_time")
            try:                                                                # 修改时间
                config.get('modified_time', 'modified_time')
            except:
                config['modified_time']['modified_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            try:                                                                # 修改时间
                read_version = config.getint('modified_time', 'version')
            except:
                read_version = 20220101

            # ======================================================================================media
            if not config.has_section("media"):
                config.add_section("media")
            try:                                                                # 视频目录
                self.Ui.lineEdit_movie_path.setText(self.convert_path(config['media']['media_path']))
            except:
                self.Ui.lineEdit_movie_path.setText(str(default_config['media_path']))
            try:                                                                # 软链接目录
                self.Ui.lineEdit_movie_softlink_path.setText(self.convert_path(config['media']['softlink_path']))
            except:
                self.Ui.lineEdit_movie_softlink_path.setText(str(default_config['softlink_path']))
            try:                                                                # 成功目录
                self.Ui.lineEdit_success.setText(self.convert_path(config['media']['success_output_folder']))
            except:
                self.Ui.lineEdit_success.setText(str(default_config['success_output_folder']))
            try:                                                                # 失败目录
                self.Ui.lineEdit_fail.setText(self.convert_path(config['media']['failed_output_folder']))
            except:
                self.Ui.lineEdit_fail.setText(str(default_config['failed_output_folder']))
            try:                                                                # 剧照副本目录
                extrafanart_folder = str(config['media']['extrafanart_folder'])
                if not extrafanart_folder or extrafanart_folder == 'extrafanart':
                    extrafanart_folder = str(default_config['extrafanart_folder'])
                self.Ui.lineEdit_extrafanart_dir.setText(extrafanart_folder)
            except:
                self.Ui.lineEdit_extrafanart_dir.setText(str(default_config['extrafanart_folder']))
            try:                                                                # 视频类型
                self.Ui.lineEdit_movie_type.setText(str(config['media']['media_type']))
            except:
                self.Ui.lineEdit_movie_type.setText(str(default_config['media_type']))
            try:                                                                # 字幕类型
                self.Ui.lineEdit_sub_type.setText(str(config['media']['sub_type']).replace('.txt|', ''))
            except:
                self.Ui.lineEdit_sub_type.setText(str(default_config['sub_type']))
            try:                                                                # 不过滤文件、文件夹
                scrape_softlink_path = config['media']['scrape_softlink_path']
            except:
                scrape_softlink_path = default_config['scrape_softlink_path']
            if scrape_softlink_path:
                self.Ui.checkBox_scrape_softlink_path.setChecked(True)
            else:
                self.Ui.checkBox_scrape_softlink_path.setChecked(False)

            # ======================================================================================escape
            if not config.has_section("escape"):
                config.add_section("escape")
            try:                                                                # 排除目录
                self.Ui.lineEdit_escape_dir.setText(str(config['escape']['folders']))
            except:
                self.Ui.lineEdit_escape_dir.setText(str(default_config['folders']))
            try:                                                                # 排除目录-工具页面
                self.Ui.lineEdit_escape_dir_move.setText(str(config['escape']['folders']))
            except:
                self.Ui.lineEdit_escape_dir_move.setText(str(default_config['folders']))
            try:                                                                # 多余字符串
                escape_string = str(config['escape']['string'])
                if read_version < 20230326:
                    escape_string = 'h_720,' + escape_string
            except:
                escape_string = str(default_config['string'])
            self.Ui.lineEdit_escape_string.setText(escape_string)
            try:                                                                # 小文件
                self.Ui.lineEdit_escape_size.setText(str(float(config['escape']['file_size'])))
            except:
                self.Ui.lineEdit_escape_size.setText(str(default_config['file_size']))
            try:                                                                # 不过滤文件、文件夹
                no_escape = config['escape']['no_escape']
            except:
                no_escape = default_config['no_escape']
            if 'no_skip_small_file' in no_escape:
                self.Ui.checkBox_no_escape_file.setChecked(True)
            else:
                self.Ui.checkBox_no_escape_file.setChecked(False)
            if 'folder' in no_escape:
                self.Ui.checkBox_no_escape_dir.setChecked(True)
            else:
                self.Ui.checkBox_no_escape_dir.setChecked(False)
            if 'skip_success_file' in no_escape:
                self.Ui.checkBox_skip_success_file.setChecked(True)
            else:
                self.Ui.checkBox_skip_success_file.setChecked(False)
            if 'record_success_file' in no_escape:
                self.Ui.checkBox_record_success_file.setChecked(True)
            else:
                self.Ui.checkBox_record_success_file.setChecked(False)
            if 'check_symlink' in no_escape:
                self.Ui.checkBox_check_symlink.setChecked(True)
            else:
                self.Ui.checkBox_check_symlink.setChecked(False)
            if 'symlink_definition' in no_escape:
                self.Ui.checkBox_check_symlink_definition.setChecked(True)
            else:
                self.Ui.checkBox_check_symlink_definition.setChecked(False)

            # ======================================================================================escape
            if not config.has_section("clean"):
                config.add_section("clean")
            try:                                                                # 清理扩展名等于
                self.Ui.lineEdit_clean_file_ext.setText(str(config['clean']['clean_ext']))
            except:
                self.Ui.lineEdit_clean_file_ext.setText(str(default_config['clean_ext']))
            try:                                                                # 清理文件名等于
                self.Ui.lineEdit_clean_file_name.setText(str(config['clean']['clean_name']))
            except:
                self.Ui.lineEdit_clean_file_name.setText(str(default_config['clean_name']))
            try:                                                                # 清理文件名包含
                self.Ui.lineEdit_clean_file_contains.setText(str(config['clean']['clean_contains']))
            except:
                self.Ui.lineEdit_clean_file_contains.setText(str(default_config['clean_contains']))
            try:                                                                # 清理文件大小
                self.Ui.lineEdit_clean_file_size.setText(str(float(config['clean']['clean_size'])))
            except:
                self.Ui.lineEdit_clean_file_size.setText(str(float(default_config['clean_size'])))
            try:                                                                # 不清理扩展名
                self.Ui.lineEdit_clean_excluded_file_ext.setText(str(config['clean']['clean_ignore_ext']))
            except:
                self.Ui.lineEdit_clean_excluded_file_ext.setText(str(default_config['clean_ignore_ext']))
            try:                                                                # 不清理文件名包含
                self.Ui.lineEdit_clean_excluded_file_contains.setText(str(config['clean']['clean_ignore_contains']))
            except:
                self.Ui.lineEdit_clean_excluded_file_contains.setText(str(default_config['clean_ignore_contains']))
            try:
                clean_enable = config['clean']['clean_enable']
            except:
                clean_enable = default_config['clean_enable']
            if 'clean_ext' in clean_enable:
                self.Ui.checkBox_clean_file_ext.setChecked(True)
            else:
                self.Ui.checkBox_clean_file_ext.setChecked(False)
            if 'clean_name' in clean_enable:
                self.Ui.checkBox_clean_file_name.setChecked(True)
            else:
                self.Ui.checkBox_clean_file_name.setChecked(False)
            if 'clean_contains' in clean_enable:
                self.Ui.checkBox_clean_file_contains.setChecked(True)
            else:
                self.Ui.checkBox_clean_file_contains.setChecked(False)
            if 'clean_size' in clean_enable:
                self.Ui.checkBox_clean_file_size.setChecked(True)
            else:
                self.Ui.checkBox_clean_file_size.setChecked(False)
            if 'clean_ignore_ext' in clean_enable:
                self.Ui.checkBox_clean_excluded_file_ext.setChecked(True)
            else:
                self.Ui.checkBox_clean_excluded_file_ext.setChecked(False)
            if 'clean_ignore_contains' in clean_enable:
                self.Ui.checkBox_clean_excluded_file_contains.setChecked(True)
            else:
                self.Ui.checkBox_clean_excluded_file_contains.setChecked(False)
            if 'i_know' in clean_enable:
                self.Ui.checkBox_i_understand_clean.setChecked(True)
            else:
                self.Ui.checkBox_i_understand_clean.setChecked(False)
            if 'i_agree' in clean_enable:
                self.Ui.checkBox_i_agree_clean.setChecked(True)
            else:
                self.Ui.checkBox_i_agree_clean.setChecked(False)
            if 'auto_clean' in clean_enable:
                self.Ui.checkBox_auto_clean.setChecked(True)
            else:
                self.Ui.checkBox_auto_clean.setChecked(False)

            # ======================================================================================website
            if not config.has_section("website"):
                config.add_section("website")

            AllItems = [self.Ui.comboBox_website_all.itemText(i) for i in range(self.Ui.comboBox_website_all.count())]
            try:                                                                # 指定单个刮削网站
                website_single = config['website']['website_single']
                self.Ui.comboBox_website_all.setCurrentIndex(AllItems.index(website_single))
            except:
                website_single = default_config['website_single']
                self.Ui.comboBox_website_all.setCurrentIndex(AllItems.index(website_single))

            try:                                                                # 有码番号刮削网站
                temp_youma = str(config['website']['website_youma'])
                website_youma = self.get_new_str(temp_youma)
            except:
                website_youma = default_config['website_youma']
            self.Ui.lineEdit_website_youma.setText(str(website_youma))
            try:                                                                # 无码番号刮削网站
                website_wuma = self.get_new_str(str(config['website']['website_wuma']))
            except:
                website_wuma = default_config['website_wuma']
            self.Ui.lineEdit_website_wuma.setText(str(website_wuma))
            try:                                                                # 素人番号刮削网站
                website_suren = self.get_new_str(str(config['website']['website_suren']))
            except:
                website_suren = default_config['website_suren']
            self.Ui.lineEdit_website_suren.setText(str(website_suren))
            try:                                                                # FC2番号刮削网站
                website_fc2 = self.get_new_str(str(config['website']['website_fc2']))
            except:
                website_fc2 = default_config['website_fc2']
            self.Ui.lineEdit_website_fc2.setText(str(website_fc2))
            try:                                                                # 欧美番号刮削网站
                temp_oumei = str(config['website']['website_oumei'])
                if 'theporndb' not in temp_oumei:
                    temp_oumei = 'theporndb,' + temp_oumei
                website_oumei = self.get_new_str(temp_oumei)
            except:
                website_oumei = default_config['website_oumei']
            self.Ui.lineEdit_website_oumei.setText(str(website_oumei))
            try:                                                                # 国产番号刮削网站
                website_guochan = self.get_new_str(str(config['website']['website_guochan']))
            except:
                website_guochan = default_config['website_guochan']
            self.Ui.lineEdit_website_guochan.setText(str(website_guochan))

            try:                                                                # 刮削偏好
                scrape_like = config['website']['scrape_like']
            except:
                scrape_like = default_config['scrape_like']
            if 'speed' in scrape_like:
                self.Ui.radioButton_scrape_speed.setChecked(True)
                self.scrape_like = '速度优先'
            elif 'single' in scrape_like:
                self.Ui.radioButton_scrape_single.setChecked(True)
                self.scrape_like = '指定网站'
            else:
                self.Ui.radioButton_scrape_info.setChecked(True)
                self.scrape_like = '字段优先'

            try:
                website_set = str(config['website']['website_set'])
            except:
                website_set = default_config['website_set']
            if 'official,' in website_set:
                self.Ui.checkBox_use_official_data.setChecked(True)
            else:
                self.Ui.checkBox_use_official_data.setChecked(False)

            try:                                                                # 标题字段网站优先级
                title_website = self.get_new_str(str(config['website']['title_website']))
                if read_version < 20230405:
                    title_website = 'theporndb,mgstage,' + title_website
            except:
                title_website = default_config['title_website']
            self.Ui.lineEdit_title_website.setText(str(title_website))
            try:                                                                # 中文标题字段网站优先级
                title_zh_website = self.get_new_str(str(config['website']['title_zh_website']))
            except:
                title_zh_website = default_config['title_zh_website']
            self.Ui.lineEdit_title_zh_website.setText(str(title_zh_website))

            try:                                                                # 标题字段排除网站
                title_website_exclude = self.get_new_str(str(config['website']['title_website_exclude']))
            except:
                title_website_exclude = default_config['title_website_exclude']
            self.Ui.lineEdit_title_website_exclude.setText(str(title_website_exclude))

            try:                                                                # 标题语言
                title_language = config['website']['title_language']
            except:
                title_language = default_config['title_language']
            if title_language == 'zh_cn':
                self.Ui.radioButton_title_zh_cn.setChecked(True)
            elif title_language == 'zh_tw':
                self.Ui.radioButton_title_zh_tw.setChecked(True)
            else:
                self.Ui.radioButton_title_jp.setChecked(True)

            try:                                                                # 增强翻译-sehua
                title_sehua = config['website']['title_sehua']
            except:
                title_sehua = default_config['title_sehua']
            if title_sehua == 'on':
                self.Ui.checkBox_title_sehua.setChecked(True)
            else:
                self.Ui.checkBox_title_sehua.setChecked(False)

            try:                                                                # 增强翻译-yesjav
                title_yesjav = config['website']['title_yesjav']
            except:
                title_yesjav = default_config['title_yesjav']
            if title_yesjav == 'on':
                self.Ui.checkBox_title_yesjav.setChecked(True)
            else:
                self.Ui.checkBox_title_yesjav.setChecked(False)

            try:                                                                # 标题增强翻译-使用翻译引擎
                title_translate = config['website']['title_translate']
            except:
                title_translate = default_config['title_translate']
            if title_translate == 'on':
                self.Ui.checkBox_title_translate.setChecked(True)
            else:
                self.Ui.checkBox_title_translate.setChecked(False)

            try:                                                                # 增强翻译-优先sehua
                title_sehua_zh = config['website']['title_sehua_zh']
            except:
                title_sehua_zh = default_config['title_sehua_zh']
            if title_sehua_zh == 'on':
                self.Ui.checkBox_title_sehua_2.setChecked(True)
            else:
                self.Ui.checkBox_title_sehua_2.setChecked(False)

            try:                                                                # 简介字段网站优先级
                outline_website = self.get_new_str(str(config['website']['outline_website']))
            except:
                outline_website = default_config['outline_website']
            self.Ui.lineEdit_outline_website.setText(str(outline_website))
            try:                                                                # 中文简介字段网站优先级
                outline_zh_website = self.get_new_str(str(config['website']['outline_zh_website']))
            except:
                outline_zh_website = default_config['outline_zh_website']
            self.Ui.lineEdit_outline_zh_website.setText(str(outline_zh_website))

            try:                                                                # 简介字段排除网站
                outline_website_exclude = self.get_new_str(str(config['website']['outline_website_exclude']))
            except:
                outline_website_exclude = default_config['outline_website_exclude']
            self.Ui.lineEdit_outline_website_exclude.setText(str(outline_website_exclude))

            try:                                                                # 简介语言
                outline_language = config['website']['outline_language']
            except:
                outline_language = default_config['outline_language']
            if outline_language == 'zh_cn':
                self.Ui.radioButton_outline_zh_cn.setChecked(True)
            elif outline_language == 'zh_tw':
                self.Ui.radioButton_outline_zh_tw.setChecked(True)
            elif outline_language == 'jp':
                self.Ui.radioButton_outline_jp.setChecked(True)
            else:
                self.Ui.radioButton_outline_zh_cn.setChecked(True)

            try:                                                                # 简介-使用翻译引擎
                outline_translate = config['website']['outline_translate']
            except:
                outline_translate = default_config['outline_translate']
            if outline_translate == 'on':
                self.Ui.checkBox_outline_translate.setChecked(True)
            else:
                self.Ui.checkBox_outline_translate.setChecked(False)
            try:                                                                # 简介-显示翻译来源、双语显示
                outline_show = config['website']['outline_show']
            except:
                outline_show = default_config['outline_show']
            if 'show_from' in outline_show:
                self.Ui.checkBox_show_translate_from.setChecked(True)
            else:
                self.Ui.checkBox_show_translate_from.setChecked(False)
            if 'show_zh_jp' in outline_show:
                self.Ui.radioButton_trans_show_zh_jp.setChecked(True)
            elif 'show_jp_zh' in outline_show:
                self.Ui.radioButton_trans_show_jp_zh.setChecked(True)
            else:
                self.Ui.radioButton_trans_show_one.setChecked(True)

            try:                                                                # 演员字段网站优先级
                actor_website = self.get_new_str(str(config['website']['actor_website']))
            except:
                actor_website = default_config['actor_website']
            self.Ui.lineEdit_actor_website.setText(str(actor_website))

            try:                                                                # 演员字段排除网站
                actor_website_exclude = self.get_new_str(str(config['website']['actor_website_exclude']))
            except:
                actor_website_exclude = default_config['actor_website_exclude']
            self.Ui.lineEdit_actor_website_exclude.setText(str(actor_website_exclude))

            try:                                                                # 演员映射表输出
                actor_language = config['website']['actor_language']
            except:
                actor_language = default_config['actor_language']
            if actor_language == 'zh_cn':
                self.Ui.radioButton_actor_zh_cn.setChecked(True)
            elif actor_language == 'zh_tw':
                self.Ui.radioButton_actor_zh_tw.setChecked(True)
            elif actor_language == 'jp':
                self.Ui.radioButton_actor_jp.setChecked(True)
            else:
                self.Ui.radioButton_actor_zh_cn.setChecked(True)

            try:                                                                # 演员-使用真实名字
                actor_realname = config['website']['actor_realname']
            except:
                actor_realname = default_config['actor_realname']
            if actor_realname == 'on':
                self.Ui.checkBox_actor_realname.setChecked(True)
            else:
                self.Ui.checkBox_actor_realname.setChecked(False)

            try:                                                                # 演员-使用演员映射表
                actor_translate = config['website']['actor_translate']
            except:
                actor_translate = default_config['actor_translate']
            if actor_translate == 'on':
                self.Ui.checkBox_actor_translate.setChecked(True)
            else:
                self.Ui.checkBox_actor_translate.setChecked(False)

            try:                                                                # 标签字段网站优先级
                tag_website = self.get_new_str(str(config['website']['tag_website']))
            except:
                tag_website = default_config['tag_website']
            self.Ui.lineEdit_tag_website.setText(str(tag_website))

            try:                                                                # 标签字段排除网站
                tag_website_exclude = self.get_new_str(str(config['website']['tag_website_exclude']))
            except:
                tag_website_exclude = default_config['tag_website_exclude']
            self.Ui.lineEdit_tag_website_exclude.setText(str(tag_website_exclude))

            try:                                                                # 标签字段语言
                tag_language = config['website']['tag_language']
            except:
                tag_language = default_config['tag_language']
            if tag_language == 'zh_cn':
                self.Ui.radioButton_tag_zh_cn.setChecked(True)
            elif tag_language == 'zh_tw':
                self.Ui.radioButton_tag_zh_tw.setChecked(True)
            elif tag_language == 'jp':
                self.Ui.radioButton_tag_jp.setChecked(True)
            else:
                self.Ui.radioButton_tag_zh_cn.setChecked(True)

            try:                                                                # 标签-使用信息映射表
                tag_translate = config['website']['tag_translate']
            except:
                tag_translate = default_config['tag_translate']
            if tag_translate == 'on':
                self.Ui.checkBox_tag_translate.setChecked(True)
            else:
                self.Ui.checkBox_tag_translate.setChecked(False)

            try:                                                                # 写入标签字段的信息
                tag_include = config['website']['tag_include']
            except:
                tag_include = default_config['tag_include']
            if 'actor' in tag_include:
                self.Ui.checkBox_tag_actor.setChecked(True)
            else:
                self.Ui.checkBox_tag_actor.setChecked(False)
            if 'letters' in tag_include:
                self.Ui.checkBox_tag_letters.setChecked(True)
            else:
                self.Ui.checkBox_tag_letters.setChecked(False)
            if 'series' in tag_include:
                self.Ui.checkBox_tag_series.setChecked(True)
            else:
                self.Ui.checkBox_tag_series.setChecked(False)
            if 'studio' in tag_include:
                self.Ui.checkBox_tag_studio.setChecked(True)
            else:
                self.Ui.checkBox_tag_studio.setChecked(False)
            if 'publisher' in tag_include:
                self.Ui.checkBox_tag_publisher.setChecked(True)
            else:
                self.Ui.checkBox_tag_publisher.setChecked(False)
            if 'cnword' in tag_include:
                self.Ui.checkBox_tag_cnword.setChecked(True)
            else:
                self.Ui.checkBox_tag_cnword.setChecked(False)
            if 'mosaic' in tag_include:
                self.Ui.checkBox_tag_mosaic.setChecked(True)
            else:
                self.Ui.checkBox_tag_mosaic.setChecked(False)
            if 'definition' in tag_include:
                self.Ui.checkBox_tag_definition.setChecked(True)
            else:
                self.Ui.checkBox_tag_definition.setChecked(False)

            try:                                                                # 系列字段网站优先级
                series_website = self.get_new_str(str(config['website']['series_website']))
            except:
                series_website = default_config['series_website']
            self.Ui.lineEdit_series_website.setText(str(series_website))

            try:                                                                # 系列字段排除网站
                series_website_exclude = self.get_new_str(str(config['website']['series_website_exclude']))
            except:
                series_website_exclude = default_config['series_website_exclude']
            self.Ui.lineEdit_series_website_exclude.setText(str(series_website_exclude))

            try:                                                                # 系列字段语言
                series_language = config['website']['series_language']
            except:
                series_language = default_config['series_language']
            if series_language == 'zh_cn':
                self.Ui.radioButton_series_zh_cn.setChecked(True)
            elif series_language == 'zh_tw':
                self.Ui.radioButton_series_zh_tw.setChecked(True)
            elif series_language == 'jp':
                self.Ui.radioButton_series_jp.setChecked(True)
            else:
                self.Ui.radioButton_series_zh_cn.setChecked(True)

            try:                                                                # 系列-使用信息映射表
                series_translate = config['website']['series_translate']
            except:
                series_translate = default_config['series_translate']
            if series_translate == 'on':
                self.Ui.checkBox_series_translate.setChecked(True)
            else:
                self.Ui.checkBox_series_translate.setChecked(False)

            try:                                                                # 片商字段网站优先级
                studio_website = self.get_new_str(str(config['website']['studio_website']))
            except:
                studio_website = default_config['studio_website']
            self.Ui.lineEdit_studio_website.setText(str(studio_website))

            try:                                                                # 片商字段排除网站
                studio_website_exclude = self.get_new_str(str(config['website']['studio_website_exclude']))
            except:
                studio_website_exclude = default_config['studio_website_exclude']
            self.Ui.lineEdit_studio_website_exclude.setText(str(studio_website_exclude))

            try:                                                                # 片商字段语言
                studio_language = config['website']['studio_language']
            except:
                studio_language = default_config['studio_language']
            if studio_language == 'zh_cn':
                self.Ui.radioButton_studio_zh_cn.setChecked(True)
            elif studio_language == 'zh_tw':
                self.Ui.radioButton_studio_zh_tw.setChecked(True)
            elif studio_language == 'jp':
                self.Ui.radioButton_studio_jp.setChecked(True)
            else:
                self.Ui.radioButton_studio_zh_cn.setChecked(True)

            try:                                                                # 片商-使用信息映射表
                studio_translate = config['website']['studio_translate']
            except:
                studio_translate = default_config['studio_translate']
            if studio_translate == 'on':
                self.Ui.checkBox_studio_translate.setChecked(True)
            else:
                self.Ui.checkBox_studio_translate.setChecked(False)

            try:                                                                # 想看人数
                wanted_website = self.get_new_str(str(config['website']['wanted_website']), field='wanted')
            except:
                wanted_website = default_config['wanted_website']
            self.Ui.lineEdit_wanted_website.setText(str(wanted_website))

            try:                                                                # 发行字段网站优先级
                publisher_website = self.get_new_str(str(config['website']['publisher_website']))
            except:
                publisher_website = default_config['publisher_website']
            self.Ui.lineEdit_publisher_website.setText(str(publisher_website))

            try:                                                                # 发行字段排除网站
                publisher_website_exclude = self.get_new_str(str(config['website']['publisher_website_exclude']))
            except:
                publisher_website_exclude = default_config['publisher_website_exclude']
            self.Ui.lineEdit_publisher_website_exclude.setText(str(publisher_website_exclude))

            try:                                                                # 发行字段语言
                publisher_language = config['website']['publisher_language']
            except:
                publisher_language = default_config['publisher_language']
            if publisher_language == 'zh_cn':
                self.Ui.radioButton_publisher_zh_cn.setChecked(True)
            elif publisher_language == 'zh_tw':
                self.Ui.radioButton_publisher_zh_tw.setChecked(True)
            elif publisher_language == 'jp':
                self.Ui.radioButton_publisher_jp.setChecked(True)
            else:
                self.Ui.radioButton_publisher_zh_cn.setChecked(True)

            try:                                                                # 发行-使用信息映射表
                publisher_translate = config['website']['publisher_translate']
            except:
                publisher_translate = default_config['publisher_translate']
            if publisher_translate == 'on':
                self.Ui.checkBox_publisher_translate.setChecked(True)
            else:
                self.Ui.checkBox_publisher_translate.setChecked(False)

            try:                                                                # 导演字段网站优先级
                director_website = self.get_new_str(str(config['website']['director_website']))
            except:
                director_website = default_config['director_website']
            self.Ui.lineEdit_director_website.setText(str(director_website))

            try:                                                                # 导演字段排除网站
                director_website_exclude = self.get_new_str(str(config['website']['director_website_exclude']))
            except:
                director_website_exclude = default_config['director_website_exclude']
            self.Ui.lineEdit_director_website_exclude.setText(str(director_website_exclude))

            try:                                                                # 导演字段语言
                director_language = config['website']['director_language']
            except:
                director_language = default_config['director_language']
            if director_language == 'zh_cn':
                self.Ui.radioButton_director_zh_cn.setChecked(True)
            elif director_language == 'zh_tw':
                self.Ui.radioButton_director_zh_tw.setChecked(True)
            elif director_language == 'jp':
                self.Ui.radioButton_director_jp.setChecked(True)
            else:
                self.Ui.radioButton_director_zh_cn.setChecked(True)

            try:                                                                # 导演-使用信息映射表
                director_translate = config['website']['director_translate']
            except:
                director_translate = default_config['director_translate']
            if director_translate == 'on':
                self.Ui.checkBox_director_translate.setChecked(True)
            else:
                self.Ui.checkBox_director_translate.setChecked(False)

            try:                                                                # 封面字段网站优先级
                poster_website = self.get_new_str(str(config['website']['poster_website']))
            except:
                poster_website = default_config['poster_website']
            self.Ui.lineEdit_poster_website.setText(str(poster_website))

            try:                                                                # 封面字段排除网站
                poster_website_exclude = self.get_new_str(str(config['website']['poster_website_exclude']))
            except:
                poster_website_exclude = default_config['poster_website_exclude']
            self.Ui.lineEdit_poster_website_exclude.setText(str(poster_website_exclude))

            try:                                                                # 背景字段网站优先级
                thumb_website = self.get_new_str(str(config['website']['thumb_website']))
            except:
                thumb_website = default_config['thumb_website']
            self.Ui.lineEdit_thumb_website.setText(str(thumb_website))

            try:                                                                # 背景字段排除网站
                thumb_website_exclude = self.get_new_str(str(config['website']['thumb_website_exclude']))
            except:
                thumb_website_exclude = default_config['thumb_website_exclude']
            self.Ui.lineEdit_thumb_website_exclude.setText(str(thumb_website_exclude))

            try:                                                                # 剧照字段网站优先级
                extrafanart_website = self.get_new_str(str(config['website']['extrafanart_website']))
            except:
                extrafanart_website = default_config['extrafanart_website']
            self.Ui.lineEdit_extrafanart_website.setText(str(extrafanart_website))

            try:                                                                # 剧照字段排除网站
                extrafanart_website_exclude = self.get_new_str(str(config['website']['extrafanart_website_exclude']))
            except:
                extrafanart_website_exclude = default_config['extrafanart_website_exclude']
            self.Ui.lineEdit_extrafanart_website_exclude.setText(str(extrafanart_website_exclude))

            try:                                                                # 评分字段网站优先级
                score_website = self.get_new_str(str(config['website']['score_website']))
            except:
                score_website = default_config['score_website']
            self.Ui.lineEdit_score_website.setText(str(score_website))

            try:                                                                # 评分字段排除网站
                score_website_exclude = self.get_new_str(str(config['website']['score_website_exclude']))
            except:
                score_website_exclude = default_config['score_website_exclude']
            self.Ui.lineEdit_score_website_exclude.setText(str(score_website_exclude))

            try:                                                                # 发行日期字段网站优先级
                release_website = self.get_new_str(str(config['website']['release_website']))
            except:
                release_website = default_config['release_website']
            self.Ui.lineEdit_release_website.setText(str(release_website))

            try:                                                                # 发行日期字段排除网站
                release_website_exclude = self.get_new_str(str(config['website']['release_website_exclude']))
            except:
                release_website_exclude = default_config['release_website_exclude']
            self.Ui.lineEdit_release_website_exclude.setText(str(release_website_exclude))

            try:                                                                # 时长字段网站优先级
                runtime_website = self.get_new_str(str(config['website']['runtime_website']))
            except:
                runtime_website = default_config['runtime_website']
            self.Ui.lineEdit_runtime_website.setText(str(runtime_website))

            try:                                                                # 时长字段排除网站
                runtime_website_exclude = self.get_new_str(str(config['website']['runtime_website_exclude']))
            except:
                runtime_website_exclude = default_config['runtime_website_exclude']
            self.Ui.lineEdit_runtime_website_exclude.setText(str(runtime_website_exclude))

            try:                                                                # 预告片字段网站优先级
                trailer_website = self.get_new_str(str(config['website']['trailer_website']))
            except:
                trailer_website = default_config['trailer_website']
            self.Ui.lineEdit_trailer_website.setText(str(trailer_website))

            try:                                                                # 预告片字段排除网站
                trailer_website_exclude = self.get_new_str(str(config['website']['trailer_website_exclude']))
            except:
                trailer_website_exclude = default_config['trailer_website_exclude']
            self.Ui.lineEdit_trailer_website_exclude.setText(str(trailer_website_exclude))

            try:                                                                # 刮削设置
                whole_fields = config['website']['whole_fields']
            except:
                whole_fields = default_config['whole_fields']
            try:
                none_fields = config['website']['none_fields']
            except:
                none_fields = default_config['none_fields']
            if 'outline' in whole_fields:
                self.Ui.radioButton_outline_more.setChecked(True)
            elif 'outline' in none_fields:
                self.Ui.radioButton_outline_none.setChecked(True)
            else:
                self.Ui.radioButton_outline_listed.setChecked(True)

            if 'actor' in whole_fields:
                self.Ui.radioButton_actor_more.setChecked(True)
            elif 'actor' in none_fields:
                self.Ui.radioButton_actor_none.setChecked(True)
            else:
                self.Ui.radioButton_actor_listed.setChecked(True)

            if 'thumb' in whole_fields:
                self.Ui.radioButton_thumb_more.setChecked(True)
            elif 'thumb' in none_fields:
                self.Ui.radioButton_thumb_none.setChecked(True)
            else:
                self.Ui.radioButton_thumb_listed.setChecked(True)

            if 'poster' in whole_fields:
                self.Ui.radioButton_poster_more.setChecked(True)
            elif 'poster' in none_fields:
                self.Ui.radioButton_poster_none.setChecked(True)
            else:
                self.Ui.radioButton_poster_listed.setChecked(True)

            if 'extrafanart' in whole_fields:
                self.Ui.radioButton_extrafanart_more.setChecked(True)
            elif 'extrafanart' in none_fields:
                self.Ui.radioButton_extrafanart_none.setChecked(True)
            else:
                self.Ui.radioButton_extrafanart_listed.setChecked(True)

            if 'trailer' in whole_fields:
                self.Ui.radioButton_trailer_more.setChecked(True)
            elif 'trailer' in none_fields:
                self.Ui.radioButton_trailer_none.setChecked(True)
            else:
                self.Ui.radioButton_trailer_listed.setChecked(True)

            if 'tag' in whole_fields:
                self.Ui.radioButton_tag_more.setChecked(True)
            elif 'tag' in none_fields:
                self.Ui.radioButton_tag_none.setChecked(True)
            else:
                self.Ui.radioButton_tag_listed.setChecked(True)

            if 'release' in whole_fields:
                self.Ui.radioButton_release_more.setChecked(True)
            elif 'release' in none_fields:
                self.Ui.radioButton_release_none.setChecked(True)
            else:
                self.Ui.radioButton_release_listed.setChecked(True)

            if 'runtime' in whole_fields:
                self.Ui.radioButton_runtime_more.setChecked(True)
            elif 'runtime' in none_fields:
                self.Ui.radioButton_runtime_none.setChecked(True)
            else:
                self.Ui.radioButton_runtime_listed.setChecked(True)

            if 'score' in whole_fields:
                self.Ui.radioButton_score_more.setChecked(True)
            elif 'score' in none_fields:
                self.Ui.radioButton_score_none.setChecked(True)
            else:
                self.Ui.radioButton_score_listed.setChecked(True)

            if 'director' in whole_fields:
                self.Ui.radioButton_director_more.setChecked(True)
            elif 'director' in none_fields:
                self.Ui.radioButton_director_none.setChecked(True)
            else:
                self.Ui.radioButton_director_listed.setChecked(True)

            if 'series' in whole_fields:
                self.Ui.radioButton_series_more.setChecked(True)
            elif 'series' in none_fields:
                self.Ui.radioButton_series_none.setChecked(True)
            else:
                self.Ui.radioButton_series_listed.setChecked(True)

            if 'studio' in whole_fields:
                self.Ui.radioButton_studio_more.setChecked(True)
            elif 'studio' in none_fields:
                self.Ui.radioButton_studio_none.setChecked(True)
            else:
                self.Ui.radioButton_studio_listed.setChecked(True)

            if 'publisher' in whole_fields:
                self.Ui.radioButton_publisher_more.setChecked(True)
            elif 'publisher' in none_fields:
                self.Ui.radioButton_publisher_none.setChecked(True)
            else:
                self.Ui.radioButton_publisher_listed.setChecked(True)

            if 'wanted' in none_fields:
                self.Ui.radioButton_wanted_none.setChecked(True)
            else:
                self.Ui.radioButton_wanted_listed.setChecked(True)

            try:                                                                # tagline
                nfo_tagline = str(config['website']['nfo_tagline'])
            except:
                nfo_tagline = default_config['nfo_tagline']
            self.Ui.lineEdit_nfo_tagline.setText(str(nfo_tagline))

            try:                                                                # nfo_tag_series
                nfo_tag_series = str(config['website']['nfo_tag_series'])
            except:
                nfo_tag_series = default_config['nfo_tag_series']
            self.Ui.lineEdit_nfo_tag_series.setText(str(nfo_tag_series))
            try:                                                                # nfo_tag_studio
                nfo_tag_studio = str(config['website']['nfo_tag_studio'])
            except:
                nfo_tag_studio = default_config['nfo_tag_studio']
            self.Ui.lineEdit_nfo_tag_studio.setText(str(nfo_tag_studio))
            try:                                                                # nfo_tag_publisher
                nfo_tag_publisher = str(config['website']['nfo_tag_publisher'])
            except:
                nfo_tag_publisher = default_config['nfo_tag_publisher']
            self.Ui.lineEdit_nfo_tag_publisher.setText(str(nfo_tag_publisher))

            try:                                                                # 写入nfo的字段
                nfo_include_new = config['website']['nfo_include_new']
            except:
                nfo_include_new = default_config['nfo_include_new']
            if read_version < 20230302:
                nfo_include_new = nfo_include_new.replace(',set,', ',series_set,')
                nfo_include_new += 'sorttitle,originaltitle,outline,plot_,originalplot,website,'
                if 'release' in nfo_include_new:
                    nfo_include_new += 'release_, releasedate,premiered,'
                if 'mpaa,' in nfo_include_new:
                    nfo_include_new += 'country,customrating,'
                if 'studio,' in nfo_include_new:
                    nfo_include_new += 'maker,'
                if 'publisher,' in nfo_include_new:
                    nfo_include_new += 'label,'

            if 'sorttitle,' in nfo_include_new:
                self.Ui.checkBox_nfo_sorttitle.setChecked(True)
            else:
                self.Ui.checkBox_nfo_sorttitle.setChecked(False)
            if 'originaltitle,' in nfo_include_new:
                self.Ui.checkBox_nfo_originaltitle.setChecked(True)
            else:
                self.Ui.checkBox_nfo_originaltitle.setChecked(False)
            if 'title_cd,' in nfo_include_new:
                self.Ui.checkBox_nfo_title_cd.setChecked(True)
            else:
                self.Ui.checkBox_nfo_title_cd.setChecked(False)
            if 'outline,' in nfo_include_new:
                self.Ui.checkBox_nfo_outline.setChecked(True)
            else:
                self.Ui.checkBox_nfo_outline.setChecked(False)
            if 'plot_,' in nfo_include_new:
                self.Ui.checkBox_nfo_plot.setChecked(True)
            else:
                self.Ui.checkBox_nfo_plot.setChecked(False)
            if 'originalplot,' in nfo_include_new:
                self.Ui.checkBox_nfo_originalplot.setChecked(True)
            else:
                self.Ui.checkBox_nfo_originalplot.setChecked(False)
            if 'outline_no_cdata,' in nfo_include_new:
                self.Ui.checkBox_outline_cdata.setChecked(True)
            else:
                self.Ui.checkBox_outline_cdata.setChecked(False)
            if 'release_,' in nfo_include_new:
                self.Ui.checkBox_nfo_release.setChecked(True)
            else:
                self.Ui.checkBox_nfo_release.setChecked(False)
            if 'releasedate,' in nfo_include_new:
                self.Ui.checkBox_nfo_relasedate.setChecked(True)
            else:
                self.Ui.checkBox_nfo_relasedate.setChecked(False)
            if 'premiered,' in nfo_include_new:
                self.Ui.checkBox_nfo_premiered.setChecked(True)
            else:
                self.Ui.checkBox_nfo_premiered.setChecked(False)

            if 'country,' in nfo_include_new:
                self.Ui.checkBox_nfo_country.setChecked(True)
            else:
                self.Ui.checkBox_nfo_country.setChecked(False)
            if 'mpaa,' in nfo_include_new:
                self.Ui.checkBox_nfo_mpaa.setChecked(True)
            else:
                self.Ui.checkBox_nfo_mpaa.setChecked(False)
            if 'customrating,' in nfo_include_new:
                self.Ui.checkBox_nfo_customrating.setChecked(True)
            else:
                self.Ui.checkBox_nfo_customrating.setChecked(False)
            if 'year,' in nfo_include_new:
                self.Ui.checkBox_nfo_year.setChecked(True)
            else:
                self.Ui.checkBox_nfo_year.setChecked(False)
            if 'runtime,' in nfo_include_new:
                self.Ui.checkBox_nfo_runtime.setChecked(True)
            else:
                self.Ui.checkBox_nfo_runtime.setChecked(False)
            if 'wanted,' in nfo_include_new:
                self.Ui.checkBox_nfo_wanted.setChecked(True)
            else:
                self.Ui.checkBox_nfo_wanted.setChecked(False)
            if 'score,' in nfo_include_new:
                self.Ui.checkBox_nfo_score.setChecked(True)
            else:
                self.Ui.checkBox_nfo_score.setChecked(False)
            if 'criticrating,' in nfo_include_new:
                self.Ui.checkBox_nfo_criticrating.setChecked(True)
            else:
                self.Ui.checkBox_nfo_criticrating.setChecked(False)
            if 'actor,' in nfo_include_new:
                self.Ui.checkBox_nfo_actor.setChecked(True)
            else:
                self.Ui.checkBox_nfo_actor.setChecked(False)
            if 'actor_all,' in nfo_include_new:
                self.Ui.checkBox_nfo_all_actor.setChecked(True)
            else:
                self.Ui.checkBox_nfo_all_actor.setChecked(False)
            if 'director,' in nfo_include_new:
                self.Ui.checkBox_nfo_director.setChecked(True)
            else:
                self.Ui.checkBox_nfo_director.setChecked(False)
            if 'series,' in nfo_include_new:
                self.Ui.checkBox_nfo_series.setChecked(True)
            else:
                self.Ui.checkBox_nfo_series.setChecked(False)
            if 'tag,' in nfo_include_new:
                self.Ui.checkBox_nfo_tag.setChecked(True)
            else:
                self.Ui.checkBox_nfo_tag.setChecked(False)
            if 'genre,' in nfo_include_new:
                self.Ui.checkBox_nfo_genre.setChecked(True)
            else:
                self.Ui.checkBox_nfo_genre.setChecked(False)
            if 'actor_set,' in nfo_include_new:
                self.Ui.checkBox_nfo_actor_set.setChecked(True)
            else:
                self.Ui.checkBox_nfo_actor_set.setChecked(False)
            if 'series_set,' in nfo_include_new:
                self.Ui.checkBox_nfo_set.setChecked(True)
            else:
                self.Ui.checkBox_nfo_set.setChecked(False)
            if 'studio,' in nfo_include_new:
                self.Ui.checkBox_nfo_studio.setChecked(True)
            else:
                self.Ui.checkBox_nfo_studio.setChecked(False)
            if 'maker,' in nfo_include_new:
                self.Ui.checkBox_nfo_maker.setChecked(True)
            else:
                self.Ui.checkBox_nfo_maker.setChecked(False)
            if 'publisher,' in nfo_include_new:
                self.Ui.checkBox_nfo_publisher.setChecked(True)
            else:
                self.Ui.checkBox_nfo_publisher.setChecked(False)
            if 'label,' in nfo_include_new:
                self.Ui.checkBox_nfo_label.setChecked(True)
            else:
                self.Ui.checkBox_nfo_label.setChecked(False)
            if 'poster,' in nfo_include_new:
                self.Ui.checkBox_nfo_poster.setChecked(True)
            else:
                self.Ui.checkBox_nfo_poster.setChecked(False)
            if 'cover,' in nfo_include_new:
                self.Ui.checkBox_nfo_cover.setChecked(True)
            else:
                self.Ui.checkBox_nfo_cover.setChecked(False)
            if 'trailer,' in nfo_include_new:
                self.Ui.checkBox_nfo_trailer.setChecked(True)
            else:
                self.Ui.checkBox_nfo_trailer.setChecked(False)
            if 'website,' in nfo_include_new:
                self.Ui.checkBox_nfo_website.setChecked(True)
            else:
                self.Ui.checkBox_nfo_website.setChecked(False)

            try:                                                                # 翻译引擎
                translate_by = config['website']['translate_by']
            except:
                translate_by = default_config['translate_by']
            if 'youdao' in translate_by:
                self.Ui.checkBox_youdao.setChecked(True)
            if 'google' in translate_by:
                self.Ui.checkBox_google.setChecked(True)
            if 'deepl' in translate_by:
                self.Ui.checkBox_deepl.setChecked(True)
            self.translate_by_list = translate_by.strip(',').split(',') if translate_by.strip(',') else []

            try:                                                                # deepl_key
                self.Ui.lineEdit_deepl_key.setText(str(config['website']['deepl_key']))
            except:
                self.Ui.lineEdit_deepl_key.setText(str(default_config['deepl_key']))

            # ======================================================================================common
            if not config.has_section("common"):
                config.add_section("common")

            try:                                                                # 线程数量
                thread_number = int(config['common']['thread_number'])
            except:
                thread_number = int(default_config['thread_number'])
            self.Ui.horizontalSlider_thread.setValue(thread_number)
            self.Ui.lcdNumber_thread.display(thread_number)

            try:                                                                # 线程延时
                thread_time = int(config['common']['thread_time'])
            except:
                thread_time = int(default_config['thread_time'])
            self.Ui.horizontalSlider_thread_time.setValue(thread_time)
            self.Ui.lcdNumber_thread_time.display(thread_time)

            try:                                                                # javdb 延时
                javdb_time = int(config['common']['javdb_time'])
            except:
                javdb_time = int(default_config['javdb_time'])
            self.Ui.horizontalSlider_javdb_time.setValue(javdb_time)
            self.Ui.lcdNumber_javdb_time.display(javdb_time)

            try:                                                                # 刮削模式
                main_mode = int(config['common']['main_mode'])
            except:
                main_mode = int(default_config['main_mode'])
            if main_mode == 1:
                self.Ui.radioButton_mode_common.setChecked(True)
                self.main_mode = '正常模式'
            elif main_mode == 2:
                self.Ui.radioButton_mode_sort.setChecked(True)
                self.main_mode = '整理模式'
            elif main_mode == 3:
                self.Ui.radioButton_mode_update.setChecked(True)
                self.main_mode = '更新模式'
            elif main_mode == 4:
                self.Ui.radioButton_mode_read.setChecked(True)
                self.main_mode = '读取模式'
            else:
                self.Ui.radioButton_mode_common.setChecked(True)
                self.main_mode = '正常模式'

            try:                                                                # 有nfo，是否执行更新模式
                read_mode = config['common']['read_mode']
            except:
                read_mode = default_config['read_mode']
            if 'has_nfo_update' in read_mode:
                self.Ui.checkBox_read_has_nfo_update.setChecked(True)
            else:
                self.Ui.checkBox_read_has_nfo_update.setChecked(False)
            if 'read_download_again' in read_mode:
                self.Ui.checkBox_read_download_file_again.setChecked(True)
            else:
                self.Ui.checkBox_read_download_file_again.setChecked(False)
            if 'read_translate_again' in read_mode:
                self.Ui.checkBox_read_translate_again.setChecked(True)
            else:
                self.Ui.checkBox_read_translate_again.setChecked(False)
            if 'no_nfo_scrape' in read_mode:
                self.Ui.checkBox_read_no_nfo_scrape.setChecked(True)
            else:
                self.Ui.checkBox_read_no_nfo_scrape.setChecked(False)

            try:                                                                # 更新模式
                self.Ui.checkBox_update_a.setChecked(False)
                update_mode = config['common']['update_mode']
            except:
                update_mode = default_config['update_mode']
            if update_mode == 'c':
                self.Ui.radioButton_update_c.setChecked(True)
            elif update_mode == 'bc':
                self.Ui.radioButton_update_b_c.setChecked(True)
            elif update_mode == 'abc':
                self.Ui.radioButton_update_b_c.setChecked(True)
                self.Ui.checkBox_update_a.setChecked(True)
            elif update_mode == 'd':
                self.Ui.radioButton_update_d_c.setChecked(True)
            else:
                self.Ui.radioButton_update_c.setChecked(True)

            try:                                                                # 更新模式 - a 目录
                self.Ui.lineEdit_update_a_folder.setText(str(config['common']['update_a_folder']))
            except:
                self.Ui.lineEdit_update_a_folder.setText(str(default_config['update_a_folder']))
            try:                                                                # 更新模式 - b 目录
                self.Ui.lineEdit_update_b_folder.setText(str(config['common']['update_b_folder']))
            except:
                self.Ui.lineEdit_update_b_folder.setText(str(default_config['update_b_folder']))
            try:                                                                # 更新模式 - d 目录
                self.Ui.lineEdit_update_d_folder.setText(str(config['common']['update_d_folder']))
            except:
                self.Ui.lineEdit_update_d_folder.setText(str(default_config['update_d_folder']))

            try:                                                                # 软链接
                soft_link = int(config['common']['soft_link'])
            except:
                soft_link = int(default_config['soft_link'])
            if soft_link == 1:
                self.Ui.radioButton_soft_on.setChecked(True)
            elif soft_link == 2:
                self.Ui.radioButton_hard_on.setChecked(True)
            else:
                self.Ui.radioButton_soft_off.setChecked(True)

            try:                                                                # 成功后移动文件
                success_file_move = int(config['common']['success_file_move'])
            except:
                success_file_move = int(default_config['success_file_move'])
            if success_file_move == 0:
                self.Ui.radioButton_succ_move_off.setChecked(True)
            else:
                self.Ui.radioButton_succ_move_on.setChecked(True)

            try:                                                                # 失败后移动文件
                failed_file_move = int(config['common']['failed_file_move'])
            except:
                failed_file_move = int(default_config['failed_file_move'])
            if failed_file_move == 0:
                self.Ui.radioButton_fail_move_off.setChecked(True)
            else:
                self.Ui.radioButton_fail_move_on.setChecked(True)

            try:                                                                # 成功后重命名文件
                success_file_rename = int(config['common']['success_file_rename'])
            except:
                success_file_rename = int(default_config['success_file_rename'])
            if success_file_rename == 0:
                self.Ui.radioButton_succ_rename_off.setChecked(True)
            else:
                self.Ui.radioButton_succ_rename_on.setChecked(True)

            try:                                                                # 结束后删除空文件夹
                del_empty_folder = int(config['common']['del_empty_folder'])
            except:
                del_empty_folder = int(default_config['del_empty_folder'])
            if del_empty_folder == 0:
                self.Ui.radioButton_del_empty_folder_off.setChecked(True)
            else:
                self.Ui.radioButton_del_empty_folder_on.setChecked(True)

            try:                                                                # 显示封面
                show_poster = int(config['common']['show_poster'])
            except:
                show_poster = int(default_config['show_poster'])
            if show_poster == 0:
                self.Ui.checkBox_cover.setChecked(False)
            else:
                self.Ui.checkBox_cover.setChecked(True)

            # ======================================================================================file_download
            if not config.has_section("file_download"):
                config.add_section("file_download")
            try:                                                                # 下载文件
                download_files = config['file_download']['download_files']
            except:
                download_files = default_config['download_files']
            if 'poster' in download_files:
                self.Ui.checkBox_download_poster.setChecked(True)
            else:
                self.Ui.checkBox_download_poster.setChecked(False)
            if 'thumb' in download_files:
                self.Ui.checkBox_download_thumb.setChecked(True)
            else:
                self.Ui.checkBox_download_thumb.setChecked(False)
            if ',fanart' in download_files:
                self.Ui.checkBox_download_fanart.setChecked(True)
            else:
                self.Ui.checkBox_download_fanart.setChecked(False)
            if 'extrafanart,' in download_files:
                self.Ui.checkBox_download_extrafanart.setChecked(True)
            else:
                self.Ui.checkBox_download_extrafanart.setChecked(False)
            if 'trailer,' in download_files:
                self.Ui.checkBox_download_trailer.setChecked(True)
            else:
                self.Ui.checkBox_download_trailer.setChecked(False)
            if 'nfo' in download_files:
                self.Ui.checkBox_download_nfo.setChecked(True)
            else:
                self.Ui.checkBox_download_nfo.setChecked(False)
            if 'extrafanart_extras' in download_files:
                self.Ui.checkBox_extras.setChecked(True)
            else:
                self.Ui.checkBox_extras.setChecked(False)
            if 'extrafanart_copy' in download_files:
                self.Ui.checkBox_download_extrafanart_copy.setChecked(True)
            else:
                self.Ui.checkBox_download_extrafanart_copy.setChecked(False)
            if 'theme_videos' in download_files:
                self.Ui.checkBox_theme_videos.setChecked(True)
            else:
                self.Ui.checkBox_theme_videos.setChecked(False)
            if 'ignore_pic_fail' in download_files:
                self.Ui.checkBox_ignore_pic_fail.setChecked(True)
            else:
                self.Ui.checkBox_ignore_pic_fail.setChecked(False)
            if 'ignore_youma' in download_files:
                self.Ui.checkBox_ignore_youma.setChecked(True)
            else:
                self.Ui.checkBox_ignore_youma.setChecked(False)
            if 'ignore_wuma' in download_files:
                self.Ui.checkBox_ignore_wuma.setChecked(True)
            else:
                self.Ui.checkBox_ignore_wuma.setChecked(False)
            if 'ignore_fc2' in download_files:
                self.Ui.checkBox_ignore_fc2.setChecked(True)
            else:
                self.Ui.checkBox_ignore_fc2.setChecked(False)
            if 'ignore_guochan' in download_files:
                self.Ui.checkBox_ignore_guochan.setChecked(True)
            else:
                self.Ui.checkBox_ignore_guochan.setChecked(False)
            if 'ignore_size' in download_files:
                self.Ui.checkBox_ignore_size.setChecked(True)
            else:
                self.Ui.checkBox_ignore_size.setChecked(False)

            try:                                                                # 保留文件
                keep_files = config['file_download']['keep_files']
            except:
                keep_files = default_config['keep_files']
            if 'poster' in keep_files:
                self.Ui.checkBox_old_poster.setChecked(True)
            else:
                self.Ui.checkBox_old_poster.setChecked(False)
            if 'thumb' in keep_files:
                self.Ui.checkBox_old_thumb.setChecked(True)
            else:
                self.Ui.checkBox_old_thumb.setChecked(False)
            if ',fanart' in keep_files:
                self.Ui.checkBox_old_fanart.setChecked(True)
            else:
                self.Ui.checkBox_old_fanart.setChecked(False)
            if 'extrafanart,' in keep_files:
                self.Ui.checkBox_old_extrafanart.setChecked(True)
            else:
                self.Ui.checkBox_old_extrafanart.setChecked(False)
            if 'trailer' in keep_files:
                self.Ui.checkBox_old_trailer.setChecked(True)
            else:
                self.Ui.checkBox_old_trailer.setChecked(False)
            if 'nfo' in keep_files:
                self.Ui.checkBox_old_nfo.setChecked(True)
            else:
                self.Ui.checkBox_old_nfo.setChecked(False)
            if 'extrafanart_copy' in keep_files:
                self.Ui.checkBox_old_extrafanart_copy.setChecked(True)
            else:
                self.Ui.checkBox_old_extrafanart_copy.setChecked(False)
            if 'theme_videos' in keep_files:
                self.Ui.checkBox_old_theme_videos.setChecked(True)
            else:
                self.Ui.checkBox_old_theme_videos.setChecked(False)

            try:                                                           # 下载高清图片
                download_hd_pics = config['file_download']['download_hd_pics']
            except:
                download_hd_pics = default_config['download_hd_pics']
            if read_version < 20230310:
                download_hd_pics += 'amazon,official,'
            if 'poster' in download_hd_pics:
                self.Ui.checkBox_hd_poster.setChecked(True)
            else:
                self.Ui.checkBox_hd_poster.setChecked(False)
            if 'thumb' in download_hd_pics:
                self.Ui.checkBox_hd_thumb.setChecked(True)
            else:
                self.Ui.checkBox_hd_thumb.setChecked(False)
            if 'amazon' in download_hd_pics:
                self.Ui.checkBox_amazon_big_pic.setChecked(True)
            else:
                self.Ui.checkBox_amazon_big_pic.setChecked(False)
            if 'official' in download_hd_pics:
                self.Ui.checkBox_official_big_pic.setChecked(True)
            else:
                self.Ui.checkBox_official_big_pic.setChecked(False)
            if 'google' in download_hd_pics:
                self.Ui.checkBox_google_big_pic.setChecked(True)
            else:
                self.Ui.checkBox_google_big_pic.setChecked(False)
            if 'goo_only' in download_hd_pics:
                self.Ui.radioButton_google_only.setChecked(True)
            else:
                self.Ui.radioButton_google_first.setChecked(True)
            try:                                                                # Google下载词
                self.Ui.lineEdit_google_used.setText(str(config['file_download']['google_used']))
            except:
                self.Ui.lineEdit_google_used.setText(str(default_config['google_used']))
            try:                                                                # Google过滤词
                default_google_exclude = str(default_config['google_exclude'])
                custom_google_exclude = str(config['file_download']['google_exclude'])
                google_exclude = self.remove_repeat(custom_google_exclude + ',' + default_google_exclude)

            except:
                google_exclude = str(default_config['google_exclude'])
            self.Ui.lineEdit_google_exclude.setText(google_exclude)

            # ======================================================================================Name_Rule
            if not config.has_section("Name_Rule"):
                config.add_section("Name_Rule")
            try:                                                                # 视频目录命名
                self.Ui.lineEdit_dir_name.setText(str(config['Name_Rule']['folder_name']))
            except:
                self.Ui.lineEdit_dir_name.setText(str(default_config['folder_name']))
            try:                                                                # 视频文件名命名（本地文件）
                self.Ui.lineEdit_local_name.setText(str(config['Name_Rule']['naming_file']))
            except:
                self.Ui.lineEdit_local_name.setText(str(default_config['naming_file']))
            try:                                                                # emby视频标题（nfo文件）
                self.Ui.lineEdit_media_name.setText(str(config['Name_Rule']['naming_media']))
            except:
                self.Ui.lineEdit_media_name.setText(str(default_config['naming_media']))
            try:                                                                # 防屏蔽字符
                self.Ui.lineEdit_prevent_char.setText(str(config['Name_Rule']['prevent_char']))
            except:
                self.Ui.lineEdit_prevent_char.setText(str(default_config['prevent_char']))

            try:                                                                # 字段命名规则
                fields_rule = config['Name_Rule']['fields_rule']
            except:
                fields_rule = default_config['fields_rule']
            if read_version < 20230317:
                fields_rule += 'del_char,'
            if 'del_actor' in fields_rule:                                      # 去除标题后的演员名
                self.Ui.checkBox_title_del_actor.setChecked(True)
            else:
                self.Ui.checkBox_title_del_actor.setChecked(False)
            if 'del_char' in fields_rule:                                       # 演员去除括号
                self.Ui.checkBox_actor_del_char.setChecked(True)
            else:
                self.Ui.checkBox_actor_del_char.setChecked(False)
            if 'fc2_seller' in fields_rule:                                     # FC2 演员名
                self.Ui.checkBox_actor_fc2_seller.setChecked(True)
            else:
                self.Ui.checkBox_actor_fc2_seller.setChecked(False)
            if 'del_num' in fields_rule:                                        # 素人番号删除前缀数字
                self.Ui.checkBox_number_del_num.setChecked(True)
            else:
                self.Ui.checkBox_number_del_num.setChecked(False)
            try:                                                                # 字段命名规则-未知演员
                self.Ui.lineEdit_actor_no_name.setText(str(config['Name_Rule']['actor_no_name']))
            except:
                self.Ui.lineEdit_actor_no_name.setText(default_config['actor_no_name'])
            try:                                                                # 字段命名规则-发行日期
                self.Ui.lineEdit_release_rule.setText(str(config['Name_Rule']['release_rule']))
            except:
                self.Ui.lineEdit_release_rule.setText(str(default_config['release_rule']))

            try:                                                                # 长度命名规则-目录
                folder_name_max = config.getint('Name_Rule', 'folder_name_max')
                if folder_name_max <= 0 or folder_name_max > 255:
                    folder_name_max = 60
            except:
                folder_name_max = default_config['folder_name_max']
            self.Ui.lineEdit_folder_name_max.setText(str(folder_name_max))

            try:                                                                # 长度命名规则-文件名
                file_name_max = config.getint('Name_Rule', 'file_name_max')
                if file_name_max <= 0 or file_name_max > 255:
                    file_name_max = 60
            except:
                file_name_max = default_config['file_name_max']
            self.Ui.lineEdit_file_name_max.setText(str(file_name_max))

            try:                                                                # 长度命名规则-演员名
                self.Ui.lineEdit_actor_name_max.setText(str(config.getint('Name_Rule', 'actor_name_max')))
            except:
                self.Ui.lineEdit_actor_name_max.setText(str(default_config['actor_name_max']))

            try:                                                                # 长度命名规则-演员名更多
                self.Ui.lineEdit_actor_name_more.setText(str(config['Name_Rule']['actor_name_more']))
            except:
                self.Ui.lineEdit_actor_name_more.setText(str(default_config['actor_name_more']))

            try:                                                                # 字段命名规则-后缀字段顺序
                suffix_sort = self.get_new_str_2(config['Name_Rule']['suffix_sort'])
            except:
                suffix_sort = str(default_config['suffix_sort'])
            self.Ui.lineEdit_suffix_sort.setText(str(suffix_sort))

            try:                                                                # 版本命名规则-无码破解版
                self.Ui.lineEdit_umr_style.setText(str(config['Name_Rule']['umr_style']))
            except:
                self.Ui.lineEdit_umr_style.setText(str(default_config['umr_style']))
            try:                                                                # 版本命名规则-无码流出版
                self.Ui.lineEdit_leak_style.setText(str(config['Name_Rule']['leak_style']))
            except:
                self.Ui.lineEdit_leak_style.setText(str(default_config['leak_style']))
            try:                                                                # 版本命名规则-无码版
                self.Ui.lineEdit_wuma_style.setText(str(config['Name_Rule']['wuma_style']))
            except:
                self.Ui.lineEdit_wuma_style.setText(str(default_config['wuma_style']))
            try:                                                                # 版本命名规则-有码版
                self.Ui.lineEdit_youma_style.setText(str(config['Name_Rule']['youma_style']))
            except:
                self.Ui.lineEdit_youma_style.setText(str(default_config['youma_style']))
            try:
                show_moword = config['Name_Rule']['show_moword']
            except:
                show_moword = default_config['show_moword']
            if 'folder' in show_moword:                                         # 显示版本命名字符-视频目录名
                self.Ui.checkBox_foldername_mosaic.setChecked(True)
            else:
                self.Ui.checkBox_foldername_mosaic.setChecked(False)
            if 'file' in show_moword:                                           # 显示版本命名字符-视频文件名
                self.Ui.checkBox_filename_mosaic.setChecked(True)
            else:
                self.Ui.checkBox_filename_mosaic.setChecked(False)
            try:
                show_4k = config['Name_Rule']['show_4k']
            except:
                show_4k = default_config['show_4k']
            if 'folder' in show_4k:                                         # 显示4k
                self.Ui.checkBox_foldername_4k.setChecked(True)
            else:
                self.Ui.checkBox_foldername_4k.setChecked(False)
            if 'file' in show_4k:                                           # 显示4k
                self.Ui.checkBox_filename_4k.setChecked(True)
            else:
                self.Ui.checkBox_filename_4k.setChecked(False)

            try:                                                                # 分集命名规则
                cd_name = int(config['Name_Rule']['cd_name'])
            except:
                cd_name = int(default_config['cd_name'])
            if cd_name == 0:
                self.Ui.radioButton_cd_part_lower.setChecked(True)
            elif cd_name == 1:
                self.Ui.radioButton_cd_part_upper.setChecked(True)
            else:
                self.Ui.radioButton_cd_part_digital.setChecked(True)

            try:
                cd_char = config['Name_Rule']['cd_char']
            except:
                cd_char = default_config['cd_char']
            if read_version < 20230321:
                cd_char += ',underline,'
            if 'letter' in cd_char:                                            # 允许分集识别字母不含C
                self.Ui.checkBox_cd_part_a.setChecked(True)
                self.Ui.checkBox_cd_part_c.setEnabled(True)
            else:
                self.Ui.checkBox_cd_part_a.setChecked(False)
                self.Ui.checkBox_cd_part_c.setEnabled(False)
            if 'endc' in cd_char:                                              # 允许分集识别字母C
                self.Ui.checkBox_cd_part_c.setChecked(True)
            else:
                self.Ui.checkBox_cd_part_c.setChecked(False)
            if 'digital' in cd_char:                                           # 允许分集识别数字
                self.Ui.checkBox_cd_part_01.setChecked(True)
            else:
                self.Ui.checkBox_cd_part_01.setChecked(False)
            if 'middle_number' in cd_char:                                     # 允许分集识别中间数字
                self.Ui.checkBox_cd_part_1_xxx.setChecked(True)
            else:
                self.Ui.checkBox_cd_part_1_xxx.setChecked(False)

            if 'underline' in cd_char:                                         # 允许分隔符下划线
                self.Ui.checkBox_cd_part_underline.setChecked(True)
            else:
                self.Ui.checkBox_cd_part_underline.setChecked(False)
            if 'space' in cd_char:                                             # 允许分隔符空格
                self.Ui.checkBox_cd_part_space.setChecked(True)
            else:
                self.Ui.checkBox_cd_part_space.setChecked(False)
            if 'point' in cd_char:                                            # 允许分隔符小数点
                self.Ui.checkBox_cd_part_point.setChecked(True)
            else:
                self.Ui.checkBox_cd_part_point.setChecked(False)

            try:                                                                # 图片命名规则
                pic_name = int(config['Name_Rule']['pic_name'])
            except:
                pic_name = int(default_config['pic_name'])
            if pic_name == 0:
                self.Ui.radioButton_pic_with_filename.setChecked(True)
            else:
                self.Ui.radioButton_pic_no_filename.setChecked(True)

            try:                                                                # 预告片命名规则
                trailer_name = int(config['Name_Rule']['trailer_name'])
            except:
                trailer_name = int(default_config['trailer_name'])
            if trailer_name == 0:
                self.Ui.radioButton_trailer_with_filename.setChecked(True)
            else:
                self.Ui.radioButton_trailer_no_filename.setChecked(True)
            try:                                                                # 画质命名规则
                hd_name = config['Name_Rule']['hd_name']
            except:
                hd_name = default_config['hd_name']
            if hd_name == 'height':
                self.Ui.radioButton_definition_height.setChecked(True)
            else:
                self.Ui.radioButton_definition_hd.setChecked(True)
            try:                                                                # 分辨率获取方式
                hd_get = config['Name_Rule']['hd_get']
            except:
                hd_get = default_config['hd_get']
            if hd_get == 'video':
                self.Ui.radioButton_videosize_video.setChecked(True)
            elif hd_get == 'path':
                self.Ui.radioButton_videosize_path.setChecked(True)
            else:
                self.Ui.radioButton_videosize_none.setChecked(True)

            # ======================================================================================字幕
            if not config.has_section("subtitle"):
                config.add_section("subtitle")

            try:                                                                # 中文字幕判断字符
                self.Ui.lineEdit_cnword_char.setText(str(config['subtitle']['cnword_char']))
            except:
                self.Ui.lineEdit_cnword_char.setText(str(default_config['cnword_char']))

            try:                                                                # 中文字幕字符样式
                self.Ui.lineEdit_cnword_style.setText(str(config['subtitle']['cnword_style']).strip('^'))
            except:
                self.Ui.lineEdit_cnword_style.setText(str(default_config['cnword_style']).strip('^'))

            try:                                                                # 显示中文字幕字符-视频目录名
                folder_cnword = config['subtitle']['folder_cnword']
            except:
                folder_cnword = default_config['folder_cnword']
            if folder_cnword == 'off':
                self.Ui.checkBox_foldername.setChecked(False)
            else:
                self.Ui.checkBox_foldername.setChecked(True)

            try:                                                                # 显示中文字幕字符-视频文件名
                file_cnword = config['subtitle']['file_cnword']
            except:
                file_cnword = default_config['file_cnword']
            if file_cnword == 'off':
                self.Ui.checkBox_filename.setChecked(False)
            else:
                self.Ui.checkBox_filename.setChecked(True)

            try:                                                                # 外挂字幕文件目录
                self.Ui.lineEdit_sub_folder.setText(self.convert_path(config['subtitle']['subtitle_folder']))
            except:
                self.Ui.lineEdit_sub_folder.setText('')

            try:                                                                # 自动添加字幕
                subtitle_add = str(config['subtitle']['subtitle_add'])
            except:
                subtitle_add = default_config['subtitle_add']
            if subtitle_add == 'on':
                self.Ui.radioButton_add_sub_on.setChecked(True)
            else:
                self.Ui.radioButton_add_sub_off.setChecked(True)

            try:                                                                # 字幕文件名添加.chs后缀
                subtitle_add_chs = config['subtitle']['subtitle_add_chs']
            except:
                subtitle_add_chs = default_config['subtitle_add_chs']
            if subtitle_add_chs == 'on':
                self.Ui.checkBox_sub_add_chs.setChecked(True)
            else:
                self.Ui.checkBox_sub_add_chs.setChecked(False)

            try:                                                                # 重新刮削新添加字幕的视频
                subtitle_add_rescrape = config['subtitle']['subtitle_add_rescrape']
            except:
                subtitle_add_rescrape = default_config['subtitle_add_rescrape']
            if subtitle_add_rescrape == 'on':
                self.Ui.checkBox_sub_rescrape.setChecked(True)
            else:
                self.Ui.checkBox_sub_rescrape.setChecked(False)

            # ======================================================================================emby
            if not config.has_section("emby"):
                config.add_section("emby")
            try:
                server_type = config['emby']['server_type']                     # 服务器类型
                if 'emby' in server_type:
                    self.Ui.radioButton_server_emby.setChecked(True)
                else:
                    self.Ui.radioButton_server_jellyfin.setChecked(True)
            except:
                self.Ui.radioButton_server_emby.setChecked(True)
            try:                                                                # emby地址
                self.Ui.lineEdit_emby_url.setText(str(config['emby']['emby_url']))
            except:
                self.Ui.lineEdit_emby_url.setText(str(default_config['emby_url']))
            try:                                                                # emby密钥
                self.Ui.lineEdit_api_key.setText(str(config['emby']['api_key']))
            except:
                self.Ui.lineEdit_api_key.setText(str(default_config['api_key']))

            try:
                emby_on = config['emby']['emby_on']
            except:
                emby_on = default_config['emby_on']
            if 'actor_info_zh_cn' in emby_on:
                self.Ui.radioButton_actor_info_zh_cn.setChecked(True)
            elif 'actor_info_zh_tw' in emby_on:
                self.Ui.radioButton_actor_info_zh_tw.setChecked(True)
            else:
                self.Ui.radioButton_actor_info_ja.setChecked(True)
            if 'actor_info_translate' in emby_on:
                self.Ui.checkBox_actor_info_translate.setChecked(True)
            else:
                self.Ui.checkBox_actor_info_translate.setChecked(False)
            if 'actor_info_all' in emby_on:
                self.Ui.radioButton_actor_info_all.setChecked(True)
            else:
                self.Ui.radioButton_actor_info_miss.setChecked(True)
            if 'actor_info_photo' in emby_on:
                self.Ui.checkBox_actor_info_photo.setChecked(True)
            else:
                self.Ui.checkBox_actor_info_photo.setChecked(False)
            if 'actor_photo_local' in emby_on:
                self.Ui.radioButton_actor_photo_local.setChecked(True)
            else:
                self.Ui.radioButton_actor_photo_net.setChecked(True)
            if 'graphis_backdrop' in emby_on:
                self.Ui.checkBox_actor_photo_ne_backdrop.setChecked(True)
            else:
                self.Ui.checkBox_actor_photo_ne_backdrop.setChecked(False)
            if 'graphis_face' in emby_on:
                self.Ui.checkBox_actor_photo_ne_face.setChecked(True)
            else:
                self.Ui.checkBox_actor_photo_ne_face.setChecked(False)
            if 'graphis_new' in emby_on:
                self.Ui.checkBox_actor_photo_ne_new.setChecked(True)
            else:
                self.Ui.checkBox_actor_photo_ne_new.setChecked(False)
            if 'actor_photo_all' in emby_on:
                self.Ui.radioButton_actor_photo_all.setChecked(True)
            else:
                self.Ui.radioButton_actor_photo_miss.setChecked(True)
            if 'actor_photo_auto' in emby_on:
                self.Ui.checkBox_actor_photo_auto.setChecked(True)
            else:
                self.Ui.checkBox_actor_photo_auto.setChecked(False)
            if 'actor_replace' in emby_on:
                self.Ui.checkBox_actor_pic_replace.setChecked(True)
            else:
                self.Ui.checkBox_actor_pic_replace.setChecked(False)

            try:                                                                # 网络头像库 gfriends 项目地址
                self.Ui.lineEdit_net_actor_photo.setText(config['emby']['gfriends_github'])
            except:
                self.Ui.lineEdit_net_actor_photo.setText('https://github.com/gfriends/gfriends')
            try:                                                                # 本地头像目录
                self.Ui.lineEdit_actor_photo_folder.setText(self.convert_path(config['emby']['actor_photo_folder']))
            except:
                self.Ui.lineEdit_actor_photo_folder.setText('')

            # ======================================================================================mark
            if not config.has_section("mark"):
                config.add_section("mark")
            try:                                                                # 封面图加水印
                poster_mark = int(config['mark']['poster_mark'])
            except:
                poster_mark = int(default_config['poster_mark'])
            if poster_mark == 0:
                self.Ui.checkBox_poster_mark.setChecked(False)
            else:
                self.Ui.checkBox_poster_mark.setChecked(True)

            try:                                                                # 缩略图加水印
                thumb_mark = int(config['mark']['thumb_mark'])
            except:
                thumb_mark = int(default_config['thumb_mark'])
            if thumb_mark == 0:
                self.Ui.checkBox_thumb_mark.setChecked(False)
            else:
                self.Ui.checkBox_thumb_mark.setChecked(True)

            try:                                                                # 艺术图加水印
                fanart_mark = int(config['mark']['fanart_mark'])
            except:
                fanart_mark = int(default_config['fanart_mark'])
            if fanart_mark == 0:
                self.Ui.checkBox_fanart_mark.setChecked(False)
            else:
                self.Ui.checkBox_fanart_mark.setChecked(True)

            try:                                                                # 水印大小
                mark_size = int(config['mark']['mark_size'])
            except:
                mark_size = int(default_config['mark_size'])
            self.Ui.horizontalSlider_mark_size.setValue(mark_size)
            self.Ui.lcdNumber_mark_size.display(mark_size)

            try:                                                                # 水印类型
                mark_type = config['mark']['mark_type']
            except:
                mark_type = default_config['mark_type']
            if 'sub' in mark_type:
                self.Ui.checkBox_sub.setChecked(True)
            else:
                self.Ui.checkBox_sub.setChecked(False)
            if 'youma' in mark_type:
                self.Ui.checkBox_censored.setChecked(True)
            else:
                self.Ui.checkBox_censored.setChecked(False)
            if 'umr' in mark_type:
                self.Ui.checkBox_umr.setChecked(True)
            else:
                self.Ui.checkBox_umr.setChecked(False)
            if 'leak' in mark_type:
                self.Ui.checkBox_leak.setChecked(True)
            else:
                self.Ui.checkBox_leak.setChecked(False)
            if 'uncensored' in mark_type:
                self.Ui.checkBox_uncensored.setChecked(True)
            else:
                self.Ui.checkBox_uncensored.setChecked(False)
            if 'hd' in mark_type:
                self.Ui.checkBox_hd.setChecked(True)
            else:
                self.Ui.checkBox_hd.setChecked(False)

            try:                                                                # 水印位置是否固定
                mark_fixed = config['mark']['mark_fixed']
            except:
                mark_fixed = default_config['mark_fixed']
            if mark_fixed == 'off':
                self.Ui.radioButton_not_fixed_position.setChecked(True)
            elif mark_fixed == 'corner':
                self.Ui.radioButton_fixed_corner.setChecked(True)
            else:
                self.Ui.radioButton_fixed_position.setChecked(True)

            try:                                                                # 首个水印位置
                mark_pos = config['mark']['mark_pos']
            except:
                mark_pos = default_config['mark_pos']
            if mark_pos == 'top_left':
                self.Ui.radioButton_top_left.setChecked(True)
            elif mark_pos == 'top_right':
                self.Ui.radioButton_top_right.setChecked(True)
            elif mark_pos == 'bottom_left':
                self.Ui.radioButton_bottom_left.setChecked(True)
            elif mark_pos == 'bottom_right':
                self.Ui.radioButton_bottom_right.setChecked(True)
            else:
                self.Ui.radioButton_top_left.setChecked(True)

            try:                                                                # 固定一个位置
                mark_pos_corner = config['mark']['mark_pos_corner']
            except:
                mark_pos_corner = default_config['mark_pos_corner']
            if mark_pos_corner == 'top_left':
                self.Ui.radioButton_top_left_corner.setChecked(True)
            elif mark_pos_corner == 'top_right':
                self.Ui.radioButton_top_right_corner.setChecked(True)
            elif mark_pos_corner == 'bottom_left':
                self.Ui.radioButton_bottom_left_corner.setChecked(True)
            elif mark_pos_corner == 'bottom_right':
                self.Ui.radioButton_bottom_right_corner.setChecked(True)
            else:
                self.Ui.radioButton_top_left_corner.setChecked(True)

            try:                                                                # hd水印位置
                mark_pos_hd = config['mark']['mark_pos_hd']
            except:
                mark_pos_hd = default_config['mark_pos_hd']
            if mark_pos_hd == 'top_left':
                self.Ui.radioButton_top_left_hd.setChecked(True)
            elif mark_pos_hd == 'top_right':
                self.Ui.radioButton_top_right_hd.setChecked(True)
            elif mark_pos_hd == 'bottom_left':
                self.Ui.radioButton_bottom_left_hd.setChecked(True)
            elif mark_pos_hd == 'bottom_right':
                self.Ui.radioButton_bottom_right_hd.setChecked(True)
            else:
                self.Ui.radioButton_bottom_right_hd.setChecked(True)

            try:                                                                # 字幕水印位置
                mark_pos_sub = config['mark']['mark_pos_sub']
            except:
                mark_pos_sub = default_config['mark_pos_sub']
            if mark_pos_sub == 'top_left':
                self.Ui.radioButton_top_left_sub.setChecked(True)
            elif mark_pos_sub == 'top_right':
                self.Ui.radioButton_top_right_sub.setChecked(True)
            elif mark_pos_sub == 'bottom_left':
                self.Ui.radioButton_bottom_left_sub.setChecked(True)
            elif mark_pos_sub == 'bottom_right':
                self.Ui.radioButton_bottom_right_sub.setChecked(True)
            else:
                self.Ui.radioButton_top_left_sub.setChecked(True)

            try:                                                                # 马赛克水印位置
                mark_pos_mosaic = config['mark']['mark_pos_mosaic']
            except:
                mark_pos_mosaic = default_config['mark_pos_mosaic']
            if mark_pos_mosaic == 'top_left':
                self.Ui.radioButton_top_left_mosaic.setChecked(True)
            elif mark_pos_mosaic == 'top_right':
                self.Ui.radioButton_top_right_mosaic.setChecked(True)
            elif mark_pos_mosaic == 'bottom_left':
                self.Ui.radioButton_bottom_left_mosaic.setChecked(True)
            elif mark_pos_mosaic == 'bottom_right':
                self.Ui.radioButton_bottom_right_mosaic.setChecked(True)
            else:
                self.Ui.radioButton_top_right_mosaic.setChecked(True)

            # ======================================================================================proxy
            if not config.has_section("proxy"):
                config.add_section("proxy")

            try:                                                                # 代理类型
                proxy_type = config['proxy']['type']
            except:
                proxy_type = default_config['type']
            if proxy_type == 'no':
                self.Ui.radioButton_proxy_nouse.setChecked(True)
            elif proxy_type == 'http':
                self.Ui.radioButton_proxy_http.setChecked(True)
            elif proxy_type == 'socks5':
                self.Ui.radioButton_proxy_socks5.setChecked(True)
            else:
                self.Ui.radioButton_proxy_nouse.setChecked(True)

            try:                                                                # 代理地址
                self.Ui.lineEdit_proxy.setText(str(config['proxy']['proxy']))
            except:
                self.Ui.lineEdit_proxy.setText(str(default_config['proxy']))

            try:                                                                # 超时时间
                timeout = int(config['proxy']['timeout'])
            except:
                timeout = int(default_config['timeout'])
            self.Ui.horizontalSlider_timeout.setValue(timeout)
            self.Ui.lcdNumber_timeout.display(timeout)

            try:                                                                # 重试次数
                retry_count = int(config['proxy']['retry'])
            except:
                retry_count = int(default_config['retry'])
            self.Ui.horizontalSlider_retry.setValue(retry_count)
            self.Ui.lcdNumber_retry.display(retry_count)

            try:                                                                # api token
                self.Ui.lineEdit_api_token_theporndb.setText(self.convert_path(config['proxy']['theporndb_api_token']))
            except:
                self.Ui.lineEdit_api_token_theporndb.setText(str(default_config['theporndb_api_token']))

            try:                                                                # javbus网址
                javbus_website = str(config['proxy']['javbus_website']).strip('/')
                if javbus_website and 'http' not in javbus_website:
                    javbus_website = 'https://' + javbus_website
                self.Ui.lineEdit_javbus_website.setText(javbus_website)
            except:
                self.Ui.lineEdit_javbus_website.setText('')

            try:                                                                # javdb网址
                javdb_website = str(config['proxy']['javdb_website']).strip('/')
                if javdb_website and 'http' not in javdb_website:
                    javdb_website = 'https://' + javdb_website
                self.Ui.lineEdit_javdb_website.setText(javdb_website)
            except:
                self.Ui.lineEdit_javdb_website.setText('')

            try:                                                                # iqqtv网址
                iqqtv_website = str(config['proxy']['iqqtv_website']).strip('/')
                if iqqtv_website and 'http' not in iqqtv_website:
                    iqqtv_website = 'https://' + iqqtv_website
                self.Ui.lineEdit_iqqtv_website.setText(iqqtv_website)
            except:
                self.Ui.lineEdit_iqqtv_website.setText('')

            try:                                                                # avsex网址
                avsex_website = str(config['proxy']['avsex_website']).replace('/#/home', '').strip('/')
                if avsex_website and 'http' not in avsex_website:
                    avsex_website = 'https://' + avsex_website
                self.Ui.lineEdit_avsex_website.setText(avsex_website)
            except:
                self.Ui.lineEdit_avsex_website.setText('')

            try:                                                                # hdouban网址
                hdouban_website = str(config['proxy']['hdouban_website']).strip('/')
                if hdouban_website and 'http' not in hdouban_website:
                    hdouban_website = 'https://' + hdouban_website
                self.Ui.lineEdit_hdouban_website.setText(hdouban_website)
            except:
                self.Ui.lineEdit_hdouban_website.setText('')

            try:                                                                # mdtv网址
                mdtv_website = str(config['proxy']['mdtv_website']).strip('/')
                if mdtv_website and 'http' not in mdtv_website:
                    mdtv_website = 'https://' + mdtv_website
                self.Ui.lineEdit_mdtv_website.setText(mdtv_website)
            except:
                self.Ui.lineEdit_mdtv_website.setText('')

            try:                                                                # airav_cc网址
                airavcc_website = str(config['proxy']['airavcc_website']).strip('/')
                if airavcc_website and 'http' not in airavcc_website:
                    airavcc_website = 'https://' + airavcc_website
                self.Ui.lineEdit_airavcc_website.setText(airavcc_website)
            except:
                self.Ui.lineEdit_airavcc_website.setText('')

            try:                                                                # lulubar网址
                lulubar_website = str(config['proxy']['lulubar_website']).strip('/')
                if lulubar_website and 'http' not in lulubar_website:
                    lulubar_website = 'https://' + lulubar_website
                self.Ui.lineEdit_lulubar_website.setText(lulubar_website)
            except:
                self.Ui.lineEdit_lulubar_website.setText('')

            try:                                                                # javlibrary 网址
                javlibrary_website = str(config['proxy']['javlibrary_website']).strip('/')
                if javlibrary_website and 'http' not in javlibrary_website:
                    javlibrary_website = 'https://' + javlibrary_website
                self.Ui.lineEdit_javlibrary_website.setText(javlibrary_website)
            except:
                self.Ui.lineEdit_javlibrary_website.setText('')

            # ======================================================================================Cookies
            if not config.has_section("Cookies"):
                config.add_section("Cookies")
            try:                                                                # javdb cookie
                self.set_javdb_cookie.emit(config['Cookies']['javdb'])
            except:
                self.set_javdb_cookie.emit('')
            try:                                                                # javbus cookie
                self.set_javbus_cookie.emit(config['Cookies']['javbus'])
            except:
                self.set_javbus_cookie.emit('')

            # ======================================================================================other
            if not config.has_section("other"):
                config.add_section("other")

            try:                                                                # 间歇刮削文件数量
                rest_count = int(config['other']['rest_count'])
                if rest_count == 0:
                    rest_count = 1
            except:
                rest_count = int(default_config['rest_count'])
            self.Ui.lineEdit_rest_count.setText(str(rest_count))
            self.rest_count = int(rest_count)

            try:                                                                # 间歇刮削间隔时间
                rest_time = config['other']['rest_time']
                if not re.search(r'^\d+:\d+:\d+$', rest_time):
                    rest_time = default_config['rest_time']
            except:
                rest_time = default_config['rest_time']
            self.Ui.lineEdit_rest_time.setText(str(rest_time))
            h, m, s = re.findall(r'^(\d+):(\d+):(\d+)$', rest_time)[0]          # 换算（秒）
            self.rest_time_convert = int(h) * 3600 + int(m) * 60 + int(s)

            try:                                                                # 循环任务间隔时间
                timed_interval = config['other']['timed_interval']
                if not re.search(r'^\d+:\d+:\d+$', timed_interval):
                    timed_interval = default_config['timed_interval']
            except:
                timed_interval = default_config['timed_interval']
            self.Ui.lineEdit_timed_interval.setText(timed_interval)
            h, m, s = re.findall(r'^(\d+):(\d+):(\d+)$', timed_interval)[0]     # 换算（毫秒）
            timed_interval_convert = (int(h) * 3600 + int(m) * 60 + int(s)) * 1000
            self.timer_scrape.stop()
            try:                                                                # 间歇刮削间隔时间
                self.statement = int(config['other']['statement'])
            except:
                self.statement = int(default_config['statement'])
            try:
                switch_on = config['other']['switch_on']
                if read_version < 20230404:
                    switch_on += 'ipv4_only,'
            except:
                switch_on = default_config['switch_on']
            if 'auto_start' in switch_on:
                self.Ui.checkBox_auto_start.setChecked(True)
            else:
                self.Ui.checkBox_auto_start.setChecked(False)
            if 'auto_exit' in switch_on:
                self.Ui.checkBox_auto_exit.setChecked(True)
            else:
                self.Ui.checkBox_auto_exit.setChecked(False)
            if 'rest_scrape' in switch_on:
                self.Ui.checkBox_rest_scrape.setChecked(True)
                self.rest_scrape = True
            else:
                self.Ui.checkBox_rest_scrape.setChecked(False)
                self.rest_scrape = False
            if 'timed_scrape' in switch_on:
                self.Ui.checkBox_timed_scrape.setChecked(True)
                self.timer_scrape.start(timed_interval_convert)
            else:
                self.Ui.checkBox_timed_scrape.setChecked(False)
            if 'remain_task' in switch_on:
                self.Ui.checkBox_remain_task.setChecked(True)
            else:
                self.Ui.checkBox_remain_task.setChecked(False)
            if 'show_dialog_exit' in switch_on:
                self.Ui.checkBox_show_dialog_exit.setChecked(True)
            else:
                self.Ui.checkBox_show_dialog_exit.setChecked(False)
            if 'show_dialog_stop_scrape' in switch_on:
                self.Ui.checkBox_show_dialog_stop_scrape.setChecked(True)
            else:
                self.Ui.checkBox_show_dialog_stop_scrape.setChecked(False)
            if 'dark_mode' in switch_on:
                self.Ui.checkBox_dark_mode.setChecked(True)
                self.dark_mode = True
            else:
                self.Ui.checkBox_dark_mode.setChecked(False)
                self.dark_mode = False
            if 'copy_netdisk_nfo' in switch_on:
                self.Ui.checkBox_copy_netdisk_nfo.setChecked(True)
            else:
                self.Ui.checkBox_copy_netdisk_nfo.setChecked(False)
            if 'show_logs' in switch_on:
                self.show_hide_logs(True)
            else:
                self.show_hide_logs(False)
            if 'ipv4_only' in switch_on:
                self.Ui.checkBox_net_ipv4_only.setChecked(True)
            else:
                self.Ui.checkBox_net_ipv4_only.setChecked(False)
            if 'qt_dialog' in switch_on:
                self.Ui.checkBox_dialog_qt.setChecked(True)
                self.options = QFileDialog.DontUseNativeDialog
            else:
                self.Ui.checkBox_dialog_qt.setChecked(False)
                self.options = QFileDialog.Options()
            if 'theporndb_no_hash' in switch_on:
                self.Ui.checkBox_theporndb_hash.setChecked(True)
            else:
                self.Ui.checkBox_theporndb_hash.setChecked(False)
            if 'sort_del' in switch_on:
                self.Ui.checkBox_sortmode_delpic.setChecked(True)
            else:
                self.Ui.checkBox_sortmode_delpic.setChecked(False)
            if 'hide_close' in switch_on:
                self.Ui.radioButton_hide_close.setChecked(True)
            elif 'hide_mini' in switch_on:
                self.Ui.radioButton_hide_mini.setChecked(True)
            else:
                self.Ui.radioButton_hide_none.setChecked(True)
            if self.is_windows:
                self.Ui.checkBox_hide_dock_icon.setEnabled(False)
                self.Ui.checkBox_hide_menu_icon.setEnabled(False)
                try:
                    self.tray_icon.show()
                except:
                    self.Init_QSystemTrayIcon()
                    if not mdcx_config:
                        self.tray_icon.showMessage(f"MDCx {self.localversion}", u'配置写入失败！所在目录没有读写权限！', QIcon(self.icon_ico), 3000)
                if 'passthrough' in switch_on:
                    self.Ui.checkBox_highdpi_passthrough.setChecked(True)
                    if not os.path.isfile('highdpi_passthrough'):
                        open('highdpi_passthrough', 'w').close()
                else:
                    self.Ui.checkBox_highdpi_passthrough.setChecked(False)
                    if os.path.isfile('highdpi_passthrough'):
                        delete_file('highdpi_passthrough')
            else:
                self.Ui.checkBox_highdpi_passthrough.setEnabled(False)
                if 'hide_menu' in switch_on:
                    self.Ui.checkBox_hide_menu_icon.setChecked(True)
                    try:
                        self.tray_icon.hide()
                    except:
                        pass
                else:
                    self.Ui.checkBox_hide_menu_icon.setChecked(False)
                    try:
                        self.tray_icon.show()
                    except:
                        self.Init_QSystemTrayIcon()
                        if not mdcx_config:
                            self.tray_icon.showMessage(f"MDCx {self.localversion}", u'配置写入失败！所在目录没有读写权限！', QIcon(self.icon_ico), 3000)

                if 'hide_dock' in switch_on:
                    self.Ui.checkBox_hide_dock_icon.setChecked(True)
                    if not os.path.isfile('Img/1'):
                        open('Img/1', 'w').close()
                else:
                    self.Ui.checkBox_hide_dock_icon.setChecked(False)
                    if os.path.isfile('Img/1'):
                        delete_file('Img/1')

            try:                                                                # 显示字段刮削过程
                if config['other']['show_web_log'] == 'on':
                    self.Ui.checkBox_show_web_log.setChecked(True)
                else:
                    self.Ui.checkBox_show_web_log.setChecked(False)
            except:
                self.Ui.checkBox_show_web_log.setChecked(False)
            try:                                                                # 显示字段来源信息
                if config['other']['show_from_log'] == 'on':
                    self.Ui.checkBox_show_from_log.setChecked(True)
                else:
                    self.Ui.checkBox_show_from_log.setChecked(False)
            except:
                self.Ui.checkBox_show_from_log.setChecked(True)
            try:                                                                # 显示字段内容信息
                if config['other']['show_data_log'] == 'on':
                    self.Ui.checkBox_show_data_log.setChecked(True)
                else:
                    self.Ui.checkBox_show_data_log.setChecked(False)
            except:
                self.Ui.checkBox_show_data_log.setChecked(True)
            try:                                                                # 保存日志
                if config['other']['save_log'] == 'off':
                    self.Ui.radioButton_log_off.setChecked(True)
                else:
                    self.Ui.radioButton_log_on.setChecked(True)
            except:
                self.Ui.radioButton_log_on.setChecked(True)
            try:                                                                # 检查更新
                if config['other']['update_check'] == 'off':
                    self.Ui.radioButton_update_off.setChecked(True)
                else:
                    self.Ui.radioButton_update_on.setChecked(True)
            except:
                self.Ui.radioButton_update_on.setChecked(True)

            try:                                                                # 本地资源库
                self.Ui.lineEdit_local_library_path.setText(self.convert_path(config['other']['local_library']))
            except:
                self.Ui.lineEdit_local_library_path.setText('')
            try:                                                                # 演员名
                self.Ui.lineEdit_actors_name.setText(str(config['other']['actors_name']))
            except:
                self.Ui.lineEdit_actors_name.setText('')
            try:                                                                # 网盘目录
                self.Ui.lineEdit_netdisk_path.setText(self.convert_path(config['other']['netdisk_path']))
            except:
                self.Ui.lineEdit_netdisk_path.setText('')
            try:                                                                # 本地磁盘目录
                self.Ui.lineEdit_localdisk_path.setText(self.convert_path(config['other']['localdisk_path']))
            except:
                self.Ui.lineEdit_localdisk_path.setText('')
            try:                                                                # 窗口标题栏
                if config['other']['window_title'] == 'hide':
                    self.Ui.checkBox_hide_window_title.setChecked(True)
                else:
                    self.Ui.checkBox_hide_window_title.setChecked(False)
            except:
                self.Ui.checkBox_hide_window_title.setChecked(True)

            # ======================================================================================END
            self.checkBox_i_agree_clean_clicked()
            self.update_userdata_path()
            self.update_mark_icon_path()
            self.save_config_clicked()
            self.show_config_info()
            self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
            self.activateWindow()
            # self.raise_()
            try:
                self.set_label_file_path.emit('🎈 当前刮削路径: \n %s' % self.get_movie_path_setting()[0]) # 主界面右上角显示提示信息
            except:
                pass
        else:                                                                                       # ini不存在，重新创建
            self.show_log_text('Create config file: %s ' % config_path)
            self.pushButton_init_config_clicked()

    def show_config_info(self):
        try:
            scrape_like = self.scrape_like
            if self.config.get('scrape_like') == 'single':
                scrape_like += f" · {self.config.get('website_single')}"
            if self.config.get('soft_link') == 1:
                scrape_like += " · 软连接开"
            elif self.config.get('soft_link') == 2:
                scrape_like += " · 硬连接开"
            self.show_log_text(' 🛠 当前配置：%s 加载完成！\n 📂 程序目录：%s \n 📂 刮削目录：%s \n 💠 刮削模式：%s · %s \n 🖥️ 系统信息：%s \n 🐰 软件版本：%s \n' % (self.config_path, self.main_path, self.get_movie_path_setting()[0], self.main_mode, scrape_like, platform.platform(), self.localversion))
        except:
            pass

    # ======================================================================================读取设置页的设置, 保存config.ini，然后重新加载

    def check_mac_config_folder(self):
        if self.check_mac and not self.is_windows and '.app/Contents/Resources' in self.config_folder:
            self.check_mac = False
            box = QMessageBox(QMessageBox.Warning, '选择配置文件目录', f'检测到当前配置文件目录为：\n {self.config_folder}\n\n由于 MacOS 平台在每次更新 APP 版本时会覆盖该目录的配置，因此请选择其他的配置目录！\n这样下次更新 APP 时，选择相同的配置目录即可读取你之前的配置！！！')
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            box.button(QMessageBox.Yes).setText('选择目录')
            box.button(QMessageBox.No).setText('取消')
            box.setDefaultButton(QMessageBox.Yes)
            reply = box.exec()
            if reply == QMessageBox.Yes:
                self.pushButton_select_config_folder_clicked()

    def pushButton_save_config_clicked(self):
        self.save_config_clicked()
        self.load_config()
        self.show_scrape_info('💡 配置已保存！%s' % self.get_current_time())

    def pushButton_save_new_config_clicked(self):
        new_config_name, ok = QInputDialog.getText(self, '另存为新配置', '请输入新配置的文件名')
        if ok and new_config_name:
            new_config_name = new_config_name.replace('/', '').replace('\\', '')
            new_config_name = re.sub(r'[\\:*?"<>|\r\n]+', '', new_config_name)
            if os.path.splitext(new_config_name)[1] != '.ini':
                new_config_name += '.ini'
            if new_config_name != self.config_file:
                self.config_file = new_config_name
                self.pushButton_save_config_clicked()

    def save_config_clicked(self):

        # ======================================================================================media & escape
        media_path = self.Ui.lineEdit_movie_path.text()                         # 待刮削目录
        softlink_path = self.Ui.lineEdit_movie_softlink_path.text()             # 软链接目录目录
        success_output_folder = self.Ui.lineEdit_success.text()                 # 成功输出目录
        failed_output_folder = self.Ui.lineEdit_fail.text()                     # 失败输出目录
        extrafanart_folder = self.Ui.lineEdit_extrafanart_dir.text().strip()    # 剧照目录
        media_type = self.Ui.lineEdit_movie_type.text().lower()                 # 视频格式
        sub_type = self.Ui.lineEdit_sub_type.text()                             # 字幕格式
        folders = self.Ui.lineEdit_escape_dir.text()                            # 排除文件夹
        string = self.Ui.lineEdit_escape_string.text()                          # 过滤字符
        if self.Ui.checkBox_scrape_softlink_path.isChecked():
            scrape_softlink_path = True
        else:
            scrape_softlink_path = ''
        try:                                                                    # 过滤小文件大小
            file_size = float(self.Ui.lineEdit_escape_size.text())
        except:
            file_size = 0.0
        no_escape = ''
        if self.Ui.checkBox_no_escape_file.isChecked():                         # 不过滤文件、文件夹，检测软链接
            no_escape += 'no_skip_small_file,'
        if self.Ui.checkBox_no_escape_dir.isChecked():
            no_escape += 'folder,'
        if self.Ui.checkBox_skip_success_file.isChecked():
            no_escape += 'skip_success_file,'
        if self.Ui.checkBox_record_success_file.isChecked():
            no_escape += 'record_success_file,'
        if self.Ui.checkBox_check_symlink.isChecked():
            no_escape += 'check_symlink,'
        if self.Ui.checkBox_check_symlink_definition.isChecked():
            no_escape += 'symlink_definition,'

        # ======================================================================================clean
        clean_ext = self.Ui.lineEdit_clean_file_ext.text().strip(' |｜')                           # 清理扩展名
        clean_name = self.Ui.lineEdit_clean_file_name.text().strip(' |｜')                         # 清理文件名
        clean_contains = self.Ui.lineEdit_clean_file_contains.text().strip(' |｜')                 # 清理文件名包含
        try:
            clean_size = float(self.Ui.lineEdit_clean_file_size.text().strip(' |｜'))              # 清理文件大小小于等于
        except:
            clean_size = 0.0
        clean_ignore_ext = self.Ui.lineEdit_clean_excluded_file_ext.text().strip(' |｜')           # 不清理扩展名
        clean_ignore_contains = self.Ui.lineEdit_clean_excluded_file_contains.text().strip(' |｜') # 不清理文件名包含
        clean_enable = ''
        if self.Ui.checkBox_clean_file_ext.isChecked():
            clean_enable += 'clean_ext,'
        if self.Ui.checkBox_clean_file_name.isChecked():
            clean_enable += 'clean_name,'
        if self.Ui.checkBox_clean_file_contains.isChecked():
            clean_enable += 'clean_contains,'
        if self.Ui.checkBox_clean_file_size.isChecked():
            clean_enable += 'clean_size,'
        if self.Ui.checkBox_clean_excluded_file_ext.isChecked():
            clean_enable += 'clean_ignore_ext,'
        if self.Ui.checkBox_clean_excluded_file_contains.isChecked():
            clean_enable += 'clean_ignore_contains,'
        if self.Ui.checkBox_i_understand_clean.isChecked():
            clean_enable += 'i_know,'
        if self.Ui.checkBox_i_agree_clean.isChecked():
            clean_enable += 'i_agree,'
        if self.Ui.checkBox_auto_clean.isChecked():
            clean_enable += 'auto_clean,'

        # ======================================================================================website
        website_single = self.Ui.comboBox_website_all.currentText()             # 指定单个网站
        website_youma = self.Ui.lineEdit_website_youma.text()                   # 有码番号刮削网站
        website_wuma = self.Ui.lineEdit_website_wuma.text()                     # 无码番号刮削网站
        website_suren = self.Ui.lineEdit_website_suren.text()                   # 素人番号刮削网站
        website_fc2 = self.Ui.lineEdit_website_fc2.text()                       # FC2番号刮削网站
        website_oumei = self.Ui.lineEdit_website_oumei.text()                   # 欧美番号刮削网站
        website_guochan = self.Ui.lineEdit_website_guochan.text()               # 国产番号刮削网站

        if self.Ui.radioButton_scrape_speed.isChecked():                        # 刮削偏好
            scrape_like = 'speed'
        elif self.Ui.radioButton_scrape_info.isChecked():
            scrape_like = 'info'
        else:
            scrape_like = 'single'

        website_set = ''
        if self.Ui.checkBox_use_official_data.isChecked():                       # 使用官网数据
            website_set += 'official,'
        title_website = self.Ui.lineEdit_title_website.text()                   # 标题字段网站优先级
        title_zh_website = self.Ui.lineEdit_title_zh_website.text()             # 中文标题字段网站优先级
        title_website_exclude = self.Ui.lineEdit_title_website_exclude.text()   # 标题字段排除网站
        if self.Ui.radioButton_title_zh_cn.isChecked():                         # 标题语言
            title_language = 'zh_cn'
        elif self.Ui.radioButton_title_zh_tw.isChecked():
            title_language = 'zh_tw'
        else:
            title_language = 'jp'
        if self.Ui.checkBox_title_sehua.isChecked():                            # 标题翻译-sehua
            title_sehua = 'on'
        else:
            title_sehua = 'off'
        if self.Ui.checkBox_title_yesjav.isChecked():                           # 标题翻译-yesjav
            title_yesjav = 'on'
        else:
            title_yesjav = 'off'
        if self.Ui.checkBox_title_translate.isChecked():                        # 标题翻译-翻译引擎
            title_translate = 'on'
        else:
            title_translate = 'off'
        if self.Ui.checkBox_title_sehua_2.isChecked():                          # 标题翻译-优先sehua
            title_sehua_zh = 'on'
        else:
            title_sehua_zh = 'off'

        outline_website = self.Ui.lineEdit_outline_website.text()                 # 简介字段网站优先级
        outline_zh_website = self.Ui.lineEdit_outline_zh_website.text()           # 中文简介字段网站优先级
        outline_website_exclude = self.Ui.lineEdit_outline_website_exclude.text() # 简介字段排除网站
        if self.Ui.radioButton_outline_zh_cn.isChecked():                         # 简介语言
            outline_language = 'zh_cn'
        elif self.Ui.radioButton_outline_zh_tw.isChecked():
            outline_language = 'zh_tw'
        else:
            outline_language = 'jp'
        if self.Ui.checkBox_outline_translate.isChecked():                        # 简介翻译-翻译引擎
            outline_translate = 'on'
        else:
            outline_translate = 'off'
        outline_show = ''
        if self.Ui.checkBox_show_translate_from.isChecked():                        # 简介翻译-翻译来源、双语显示
            outline_show += 'show_from,'
        if self.Ui.radioButton_trans_show_zh_jp.isChecked():                        # 简介翻译-翻译来源、双语显示
            outline_show += 'show_zh_jp,'
        elif self.Ui.radioButton_trans_show_jp_zh.isChecked():
            outline_show += 'show_jp_zh,'

        actor_website = self.Ui.lineEdit_actor_website.text()                   # 演员字段网站优先级
        actor_website_exclude = self.Ui.lineEdit_actor_website_exclude.text()   # 演员字段排除网站
        if self.Ui.radioButton_actor_zh_cn.isChecked():                         # 演员语言
            actor_language = 'zh_cn'
        elif self.Ui.radioButton_actor_zh_tw.isChecked():
            actor_language = 'zh_tw'
        else:
            actor_language = 'jp'
        if self.Ui.checkBox_actor_realname.isChecked():                         # 演员使用真实名字
            actor_realname = 'on'
        else:
            actor_realname = 'off'
        if self.Ui.checkBox_actor_translate.isChecked():                        # 演员-映射表
            actor_translate = 'on'
        else:
            actor_translate = 'off'

        tag_website = self.Ui.lineEdit_tag_website.text()                       # 标签字段网站优先级
        tag_website_exclude = self.Ui.lineEdit_tag_website_exclude.text()       # 标签字段排除网站
        if self.Ui.radioButton_tag_zh_cn.isChecked():                           # 标签语言
            tag_language = 'zh_cn'
        elif self.Ui.radioButton_tag_zh_tw.isChecked():
            tag_language = 'zh_tw'
        else:
            tag_language = 'jp'
        if self.Ui.checkBox_tag_translate.isChecked():                          # 标签-映射表
            tag_translate = 'on'
        else:
            tag_translate = 'off'
        tag_include = ''                                                        # 写入标签字段的信息
        if self.Ui.checkBox_tag_actor.isChecked():
            tag_include += 'actor,'
        if self.Ui.checkBox_tag_letters.isChecked():
            tag_include += 'letters,'
        if self.Ui.checkBox_tag_series.isChecked():
            tag_include += 'series,'
        if self.Ui.checkBox_tag_studio.isChecked():
            tag_include += 'studio,'
        if self.Ui.checkBox_tag_publisher.isChecked():
            tag_include += 'publisher,'
        if self.Ui.checkBox_tag_cnword.isChecked():
            tag_include += 'cnword,'
        if self.Ui.checkBox_tag_mosaic.isChecked():
            tag_include += 'mosaic,'
        if self.Ui.checkBox_tag_definition.isChecked():
            tag_include += 'definition,'

        series_website = self.Ui.lineEdit_series_website.text()                 # 系列字段网站优先级
        series_website_exclude = self.Ui.lineEdit_series_website_exclude.text() # 系列字段排除网站
        if self.Ui.radioButton_series_zh_cn.isChecked():                        # 系列字段语言
            series_language = 'zh_cn'
        elif self.Ui.radioButton_series_zh_tw.isChecked():
            series_language = 'zh_tw'
        else:
            series_language = 'jp'
        if self.Ui.checkBox_series_translate.isChecked():                       # 系列-映射表
            series_translate = 'on'
        else:
            series_translate = 'off'

        studio_website = self.Ui.lineEdit_studio_website.text()                 # 片商字段网站优先级
        studio_website_exclude = self.Ui.lineEdit_studio_website_exclude.text() # 片商字段排除网站
        if self.Ui.radioButton_studio_zh_cn.isChecked():                        # 片商字段语言
            studio_language = 'zh_cn'
        elif self.Ui.radioButton_studio_zh_tw.isChecked():
            studio_language = 'zh_tw'
        else:
            studio_language = 'jp'
        if self.Ui.checkBox_studio_translate.isChecked():                       # 片商-映射表
            studio_translate = 'on'
        else:
            studio_translate = 'off'

        publisher_website = self.Ui.lineEdit_publisher_website.text()                 # 发行字段网站优先级
        publisher_website_exclude = self.Ui.lineEdit_publisher_website_exclude.text() # 发行字段排除网站
        if self.Ui.radioButton_publisher_zh_cn.isChecked():                           # 发行字段语言
            publisher_language = 'zh_cn'
        elif self.Ui.radioButton_publisher_zh_tw.isChecked():
            publisher_language = 'zh_tw'
        else:
            publisher_language = 'jp'
        if self.Ui.checkBox_publisher_translate.isChecked():                          # 发行-映射表
            publisher_translate = 'on'
        else:
            publisher_translate = 'off'

        director_website = self.Ui.lineEdit_director_website.text()                 # 导演字段网站优先级
        director_website_exclude = self.Ui.lineEdit_director_website_exclude.text() # 导演字段排除网站
        if self.Ui.radioButton_director_zh_cn.isChecked():                          # 导演字段语言
            director_language = 'zh_cn'
        elif self.Ui.radioButton_director_zh_tw.isChecked():
            director_language = 'zh_tw'
        else:
            director_language = 'jp'
        if self.Ui.checkBox_director_translate.isChecked():                         # 导演-映射表
            director_translate = 'on'
        else:
            director_translate = 'off'

        poster_website = self.Ui.lineEdit_poster_website.text()                           # 封面字段网站优先级
        poster_website_exclude = self.Ui.lineEdit_poster_website_exclude.text()           # 封面字段排除网站
        thumb_website = self.Ui.lineEdit_thumb_website.text()                             # 背景字段网站优先级
        thumb_website_exclude = self.Ui.lineEdit_thumb_website_exclude.text()             # 背景字段排除网站
        extrafanart_website = self.Ui.lineEdit_extrafanart_website.text()                 # 剧照字段网站优先级
        extrafanart_website_exclude = self.Ui.lineEdit_extrafanart_website_exclude.text() # 剧照字段排除网站
        score_website = self.Ui.lineEdit_score_website.text()                             # 评分字段网站优先级
        score_website_exclude = self.Ui.lineEdit_score_website_exclude.text()             # 评分字段排除网站
        release_website = self.Ui.lineEdit_release_website.text()                         # 发行日期字段网站优先级
        release_website_exclude = self.Ui.lineEdit_release_website_exclude.text()         # 发行日期字段排除网站
        runtime_website = self.Ui.lineEdit_runtime_website.text()                         # 时长字段网站优先级
        runtime_website_exclude = self.Ui.lineEdit_runtime_website_exclude.text()         # 时长字段排除网站
        trailer_website = self.Ui.lineEdit_trailer_website.text()                         # 预告片字段网站优先级
        trailer_website_exclude = self.Ui.lineEdit_trailer_website_exclude.text()         # 预告片字段排除网站
        wanted_website = self.Ui.lineEdit_wanted_website.text()                           # 想看人数网站
        nfo_tagline = self.Ui.lineEdit_nfo_tagline.text()                                 # tagline格式
        nfo_tag_series = self.Ui.lineEdit_nfo_tag_series.text()                           # nfo_tag_series 格式
        nfo_tag_studio = self.Ui.lineEdit_nfo_tag_studio.text()                           # nfo_tag_studio 格式
        nfo_tag_publisher = self.Ui.lineEdit_nfo_tag_publisher.text()                     # nfo_tag_publisher 格式

        whole_fields = ''
        none_fields = ''
        if self.Ui.radioButton_outline_more.isChecked():
            whole_fields += 'outline,'
        elif self.Ui.radioButton_outline_none.isChecked():
            none_fields += 'outline,'

        if self.Ui.radioButton_actor_more.isChecked():
            whole_fields += 'actor,'
        elif self.Ui.radioButton_actor_none.isChecked():
            none_fields += 'actor,'

        if self.Ui.radioButton_thumb_more.isChecked():
            whole_fields += 'thumb,'
        elif self.Ui.radioButton_thumb_none.isChecked():
            none_fields += 'thumb,'

        if self.Ui.radioButton_poster_more.isChecked():
            whole_fields += 'poster,'
        elif self.Ui.radioButton_poster_none.isChecked():
            none_fields += 'poster,'

        if self.Ui.radioButton_extrafanart_more.isChecked():
            whole_fields += 'extrafanart,'
        elif self.Ui.radioButton_extrafanart_none.isChecked():
            none_fields += 'extrafanart,'

        if self.Ui.radioButton_trailer_more.isChecked():
            whole_fields += 'trailer,'
        elif self.Ui.radioButton_trailer_none.isChecked():
            none_fields += 'trailer,'

        if self.Ui.radioButton_release_more.isChecked():
            whole_fields += 'release,'
        elif self.Ui.radioButton_release_none.isChecked():
            none_fields += 'release,'

        if self.Ui.radioButton_runtime_more.isChecked():
            whole_fields += 'runtime,'
        elif self.Ui.radioButton_runtime_none.isChecked():
            none_fields += 'runtime,'

        if self.Ui.radioButton_score_more.isChecked():
            whole_fields += 'score,'
        elif self.Ui.radioButton_score_none.isChecked():
            none_fields += 'score,'

        if self.Ui.radioButton_tag_more.isChecked():
            whole_fields += 'tag,'
        elif self.Ui.radioButton_tag_none.isChecked():
            none_fields += 'tag,'

        if self.Ui.radioButton_director_more.isChecked():
            whole_fields += 'director,'
        elif self.Ui.radioButton_director_none.isChecked():
            none_fields += 'director,'

        if self.Ui.radioButton_series_more.isChecked():
            whole_fields += 'series,'
        elif self.Ui.radioButton_series_none.isChecked():
            none_fields += 'series,'

        if self.Ui.radioButton_studio_more.isChecked():
            whole_fields += 'studio,'
        elif self.Ui.radioButton_studio_none.isChecked():
            none_fields += 'studio,'

        if self.Ui.radioButton_publisher_more.isChecked():
            whole_fields += 'publisher,'
        elif self.Ui.radioButton_publisher_none.isChecked():
            none_fields += 'publisher,'

        if self.Ui.radioButton_wanted_none.isChecked():
            none_fields += 'wanted,'

        nfo_include_new = ''                                                        # 写入nfo的字段：
        if self.Ui.checkBox_nfo_sorttitle.isChecked():
            nfo_include_new += 'sorttitle,'
        if self.Ui.checkBox_nfo_originaltitle.isChecked():
            nfo_include_new += 'originaltitle,'
        if self.Ui.checkBox_nfo_title_cd.isChecked():
            nfo_include_new += 'title_cd,'
        if self.Ui.checkBox_nfo_outline.isChecked():
            nfo_include_new += 'outline,'
        if self.Ui.checkBox_nfo_plot.isChecked():
            nfo_include_new += 'plot_,'
        if self.Ui.checkBox_nfo_originalplot.isChecked():
            nfo_include_new += 'originalplot,'
        if self.Ui.checkBox_outline_cdata.isChecked():
            nfo_include_new += 'outline_no_cdata,'
        if self.Ui.checkBox_nfo_release.isChecked():
            nfo_include_new += 'release_,'
        if self.Ui.checkBox_nfo_relasedate.isChecked():
            nfo_include_new += 'releasedate,'
        if self.Ui.checkBox_nfo_premiered.isChecked():
            nfo_include_new += 'premiered,'
        if self.Ui.checkBox_nfo_country.isChecked():
            nfo_include_new += 'country,'
        if self.Ui.checkBox_nfo_mpaa.isChecked():
            nfo_include_new += 'mpaa,'
        if self.Ui.checkBox_nfo_customrating.isChecked():
            nfo_include_new += 'customrating,'
        if self.Ui.checkBox_nfo_year.isChecked():
            nfo_include_new += 'year,'
        if self.Ui.checkBox_nfo_runtime.isChecked():
            nfo_include_new += 'runtime,'
        if self.Ui.checkBox_nfo_wanted.isChecked():
            nfo_include_new += 'wanted,'
        if self.Ui.checkBox_nfo_score.isChecked():
            nfo_include_new += 'score,'
        if self.Ui.checkBox_nfo_criticrating.isChecked():
            nfo_include_new += 'criticrating,'
        if self.Ui.checkBox_nfo_actor.isChecked():
            nfo_include_new += 'actor,'
        if self.Ui.checkBox_nfo_all_actor.isChecked():
            nfo_include_new += 'actor_all,'
        if self.Ui.checkBox_nfo_director.isChecked():
            nfo_include_new += 'director,'
        if self.Ui.checkBox_nfo_series.isChecked():
            nfo_include_new += 'series,'
        if self.Ui.checkBox_nfo_tag.isChecked():
            nfo_include_new += 'tag,'
        if self.Ui.checkBox_nfo_genre.isChecked():
            nfo_include_new += 'genre,'
        if self.Ui.checkBox_nfo_actor_set.isChecked():
            nfo_include_new += 'actor_set,'
        if self.Ui.checkBox_nfo_set.isChecked():
            nfo_include_new += 'series_set,'
        if self.Ui.checkBox_nfo_studio.isChecked():
            nfo_include_new += 'studio,'
        if self.Ui.checkBox_nfo_maker.isChecked():
            nfo_include_new += 'maker,'
        if self.Ui.checkBox_nfo_publisher.isChecked():
            nfo_include_new += 'publisher,'
        if self.Ui.checkBox_nfo_label.isChecked():
            nfo_include_new += 'label,'
        if self.Ui.checkBox_nfo_poster.isChecked():
            nfo_include_new += 'poster,'
        if self.Ui.checkBox_nfo_cover.isChecked():
            nfo_include_new += 'cover,'
        if self.Ui.checkBox_nfo_trailer.isChecked():
            nfo_include_new += 'trailer,'
        if self.Ui.checkBox_nfo_website.isChecked():
            nfo_include_new += 'website,'
        translate_by = ''
        if self.Ui.checkBox_youdao.isChecked():                                 # 有道翻译
            translate_by += 'youdao,'
        if self.Ui.checkBox_google.isChecked():                                 # google 翻译
            translate_by += 'google,'
        if self.Ui.checkBox_deepl.isChecked():                                  # deepl 翻译
            translate_by += 'deepl,'
        deepl_key = self.Ui.lineEdit_deepl_key.text()                           # deepl key

        # ======================================================================================common
        thread_number = self.Ui.horizontalSlider_thread.value()                 # 线程数量
        thread_time = self.Ui.horizontalSlider_thread_time.value()              # 线程延时
        javdb_time = self.Ui.horizontalSlider_javdb_time.value()                # javdb 延时
        if self.Ui.radioButton_mode_common.isChecked():                         # 普通模式
            main_mode = 1
        elif self.Ui.radioButton_mode_sort.isChecked():                         # 整理模式
            main_mode = 2
        elif self.Ui.radioButton_mode_update.isChecked():                       # 整理模式
            main_mode = 3
        elif self.Ui.radioButton_mode_read.isChecked():                         # 读取模式
            main_mode = 4
        else:
            main_mode = 1
        read_mode = ''
        if self.Ui.checkBox_read_has_nfo_update.isChecked():                    # 读取模式有nfo是否执行更新模式
            read_mode += 'has_nfo_update,'
        if self.Ui.checkBox_read_no_nfo_scrape.isChecked():                     # 读取模式无nfo是否刮削
            read_mode += 'no_nfo_scrape,'
        if self.Ui.checkBox_read_download_file_again.isChecked():                     # 读取模式允许下载文件
            read_mode += 'read_download_again,'
        if self.Ui.checkBox_read_translate_again.isChecked():                     # 读取模式启用字段翻译
            read_mode += 'read_translate_again,'
        if self.Ui.radioButton_update_c.isChecked():                            # update 模式
            update_mode = 'c'
        elif self.Ui.radioButton_update_b_c.isChecked():
            update_mode = 'bc'
            if self.Ui.checkBox_update_a.isChecked():
                update_mode = 'abc'
        elif self.Ui.radioButton_update_d_c.isChecked():
            update_mode = 'd'
        else:
            update_mode = 'c'
        update_a_folder = self.Ui.lineEdit_update_a_folder.text()               # 更新模式 - a 目录
        update_b_folder = self.Ui.lineEdit_update_b_folder.text()               # 更新模式 - b 目录
        update_d_folder = self.Ui.lineEdit_update_d_folder.text()               # 更新模式 - d 目录
        if self.Ui.radioButton_soft_on.isChecked():                             # 软链接开
            soft_link = 1
        elif self.Ui.radioButton_hard_on.isChecked():                           # 硬链接开
            soft_link = 2
        else:                                                                   # 软链接关
            soft_link = 0
        if self.Ui.radioButton_succ_move_on.isChecked():                        # 成功移动开
            success_file_move = 1
        elif self.Ui.radioButton_succ_move_off.isChecked():                     # 成功移动关
            success_file_move = 0
        if self.Ui.radioButton_fail_move_on.isChecked():                        # 失败移动开
            failed_file_move = 1
        else:
            failed_file_move = 0
        if self.Ui.radioButton_succ_rename_on.isChecked():                      # 成功重命名开
            success_file_rename = 1
        elif self.Ui.radioButton_succ_rename_off.isChecked():                   # 成功重命名关
            success_file_rename = 0
        if self.Ui.radioButton_del_empty_folder_on.isChecked():                 # 结束后删除空文件夹开
            del_empty_folder = 1
        elif self.Ui.radioButton_del_empty_folder_off.isChecked():              # 结束后删除空文件夹关
            del_empty_folder = 0
        if self.Ui.checkBox_cover.isChecked():                                  # 显示封面
            show_poster = 1
        else:                                                                   # 关闭封面
            show_poster = 0

        # ======================================================================================下载文件，剧照
        download_files = ','
        if self.Ui.checkBox_download_poster.isChecked():                        # 下载 poster
            download_files += 'poster,'
        if self.Ui.checkBox_download_thumb.isChecked():                         # 下载 thumb
            download_files += 'thumb,'
        if self.Ui.checkBox_download_fanart.isChecked():                        # 下载 fanart
            download_files += 'fanart,'
        if self.Ui.checkBox_download_extrafanart.isChecked():                   # 下载 extrafanart
            download_files += 'extrafanart,'
        if self.Ui.checkBox_download_trailer.isChecked():                       # 下载 trailer
            download_files += 'trailer,'
        if self.Ui.checkBox_download_nfo.isChecked():                           # 下载 nfo
            download_files += 'nfo,'
        if self.Ui.checkBox_extras.isChecked():                                 # 下载 剧照附加内容
            download_files += 'extrafanart_extras,'
        if self.Ui.checkBox_download_extrafanart_copy.isChecked():              # 下载 剧照副本
            download_files += 'extrafanart_copy,'
        if self.Ui.checkBox_theme_videos.isChecked():                           # 下载 主题视频
            download_files += 'theme_videos,'
        if self.Ui.checkBox_ignore_pic_fail.isChecked():                        # 图片下载失败时，不视为刮削失败
            download_files += 'ignore_pic_fail,'
        if self.Ui.checkBox_ignore_youma.isChecked():                           # 有码封面不裁剪
            download_files += 'ignore_youma,'
        if self.Ui.checkBox_ignore_wuma.isChecked():                            # 无码封面不裁剪
            download_files += 'ignore_wuma,'
        if self.Ui.checkBox_ignore_fc2.isChecked():                             # fc2 封面不裁剪
            download_files += 'ignore_fc2,'
        if self.Ui.checkBox_ignore_guochan.isChecked():                         # 国产封面不裁剪
            download_files += 'ignore_guochan,'
        if self.Ui.checkBox_ignore_size.isChecked():                            # 不校验预告片文件大小
            download_files += 'ignore_size,'

        keep_files = ','
        if self.Ui.checkBox_old_poster.isChecked():                             # 保留 poster
            keep_files += 'poster,'
        if self.Ui.checkBox_old_thumb.isChecked():                              # 保留 thumb
            keep_files += 'thumb,'
        if self.Ui.checkBox_old_fanart.isChecked():                             # 保留 fanart
            keep_files += 'fanart,'
        if self.Ui.checkBox_old_extrafanart.isChecked():                        # 保留 extrafanart
            keep_files += 'extrafanart,'
        if self.Ui.checkBox_old_trailer.isChecked():                            # 保留 trailer
            keep_files += 'trailer,'
        if self.Ui.checkBox_old_nfo.isChecked():                                # 保留 nfo
            keep_files += 'nfo,'
        if self.Ui.checkBox_old_extrafanart_copy.isChecked():                   # 保留 剧照副本
            keep_files += 'extrafanart_copy,'
        if self.Ui.checkBox_old_theme_videos.isChecked():                       # 保留 主题视频
            keep_files += 'theme_videos,'

        download_hd_pics = ''
        if self.Ui.checkBox_hd_poster.isChecked():                              # 高清封面图
            download_hd_pics += 'poster,'
        if self.Ui.checkBox_hd_thumb.isChecked():                               # 高清缩略图
            download_hd_pics += 'thumb,'
        if self.Ui.checkBox_amazon_big_pic.isChecked():                         # amazon
            download_hd_pics += 'amazon,'
        if self.Ui.checkBox_official_big_pic.isChecked():                         # google 以图搜图
            download_hd_pics += 'official,'
        if self.Ui.checkBox_google_big_pic.isChecked():                         # google 以图搜图
            download_hd_pics += 'google,'
        if self.Ui.radioButton_google_only.isChecked():                         # google 只下载
            download_hd_pics += 'goo_only,'

        google_used = self.Ui.lineEdit_google_used.text()                       # google 下载词
        google_exclude = self.Ui.lineEdit_google_exclude.text()                 # google 过滤词

        # ======================================================================================命名
        folder_name = self.Ui.lineEdit_dir_name.text()                          # 视频文件夹命名
        naming_file = self.Ui.lineEdit_local_name.text()                        # 视频文件名命名
        naming_media = self.Ui.lineEdit_media_name.text()                       # nfo标题命名
        prevent_char = self.Ui.lineEdit_prevent_char.text()                     # 防屏蔽字符

        fields_rule = ''                                                        # 字段规则
        if self.Ui.checkBox_title_del_actor.isChecked():                        # 去除标题后的演员名
            fields_rule += 'del_actor,'
        if self.Ui.checkBox_actor_del_char.isChecked():                         # 去除演员括号
            fields_rule += 'del_char,'
        if self.Ui.checkBox_actor_fc2_seller.isChecked():                       # fc2 卖家
            fields_rule += 'fc2_seller,'
        if self.Ui.checkBox_number_del_num.isChecked():                         # 素人番号去除番号前缀数字
            fields_rule += 'del_num,'
        suffix_sort = self.Ui.lineEdit_suffix_sort.text()                       # 后缀字段顺序
        actor_no_name = self.Ui.lineEdit_actor_no_name.text()                   # 未知演员
        actor_name_more = self.Ui.lineEdit_actor_name_more.text()               # 等演员
        release_rule = self.Ui.lineEdit_release_rule.text()                     # 发行日期
        release_rule = re.sub(r'[\\/:*?"<>|\r\n]+', '-', release_rule).strip()

        folder_name_max = self.Ui.lineEdit_folder_name_max.text()               # 长度命名规则-目录
        file_name_max = self.Ui.lineEdit_file_name_max.text()                   # 长度命名规则-文件名
        actor_name_max = self.Ui.lineEdit_actor_name_max.text()                 # 长度命名规则-演员数量

        umr_style = self.Ui.lineEdit_umr_style.text()                           # 无码破解版本命名
        leak_style = self.Ui.lineEdit_leak_style.text()                         # 无码流出版本命名
        wuma_style = self.Ui.lineEdit_wuma_style.text()                         # 无码版本命名
        youma_style = self.Ui.lineEdit_youma_style.text()                       # 有码版本命名
        show_moword = ''
        if self.Ui.checkBox_foldername_mosaic.isChecked():                      # 视频目录名显示版本命名字符
            show_moword += 'folder,'
        if self.Ui.checkBox_filename_mosaic.isChecked():                        # 视频文件名显示版本命名字符
            show_moword += 'file,'
        show_4k = ''
        if self.Ui.checkBox_foldername_4k.isChecked():                          # 视频目录名显示4k
            show_4k += 'folder,'
        if self.Ui.checkBox_filename_4k.isChecked():                            # 视频文件名显示4k
            show_4k += 'file,'

        if self.Ui.radioButton_cd_part_lower.isChecked():                       # 分集命名规则-小写
            cd_name = 0
        elif self.Ui.radioButton_cd_part_upper.isChecked():                     # 分集命名规则-小写
            cd_name = 1
        else:
            cd_name = 2
        cd_char = ''
        if self.Ui.checkBox_cd_part_a.isChecked():                              # 字母结尾的分集
            cd_char += 'letter,'
        if self.Ui.checkBox_cd_part_c.isChecked():                              # 字母C结尾的分集
            cd_char += 'endc,'
        if self.Ui.checkBox_cd_part_01.isChecked():                             # 两位数字结尾的分集
            cd_char += 'digital,'
        if self.Ui.checkBox_cd_part_1_xxx.isChecked():                          # 中间数字的分集
            cd_char += 'middle_number,'

        if self.Ui.checkBox_cd_part_underline.isChecked():                      # 下划线分隔符
            cd_char += 'underline,'
        if self.Ui.checkBox_cd_part_space.isChecked():                          # 空格分隔符
            cd_char += 'space,'
        if self.Ui.checkBox_cd_part_point.isChecked():                          # 小数点分隔符
            cd_char += 'point,'

        if self.Ui.radioButton_pic_with_filename.isChecked():                   # 图片命名规则-加文件名
            pic_name = 0
        else:                                                                   # 图片命名规则-不加文件名
            pic_name = 1
        if self.Ui.radioButton_trailer_with_filename.isChecked():               # 预告片命名规则-加文件名
            trailer_name = 0
        else:                                                                   # 预告片命名规则-不加文件名
            trailer_name = 1
        if self.Ui.radioButton_definition_height.isChecked():                   # 画质命名规则-高度
            hd_name = 'height'
        else:                                                                   # 画质命名规则-清晰度
            hd_name = 'hd'
        if self.Ui.radioButton_videosize_video.isChecked():                     # 分辨率获取方式-视频
            hd_get = 'video'
        elif self.Ui.radioButton_videosize_path.isChecked():                    # 分辨率获取方式-路径
            hd_get = 'path'
        else:                                                                   # 分辨率获取方式-无
            hd_get = 'none'

        # ======================================================================================字幕
        cnword_char = self.Ui.lineEdit_cnword_char.text()                       # 中文字幕判断字符
        cnword_style = self.Ui.lineEdit_cnword_style.text()                     # 中文字幕字符样式
        if self.Ui.checkBox_foldername.isChecked():                             # 视频目录名显示中文字幕
            folder_cnword = 'on'
        else:
            folder_cnword = 'off'
        if self.Ui.checkBox_filename.isChecked():                               # 视频文件名显示中文字幕
            file_cnword = 'on'
        else:
            file_cnword = 'off'
        subtitle_folder = self.Ui.lineEdit_sub_folder.text()                    # 字幕文件目录
        if self.Ui.radioButton_add_sub_on.isChecked():                          # 自动添加字幕
            subtitle_add = 'on'
        elif self.Ui.radioButton_add_sub_off.isChecked():
            subtitle_add = 'off'
        if self.Ui.checkBox_sub_add_chs.isChecked():                            # 字幕添加.chs后缀
            subtitle_add_chs = 'on'
        else:
            subtitle_add_chs = 'off'
        if self.Ui.checkBox_sub_rescrape.isChecked():                           # 重新刮削新添加字幕的视频
            subtitle_add_rescrape = 'on'
        else:
            subtitle_add_rescrape = 'off'

        # ======================================================================================头像
        if self.Ui.radioButton_server_emby.isChecked():
            server_type = 'emby'
        else:
            server_type = 'jellyfin'
        emby_url = self.Ui.lineEdit_emby_url.text()                             # emby地址
        emby_url = emby_url.replace('：', ':').strip('/ ')
        if emby_url and '://' not in emby_url:
            emby_url = 'http://' + emby_url
        api_key = self.Ui.lineEdit_api_key.text()                               # emby密钥
        actor_photo_folder = self.Ui.lineEdit_actor_photo_folder.text()         # 头像图片目录
        gfriends_github = self.Ui.lineEdit_net_actor_photo.text().strip(' /')   # gfriends github 项目地址
        if not gfriends_github:
            gfriends_github = 'https://github.com/gfriends/gfriends'
        elif '://' not in gfriends_github:
            gfriends_github = 'https://' + gfriends_github
        emby_on = ''
        if self.Ui.radioButton_actor_info_zh_cn.isChecked():
            emby_on += 'actor_info_zh_cn,'
        elif self.Ui.radioButton_actor_info_zh_tw.isChecked():
            emby_on += 'actor_info_zh_tw,'
        else:
            emby_on += 'actor_info_ja,'
        if self.Ui.checkBox_actor_info_translate.isChecked():
            emby_on += 'actor_info_translate,'
        if self.Ui.radioButton_actor_info_all.isChecked():
            emby_on += 'actor_info_all,'
        else:
            emby_on += 'actor_info_miss,'
        if self.Ui.checkBox_actor_info_photo.isChecked():
            emby_on += 'actor_info_photo,'

        if self.Ui.radioButton_actor_photo_net.isChecked():
            emby_on += 'actor_photo_net,'
        else:
            emby_on += 'actor_photo_local,'
        if self.Ui.checkBox_actor_photo_ne_backdrop.isChecked():
            emby_on += 'graphis_backdrop,'
        if self.Ui.checkBox_actor_photo_ne_face.isChecked():
            emby_on += 'graphis_face,'
        if self.Ui.checkBox_actor_photo_ne_new.isChecked():
            emby_on += 'graphis_new,'
        if self.Ui.radioButton_actor_photo_all.isChecked():
            emby_on += 'actor_photo_all,'
        else:
            emby_on += 'actor_photo_miss,'
        if self.Ui.checkBox_actor_photo_auto.isChecked():
            emby_on += 'actor_photo_auto,'
        if self.Ui.checkBox_actor_pic_replace.isChecked():
            emby_on += 'actor_replace,'

        # ======================================================================================水印
        if self.Ui.checkBox_poster_mark.isChecked():                            # 封面添加水印
            poster_mark = 1
        else:                                                                   # 关闭封面添加水印
            poster_mark = 0
        if self.Ui.checkBox_thumb_mark.isChecked():                             # 缩略图添加水印
            thumb_mark = 1
        else:                                                                   # 关闭缩略图添加水印
            thumb_mark = 0
        if self.Ui.checkBox_fanart_mark.isChecked():                            # 艺术图添加水印
            fanart_mark = 1
        else:                                                                   # 关闭艺术图添加水印
            fanart_mark = 0
        mark_size = self.Ui.horizontalSlider_mark_size.value()                  # 水印大小
        mark_type = ''
        if self.Ui.checkBox_sub.isChecked():                                    # 字幕
            mark_type += 'sub,'
        if self.Ui.checkBox_censored.isChecked():                               # 有码
            mark_type += 'youma,'
        if self.Ui.checkBox_umr.isChecked():                                    # 破解
            mark_type += 'umr,'
        if self.Ui.checkBox_leak.isChecked():                                   # 流出
            mark_type += 'leak,'
        if self.Ui.checkBox_uncensored.isChecked():                             # 无码
            mark_type += 'uncensored,'
        if self.Ui.checkBox_hd.isChecked():                                     # 4k/8k
            mark_type += 'hd,'
        if self.Ui.radioButton_not_fixed_position.isChecked():                  # 水印位置
            mark_fixed = 'off'
        elif self.Ui.radioButton_fixed_corner.isChecked():                      # 水印位置
            mark_fixed = 'corner'
        else:
            mark_fixed = 'on'
        if self.Ui.radioButton_top_left.isChecked():                            # 首个水印位置-左上
            mark_pos = 'top_left'
        elif self.Ui.radioButton_top_right.isChecked():                         # 首个水印位置-右上
            mark_pos = 'top_right'
        elif self.Ui.radioButton_bottom_left.isChecked():                       # 首个水印位置-左下
            mark_pos = 'bottom_left'
        elif self.Ui.radioButton_bottom_right.isChecked():                      # 首个水印位置-右下
            mark_pos = 'bottom_right'
        if self.Ui.radioButton_top_left_corner.isChecked():                     # 固定一个位置-左上
            mark_pos_corner = 'top_left'
        elif self.Ui.radioButton_top_right_corner.isChecked():                  # 固定一个位置-右上
            mark_pos_corner = 'top_right'
        elif self.Ui.radioButton_bottom_left_corner.isChecked():                # 固定一个位置-左下
            mark_pos_corner = 'bottom_left'
        elif self.Ui.radioButton_bottom_right_corner.isChecked():               # 固定一个位置-右下
            mark_pos_corner = 'bottom_right'
        if self.Ui.radioButton_top_left_hd.isChecked():                         # hd水印位置-左上
            mark_pos_hd = 'top_left'
        elif self.Ui.radioButton_top_right_hd.isChecked():                      # hd水印位置-右上
            mark_pos_hd = 'top_right'
        elif self.Ui.radioButton_bottom_left_hd.isChecked():                    # hd水印位置-左下
            mark_pos_hd = 'bottom_left'
        elif self.Ui.radioButton_bottom_right_hd.isChecked():                   # hd水印位置-右下
            mark_pos_hd = 'bottom_right'
        if self.Ui.radioButton_top_left_sub.isChecked():                        # 字幕水印位置-左上
            mark_pos_sub = 'top_left'
        elif self.Ui.radioButton_top_right_sub.isChecked():                     # 字幕水印位置-右上
            mark_pos_sub = 'top_right'
        elif self.Ui.radioButton_bottom_left_sub.isChecked():                   # 字幕水印位置-左下
            mark_pos_sub = 'bottom_left'
        elif self.Ui.radioButton_bottom_right_sub.isChecked():                  # 字幕水印位置-右下
            mark_pos_sub = 'bottom_right'
        if self.Ui.radioButton_top_left_mosaic.isChecked():                     # 马赛克水印位置-左上
            mark_pos_mosaic = 'top_left'
        elif self.Ui.radioButton_top_right_mosaic.isChecked():                  # 马赛克水印位置-右上
            mark_pos_mosaic = 'top_right'
        elif self.Ui.radioButton_bottom_left_mosaic.isChecked():                # 马赛克水印位置-左下
            mark_pos_mosaic = 'bottom_left'
        elif self.Ui.radioButton_bottom_right_mosaic.isChecked():               # 马赛克水印位置-右下
            mark_pos_mosaic = 'bottom_right'

        # ======================================================================================proxy
        if self.Ui.radioButton_proxy_http.isChecked():                          # http proxy
            proxy_type = 'http'
        elif self.Ui.radioButton_proxy_socks5.isChecked():                      # socks5 proxy
            proxy_type = 'socks5'
        elif self.Ui.radioButton_proxy_nouse.isChecked():                       # no use proxy
            proxy_type = 'no'
        proxy = self.Ui.lineEdit_proxy.text()                                   # 代理地址
        proxy = proxy.replace('https://', '').replace('http://', '')
        timeout = self.Ui.horizontalSlider_timeout.value()                      # 超时时间
        retry = self.Ui.horizontalSlider_retry.value()                          # 重试次数
        javbus_website = self.Ui.lineEdit_javbus_website.text()                 # javbus 地址
        javdb_website = self.Ui.lineEdit_javdb_website.text()                   # javdb 地址
        iqqtv_website = self.Ui.lineEdit_iqqtv_website.text()                   # iqqtv 地址
        avsex_website = self.Ui.lineEdit_avsex_website.text()                   # avsex 地址
        hdouban_website = self.Ui.lineEdit_hdouban_website.text()               # hdouban 地址
        mdtv_website = self.Ui.lineEdit_mdtv_website.text()                     # mdtv 地址
        airavcc_website = self.Ui.lineEdit_airavcc_website.text()               # airavcc 地址
        lulubar_website = self.Ui.lineEdit_lulubar_website.text()               # lulubar 地址
        javlibrary_website = self.Ui.lineEdit_javlibrary_website.text()         # javlibrary 地址
        javdb = self.Ui.plainTextEdit_cookie_javdb.toPlainText()                # javdb cookie
        javbus = self.Ui.plainTextEdit_cookie_javbus.toPlainText()              # javbus cookie
        theporndb_api_token = self.Ui.lineEdit_api_token_theporndb.text()       # api token
        if javdb:
            javdb = javdb.replace('locale=en', 'locale=zh')

        # ======================================================================================other
        rest_count = self.Ui.lineEdit_rest_count.text()                         # 间歇刮削文件数量
        rest_time = self.Ui.lineEdit_rest_time.text()                           # 间歇刮削休息时间
        timed_interval = self.Ui.lineEdit_timed_interval.text()                 # 循环任务间隔时间

        # ======================================================================================开关汇总
        switch_on = ''
        if self.Ui.checkBox_auto_start.isChecked():
            switch_on += 'auto_start,'
        if self.Ui.checkBox_auto_exit.isChecked():
            switch_on += 'auto_exit,'
        if self.Ui.checkBox_rest_scrape.isChecked():
            switch_on += 'rest_scrape,'
        if self.Ui.checkBox_timed_scrape.isChecked():
            switch_on += 'timed_scrape,'
        if self.Ui.checkBox_remain_task.isChecked():
            switch_on += 'remain_task,'
        if self.Ui.checkBox_show_dialog_exit.isChecked():
            switch_on += 'show_dialog_exit,'
        if self.Ui.checkBox_show_dialog_stop_scrape.isChecked():
            switch_on += 'show_dialog_stop_scrape,'
        if not self.Ui.textBrowser_log_main_2.isHidden():
            switch_on += 'show_logs,'
        if self.Ui.checkBox_sortmode_delpic.isChecked():
            switch_on += 'sort_del,'
        if self.Ui.checkBox_net_ipv4_only.isChecked():
            switch_on += 'ipv4_only,'
        if self.Ui.checkBox_dialog_qt.isChecked():
            switch_on += 'qt_dialog,'
        if self.Ui.checkBox_theporndb_hash.isChecked():
            switch_on += 'theporndb_no_hash,'
        if self.Ui.radioButton_hide_close.isChecked():
            switch_on += 'hide_close,'
        elif self.Ui.radioButton_hide_mini.isChecked():
            switch_on += 'hide_mini,'
        else:
            switch_on += 'hide_none,'
        if self.Ui.checkBox_hide_dock_icon.isChecked():
            switch_on += 'hide_dock,'
        if self.Ui.checkBox_highdpi_passthrough.isChecked():
            switch_on += 'passthrough,'
        if self.Ui.checkBox_hide_menu_icon.isChecked():
            switch_on += 'hide_menu,'
        if self.Ui.checkBox_dark_mode.isChecked():
            switch_on += 'dark_mode,'
        if self.Ui.checkBox_copy_netdisk_nfo.isChecked():
            switch_on += 'copy_netdisk_nfo,'

        if self.Ui.checkBox_show_web_log.isChecked():                           # 显示字段刮削过程信息
            show_web_log = 'on'
        else:
            show_web_log = 'off'
        if self.Ui.checkBox_show_from_log.isChecked():                          # 显示字段来源网站信息
            show_from_log = 'on'
        else:
            show_from_log = 'off'
        if self.Ui.checkBox_show_data_log.isChecked():                          # 显示字段内容信息
            show_data_log = 'on'
        else:
            show_data_log = 'off'
        if self.Ui.radioButton_log_on.isChecked():                              # 开启日志
            save_log = 'on'
        elif self.Ui.radioButton_log_off.isChecked():                           # 关闭日志
            save_log = 'off'
        if self.Ui.radioButton_update_on.isChecked():                           # 检查更新
            update_check = 'on'
        elif self.Ui.radioButton_update_off.isChecked():                        # 不检查更新
            update_check = 'off'
        local_library = self.Ui.lineEdit_local_library_path.text()              # 本地资源库
        actors_name = self.Ui.lineEdit_actors_name.text().replace('\n', '')     # 演员名
        netdisk_path = self.Ui.lineEdit_netdisk_path.text()                     # 网盘路径
        localdisk_path = self.Ui.lineEdit_localdisk_path.text()                 # 本地磁盘路径
        if self.Ui.checkBox_hide_window_title.isChecked():                      # 隐藏窗口标题栏
            window_title = 'hide'
        else:                                                                   # 显示窗口标题栏
            window_title = 'show'
        config_file = self.config_file
        config_folder = self.Ui.lineEdit_config_folder.text()                   # 配置文件目录
        if not os.path.exists(config_folder):
            config_folder = self.main_path
        config_path = self.convert_path(os.path.join(config_folder, config_file))

        json_config = {
            'version': self.localversion,
            'config_path': config_path,
            'media_path': media_path,
            'softlink_path': softlink_path,
            'failed_output_folder': failed_output_folder,
            'success_output_folder': success_output_folder,
            'extrafanart_folder': extrafanart_folder,
            'media_type': media_type,
            'sub_type': sub_type,
            'scrape_softlink_path': scrape_softlink_path,
            'folders': folders,
            'string': string,
            'file_size': file_size,
            'no_escape': no_escape,
            'clean_ext': clean_ext,
            'clean_name': clean_name,
            'clean_contains': clean_contains,
            'clean_size': clean_size,
            'clean_ignore_ext': clean_ignore_ext,
            'clean_ignore_contains': clean_ignore_contains,
            'clean_enable': clean_enable,
            'website_single': website_single,
            'website_youma': website_youma,
            'website_wuma': website_wuma,
            'website_suren': website_suren,
            'website_fc2': website_fc2,
            'website_oumei': website_oumei,
            'website_guochan': website_guochan,
            'scrape_like': scrape_like,
            'website_set': website_set,
            'title_website': title_website,
            'title_zh_website': title_zh_website,
            'title_website_exclude': title_website_exclude,
            'title_language': title_language,
            'title_sehua': title_sehua,
            'title_yesjav': title_yesjav,
            'title_translate': title_translate,
            'title_sehua_zh': title_sehua_zh,
            'outline_website': outline_website,
            'outline_zh_website': outline_zh_website,
            'outline_website_exclude': outline_website_exclude,
            'outline_language': outline_language,
            'outline_translate': outline_translate,
            'outline_show': outline_show,
            'actor_website': actor_website,
            'actor_website_exclude': actor_website_exclude,
            'actor_language': actor_language,
            'actor_realname': actor_realname,
            'actor_translate': actor_translate,
            'tag_website': tag_website,
            'tag_website_exclude': tag_website_exclude,
            'tag_language': tag_language,
            'tag_translate': tag_translate,
            'tag_include': tag_include,
            'series_website': series_website,
            'series_website_exclude': series_website_exclude,
            'series_language': series_language,
            'series_translate': series_translate,
            'studio_website': studio_website,
            'studio_website_exclude': studio_website_exclude,
            'studio_language': studio_language,
            'studio_translate': studio_translate,
            'publisher_website': publisher_website,
            'publisher_website_exclude': publisher_website_exclude,
            'publisher_language': publisher_language,
            'publisher_translate': publisher_translate,
            'director_website': director_website,
            'director_website_exclude': director_website_exclude,
            'director_language': director_language,
            'director_translate': director_translate,
            'poster_website': poster_website,
            'poster_website_exclude': poster_website_exclude,
            'thumb_website': thumb_website,
            'thumb_website_exclude': thumb_website_exclude,
            'extrafanart_website': extrafanart_website,
            'extrafanart_website_exclude': extrafanart_website_exclude,
            'score_website': score_website,
            'score_website_exclude': score_website_exclude,
            'release_website': release_website,
            'release_website_exclude': release_website_exclude,
            'runtime_website': runtime_website,
            'runtime_website_exclude': runtime_website_exclude,
            'trailer_website': trailer_website,
            'trailer_website_exclude': trailer_website_exclude,
            'wanted_website': wanted_website,
            'whole_fields': whole_fields,
            'none_fields': none_fields,
            'nfo_include_new': nfo_include_new,
            'nfo_tagline': nfo_tagline,
            'nfo_tag_series': nfo_tag_series,
            'nfo_tag_studio': nfo_tag_studio,
            'nfo_tag_publisher': nfo_tag_publisher,
            'translate_by': translate_by,
            'deepl_key': deepl_key,
            'thread_number': thread_number,
            'javdb_time': javdb_time,
            'thread_time': thread_time,
            'main_mode': main_mode,
            'read_mode': read_mode,
            'update_mode': update_mode,
            'update_a_folder': update_a_folder,
            'update_b_folder': update_b_folder,
            'update_d_folder': update_d_folder,
            'soft_link': soft_link,
            'success_file_move': success_file_move,
            'failed_file_move': failed_file_move,
            'success_file_rename': success_file_rename,
            'del_empty_folder': del_empty_folder,
            'show_poster': show_poster,
            'download_files': download_files,
            'keep_files': keep_files,
            'download_hd_pics': download_hd_pics,
            'google_used': google_used,
            'google_exclude': google_exclude,
            'folder_name': folder_name,
            'naming_file': naming_file,
            'naming_media': naming_media,
            'prevent_char': prevent_char,
            'fields_rule': fields_rule,
            'suffix_sort': suffix_sort,
            'actor_no_name': actor_no_name,
            'release_rule': release_rule,
            'folder_name_max': folder_name_max,
            'file_name_max': file_name_max,
            'actor_name_max': actor_name_max,
            'actor_name_more': actor_name_more,
            'umr_style': umr_style,
            'leak_style': leak_style,
            'wuma_style': wuma_style,
            'youma_style': youma_style,
            'show_moword': show_moword,
            'show_4k': show_4k,
            'cd_name': cd_name,
            'cd_char': cd_char,
            'pic_name': pic_name,
            'trailer_name': trailer_name,
            'hd_name': hd_name,
            'hd_get': hd_get,
            'cnword_char': cnword_char,
            'cnword_style': '^%s^' % cnword_style,
            'folder_cnword': folder_cnword,
            'file_cnword': file_cnword,
            'subtitle_folder': subtitle_folder,
            'subtitle_add': subtitle_add,
            'subtitle_add_chs': subtitle_add_chs,
            'subtitle_add_rescrape': subtitle_add_rescrape,
            'server_type': server_type,
            'emby_url': emby_url,
            'api_key': api_key,
            'emby_on': emby_on,
            'gfriends_github': gfriends_github,
            'actor_photo_folder': actor_photo_folder,
            'poster_mark': poster_mark,
            'thumb_mark': thumb_mark,
            'fanart_mark': fanart_mark,
            'mark_size': mark_size,
            'mark_type': mark_type.strip(','),
            'mark_fixed': mark_fixed,
            'mark_pos': mark_pos,
            'mark_pos_corner': mark_pos_corner,
            'mark_pos_sub': mark_pos_sub,
            'mark_pos_mosaic': mark_pos_mosaic,
            'mark_pos_hd': mark_pos_hd,
            'type': proxy_type,
            'proxy': proxy,
            'timeout': timeout,
            'retry': retry,
            'javbus_website': javbus_website,
            'javdb_website': javdb_website,
            'iqqtv_website': iqqtv_website,
            'avsex_website': avsex_website,
            'hdouban_website': hdouban_website,
            'mdtv_website': mdtv_website,
            'airavcc_website': airavcc_website,
            'lulubar_website': lulubar_website,
            'javlibrary_website': javlibrary_website,
            'javdb': javdb,
            'javbus': javbus,
            'theporndb_api_token': theporndb_api_token,
            'show_web_log': show_web_log,
            'show_from_log': show_from_log,
            'show_data_log': show_data_log,
            'save_log': save_log,
            'update_check': update_check,
            'local_library': local_library,
            'actors_name': actors_name,
            'netdisk_path': netdisk_path,
            'localdisk_path': localdisk_path,
            'window_title': window_title,
            'switch_on': switch_on,
            'timed_interval': timed_interval,
            'rest_count': rest_count,
            'rest_time': rest_time,
            'statement': self.statement,
        }
        cf.save_config(json_config)
        try:
            self.config = cf.get_config()                                       # 更新全局配置信息
            self.check_proxyChange()                                            # 更新代理信息
            self.windows_auto_adjust()                                          # 界面自动调整
        except:
            pass

    # ======================================================================================检测代理变化

    def check_proxyChange(self):
        proxy_type = self.config.get('type')
        proxy = self.config.get('proxy')
        timeout = self.config.get('timeout')
        retry_count = self.config.get('retry')
        self.new_proxy = (proxy_type, proxy, timeout, retry_count)
        if self.current_proxy:
            if self.new_proxy != self.current_proxy:
                self.show_net_info('\n🌈 代理设置已改变：')
                self.show_netstatus(self.new_proxy)
        self.current_proxy = self.new_proxy
        return self.new_proxy

    # ========================================================================获取/保存剩余待刮削列表

    def get_remain_list(self):
        if os.path.isfile(self.remain_list_path):
            with open(self.remain_list_path, 'r', encoding='utf-8', errors='ignore') as f:
                temp = f.read()
                self.remain_list = temp.split('\n') if temp.strip() else []

                if 'remain_task' in self.config.get('switch_on') and len(self.remain_list):
                    box = QMessageBox(QMessageBox.Information, '继续刮削', '上次刮削未完成，是否继续刮削剩余任务？')
                    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                    box.button(QMessageBox.Yes).setText('继续刮削剩余任务')
                    box.button(QMessageBox.No).setText('从头刮削')
                    box.button(QMessageBox.Cancel).setText('取消')
                    box.setDefaultButton(QMessageBox.No)
                    reply = box.exec()
                    if reply == QMessageBox.Cancel:
                        return True                                         # 不刮削

                    if reply == QMessageBox.Yes:
                        movie_path = self.config.get('media_path')
                        if movie_path == '':
                            movie_path = self.main_path
                        if not re.findall(r'[/\\]$', movie_path):
                            movie_path += '/'
                        movie_path = self.convert_path(movie_path)
                        temp_remain_path = self.convert_path(self.remain_list[0])
                        if movie_path not in temp_remain_path:
                            box = QMessageBox(QMessageBox.Warning, '提醒', f'很重要！！请注意：\n当前待刮削目录：{movie_path}\n剩余任务文件路径：{temp_remain_path}\n剩余任务的文件路径，并不在当前待刮削目录中！\n剩余任务很可能是使用其他配置扫描的！\n请确认成功输出目录和失败目录是否正确！如果配置不正确，继续刮削可能会导致文件被移动到新配置的输出位置！\n是否继续刮削？')
                            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                            box.button(QMessageBox.Yes).setText('继续')
                            box.button(QMessageBox.No).setText('取消')
                            box.setDefaultButton(QMessageBox.No)
                            reply = box.exec()
                            if reply == QMessageBox.No:
                                return True
                        self.show_log_text(f'🍯 🍯 🍯 NOTE: 继续刮削未完成任务！！！ 剩余未刮削文件数量（{len(self.remain_list)})')
                        self.start_new_scrape('default_folder', self.remain_list)
                        return True
        return False

    def update_remain_list(self, file_path=''):
        if file_path:
            file_path = self.convert_path(file_path)
            try:
                self.remain_list.remove(file_path)
                self.can_save_remain = True
            except Exception as e:
                self.show_log_text(f'remove:  {file_path}\n {str(e)}\n {traceback.format_exc()}')

    def save_remain_list(self):
        if self.can_save_remain and 'remain_task' in self.config.get('switch_on'):
            if not os.path.isdir(self.userdata_folder):
                os.makedirs(self.userdata_folder)
            try:
                with open(self.remain_list_path, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write('\n'.join(self.remain_list))
                    self.can_save_remain = False
            except Exception as e:
                self.show_log_text(f'save remain list error: {str(e)}\n {traceback.format_exc()}')

    # ========================================================================获取/保存成功刮削列表

    def get_success_list(self):
        self.success_save_time = time.time()
        if os.path.isfile(self.success_list_path):
            with open(self.success_list_path, 'r', encoding='utf-8', errors='ignore') as f:
                temp = f.read()
                self.success_list = set(temp.split('\n')) if temp.strip() else set()
                if '' in self.success_list:
                    self.success_list.remove('')
                self.save_success_list()
        self.Ui.pushButton_view_success_file.setText(f'查看 ({len(self.success_list)})')

    def save_success_list(self, old_path='', new_path=''):
        if old_path and self.config.get('record_success_file'):
            # 软硬链接时，保存原路径；否则保存新路径
            if self.config.get('soft_link') != 0:
                self.success_list.add(self.convert_path(old_path))
            else:
                self.success_list.add(self.convert_path(new_path))
                if os.path.islink(new_path):
                    self.success_list.add(self.convert_path(old_path))
                    self.success_list.add(self.convert_path(read_link(new_path)))
        if self.get_used_time(self.success_save_time) > 5 or not old_path:
            self.success_save_time = time.time()
            if not os.path.isdir(self.userdata_folder):
                os.makedirs(self.userdata_folder)
            try:
                with open(self.success_list_path, 'w', encoding='utf-8', errors='ignore') as f:
                    temp = list(self.success_list)
                    temp.sort()
                    f.write('\n'.join(temp))
            except Exception as e:
                self.show_log_text(f'  Save success list Error {str(e)}\n {traceback.format_exc()}')
            self.Ui.pushButton_view_success_file.setText(f'查看 ({len(self.success_list)})')

    def pushButton_success_list_save_clicked(self):
        box = QMessageBox(QMessageBox.Warning, '保存成功列表', '确定要将当前列表保存为已刮削成功文件列表吗？')
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.button(QMessageBox.Yes).setText('保存')
        box.button(QMessageBox.No).setText('取消')
        box.setDefaultButton(QMessageBox.No)
        reply = box.exec()
        if reply == QMessageBox.Yes:
            with open(self.success_list_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(self.Ui.textBrowser_show_success_list.toPlainText().replace('暂无成功刮削的文件', '').strip())
                self.get_success_list()
            self.Ui.widget_show_success.hide()

    def pushButton_success_list_clear_clicked(self):
        box = QMessageBox(QMessageBox.Warning, '清空成功列表', '确定要清空当前已刮削成功文件列表吗？')
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.button(QMessageBox.Yes).setText('清空')
        box.button(QMessageBox.No).setText('取消')
        box.setDefaultButton(QMessageBox.No)
        reply = box.exec()
        if reply == QMessageBox.Yes:
            self.success_list.clear()
            self.save_success_list()
            self.Ui.widget_show_success.hide()

    def show_success_list(self):
        self.Ui.widget_show_success.show()
        info = '暂无成功刮削的文件'
        if len(self.success_list):
            temp = list(self.success_list)
            temp.sort()
            info = '\n'.join(temp)
        self.Ui.textBrowser_show_success_list.setText(info)

    # ========================================================================获取视频列表

    def movie_lists(self, escape_folder_list, movie_type, movie_path):
        start_time = time.time()
        total = []
        temp_total = []
        file_type = movie_type.split('|')
        skip_list = ['skip', '.skip', '.ignore']
        not_skip_success = bool('skip_success_file' not in self.config.get('no_escape'))
        i = 100
        skip = 0
        skip_repeat_softlink = 0
        self.show_traceback_log("🔎 遍历待刮削目录....")
        for root, dirs, files in os.walk(movie_path):

            # 文件夹是否在排除目录
            root = os.path.join(root, '').replace('\\', '/')
            if 'behind the scenes' in root or root in escape_folder_list:
                dirs[:] = []                                                    # 忽略当前文件夹子目录
                continue

            # 文件夹是否存在跳过文件
            for skip_key in skip_list:
                if skip_key in files:
                    dirs[:] = []
                    break
            else:
                # 处理文件列表
                for f in files:
                    file_name, file_type_current = os.path.splitext(f)

                    # 跳过隐藏文件、预告片、主题视频
                    if re.search(r'^\..+', file_name):
                        continue
                    if 'trailer.' in f or 'trailers.' in f:
                        continue
                    if 'theme_video.' in f:
                        continue

                    # 判断清理文件
                    path = os.path.join(root, f)
                    if need_clean(path, f, file_type_current):
                        result, error_info = delete_file(path)
                        if result:
                            self.show_log_text(' 🗑 Clean: %s ' % path)
                        else:
                            self.show_log_text(' 🗑 Clean error: %s ' % error_info)
                        continue

                    # 添加文件
                    if file_type_current.lower() in file_type:
                        if os.path.islink(path):
                            real_path = read_link(path).replace("\\\\", "/").replace("\\", "/")
                            # 清理失效的软链接文件
                            if 'check_symlink' in self.config.get('no_escape') and not os.path.exists(real_path):
                                result, error_info = delete_file(path)
                                if result:
                                    self.show_log_text(' 🗑 Clean dead link: %s ' % path)
                                else:
                                    self.show_log_text(' 🗑 Clean dead link error: %s ' % error_info)
                                continue
                            if real_path in temp_total:
                                skip_repeat_softlink += 1
                                delete_file(path)
                                continue
                            else:
                                temp_total.append(real_path)

                        path = path.replace("\\\\", "/").replace("\\", "/")
                        if path in temp_total:
                            skip_repeat_softlink += 1
                            continue
                        else:
                            temp_total.append(path)
                        # mac 转换成 NFC，因为mac平台nfc和nfd指向同一个文件，windows平台指向不同文件
                        if not self.is_windows:
                            path = self.nfd2c(path)
                        new_path = self.convert_path(path)
                        if not_skip_success or new_path not in self.success_list:
                            total.append(new_path)
                        else:
                            skip += 1

            found_count = len(total)
            if found_count >= i:
                i = found_count + 100
                self.show_traceback_log(f"✅ Found ({found_count})! Skip successfully scraped ({skip}) repeat softlink ({skip_repeat_softlink})! ({self.get_used_time(start_time)}s)... Still searching, please wait... \u3000")
                self.show_log_text('    %s Found (%s)! Skip successfully scraped (%s) repeat softlink (%s)! (%ss)... Still searching, please wait... \u3000' % (self.get_current_time(), found_count, skip, skip_repeat_softlink, self.get_used_time(start_time)))

        total.sort()
        self.show_traceback_log(f"🎉 Done!!! Found ({len(total)})! Skip successfully scraped ({skip}) repeat softlink ({skip_repeat_softlink})! ({self.get_used_time(start_time)}s) \u3000")
        self.show_log_text(f'    Done!!! Found ({len(total)})! Skip successfully scraped ({skip}) repeat softlink ({skip_repeat_softlink})! ({self.get_used_time(start_time)}s) \u3000')
        return total

    def deal_url(self, url):
        if '://' not in url:
            url = 'https://' + url
        url = url.strip('/ ')
        web_dic = {
            'airav.cc': 'airav_cc',
            'airav.wiki': 'airav',
            '9sex': 'avsex',
            'avsex': 'avsex',
            'avsox': 'avsox',
            'dmm.co': 'dmm',
            'fc2.com': 'fc2',
            'fc2club': 'fc2club',
            'fc2hub': 'fc2hub',
            'iqq': 'iqqtv',
            'jav321': 'jav321',
            'javbus': 'javbus',
            'javdb': 'javdb',
            'javlibrary': 'javlibrary',
            'mdtv': 'mdtv',
            'mdpjzip': 'mdtv',
            'madouqu': 'madouqu',
            'mgstage': 'mgstage',
            '7mmtv': '7mmtv',
            'bb9711': '7mmtv',
            'xcity': 'xcity',
            'freejavbt': 'freejavbt',
            'getchu': 'getchu',
            'mywife': 'mywife',
            'giga': 'giga',
            'faleno': 'faleno',
            'dahlia': 'dahlia',
            'hdouban': 'hdouban',
            'byym21': 'hdouban',
            'huangdb2': 'hdouban',
            'lulubar': 'lulubar',
            'love6': 'love6',
            'cnmdb': 'cnmdb',
            'kin8': 'kin8',
            'fantastica': 'fantastica',
            'metadataapi': 'theporndb',
            'prestige': 'prestige',
        }
        for key, vlaue in web_dic.items():
            if key.lower() in url.lower():
                return vlaue, url

        # 自定义的网址
        avsex_website = self.config.get('avsex_website')
        if avsex_website and avsex_website in url:
            return 'avsex', url
        iqqtv_website = self.config.get('iqqtv_website')
        if iqqtv_website and iqqtv_website in url:
            return 'iqqtv', url
        hdouban_website = self.config.get('hdouban_website')
        if hdouban_website and hdouban_website in url:
            return 'hdouban', url
        mdtv_website = self.config.get('mdtv_website')
        if mdtv_website and mdtv_website in url:
            return 'mdtv', url
        airavcc_website = self.config.get('airavcc_website')
        if airavcc_website and airavcc_website in url:
            return 'airav_cc', url
        lulubar_website = self.config.get('lulubar_website')
        if lulubar_website and lulubar_website in url:
            return 'lulubar', url
        javbus_website = self.config.get('javbus_website')
        if javbus_website and javbus_website in url:
            return 'javbus', url
        javdb_website = self.config.get('javdb_website')
        if javdb_website and javdb_website in url:
            return 'javdb', url
        javlibrary_website = self.config.get('javlibrary_website')
        if javlibrary_website and javlibrary_website in url:
            return 'javlibrary', url

        return False, url

    # ======================================================================================点选择目录弹窗
    def get_select_folder_path(self):
        media_path = self.Ui.lineEdit_movie_path.text()                         # 获取待刮削目录作为打开目录
        if not media_path:
            media_path = self.main_path
        media_folder_path = QFileDialog.getExistingDirectory(None, "选择目录", media_path, options=self.options)
        return self.convert_path(media_folder_path)

    # ======================================================================================工具页面本地资源库点选择目录
    def pushButton_select_local_library_clicked(self):
        media_folder_path = self.get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_local_library_path.setText(self.convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # ======================================================================================工具页面网盘目录点选择目录
    def pushButton_select_netdisk_path_clicked(self):
        media_folder_path = self.get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_netdisk_path.setText(self.convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # ======================================================================================工具页面本地目录点选择目录
    def pushButton_select_localdisk_path_clicked(self):
        media_folder_path = self.get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_localdisk_path.setText(self.convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # ======================================================================================工具/设置页面点选择目录
    def pushButton_select_media_folder_clicked(self):
        media_folder_path = self.get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_movie_path.setText(self.convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # ======================================================================================设置-目录-软链接目录-点选择目录
    def pushButton_select_softlink_folder_clicked(self):
        media_folder_path = self.get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_movie_softlink_path.setText(self.convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # ======================================================================================设置-目录-成功输出目录-点选择目录
    def pushButton_select_sucess_folder_clicked(self):
        media_folder_path = self.get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_success.setText(self.convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # ======================================================================================设置-目录-失败输出目录-点选择目录
    def pushButton_select_failed_folder_clicked(self):
        media_folder_path = self.get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_fail.setText(self.convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # ======================================================================================设置-目录-跳过已刮削文件-点查看
    def pushButton_view_success_file_clicked(self):
        media_folder_path = self.get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_fail.setText(self.convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # ======================================================================================设置-字幕-字幕文件目录-点选择目录
    def pushButton_select_subtitle_folder_clicked(self):
        media_folder_path = self.get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_sub_folder.setText(self.convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # ======================================================================================设置-头像-头像文件目录-点选择目录
    def pushButton_select_actor_photo_folder_clicked(self):
        media_folder_path = self.get_select_folder_path()
        if media_folder_path:
            self.Ui.lineEdit_actor_photo_folder.setText(self.convert_path(media_folder_path))
            self.pushButton_save_config_clicked()

    # ======================================================================================设置-其他-配置文件目录-点选择目录
    def pushButton_select_config_folder_clicked(self):
        media_folder_path = self.convert_path(self.get_select_folder_path())
        if media_folder_path and media_folder_path != self.config_folder:
            config_path = os.path.join(media_folder_path, 'config.ini')
            with open('MDCx.config', 'w', encoding='UTF-8') as f:
                f.write(config_path)
            if os.path.isfile(config_path):
                temp_dark = self.dark_mode
                temp_window_radius = self.window_radius
                self.load_config()
                if temp_dark != self.dark_mode and temp_window_radius == self.window_radius:
                    self.show_flag = True
                    self.windows_auto_adjust()
            else:
                self.Ui.lineEdit_config_folder.setText(media_folder_path)
                self.pushButton_save_config_clicked()
            self.show_scrape_info('💡 目录已切换！%s' % self.get_current_time())

    # ======================================================================================工具-软链接助手
    # 工具点一键创建软链接
    def pushButton_creat_symlink_clicked(self):
        self.pushButton_show_log_clicked()                                      # 点击按钮后跳转到日志页面

        if bool('copy_netdisk_nfo' in self.config.get('switch_on')) != bool(self.Ui.checkBox_copy_netdisk_nfo.isChecked()):
            self.pushButton_save_config_clicked()

        try:
            t = threading.Thread(target=self.newtdisk_creat_symlink, args=(bool(self.Ui.checkBox_copy_netdisk_nfo.isChecked()), ))
            self.threads_list.append(t)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())

    def newtdisk_creat_symlink(self, copy_flag, netdisk_path='', local_path=''):
        real_path_list = []
        from_tool = False
        if not netdisk_path:
            from_tool = True
            self.change_buttons_status()
        start_time = time.time()
        if not netdisk_path:
            netdisk_path = self.convert_path(self.config.get('netdisk_path'))
        if not local_path:
            local_path = self.convert_path(self.config.get('localdisk_path'))
        self.show_log_text('🍯 🍯 🍯 NOTE: Begining creat symlink!!!')
        self.show_log_text('\n ⏰ Start time: ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        self.show_log_text(f' 📁 Source path: {netdisk_path} \n 📁 Softlink path: {local_path} \n')
        try:
            if netdisk_path and local_path:
                nfo_type_list = ['.nfo', '.jpg', '.png'] + self.config.get('sub_type').split('|')
                file_type_list = self.config.get('media_type').lower().split('|') + nfo_type_list + self.config.get('sub_type').split('|')
                total = 0
                copy_num = 0
                link_num = 0
                fail_num = 0
                skip_num = 0
                for root, dirs, files in os.walk(netdisk_path, topdown=True):
                    if self.convert_path(root) == self.convert_path(local_path):
                        dirs[:] = []                                                    # 忽略当前文件夹子目录
                        continue
                    for f in files:
                        # 跳过隐藏文件、预告片、主题视频
                        if re.search(r'^\..+', f):
                            continue
                        if 'trailer.' in f or 'trailers.' in f:
                            continue
                        if 'theme_video.' in f:
                            continue

                        net_folder_path = self.convert_path(root)
                        local_folder_path = self.convert_path(os.path.join(local_path, net_folder_path.replace(netdisk_path, '', 1).strip('/\\')))
                        local_folder_path = re.sub(r"\s", ' ', local_folder_path).replace(' \\', "\\").replace('\\ ', "\\").strip().replace('■', '')
                        file_type_current = os.path.splitext(f)[1].lower()
                        if file_type_current in file_type_list:
                            total += 1
                            net_file_path = self.convert_path(os.path.join(root, f))
                            local_file_path = self.convert_path(os.path.join(local_folder_path, f.strip()))
                            local_file_path = re.sub(r"\s", ' ', local_file_path).strip().replace('■', '')
                            if file_type_current in nfo_type_list:
                                if copy_flag:
                                    if not os.path.isfile(local_file_path):
                                        if not os.path.isdir(local_folder_path):
                                            os.makedirs(local_folder_path)
                                        copy_file(net_file_path, local_file_path)
                                        self.show_log_text(f' {total} 🍀 Copy done!\n {net_file_path} ')
                                        copy_num += 1
                                        continue
                                    else:
                                        self.show_log_text(f' {total} 🟠 Copy skip! Softlink path already exists this file!\n {net_file_path} ')
                                        skip_num += 1
                            else:
                                if os.path.islink(net_file_path):
                                    net_file_path = read_link(net_file_path)
                                if not os.path.exists(net_file_path):
                                    self.show_log_text(f' {total} 🟠 Link skip! Source file doesnot exist!\n {net_file_path} ')
                                    skip_num += 1
                                    continue
                                elif net_file_path in real_path_list:
                                    self.show_log_text(f' {total} 🟠 Link skip! Source file already linked, this file is duplicate!\n {net_file_path} ')
                                    skip_num += 1
                                    continue
                                else:
                                    real_path_list.append(net_file_path)

                                if os.path.islink(local_file_path):
                                    delete_file(local_file_path)
                                elif os.path.exists(local_file_path):
                                    self.show_log_text(f' {total} 🟠 Link skip! Softlink path already exists a real file!\n {net_file_path} ')
                                    fail_num += 1
                                    continue
                                elif not os.path.isdir(local_folder_path):
                                    os.makedirs(local_folder_path)

                                try:
                                    os.symlink(net_file_path, local_file_path)
                                    self.show_log_text(f' {total} 🍀 Link done!\n {net_file_path} ')
                                    link_num += 1
                                except Exception as e:
                                    print(traceback.format_exc())
                                    error_info = ''
                                    if 'symbolic link privilege not held' in str(e):
                                        error_info = '   \n没有创建权限，请尝试管理员权限！或按照教程开启用户权限： https://www.jianshu.com/p/0e307bfe8770'
                                    self.show_log_text(f' {total} 🔴 Link failed!{error_info} \n {net_file_path} ')
                                    self.show_log_text(traceback.format_exc())
                                    fail_num += 1

                self.show_log_text("\n 🎉🎉🎉 All finished!!!(%ss) Total %s , Linked %s , Copied %s , Skiped %s , Failed %s " % (self.get_used_time(start_time), total, link_num, copy_num, skip_num, fail_num))
            else:
                self.show_log_text(' 🔴 网盘目录和本地目录不能为空！请重新设置！(%ss)' % (self.get_used_time(start_time)))
        except Exception as e:
            print(traceback.format_exc())
            self.show_log_text(str(e), traceback.format_exc())

        self.show_log_text('================================================================================')
        if from_tool:
            self.reset_buttons_status()

    # ======================================================================================工具-检查番号
    # 工具点检查缺失番号
    def pushButton_find_missing_number_clicked(self):
        self.pushButton_show_log_clicked()                                      # 点击按钮后跳转到日志页面

        # 如果本地资源库或演员与配置内容不同，则自动保存
        if self.Ui.lineEdit_actors_name.text() != self.config.get('actors_name') or self.Ui.lineEdit_local_library_path.text() != self.config.get('local_library'):
            self.pushButton_save_config_clicked()
        try:
            t = threading.Thread(target=self.check_missing_number, args=(True, ))
            self.threads_list.append(t)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())

    # 检查缺失番号
    def check_missing_number(self, actor_flag):
        self.change_buttons_status()
        start_time = time.time()
        json_data_new = {}

        # 获取资源库配置
        movie_type = self.config.get('media_type')
        movie_path = self.config.get('local_library').replace('\\', '/')        # 用户设置的扫描媒体路径
        movie_path_list = set(re.split(r'[,，]', movie_path))                    # 转成集合，去重
        new_movie_path_list = set()
        for i in movie_path_list:
            if i == '':                                                         # 为空时，使用主程序目录
                i = self.main_path
            new_movie_path_list.add(i)
        new_movie_path_list = sorted(new_movie_path_list)

        # 遍历本地资源库
        if self.local_number_flag != new_movie_path_list:
            self.show_log_text('')
            self.show_log_text('\n本地资源库地址:\n   %s\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n⏳ 开始遍历本地资源库，以获取本地视频的最新列表...\n   提示：每次启动第一次查询将更新本地视频数据。（大概1000个/30秒，如果视频较多，请耐心等待。）' % '\n   '.join(new_movie_path_list))
            all_movie_list = []
            for i in new_movie_path_list:
                movie_list = self.movie_lists('', movie_type, i)                # 获取所有需要刮削的影片列表
                all_movie_list.extend(movie_list)
            self.show_log_text('🎉 获取完毕！共找到视频数量（%s）(%ss)' % (len(all_movie_list), self.get_used_time(start_time)))

            # 获取本地番号
            start_time_local = time.time()
            self.show_log_text('\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n⏳ 开始获取本地视频的番号信息...')
            local_number_list = self.local_number_list_path
            if not os.path.exists(local_number_list):
                self.show_log_text('   提示：正在生成本地视频的番号信息数据...（第一次较慢，请耐心等待，以后只需要查找新视频，速度很快）')
                with open(local_number_list, 'w', encoding='utf-8') as f:
                    f.write('{}')
            with open(local_number_list, 'r', encoding='utf-8') as data:
                json_data = json.load(data)
            for movie_path in all_movie_list:
                nfo_path = os.path.splitext(movie_path)[0] + '.nfo'
                json_data_temp = {}
                number = ''
                if json_data.get(movie_path):
                    number, has_sub = json_data.get(movie_path)

                else:
                    if os.path.exists(nfo_path):
                        with open(nfo_path, 'r', encoding='utf-8') as f:
                            nfo_content = f.read()
                        number_result = re.findall(r'<num>(.+)</num>', nfo_content)
                        if number_result:
                            number = number_result[0]

                            if '<genre>中文字幕</genre>' in nfo_content or '<tag>中文字幕</tag>' in nfo_content:
                                has_sub = True
                            else:
                                has_sub = False
                    if not number:
                        json_data_temp, number, folder_old_path, file_name, file_ex, sub_list, file_show_name, file_show_path = self.get_file_info(movie_path, copy_sub=False)
                        has_sub = json_data_temp['has_sub']                     # 视频中文字幕标识
                    cn_word_icon = '🀄️' if has_sub else ''
                    self.show_log_text('   发现新番号：{:<10} {}'.format(number, cn_word_icon))
                temp_number = re.findall(r'\d{3,}([a-zA-Z]+-\d+)', number)      # 去除前缀，因为 javdb 不带前缀
                number = temp_number[0] if temp_number else number
                json_data_new[movie_path] = [number, has_sub]                   # 用新表，更新完重新写入到本地文件中
                self.local_number_set.add(number)                               # 添加到本地番号集合
                if has_sub:
                    self.local_number_cnword_set.add(number)                    # 添加到本地有字幕的番号集合

            with open(local_number_list, 'w', encoding='utf-8') as f:
                json.dump(
                    json_data_new,
                    f,
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=4,
                    separators=(',', ': '),
                )
            self.local_number_flag = new_movie_path_list
            self.show_log_text('🎉 获取完毕！共获取番号数量（%s）(%ss)' % (len(json_data_new), self.get_used_time(start_time_local)))

        # 查询演员番号
        if self.config.get('actors_name'):
            actor_list = re.split(r'[,，]', self.config.get('actors_name'))
            self.show_log_text('\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n🔍 需要查询的演员：\n   %s' % (', '.join(actor_list)))
            for actor_name in actor_list:
                if not actor_name:
                    continue
                if 'http' in actor_name:
                    actor_url = actor_name
                else:
                    actor_url = self.get_actor_data(actor_name).get('href')
                if actor_url:
                    self.show_log_text('\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n⏳ 从 JAVDB 获取 [ %s ] 的所有番号列表...' % actor_name)
                    self.get_actor_missing_numbers(actor_name, actor_url, actor_flag)
                else:
                    self.show_log_text('\n🔴 未找到 [ %s ] 的主页地址，你可以填写演员的 JAVDB 主页地址替换演员名称...' % actor_name)
        else:
            self.show_log_text('\n🔴 没有要查询的演员！')

        self.show_log_text('\n🎉 查询完毕！共用时(%ss)' % (self.get_used_time(start_time)))
        self.reset_buttons_status()

    # 获取演员缺少的番号列表
    def get_actor_missing_numbers(self, actor_name, actor_url, actor_flag):
        start_time = time.time()
        actor_single_url = actor_url + '?t=s'

        # 获取演员的所有番号，如果字典有，就从字典读取，否则去网络请求
        if not self.actor_numbers_dic.get(actor_url):
            self.actor_numbers_dic[actor_url] = {}
            self.actor_numbers_dic[actor_single_url] = {}                       # 单体作品
            self.get_actor_numbers(actor_url, actor_single_url)                 # 如果字典里没有该演员主页的番号，则从网络获取演员番号

        # 演员信息排版和显示
        actor_info = self.actor_numbers_dic.get(actor_url)
        len_single = len(self.actor_numbers_dic.get(actor_single_url))
        self.show_log_text('🎉 获取完毕！共找到 [ %s ] 番号数量（%s）单体数量（%s）(%ss)' % (actor_name, len(actor_info), len_single, self.get_used_time(start_time)))
        if actor_info:
            actor_numbers = actor_info.keys()
            all_list = set()
            not_download_list = set()
            not_download_magnet_list = set()
            not_download_cnword_list = set()
            for actor_number in actor_numbers:
                video_number, video_date, video_url, download_info, video_title, single_info = actor_info.get(actor_number)
                if actor_flag:
                    video_url = video_title[:30]
                number_str = ('{:>13}  {:<10} {}  {:\u3000>5}   {}'.format(video_date, video_number, single_info, download_info, video_url))
                all_list.add(number_str)
                if actor_number not in self.local_number_set:
                    not_download_list.add(number_str)
                    if '🧲' in download_info:
                        not_download_magnet_list.add(number_str)

                    if '🀄️' in download_info:
                        not_download_cnword_list.add(number_str)
                elif actor_number not in self.local_number_cnword_set and '🀄️' in download_info:
                    not_download_cnword_list.add(number_str)

            all_list = sorted(all_list, reverse=True)
            not_download_list = sorted(not_download_list, reverse=True)
            not_download_magnet_list = sorted(not_download_magnet_list, reverse=True)
            not_download_cnword_list = sorted(not_download_cnword_list, reverse=True)

            self.show_log_text('\n👩 [ %s ] 的全部网络番号(%s)...\n%s' % (actor_name, len(all_list), ('=' * 97)))
            if all_list:
                for each in all_list:
                    self.show_log_text(each)
            else:
                self.show_log_text('🎉 没有缺少的番号...\n')

            self.show_log_text('\n👩 [ %s ] 本地缺失的番号(%s)...\n%s' % (actor_name, len(not_download_list), ('=' * 97)))
            if not_download_list:
                for each in not_download_list:
                    self.show_log_text(each)
            else:
                self.show_log_text('🎉 没有缺少的番号...\n')

            self.show_log_text('\n👩 [ %s ] 本地缺失的有磁力的番号(%s)...\n%s' % (actor_name, len(not_download_magnet_list), ('=' * 97)))
            if not_download_magnet_list:
                for each in not_download_magnet_list:
                    self.show_log_text(each)
            else:
                self.show_log_text('🎉 没有缺少的番号...\n')

            self.show_log_text('\n👩 [ %s ] 本地缺失的有字幕的番号(%s)...\n%s' % (actor_name, len(not_download_cnword_list), ('=' * 97)))
            if not_download_cnword_list:
                for each in not_download_cnword_list:
                    self.show_log_text(each)
            else:
                self.show_log_text('🎉 没有缺少的番号...\n')

    # 获取演员的番号列表
    def get_actor_numbers(self, actor_url, actor_single_url):

        # 获取单体番号
        next_page = True
        number_single_list = set()
        i = 1
        while next_page:
            page_url = actor_url + '?page=%s' % i + '&t=s'
            result, html = get_html(page_url)
            if not result:
                result, html = scraper_html(page_url)
            if not result:
                return
            if 'pagination-next' not in html or i >= 60:
                next_page = False
                if i == 60:
                    self.show_log_text('   已达 60 页上限！！！（JAVDB 仅能返回该演员的前 60 页数据！）')
            html = etree.fromstring(html, etree.HTMLParser())
            actor_info = html.xpath('//a[@class="box"]')
            for each in actor_info:
                video_number = each.xpath('div[@class="video-title"]/strong/text()')[0]
                number_single_list.add(video_number)
            i += 1
        self.actor_numbers_dic[actor_single_url] = number_single_list

        # 获取全部番号
        next_page = True
        i = 1
        while next_page:
            page_url = actor_url + '?page=%s' % i
            html = self.scraper_web(page_url)
            if len(html) < 1:
                return
            if 'pagination-next' not in html or i >= 60:
                next_page = False
                if i == 60:
                    self.show_log_text('   已达 60 页上限！！！（JAVDB 仅能返回该演员的前 60 页数据！）')
            html = etree.fromstring(html, etree.HTMLParser(encoding="utf-8"))
            actor_info = html.xpath('//a[@class="box"]')
            for each in actor_info:
                video_number = each.xpath('div[@class="video-title"]/strong/text()')[0]
                video_title = each.xpath('div[@class="video-title"]/text()')[0]
                video_date = each.xpath('div[@class="meta"]/text()')[0].strip()
                video_url = 'https://javdb.com' + each.get('href')
                video_download_link = each.xpath('div[@class="tags has-addons"]/span[@class="tag is-success"]/text()')
                video_sub_link = each.xpath('div[@class="tags has-addons"]/span[@class="tag is-warning"]/text()')
                download_info = '   '
                if video_sub_link:
                    download_info = '🧲  🀄️'
                elif video_download_link:
                    download_info = '🧲    '
                if video_number in number_single_list:
                    single_info = '单体'
                else:
                    single_info = '\u3000\u3000'
                time_list = re.split(r'[./-]', video_date)
                if len(time_list[0]) == 2:
                    video_date = '%s/%s/%s' % (time_list[2], time_list[0], time_list[1])
                else:
                    video_date = '%s/%s/%s' % (time_list[0], time_list[1], time_list[2])
                # self.show_log_text('{}  {:<10}{:\u3000>5}   {}'.format(video_date, video_number, download_info, video_url))
                self.actor_numbers_dic[actor_url].update({video_number: [video_number, video_date, video_url, download_info, video_title, single_info]})
            i += 1

    def sleep_request(self):
        rr = random.randint(0, 2)
        time.sleep(rr)

    def scraper_web(self, url):
        # self.sleep_request()

        result, html = scraper_html(url)
        if not result:
            self.show_log_text('请求错误: %s' % html)
            return ''
        if "The owner of this website has banned your access based on your browser's behaving" in html:
            self.show_log_text('由于请求过多，javdb网站暂时禁止了你当前IP的访问！！可访问javdb.com查看详情！ %s' % html)
            return ''
        if 'Cloudflare' in html:
            self.show_log_text('被 Cloudflare 5 秒盾拦截！请尝试更换cookie！')
            return ''
        return html

    # ======================================================================================工具-单文件刮削
    # 点选择文件
    def pushButton_select_file_clicked(self):
        media_path = self.Ui.lineEdit_movie_path.text()                         # 获取待刮削目录作为打开目录
        if not media_path:
            media_path = self.main_path
        file_path, filetype = QFileDialog.getOpenFileName(None, "选取视频文件", media_path, "Movie Files(*.mp4 " "*.avi *.rmvb *.wmv " "*.mov *.mkv *.flv *.ts " "*.webm *.MP4 *.AVI " "*.RMVB *.WMV *.MOV " "*.MKV *.FLV *.TS " "*.WEBM);;All Files(*)", options=self.options)
        if file_path:
            self.Ui.lineEdit_single_file_path.setText(self.convert_path(file_path))

    def pushButton_start_single_file_clicked(self):                             # 点刮削
        self.single_file_path = self.Ui.lineEdit_single_file_path.text().strip()
        if not self.single_file_path:
            self.show_scrape_info('💡 请选择文件！')
            return

        if not os.path.isfile(self.single_file_path):
            self.show_scrape_info('💡 文件不存在！')                                   # 主界面左下角显示信息
            return

        if not self.Ui.lineEdit_appoint_url.text():
            self.show_scrape_info('💡 请填写番号网址！')                                 # 主界面左下角显示信息
            return

        if not self.Ui.comboBox_website.currentIndex():
            self.show_scrape_info('💡 请选择刮削网站！')                                 # 主界面左下角显示信息
            return

        self.pushButton_show_log_clicked()                                      # 点击刮削按钮后跳转到日志页面
        self.start_new_scrape('single_file')

    def pushButton_select_file_clear_info_clicked(self):                        # 点清空信息
        self.Ui.lineEdit_single_file_path.setText('')
        self.Ui.lineEdit_appoint_url.setText('')

        # self.Ui.lineEdit_movie_number.setText('')
        self.Ui.comboBox_website.setCurrentIndex(0)

    # ======================================================================================工具-裁剪封面图

    def pushButton_select_thumb_clicked(self):
        path = self.Ui.lineEdit_movie_path.text()
        if not path:
            path = self.main_path
        file_path, fileType = QFileDialog.getOpenFileName(None, "选取缩略图", path, "Picture Files(*.jpg *.png);;All Files(*)", options=self.options)
        if file_path != '':
            newWin2.showimage(file_path)
            newWin2.show()

    # ======================================================================================设置-点问号

    def pushButton_tips_normal_mode_clicked(self):
        self.show_tips(self.Ui.pushButton_tips_normal_mode.toolTip())

    def pushButton_tips_sort_mode_clicked(self):
        self.show_tips(self.Ui.pushButton_tips_sort_mode.toolTip())

    def pushButton_tips_update_mode_clicked(self):
        self.show_tips(self.Ui.pushButton_tips_update_mode.toolTip())

    def pushButton_tips_read_mode_clicked(self):
        self.show_tips(self.Ui.pushButton_tips_read_mode.toolTip())

    def pushButton_tips_soft_clicked(self):
        self.show_tips(self.Ui.pushButton_tips_soft.toolTip())

    def pushButton_tips_hard_clicked(self):
        self.show_tips(self.Ui.pushButton_tips_hard.toolTip())

    # ======================================================================================设置-显示说明信息

    def show_tips(self, msg):
        self.Ui.textBrowser_show_tips.setText(msg)
        self.Ui.widget_show_tips.show()

    # ======================================================================================设置-刮削网站和字段中的详细说明弹窗

    def pushButton_scrape_note_clicked(self):
        self.show_tips('''<html><head/><body><p><span style=" font-weight:700;">1、以下类型番号，请指定刮削网站，可以提供成功率，节省刮削用时</span></p><p>· 欧美：theporndb </p><p>· 国产：mdtv、madouqu、hdouban、cnmdb、love6</p><p>· 里番：getchu_dmm </p><p>· Mywife：mywife </p><p>· GIGA：giga </p><p>· Kin8：Kin8 </p><p><span style=" font-weight:700;">2、下不了预告片和剧照，请选择「字段优先」</span></p>\
            <p>· 速度优先：字段来自一个网站 </p><p>· 字段优先：分字段刮削，不同字段来自不同网站</p><p>字段优先的信息会比速度优先好很多！建议默认使用「字段优先」</p><p>当文件数量较多，线程数量10+以上，两者耗时差不太多 </p><p><span style=" font-weight:700;">3、匹配到同名的另一个番号信息或者错误番号</span></p><p>请使用单文件刮削。路径：工具 - 单文件刮削 </p><p><span style=" font-weight:700;">4、频繁请求被封 IP 了</span></p><p>建议更换节点，启用「间歇刮削」： 设置 - 其他 - 间歇刮削</p></body></html>''')

    # ======================================================================================设置-刮削网站和字段中的详细说明弹窗

    def pushButton_field_tips_website_clicked(self):
        self.show_tips('''<html><head/><body><p><span style=" font-weight:700;">字段说明</span></p><p>举个🌰，比如刮削一个有码番号的简介字段时，假定： </p><p>1，有码番号设置的网站为（1，2，3，4，5，6，7） </p><p>2，简介字段设置的网站为（9，5，2，7） </p><p>3，简介字段的排除网站为（3，6） （比如3和6的网站没有简介，这时没必要去请求，因此可以加入到排除网站）</p><p><br/></p><p><span style=" font-weight:700;">程序将通过以下方法生成请求网站的顺序表：</span></p><p>1，取简介字段网站和有码番号网站的交集：（5，2，7） （此顺序以简介字段设置的网站顺序为准） </p><p>\
            2，取有码番号剩余的网站，补充在后面，结果为（5，2，7，1，3，4，6） （此顺序以有码番号设置的网站顺序为准。补充的原因是当设置的字段网站未请求到时，可以继续使用有码网站查询，如不想查询可加到排除网站或去掉尽量补全字段的勾选） </p><p>3，去除排除的网站，生成简介的网站请求顺序为（5，2，7，1，4） </p><p>程序将按此顺序进行刮削，即优先请求5，当5获取成功后，就不再继续请求。当5没有获取成功，继续按顺序请求2，依次类推……刮削其他番号和字段同理。</p></body></html>''')

    # ======================================================================================设置-刮削网站和字段中的详细说明弹窗

    def pushButton_field_tips_nfo_clicked(self):
        msg = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n\
<movie>\n\
    <plot><![CDATA[剧情简介]]></plot>\n\
    <outline><![CDATA[剧情简介]]></outline>\n\
    <originalplot><![CDATA[原始剧情简介]]></originalplot>\n\
    <tagline>发行日期 XXXX-XX-XX</tagline> \n\
    <premiered>发行日期</premiered>\n\
    <releasedate>发行日期</releasedate>\n\
    <release>发行日期</release>\n\
    <num>番号</num>\n\
    <title>标题</title>\n\
    <originaltitle>原始标题</originaltitle>\n\
    <sorttitle>类标题 </sorttitle>\n\
    <mpaa>家长分级</mpaa>\n\
    <customrating>自定义分级</customrating>\n\
    <actor>\n\
        <name>名字</name>\n\
        <type>类型：演员</type>\n\
    </actor>\n\
    <director>导演</director>\n\
    <rating>评分</rating>\n\
    <criticrating>影评人评分</criticrating>\n\
    <votes>想看人数</votes>\n\
    <year>年份</year>\n\
    <runtime>时长</runtime>\n\
    <series>系列</series>\n\
    <set>\n\
        <name>合集</name>\n\
    </set>\n\
    <studio>片商/制作商</studio> \n\
    <maker>片商/制作商</maker>\n\
    <publisher>厂牌/发行商</publisher>\n\
    <label>厂牌/发行商</label>\n\
    <tag>标签</tag>\n\
    <genre>风格</genre>\n\
    <cover>背景图地址</cover>\n\
    <poster>封面图地址</poster>\n\
    <trailer>预告片地址</trailer>\n\
    <website>刮削网址</website>\n\
</movie>\n\
        '''
        self.show_tips(msg)

    # ======================================================================================申明

    def show_statement(self):
        if not self.statement:
            return
        msg = '''申明
————————————————————————————————————————————————————————————————
当你查阅、下载了本项目源代码或二进制程序，即代表你接受了以下条款

    · 本项目和项目成果仅供技术，学术交流和Python3性能测试使用
    · 用户必须确保获取影片的途径在用户当地是合法的
    · 运行时和运行后所获取的元数据和封面图片等数据的版权，归版权持有人持有
    · 本项目贡献者编写该项目旨在学习Python3 ，提高编程水平
    · 本项目不提供任何影片下载的线索
    · 请勿提供运行时和运行后获取的数据提供给可能有非法目的的第三方，例如用于非法交易、侵犯未成年人的权利等
    · 用户仅能在自己的私人计算机或者测试环境中使用该工具，禁止将获取到的数据用于商业目的或其他目的，如销售、传播等
    · 用户在使用本项目和项目成果前，请用户了解并遵守当地法律法规，如果本项目及项目成果使用过程中存在违反当地法律法规的行为，请勿使用该项目及项目成果
    · 法律后果及使用后果由使用者承担
    · GPL LICENSE
    · 若用户不同意上述条款任意一条，请勿使用本项目和项目成果
        '''
        box = QMessageBox(QMessageBox.Warning, '申明', msg)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.button(QMessageBox.Yes).setText('同意')
        box.button(QMessageBox.No).setText('不同意')
        box.setDefaultButton(QMessageBox.No)
        reply = box.exec()
        if reply == QMessageBox.No:
            os._exit(0)
        else:
            self.statement -= 1
            self.save_config_clicked()

    # ======================================================================================小工具-视频移动

    def pushButton_move_mp4_clicked(self):
        box = QMessageBox(QMessageBox.Warning, '移动视频和字幕', '确定要移动视频和字幕吗？')
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.button(QMessageBox.Yes).setText('移动')
        box.button(QMessageBox.No).setText('取消')
        box.setDefaultButton(QMessageBox.No)
        reply = box.exec()
        if reply == QMessageBox.Yes:
            self.pushButton_show_log_clicked()                                  # 点击开始移动按钮后跳转到日志页面
            try:
                t = threading.Thread(target=self.move_file_thread)
                self.threads_list.append(t)
                t.start()                                                       # 启动线程,即让线程开始执行
            except:
                self.show_traceback_log(traceback.format_exc())
                self.show_log_text(traceback.format_exc())

    def move_file_thread(self):
        self.change_buttons_status()
        movie_type = self.Ui.lineEdit_movie_type.text().lower()
        sub_type = self.Ui.lineEdit_sub_type.text().lower().replace('|.txt', '')
        all_type = movie_type.strip('|') + '|' + sub_type.strip('|')
        movie_path = self.config.get('media_path').replace('\\', '/')           # 用户设置的扫描媒体路径
        if movie_path == '':                                                    # 未设置为空时，使用主程序目录
            movie_path = self.main_path
        escape_dir = self.Ui.lineEdit_escape_dir_move.text().replace('\\', '/')
        escape_dir = escape_dir + ',Movie_moved'
        escape_folder_list = escape_dir.split(',')
        escape_folder_new_list = []
        for es in escape_folder_list:                                           # 排除目录可以多个，以，,分割
            es = es.strip(' ')
            if es:
                es = self.get_path(movie_path, es).replace('\\', '/')
                if es[-1] != '/':                                               # 路径尾部添加“/”，方便后面move_list查找时匹配路径
                    es += '/'
                escape_folder_new_list.append(es)
        movie_list = self.movie_lists(escape_folder_new_list, all_type, movie_path)
        if not movie_list:
            self.show_log_text("No movie found!")
            self.show_log_text("================================================================================")
            self.reset_buttons_status()
            return
        des_path = os.path.join(movie_path, 'Movie_moved')
        if not os.path.exists(des_path):
            self.show_log_text('Created folder: Movie_moved')
            os.makedirs(des_path)
        self.show_log_text('Start move movies...')
        skip_list = []
        for file_path in movie_list:
            file_name = split_path(file_path)[1]
            file_ext = os.path.splitext(file_name)[1]
            try:
                move_file(file_path, des_path)
                if file_ext in movie_type:
                    self.show_log_text('   Move movie: ' + file_name + ' to Movie_moved Success!')
                else:
                    self.show_log_text('   Move sub: ' + file_name + ' to Movie_moved Success!')
            except Exception as e:
                skip_list.append([file_name, file_path, str(e)])
        if skip_list:
            self.show_log_text("\n%s file(s) did not move!" % len(skip_list))
            i = 0
            for info in skip_list:
                i += 1
                self.show_log_text("[%s] %s\n file path: %s\n %s\n" % (i, info[0], info[1], info[2]))
        self.show_log_text("Move movies finished!")
        self.show_log_text("================================================================================")
        self.reset_buttons_status()

    # ======================================================================================设置-emby
    # 设置页面点补全演员信息按钮
    def pushButton_add_actor_info_clicked(self):
        self.pushButton_save_config_clicked()
        self.pushButton_show_log_clicked()                                      # 点按钮后跳转到日志页面
        try:
            t = threading.Thread(target=self.update_emby_actor_info)
            self.threads_list.append(t)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_log_text(traceback.format_exc())

    # 设置页面点补全演员头像按钮
    def pushButton_add_actor_pic_clicked(self):
        self.pushButton_save_config_clicked()
        self.pushButton_show_log_clicked()                                      # 点按钮后跳转到日志页面
        try:
            t = threading.Thread(target=self.update_emby_actor_photo)
            self.threads_list.append(t)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_log_text(traceback.format_exc())

    # 设置页面点补全演员头像按钮 kodi
    def pushButton_add_actor_pic_kodi_clicked(self):
        self.pushButton_save_config_clicked()
        self.pushButton_show_log_clicked()                                      # 点按钮后跳转到日志页面
        try:
            t = threading.Thread(target=self.creat_kodi_actors, args=(True,))
            self.threads_list.append(t)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_log_text(traceback.format_exc())

    # 设置页面点清除演员头像按钮 kodi
    def pushButton_del_actor_folder_clicked(self):
        self.pushButton_show_log_clicked()                                      # 点按钮后跳转到日志页面
        try:
            t = threading.Thread(target=self.creat_kodi_actors, args=(False,))
            self.threads_list.append(t)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_log_text(traceback.format_exc())

    # 设置页面点查看演员列表按钮
    def pushButton_show_pic_actor_clicked(self):
        self.pushButton_show_log_clicked()                                      # 点按钮后跳转到日志页面
        try:
            t = threading.Thread(target=self.show_actor_list, args=(self.Ui.comboBox_pic_actor.currentIndex(), ))
            self.threads_list.append(t)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_log_text(traceback.format_exc())

    # 获取 emby 的演员列表
    def get_emby_actor_list(self):
        server_type = self.config.get('server_type')
        emby_url = self.config.get('emby_url')
        api_key = self.config.get('api_key')
        if 'emby' in server_type:
            server_name = 'Emby'
            url = emby_url + '/emby/Persons?api_key=' + api_key
            # http://192.168.5.191:8096/emby/Persons?api_key=ee9a2f2419704257b1dd60b975f2d64e
            # http://192.168.5.191:8096/emby/Persons/梦乃爱华?api_key=ee9a2f2419704257b1dd60b975f2d64e
        else:
            server_name = 'Jellyfin'
            url = emby_url + '/Persons?api_key=' + api_key

        self.show_log_text(f"⏳ 连接 {server_name} 服务器...")

        if emby_url == '':
            self.show_log_text(f'🔴 {server_name} 地址未填写！')
            self.show_log_text("================================================================================")
            return False
        if api_key == '':
            self.show_log_text(f'🔴 {server_name} API 密钥未填写！')
            self.show_log_text("================================================================================")
            return False

        result, response = get_html(url, proxies=False, json_data=True)
        if not result:
            self.show_log_text(f'🔴 {server_name} 连接失败！请检查 {server_name} 地址 和 API 密钥是否正确填写！ {response}')
            self.show_log_text(traceback.format_exc())
            return False

        actor_list = response['Items']
        self.show_log_text(f"✅ {server_name} 连接成功！共有 {len(actor_list)} 个演员！")
        if not actor_list:
            self.show_log_text("================================================================================")
            return False
        return actor_list

    # 按模式显示演员列表
    def show_actor_list(self, mode):
        self.change_buttons_status()
        start_time = time.time()

        mode += 1
        if mode == 1:
            self.show_log_text('🚀 开始查询所有演员列表...')
        elif mode == 2:
            self.show_log_text('🚀 开始查询 有头像，有信息 的演员列表...')
        elif mode == 3:
            self.show_log_text('🚀 开始查询 没头像，有信息 的演员列表...')
        elif mode == 4:
            self.show_log_text('🚀 开始查询 有头像，没信息 的演员列表...')
        elif mode == 5:
            self.show_log_text('🚀 开始查询 没信息，没头像 的演员列表...')
        elif mode == 6:
            self.show_log_text('🚀 开始查询 有信息 的演员列表...')
        elif mode == 7:
            self.show_log_text('🚀 开始查询 没信息 的演员列表...')
        elif mode == 8:
            self.show_log_text('🚀 开始查询 有头像 的演员列表...')
        elif mode == 9:
            self.show_log_text('🚀 开始查询 没头像 的演员列表...')

        actor_list = self.get_emby_actor_list()
        if actor_list:
            count = 1
            succ_pic = 0
            fail_pic = 0
            succ_info = 0
            fail_info = 0
            succ = 0
            fail_noinfo = 0
            fail_nopic = 0
            fail = 0
            total = len(actor_list)
            actor_list_temp = ''
            logs = ''
            for actor_js in actor_list:
                actor_name = actor_js['Name']
                actor_imagetages = actor_js["ImageTags"]
                actor_homepage, actor_person, pic_url, backdrop_url, backdrop_url_0, update_url = self.get_server_url(actor_js)
                # http://192.168.5.191:8096/web/index.html#!/item?id=2146&serverId=57cdfb2560294a359d7778e7587cdc98

                if actor_imagetages:
                    succ_pic += 1
                    actor_list_temp = f"\n✅ {count}/{total} 已有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
                else:
                    fail_pic += 1
                    actor_list_temp = f"\n🔴 {count}/{total} 没有头像！ 👩🏻 {actor_name} \n{actor_homepage}"

                if mode > 7:
                    if mode == 8 and actor_imagetages:
                        actor_list_temp = f"\n✅ {succ_pic}/{total} 已有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
                        logs += actor_list_temp + '\n'
                    elif mode == 9 and not actor_imagetages:
                        actor_list_temp = f"\n🔴 {fail_pic}/{total} 没有头像！ 👩🏻 {actor_name} \n{actor_homepage}"
                        logs += actor_list_temp + '\n'
                    if count % 100 == 0 or (succ_pic + fail_pic) == total:
                        self.show_log_text(logs)
                        time.sleep(0.01)
                        logs = ''
                    count += 1
                else:
                    # http://192.168.5.191:8096/emby/Persons/梦乃爱华?api_key=ee9a2f2419704257b1dd60b975f2d64e
                    result, res = get_html(actor_person, proxies=False, json_data=True)
                    if not result:
                        self.show_log_text(f"\n🔴 {count}/{total} Emby 获取演员信息错误！👩🏻 {actor_name} \n    错误信息: {res}")
                        continue
                    overview = res.get('Overview')

                    if overview:
                        succ_info += 1
                    else:
                        fail_info += 1

                    if mode == 1:
                        if actor_imagetages and overview:
                            self.show_log_text(f"\n✅ {count}/{total} 已有信息！已有头像！ 👩🏻 {actor_name} \n{actor_homepage}")
                            succ += 1
                        elif actor_imagetages:
                            self.show_log_text(f"\n🔴 {count}/{total} 没有信息！已有头像！ 👩🏻 {actor_name} \n{actor_homepage}")
                            fail_noinfo += 1
                        elif overview:
                            self.show_log_text(f"\n🔴 {count}/{total} 已有信息！没有头像！ 👩🏻 {actor_name} \n{actor_homepage}")
                            fail_nopic += 1
                        else:
                            self.show_log_text(f"\n🔴 {count}/{total} 没有信息！没有头像！ 👩🏻 {actor_name} \n{actor_homepage}")
                            fail += 1
                        count += 1
                    elif mode == 2 and actor_imagetages and overview:
                        self.show_log_text(f"\n✅ {count}/{total} 已有信息！已有头像！ 👩🏻 {actor_name} \n{actor_homepage}")
                        count += 1
                        succ += 1
                    elif mode == 3 and not actor_imagetages and overview:
                        self.show_log_text(f"\n🔴 {count}/{total} 已有信息！没有头像！ 👩🏻 {actor_name} \n{actor_homepage}")
                        count += 1
                        fail_nopic += 1
                    elif mode == 4 and actor_imagetages and not overview:
                        self.show_log_text(f"\n🔴 {count}/{total} 没有信息！已有头像！ 👩🏻 {actor_name} \n{actor_homepage}")
                        count += 1
                        fail_noinfo += 1
                    elif mode == 5 and not actor_imagetages and not overview:
                        self.show_log_text(f"\n🔴 {count}/{total} 没有信息！没有头像！ 👩🏻 {actor_name} \n{actor_homepage}")
                        count += 1
                        fail += 1
                    elif mode == 6 and overview:
                        self.show_log_text(f"\n✅ {count}/{total} 已有信息！ 👩🏻 {actor_name} \n{actor_homepage}")
                        count += 1
                    elif mode == 7 and not overview:
                        self.show_log_text(f"\n🔴 {count}/{total} 没有信息！ 👩🏻 {actor_name} \n{actor_homepage}")
                        count += 1

            self.show_log_text(f'\n\n🎉🎉🎉 查询完成！ 用时: {self.get_used_time(start_time)}秒')
            if mode == 1:
                self.show_log_text(f'👩🏻 演员数量: {total} ✅ 有头像有信息: {succ} 🔴 有头像没信息: {fail_noinfo} 🔴 没头像有信息: {fail_nopic} 🔴 没头像没信息: {fail}\n')
            elif mode == 2:
                other = total - succ
                self.show_log_text(f'👩🏻 演员数量: {total} ✅ 有头像有信息: {succ} 🔴 其他: {other}\n')
            elif mode == 3:
                self.show_log_text(f'👩🏻 演员数量: {total} 🔴 有信息没头像: {fail_nopic}\n')
            elif mode == 4:
                self.show_log_text(f'👩🏻 演员数量: {total} 🔴 有头像没信息: {fail_noinfo}\n')
            elif mode == 5:
                self.show_log_text(f'👩🏻 演员数量: {total} 🔴 没信息没头像: {fail}\n')
            elif mode == 6 or mode == 7:
                self.show_log_text(f'👩🏻 演员数量: {total} ✅ 已有信息: {succ_info} 🔴 没有信息: {fail_info}\n')
            else:
                self.show_log_text(f'👩🏻 演员数量: {total} ✅ 已有头像: {succ_pic} 🔴 没有头像: {fail_pic}\n')
            self.show_log_text("================================================================================")
        self.reset_buttons_status()

    # 补全 kodi 演员头像
    def creat_kodi_actors(self, add):
        self.change_buttons_status()
        self.show_log_text(f"📂 待刮削目录: {self.get_movie_path_setting()[0]}")
        if add:
            self.show_log_text("💡 将为待刮削目录中的每个视频创建 .actors 文件夹，并补全演员图片到 .actors 文件夹中\n")
            self.show_log_text("👩🏻 开始补全 Kodi/Plex/Jvedio 演员头像...")
            gfriends_actor_data = self.get_gfriends_actor_data()
        else:
            self.show_log_text("💡 将清除该目录下的所有 .actors 文件夹...\n")
            gfriends_actor_data = True

        if gfriends_actor_data:
            self.deal_kodi_actors(gfriends_actor_data, add)
        self.reset_buttons_status()
        self.show_log_text("================================================================================")

    # 补全 kodi 头像
    def deal_kodi_actors(self, gfriends_actor_data, add):
        vedio_path = self.get_movie_path_setting()[0]
        if vedio_path == '' or not os.path.isdir(vedio_path):
            self.show_log_text('🔴 待刮削目录不存在！任务已停止！')
            return False
        else:
            actor_folder = os.path.join(self.userdata_folder, 'actor')
            emby_on = self.config.get('emby_on')
            all_files = os.walk(vedio_path)
            all_actor = set()
            success = set()
            failed = set()
            download_failed = set()
            no_pic = set()
            actor_clear = set()
            for root, dirs, files in all_files:
                if not add:
                    for each_dir in dirs:
                        if each_dir == '.actors':
                            kodi_actor_folder = os.path.join(root, each_dir)
                            shutil.rmtree(kodi_actor_folder, ignore_errors=True)
                            self.show_log_text(f'✅ 头像文件夹已清理！{kodi_actor_folder}')
                            actor_clear.add(kodi_actor_folder)
                    continue
                for file in files:
                    if file.lower().endswith('.nfo'):
                        nfo_path = os.path.join(root, file)
                        vedio_actor_folder = os.path.join(root, '.actors')
                        try:
                            with open(nfo_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            parser = etree.HTMLParser(encoding="utf-8")
                            xml_nfo = etree.HTML(content.encode('utf-8'), parser)
                            actor_list = xml_nfo.xpath('//actor/name/text()')
                            for each in actor_list:
                                all_actor.add(each)
                                actor_name_list = self.get_actor_data(each)['keyword']
                                for actor_name in actor_name_list:
                                    if actor_name:
                                        net_pic_path = gfriends_actor_data.get(f'{actor_name}.jpg')
                                        if net_pic_path:
                                            vedio_actor_path = os.path.join(vedio_actor_folder, each + '.jpg')
                                            if os.path.isfile(vedio_actor_path):
                                                if 'actor_replace' not in emby_on:
                                                    success.add(each)
                                                    continue
                                            if 'https://' in net_pic_path:
                                                net_file_name = net_pic_path.split('/')[-1]
                                                net_file_name = re.findall(r'^[^?]+', net_file_name)[0]
                                                local_file_path = os.path.join(actor_folder, net_file_name)
                                                if not os.path.isfile(local_file_path):
                                                    if not self.download_file_with_filepath({'logs': ''}, net_pic_path, local_file_path, actor_folder):
                                                        self.show_log_text(f'🔴 {actor_name} 头像下载失败！{net_pic_path}')
                                                        failed.add(each)
                                                        download_failed.add(each)
                                                        continue
                                            else:
                                                local_file_path = net_pic_path
                                            if not os.path.isdir(vedio_actor_folder):
                                                os.mkdir(vedio_actor_folder)
                                            copy_file(local_file_path, vedio_actor_path)
                                            self.show_log_text(f'✅ {actor_name} 头像已创建！ {vedio_actor_path}')
                                            success.add(each)
                                            break
                                else:
                                    self.show_log_text(f'🔴 {each} 没有头像资源！')
                                    failed.add(each)
                                    no_pic.add(each)
                        except:
                            pass
            if add:
                self.show_log_text(f'\n🎉 操作已完成! 共有演员: {len(all_actor)}, 已有头像: {len(success)}, 没有头像: {len(failed)}, 下载失败: {len(download_failed)}, 没有资源: {len(no_pic)}')
            else:
                self.show_log_text(f'\n🎉 操作已完成! 共清理了 {len(actor_clear)} 个 .actors 文件夹!')
            return

    # 补全 emby 演员头像
    def update_emby_actor_photo(self):
        self.change_buttons_status()
        server_type = self.config.get('server_type')
        if 'emby' in server_type:
            self.show_log_text("👩🏻 开始补全 Emby 演员头像...")
        else:
            self.show_log_text("👩🏻 开始补全 Jellyfin 演员头像...")
        actor_list = self.get_emby_actor_list()
        if actor_list:
            gfriends_actor_data = self.get_gfriends_actor_data()
            if gfriends_actor_data:
                self.deal_actor_photo(actor_list, gfriends_actor_data)
        self.reset_buttons_status()

    # 获取演员头像库数据
    def get_gfriends_actor_data(self):
        emby_on = self.config.get('emby_on')
        gfriends_github = self.config.get('gfriends_github')
        raw_url = f'{gfriends_github}'.replace('github.com/', 'raw.githubusercontent.com/').replace('://www.', '://')
        # 'https://raw.githubusercontent.com/gfriends/gfriends'

        if 'actor_photo_net' in emby_on:
            update_data = False
            self.show_log_text('⏳ 连接 Gfriends 网络头像库...')
            net_url = f'{gfriends_github}/commits/master/Filetree.json'
            result, response = get_html(net_url)
            if not result:
                self.show_log_text('🔴 Gfriends 查询最新数据更新时间失败！')
                net_float = 0
                update_data = True
            else:
                date_time = re.findall(r'datetime="([^"]+)', response)
                lastest_time = time.strptime(date_time[0], '%Y-%m-%dT%H:%M:%SZ')
                net_float = time.mktime(lastest_time) - time.timezone
                net_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(net_float))
                self.show_log_text(f'✅ Gfriends 连接成功！最新数据更新时间: {net_time}')

            # 更新：本地无文件时；更新时间过期；本地文件读取失败时，重新更新
            if not os.path.exists(self.gfriends_json_path) or os.path.getmtime(self.gfriends_json_path) < 1657285200:
                update_data = True
            else:
                try:
                    with open(self.gfriends_json_path, 'r', encoding='utf-8') as f:
                        gfriends_actor_data = json.load(f)
                except:
                    self.show_log_text('🔴 本地缓存数据读取失败！需重新缓存！')
                    update_data = True
                else:
                    local_float = os.path.getmtime(self.gfriends_json_path)
                    local_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(local_float))
                    if not net_float or net_float > local_float:
                        self.show_log_text(f'🍉 本地缓存数据需要更新！本地数据更新时间: {local_time}')
                        update_data = True
                    else:
                        self.show_log_text(f'✅ 本地缓存数据无需更新！本地数据更新时间: {local_time}')
                        return gfriends_actor_data

            # 更新数据
            if update_data:
                self.show_log_text('⏳ 开始缓存 Gfriends 最新数据表...')
                filetree_url = f'{raw_url}/master/Filetree.json'
                result, response = get_html(filetree_url, content=True)
                if not result:
                    self.show_log_text('🔴 Gfriends 数据表获取失败！补全已停止！')
                    return False
                with open(self.gfriends_json_path, "wb") as f:
                    f.write(response)
                self.show_log_text('✅ Gfriends 数据表已缓存！')
                try:
                    with open(self.gfriends_json_path, 'r', encoding='utf-8') as f:
                        gfriends_actor_data = json.load(f)
                except:
                    self.show_log_text('🔴 本地缓存数据读取失败！补全已停止！')
                    return False
                else:
                    content = gfriends_actor_data.get('Content')
                    new_gfriends_actor_data = {}
                    content_list = list(content.keys())
                    content_list.sort()
                    for each_key in content_list:
                        for key, value in content.get(each_key).items():
                            if key not in new_gfriends_actor_data:
                                # https://raw.githubusercontent.com/gfriends/gfriends/master/Content/z-Derekhsu/%E5%A4%A2%E4%B9%83%E3%81%82%E3%81%84%E3%81%8B.jpg
                                actor_url = f'{raw_url}/master/Content/{each_key}/{value}'
                                new_gfriends_actor_data[key] = actor_url
                    with open(self.gfriends_json_path, 'w', encoding='utf-8') as f:
                        json.dump(
                            new_gfriends_actor_data,
                            f,
                            ensure_ascii=False,
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '),
                        )
                    return new_gfriends_actor_data
        else:
            return self.get_local_actor_photo()

    # 获取本地头像库的图片列表
    def get_local_actor_photo(self):
        actor_photo_folder = self.config.get('actor_photo_folder')
        if actor_photo_folder == '' or not os.path.isdir(actor_photo_folder):
            self.show_log_text('🔴 本地头像库文件夹不存在！补全已停止！')
            self.show_log_text("================================================================================")
            return False
        else:
            local_actor_photo_dic = {}
            all_files = os.walk(actor_photo_folder)
            for root, dirs, files in all_files:
                for file in files:
                    if file.endswith('jpg') or file.endswith('png'):
                        if file not in local_actor_photo_dic:
                            pic_path = os.path.join(root, file)
                            local_actor_photo_dic[file] = pic_path

            if not local_actor_photo_dic:
                self.show_log_text('🔴 本地头像库文件夹未发现头像图片！请把图片放到文件夹中！')
                self.show_log_text("================================================================================")
                return False
            return local_actor_photo_dic

    def get_server_url(self, actor_js):
        server_type = self.config.get('server_type')
        emby_url = self.config.get('emby_url')
        api_key = self.config.get('api_key')
        actor_name = actor_js['Name'].replace(' ', '%20')
        actor_id = actor_js['Id']
        server_id = actor_js['ServerId']

        if 'emby' in server_type:
            actor_homepage = f"{emby_url}/web/index.html#!/item?id={actor_id}&serverId={server_id}"
            actor_person = f'{emby_url}/emby/Persons/{actor_name}?api_key={api_key}'
            pic_url = f"{emby_url}/emby/Items/{actor_id}/Images/Primary?api_key={api_key}"
            backdrop_url = f"{emby_url}/emby/Items/{actor_id}/Images/Backdrop?api_key={api_key}"
            backdrop_url_0 = f"{emby_url}/emby/Items/{actor_id}/Images/Backdrop/0?api_key={api_key}"
            update_url = f"{emby_url}/emby/Items/{actor_id}?api_key={api_key}"
        else:
            actor_homepage = f"{emby_url}/web/index.html#!/details?id={actor_id}&serverId={server_id}"
            actor_person = f'{emby_url}/Persons/{actor_name}?api_key={api_key}'
            pic_url = f"{emby_url}/Items/{actor_id}/Images/Primary?api_key={api_key}"
            backdrop_url = f"{emby_url}/Items/{actor_id}/Images/Backdrop?api_key={api_key}"
            backdrop_url_0 = f"{emby_url}/Items/{actor_id}/Images/Backdrop/0?api_key={api_key}"
            update_url = f"{emby_url}/Items/{actor_id}?api_key={api_key}"
            # http://192.168.5.191:8097/Items/f840883833eaaebd915822f5f39e945b/Images/Primary?api_key=9e0fce1acde54158b0d4294731ff7a46
            # http://192.168.5.191:8097/Items/f840883833eaaebd915822f5f39e945b/Images/Backdrop?api_key=9e0fce1acde54158b0d4294731ff7a46
        return actor_homepage, actor_person, pic_url, backdrop_url, backdrop_url_0, update_url

    # 处理演员头像并上传
    def deal_actor_photo(self, actor_list, gfriends_actor_data):
        start_time = time.time()
        emby_on = self.config.get('emby_on')
        actor_folder = os.path.join(self.userdata_folder, 'actor')

        i = 0
        succ = 0
        fail = 0
        skip = 0
        count_all = len(actor_list)
        for actor_js in actor_list:
            i += 1
            deal_percent = '{:.2%}'.format(i / count_all)
            # Emby 有头像时处理
            actor_name = actor_js['Name']
            actor_imagetages = actor_js["ImageTags"]
            actor_backdrop_imagetages = actor_js["BackdropImageTags"]
            if ' ' in actor_name:
                skip += 1
                continue
            actor_homepage, actor_person, pic_url, backdrop_url, backdrop_url_0, update_url = self.get_server_url(actor_js)
            if actor_imagetages and 'actor_photo_miss' in emby_on:
                # self.show_log_text(f'\n{deal_percent} ✅ {i}/{count_all} 已有头像！跳过！ 👩🏻 {actor_name} \n{actor_homepage}')
                skip += 1
                continue

            # 获取演员日文名字
            actor_name_data = self.get_actor_data(actor_name)
            has_name = actor_name_data['has_name']
            jp_name = actor_name
            if has_name:
                jp_name = actor_name_data['jp']

            # graphis 判断
            pic_path, backdrop_path, logs = '', '', ''
            if 'actor_photo_net' in emby_on and has_name:
                if 'graphis_backdrop' in emby_on or 'graphis_face' in emby_on:
                    pic_path, backdrop_path, logs = self.get_graphis_pic(jp_name)

            # 要上传的头像图片未找到时
            if not pic_path:
                pic_path = gfriends_actor_data.get(f'{jp_name}.jpg')
                if not pic_path:
                    pic_path = gfriends_actor_data.get(f'{jp_name}.png')
                    if not pic_path:
                        if actor_imagetages:
                            self.show_log_text(f'\n{deal_percent} ✅ {i}/{count_all} 没有找到头像！继续使用原有头像！ 👩🏻 {actor_name} {logs}\n{actor_homepage}')
                            succ += 1
                            continue
                        self.show_log_text(f'\n{deal_percent} 🔴 {i}/{count_all} 没有找到头像！ 👩🏻 {actor_name}  {logs}\n{actor_homepage}')
                        fail += 1
                        continue
            else:
                pass

            # 头像需要下载时
            if 'https://' in pic_path:
                file_name = pic_path.split('/')[-1]
                file_name = re.findall(r'^[^?]+', file_name)[0]
                file_path = os.path.join(actor_folder, file_name)
                if not os.path.isfile(file_path):
                    if not self.download_file_with_filepath({'logs': ''}, pic_path, file_path, actor_folder):
                        self.show_log_text(f'\n{deal_percent} 🔴 {i}/{count_all} 头像下载失败！ 👩🏻 {actor_name}  {logs}\n{actor_homepage}')
                        fail += 1
                        continue
                pic_path = file_path

            # 检查背景是否存在
            if not backdrop_path:
                backdrop_path = pic_path.replace('.jpg', '-big.jpg')
                if not os.path.isfile(backdrop_path):
                    self.fix_pic(pic_path, backdrop_path)

            # 检查图片尺寸并裁剪为2:3
            self.cut_pic(pic_path)

            # 清理旧图片（backdrop可以多张，不清理会一直累积）
            if actor_backdrop_imagetages:
                for _ in range(len(actor_backdrop_imagetages)):
                    requests.delete(backdrop_url_0)

            # 上传头像到 emby
            if self.upload_actor_photo(pic_url, pic_path) and self.upload_actor_photo(backdrop_url, backdrop_path):
                if not logs or logs == '🍊 graphis.ne.jp 无结果！':
                    if 'actor_photo_net' in self.config.get('emby_on'):
                        logs += ' ✅ 使用 Gfriends 头像和背景！'
                    else:
                        logs += ' ✅ 使用本地头像库头像和背景！'
                self.show_log_text(f'\n{deal_percent} ✅ {i}/{count_all} 头像更新成功！ 👩🏻 {actor_name}  {logs}\n{actor_homepage}')
                succ += 1
            else:
                self.show_log_text(f'\n{deal_percent} 🔴 {i}/{count_all} 头像上传失败！ 👩🏻 {actor_name}  {logs}\n{actor_homepage}')
                fail += 1
        self.show_log_text(f'\n\n 🎉🎉🎉 演员头像补全完成！用时: {self.get_used_time(start_time)}秒 成功: {succ} 失败: {fail} 跳过: {skip}\n')

    def get_graphis_pic(self, actor_name):
        emby_on = self.config.get('emby_on')

        # 生成图片路径和请求地址
        actor_folder = os.path.join(self.userdata_folder, 'actor/graphis')
        pic_old = os.path.join(actor_folder, f'{actor_name}-org-old.jpg')
        fix_old = os.path.join(actor_folder, f'{actor_name}-fix-old.jpg')
        big_old = os.path.join(actor_folder, f'{actor_name}-big-old.jpg')
        pic_new = os.path.join(actor_folder, f'{actor_name}-org-new.jpg')
        fix_new = os.path.join(actor_folder, f'{actor_name}-fix-new.jpg')
        big_new = os.path.join(actor_folder, f'{actor_name}-big-new.jpg')
        if 'graphis_new' in emby_on:
            pic_path = pic_new
            backdrop_path = big_new
            if 'graphis_backgrop' not in emby_on:
                backdrop_path = fix_new
            url = f'https://graphis.ne.jp/monthly/?K={actor_name}'
        else:
            pic_path = pic_old
            backdrop_path = big_old
            if 'graphis_backgrop' not in emby_on:
                backdrop_path = fix_old
            url = f'https://graphis.ne.jp/monthly/?S=1&K={actor_name}'
            # https://graphis.ne.jp/monthly/?S=1&K=夢乃あいか

        # 查看本地有没有缓存
        logs = ''
        has_pic = False
        has_backdrop = False
        if os.path.isfile(pic_path):
            has_pic = True
        if os.path.isfile(backdrop_path):
            has_backdrop = True
        if 'graphis_face' not in emby_on:
            pic_path = ''
            if has_backdrop:
                logs += '✅ graphis.ne.jp 本地背景！ '
                return '', backdrop_path, logs
        elif 'graphis_backdrop' not in emby_on:
            if has_pic:
                logs += '✅ graphis.ne.jp 本地头像！ '
                return pic_path, '', logs
        elif has_pic and has_backdrop:
            return pic_path, backdrop_path, ''

        # 请求图片
        result, res = get_html(url)
        if not result:
            logs += f'🔴 graphis.ne.jp 请求失败！\n{res}'
            return '', '', logs
        html = etree.fromstring(res, etree.HTMLParser())
        src = html.xpath("//div[@class='gp-model-box']/ul/li/a/img/@src")
        jp_name = html.xpath("//li[@class='name-jp']/span/text()")
        if actor_name not in jp_name:
            # logs += '🍊 graphis.ne.jp 无结果！'
            return '', '', logs
        small_pic = src[jp_name.index(actor_name)]
        big_pic = small_pic.replace('/prof.jpg', '/model.jpg')

        # 保存图片
        if not has_pic and pic_path:
            if self.download_file_with_filepath({'logs': ''}, small_pic, pic_path, actor_folder):
                logs += '🍊 使用 graphis.ne.jp 头像！ '
                if 'graphis_backdrop' not in emby_on:
                    if not has_backdrop:
                        self.fix_pic(pic_path, backdrop_path)
                    return pic_path, backdrop_path, logs
            else:
                logs += '🔴 graphis.ne.jp 头像获取失败！ '
                pic_path = ''
        if not has_backdrop and 'graphis_backdrop' in emby_on:
            if self.download_file_with_filepath({'logs': ''}, big_pic, backdrop_path, actor_folder):
                logs += '🍊 使用 graphis.ne.jp 背景！ '
                self.fix_pic(backdrop_path, backdrop_path)
            else:
                logs += '🔴 graphis.ne.jp 背景获取失败！ '
                backdrop_path = ''
        return pic_path, backdrop_path, logs

    # 生成背景图
    def fix_pic(self, pic_path, new_path):
        try:
            pic = Image.open(pic_path)
            (w, h) = pic.size
            prop = w / h
            if prop < 1.156:                                                    # 左右居中
                backdrop_w = int(1.156 * h)                                     # 背景宽度
                backdrop_h = int(h)                                             # 背景宽度
                foreground_x = int((backdrop_w - w) / 2)                        # 前景x点
                foreground_y = 0                                                # 前景y点
            else:                                                               # 下面对齐
                ax, ay, bx, by = int(w * 0.0155), int(h * 0.0888), int(w * 0.9833), int(h * 0.9955)
                pic_new = pic.convert('RGB')
                pic = pic_new.crop((ax, ay, bx, by))
                backdrop_w = bx - ax
                backdrop_h = int((bx - ax) / 1.156)
                foreground_x = 0
                foreground_y = int(backdrop_h - (by - ay))
            fixed_pic = pic.resize((backdrop_w, backdrop_h))                    # 背景拉伸
            fixed_pic = fixed_pic.filter(ImageFilter.GaussianBlur(radius=50))   # 背景高斯模糊
            fixed_pic.paste(pic, (foreground_x, foreground_y))                  # 粘贴原图
            fixed_pic = fixed_pic.convert('RGB')
            fixed_pic.save(new_path, quality=95, subsampling=0)
            pic.close()
        except:
            self.show_log_text(f"{traceback.format_exc()}\n Pic: {pic_path}")
            self.show_traceback_log(traceback.format_exc())

    # 裁剪头像为2:3
    def cut_pic(self, pic_path):
        # 打开图片, 获取图片尺寸
        try:
            img = Image.open(pic_path)                                          # 返回一个Image对象
        except:
            self.show_log_text(f"{traceback.format_exc()}\n Pic: {pic_path}")
            return

        w, h = img.size
        prop = h / w

        # 判断裁剪方式
        if prop < 1.4:                                                          # 胖，裁剪左右
            ax = int((w - h / 1.5) / 2)
            ay = 0
            bx = int(ax + h / 1.5)
            by = int(h)
        elif prop > 1.6:                                                        # 瘦，裁剪上下
            ax = 0
            ay = int((h - 1.5 * w) / 2)
            bx = int(w)
            by = int(h - ay)
        else:
            img.close()
            return

        # 裁剪并保存
        try:
            img_new = img.convert('RGB')
            img_new_png = img_new.crop((ax, ay, bx, by))
            img_new_png.save(pic_path, quality=95, subsampling=0)
            img.close()
        except Exception:
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())

    # 上传头像到 emby
    def upload_actor_photo(self, url, pic_path):
        try:
            with open(pic_path, 'rb') as f:
                b6_pic = base64.b64encode(f.read())                             # 读取文件内容, 转换为base64编码

            if pic_path.endswith('jpg'):
                header = {
                    "Content-Type": 'image/jpeg',
                }
            else:
                header = {
                    "Content-Type": 'image/png',
                }
            requests.post(url=url, data=b6_pic, headers=header)
            return True
        except:
            self.show_log_text(traceback.format_exc())
            return False

    # 补全 emby 演员信息
    def update_emby_actor_info(self):
        self.change_buttons_status()
        start_time = time.time()
        emby_on = self.config.get('emby_on')
        server_type = self.config.get('server_type')
        if 'emby' in server_type:
            server_name = 'Emby'
        else:
            server_name = 'Jellyfin'
        self.show_log_text(f"👩🏻 开始补全 {server_name} 演员信息...")

        actor_list = self.get_emby_actor_list()
        if actor_list:
            i = 0
            a = len(actor_list)
            for actor in actor_list:
                i += 1
                actor_name = actor.get('Name')
                server_id = actor.get('ServerId')
                actor_id = actor.get('Id')

                # 名字含有空格时跳过
                if re.search(r'[ .·・-]', actor_name):
                    self.show_log_text(f"🔍 {i}/{a} {actor_name}: 名字含有空格等分隔符，识别为非女优，跳过！")
                    continue

                # 已有资料时跳过
                # http://192.168.5.191:8096/emby/Persons/梦乃爱华?api_key=ee9a2f2419704257b1dd60b975f2d64e
                actor_homepage, actor_person, pic_url, backdrop_url, backdrop_url_0, update_url = self.get_server_url(actor)
                result, res = get_html(actor_person, proxies=False, json_data=True)
                if not result:
                    self.show_log_text(f"🔴 {i}/{a} {actor_name}: {server_name} 获取演员信息错误！\n    错误信息: {res}")
                    continue
                if res.get('Overview') and 'actor_info_miss' in emby_on:
                    self.show_log_text(f"✅ {i}/{a} {actor_name}: {server_name} 已有演员信息！跳过！")
                    continue

                # 请求 wiki 数据并补全
                self.show_log_text(f"🔍 {i}/{a} 开始请求： {actor_name}\n" + '=' * 80)
                actor_js = {
                    "Name": actor_name,
                    "ServerId": server_id,
                    "Id": actor_id,
                    "Genres": [],
                    "Tags": [],
                    "ProviderIds": {},
                    "Taglines_translate": False,
                }
                self.get_wiki_url(actor_name, actor_js, actor_homepage, update_url)
                self.show_log_text('=' * 80)
            self.show_log_text(f"\n\n🎉🎉🎉 补全完成！！！ 用时 {self.get_used_time(start_time)} 秒\n")

        if 'actor_info_photo' in emby_on:
            for i in range(5):
                self.show_log_text(f"{5 - i} 秒后开始补全演员头像头像...")
                time.sleep(1)
            self.show_log_text('\n')
            self.update_emby_actor_photo()
        else:
            self.reset_buttons_status()

    # 通过演员名字获取 wiki url
    def get_wiki_url(self, actor_name, actor_js, actor_homepage, update_url):

        # 优先用日文去查找，其次繁体。wiki的搜索很烂，因为跨语言的原因，经常找不到演员
        actor_data = self.get_actor_data(actor_name)
        actor_name_tw = ''
        if actor_data['has_name']:
            actor_name = actor_data['jp']
            actor_name_tw = actor_data['zh_tw']
            if actor_name_tw == actor_name:
                actor_name_tw = ''
        else:
            actor_name = zhconv.convert(actor_name, 'zh-hant')

        # 请求维基百科搜索页接口
        url = f'https://www.wikidata.org/w/api.php?action=wbsearchentities&search={actor_name}&language=zh&format=json'
        # https://www.wikidata.org/w/api.php?action=wbsearchentities&search=夢乃あいか&language=zh&format=json
        # https://www.wikidata.org/w/api.php?action=wbsearchentities&search=吉根柚莉愛&language=zh&format=json
        self.show_log_text(f" 🌐 请求搜索页: {url}")
        result, res = get_html(url, json_data=True)
        if not result:
            self.show_log_text(f" 🔴 维基百科搜索结果请求失败！\n    错误信息: {res}")
            return
        try:
            search_result = res.get('search')

            # 搜索无结果
            if not search_result:
                if not actor_name_tw:
                    self.show_log_text(" 🔴 维基百科暂未收录!")
                    return
                url = f'https://www.wikidata.org/w/api.php?action=wbsearchentities&search={actor_name_tw}&language=zh&format=json'
                self.show_log_text(f" 🌐 尝试再次搜索: {url}")
                result, res = get_html(url, json_data=True)
                if not result:
                    self.show_log_text(f" 🔴 维基百科搜索结果请求失败！\n    错误信息: {res}")
                    return
                search_result = res.get('search')
                # 搜索无结果
                if not search_result:
                    self.show_log_text(" 🔴 维基百科暂未收录!")
                    return

            # 判断描述信息
            des_list = ['AV idol', 'pornographic', 'pornoactrice', 'Japanese idol', 'Japanese actress', 'AV actress', 'porn star', 'gravure', 'director', 'voice actor', 'gravure idol', 'model', 'Porn actresses']
            for each_result in search_result:
                description = each_result.get('description')
                match_name = each_result.get('match')
                temp_name = actor_name
                if match_name:
                    temp_name = match_name.get('text')
                    self.show_log_text(f" 👩🏻 匹配名字: {temp_name}")
                if description:
                    description_en = description
                    self.show_log_text(f" 📄 描述信息: {description}")
                    for each_des in des_list:
                        if each_des.lower() in description.lower():
                            self.show_log_text(f" 🎉 描述命中关键词: {each_des}")
                            break
                    else:
                        self.show_log_text(" 🔴 描述未命中关键词，识别为非女优，跳过！")
                        continue
                    actor_js["Taglines"] = [f"{description}"]
                else:
                    self.show_log_text(" 💡 不存在描述信息，尝试请求页面内容进行匹配！")
                    description_en = ''

                # 通过id请求数据，获取 wiki url
                wiki_id = each_result.get('id')
                url = f'https://m.wikidata.org/wiki/Special:EntityData/{wiki_id}.json'
                # https://m.wikidata.org/wiki/Special:EntityData/Q24836820.json
                # https://m.wikidata.org/wiki/Special:EntityData/Q76283484.json
                self.show_log_text(f" 🌐 请求 ID 数据: {url}")
                result, res = get_html(url, json_data=True)
                if not result:
                    self.show_log_text(f" 🔴 通过 id 获取 wiki url 失败！\n    错误信息: {res}")
                    continue

                # 更新 descriptions
                description_zh = ''
                description_ja = ''
                try:
                    descriptions = res['entities'][wiki_id]['descriptions']
                    if descriptions:
                        try:
                            description_zh = descriptions['zh']['value']
                        except:
                            pass
                        try:
                            description_ja = descriptions['ja']['value']
                        except:
                            pass
                        if description_en:
                            if not description_zh:
                                en_zh = {
                                    'Japanese AV idol': '日本AV女优',
                                    'Japanese pornographic actress': '日本AV女优',
                                    'Japanese idol': '日本偶像',
                                    'Japanese pornographic film director': '日本AV影片导演',
                                    'Japanese film director': '日本电影导演',
                                    'pornographic actress': '日本AV女优',
                                    'Japanese actress': '日本AV女优',
                                    'gravure idol': '日本写真偶像',
                                }
                                temp_zh = en_zh.get(description_en)
                                if temp_zh:
                                    description_zh = temp_zh
                            if not description_ja:
                                en_ja = {
                                    'Japanese AV idol': '日本のAVアイドル',
                                    'Japanese pornographic actress': '日本のポルノ女優',
                                    'Japanese idol': '日本のアイドル',
                                    'Japanese pornographic film director': '日本のポルノ映画監督',
                                    'Japanese film director': '日本の映画監督',
                                    'pornographic actress': '日本のAVアイドル',
                                    'Japanese actress': '日本のAVアイドル',
                                    'gravure idol': '日本のグラビアアイドル',
                                }
                                temp_ja = en_ja.get(description_en)
                                if temp_ja:
                                    description_ja = temp_ja
                except:
                    pass

                # 获取 Tmdb，Imdb，Twitter，Instagram等id
                temp_urls = ''
                try:
                    claims = res['entities'][wiki_id]['claims']
                    if claims:
                        try:
                            tmdb_id = claims["P4985"][0]["mainsnak"]["datavalue"]["value"]
                            actor_js["ProviderIds"]['Tmdb'] = tmdb_id
                            temp_urls += f"TheMovieDb: https://www.themoviedb.org/person/{tmdb_id} \n"
                        except:
                            pass
                        try:
                            imdb_id = claims["P345"][0]["mainsnak"]["datavalue"]["value"]
                            actor_js["ProviderIds"]['Imdb'] = imdb_id
                            temp_urls += f"IMDb: https://www.imdb.com/name/{imdb_id} \n",
                        except:
                            pass
                        try:
                            twitter_id = claims["P2002"][0]["mainsnak"]["datavalue"]["value"]
                            actor_js["ProviderIds"]['Twitter'] = f'https://twitter.com/{twitter_id}'
                            temp_urls += f"Twitter: https://twitter.com/{twitter_id} \n"
                        except:
                            pass
                        try:
                            instagram_id = claims["P2003"][0]["mainsnak"]["datavalue"]["value"]
                            actor_js["ProviderIds"]['Instagram'] = f'https://www.instagram.com/{instagram_id}'
                            temp_urls += f'Instagram: https://www.instagram.com/{instagram_id} \n'
                        except:
                            pass
                        try:
                            fanza_id = claims["P9781"][0]["mainsnak"]["datavalue"]["value"]
                            actor_js["ProviderIds"]['Fanza'] = f'https://actress.dmm.co.jp/-/detail/=/actress_id={fanza_id}'
                            temp_urls += f'Fanza: https://actress.dmm.co.jp/-/detail/=/actress_id={fanza_id} \n'
                        except:
                            pass
                        try:
                            xhamster_id = claims["P8720"][0]["mainsnak"]["datavalue"]["value"]
                            actor_js["ProviderIds"]['xHamster'] = f'https://xhamster.com/pornstars/{xhamster_id}'
                            temp_urls += f'xHamster: https://xhamster.com/pornstars/{xhamster_id} \n'
                        except:
                            pass
                except:
                    pass

                # 获取 wiki url 和 description
                try:
                    sitelinks = res['entities'][wiki_id]['sitelinks']
                    if sitelinks:
                        jawiki = sitelinks.get('jawiki')
                        zhwiki = sitelinks.get('zhwiki')
                        ja_url = jawiki.get('url') if jawiki else ''
                        zh_url = zhwiki.get('url') if zhwiki else ''
                        url_final = ''
                        emby_on = self.config.get('emby_on')
                        if 'actor_info_zh_cn' in emby_on:
                            if zh_url:
                                url_final = zh_url.replace('zh.wikipedia.org/wiki/', 'zh.m.wikipedia.org/zh-cn/')
                            elif ja_url:
                                url_final = ja_url.replace('ja.', 'ja.m.')

                            if description_zh:
                                description_zh = zhconv.convert(description_zh, 'zh-cn')
                                actor_js["Taglines"] = [f"{description_zh}"]
                            else:
                                if description_ja:
                                    actor_js["Taglines"] = [f"{description_ja}"]
                                elif description_en:
                                    actor_js["Taglines"] = [f"{description_en}"]
                                if 'actor_info_translate' in emby_on and (description_ja or description_en):
                                    actor_js["Taglines_translate"] = True

                        elif 'actor_info_zh_tw' in emby_on:
                            if zh_url:
                                url_final = zh_url.replace('zh.wikipedia.org/wiki/', 'zh.m.wikipedia.org/zh-tw/')
                            elif ja_url:
                                url_final = ja_url.replace('ja.', 'ja.m.')

                            if description_zh:
                                description_zh = zhconv.convert(description_zh, 'zh-hant')
                                actor_js["Taglines"] = [f"{description_zh}"]
                            else:
                                if description_ja:
                                    actor_js["Taglines"] = [f"{description_ja}"]
                                elif description_en:
                                    actor_js["Taglines"] = [f"{description_en}"]

                                if 'actor_info_translate' in emby_on and (description_ja or description_en):
                                    actor_js["Taglines_translate"] = True

                        elif ja_url:
                            url_final = ja_url.replace('ja.', 'ja.m.')
                            if description_ja:
                                actor_js["Taglines"] = [f"{description_ja}"]
                            elif description_zh:
                                actor_js["Taglines"] = [f"{description_zh}"]
                            elif description_en:
                                actor_js["Taglines"] = [f"{description_en}"]

                        if url_final:
                            url_unquote = urllib.parse.unquote(url_final)
                            temp_urls += f'Wikipedia: {url_unquote}'
                            actor_js["temp_urls"] = temp_urls
                            self.show_log_text(f" 🌐 请求演员页: {url_final}")
                            self.get_wiki_info(url_final, actor_js, actor_homepage, update_url)
                        else:
                            self.show_log_text(" 🔴 维基百科未获取到演员页 url！")
                        return
                except:
                    pass

        except:
            self.show_log_text(traceback.format_exc())

    # 通过 wiki url 获取 演员信息
    def get_wiki_info(self, url, actor_js, actor_homepage, update_url):
        ja = True if 'ja.' in url else False
        emby_on = self.config.get('emby_on')
        result, res = get_html(url)
        if not result:
            self.show_log_text(f" 🔴 维基百科演员页请求失败！\n    错误信息: {res}\n    请求地址: {url}")
            return
        if 'noarticletext mw-content-ltr' in res:
            self.show_log_text(" 🔴 维基百科演员页没有该词条！")
            return
        av_key = ['女优', '女優', '男优', '男優', '（AV）导演', 'AV导演', 'AV監督', '成人电影', '成人影片', '映画監督', 'アダルトビデオ監督', '电影导演', '配音員', '配音员', '声優', '声优', 'グラビアアイドル', 'モデル']
        for key in av_key:
            if key in res:
                self.show_log_text(f" 🎉 页面内容命中关键词: {key}，识别为女优或写真偶像或导演！\n")
                break
        else:
            self.show_log_text(" 🔴 页面内容未命中关键词，识别为非女优或导演！")
            return
        res = re.sub(r'\[\d+\]', '', res)                                       # 替换[1],[2]等注释
        soup = bs4.BeautifulSoup(res, 'lxml')
        begin_intro = soup.find_all(role='note', class_='hatnote navigation-not-searchable')
        actor_output = soup.find(class_='mw-parser-output')

        # 开头简介
        actor_introduce_0 = actor_output.find(id="mf-section-0")
        begin_intro = actor_introduce_0.find_all(name='p')
        overview = ''
        for each in begin_intro:
            info = each.get_text('', strip=True)
            overview += info + '\n'

        # 个人资料
        actor_js["ProductionLocations"] = ["日本"]
        actor_profile = actor_output.find(name='table', class_=['infobox', 'infobox vcard plainlist'])
        if actor_profile:
            att_keys = actor_profile.find_all(scope=["row"])
            att_values = actor_profile.find_all(name='td', style=[''])
            bday = actor_output.find(class_='bday')
            bday = '(%s)' % bday.get_text('', strip=True) if bday else ''
            if att_keys and att_values:
                overview += '\n===== 个人资料 =====\n'
                i = 0
                for each in att_keys:
                    info_left = each.text.strip()
                    info_right = att_values[i].get_text('', strip=True).replace(bday, '')
                    info = info_left + ': ' + info_right
                    overview += info + '\n'
                    if '出生' in info_left or '生年' in info_left:
                        result = re.findall(r'(\d+)年(\d+)月(\d+)日', info_right)
                        if result:
                            result = result[0]
                            year = str(result[0]) if len(result[0]) == 4 else '19' + str(result[0]) if len(result[0]) == 2 else '1970'
                            month = str(result[1]) if len(result[1]) == 2 else '0' + str(result[1])
                            day = str(result[2]) if len(result[2]) == 2 else '0' + str(result[2])
                            brithday = f"{year}-{month}-{day}"
                            actor_js["PremiereDate"] = brithday
                            actor_js["ProductionYear"] = year
                    elif '出身地' in info_left or '出道地点' in info_left:
                        location = re.findall(r'[^ →]+', info_right)
                        if location:
                            location = location[0]
                            if location != '日本':
                                if ja and 'actor_info_translate' in emby_on and 'actor_info_ja' not in emby_on:
                                    location = location.replace('県', '县')
                                    if 'actor_info_zh_cn' in emby_on:
                                        location = zhconv.convert(location, 'zh-cn')
                                    elif 'actor_info_zh_tw' in emby_on:
                                        location = zhconv.convert(location, 'zh-hant')
                                location = '日本·' + location.replace('日本・', '').replace('日本·', '').replace('日本', '')
                            actor_js["ProductionLocations"] = [f"{location}"]
                    i += 1

        # 人物
        try:
            s = actor_introduce_0.find(class_='toctext', text=['人物']).find_previous_sibling().string
            if s:
                ff = actor_output.find(id=f'mf-section-{s}')
                if ff:
                    actor_1 = ff.find_all(name=['p', 'li'])
                    overview += '\n===== 人物介绍 =====\n'
                    for each in actor_1:
                        info = each.get_text('', strip=True)
                        overview += info + '\n'
        except:
            pass

        # 简历
        try:
            s = actor_introduce_0.find(class_='toctext', text=['简历', '簡歷', '个人简历', '個人簡歷', '略歴', '経歴', '来歴', '生平', '生平与职业生涯', '略歴・人物']).find_previous_sibling().string
            if s:
                ff = actor_output.find(id=f'mf-section-{s}')
                if ff:
                    overview += '\n===== 个人经历 =====\n'
                    actor_1 = ff.find_all(name=['p', 'li'])
                    for each in actor_1:
                        info = each.get_text('', strip=True)
                        overview += info + '\n'
        except:
            pass

        # 翻译
        try:
            overview_req = ''
            tag_req = ''
            tag_trans = actor_js["Taglines_translate"]
            if (ja or tag_trans) and 'actor_info_translate' in emby_on and 'actor_info_ja' not in emby_on:
                translate_by_list = self.translate_by_list.copy()
                random.shuffle(translate_by_list)
                if ja and overview:
                    overview_req = overview
                if tag_trans:
                    tag_req = actor_js["Taglines"][0]

                    # 为英文时要单独进行翻译
                    if tag_req and langid.classify(tag_req)[0] == 'en' and translate_by_list:
                        for each in translate_by_list:
                            self.show_log_text(f" 🐙 识别到演员描述信息为英文({tag_req})，请求 {each.capitalize()} 进行翻译...")
                            if each == 'youdao':                                                # 使用有道翻译
                                t, o, r = self.youdao_translate(tag_req, '')
                            elif each == 'google':                                              # 使用 google 翻译
                                t, o, r = self.google_translate(tag_req, '')
                            else:                                                               # 使用deepl翻译
                                t, o, r = self.deepl_translate(tag_req, '', ls='EN')
                            if r:
                                self.show_log_text(f' 🔴 Translation failed!({each.capitalize()}) Error: {r}')
                            else:
                                actor_js["Taglines"] = [t]
                                tag_req = ''
                                break
                        else:
                            self.show_log_text(f'\n 🔴 Translation failed! {each.capitalize()} 不可用！')

                if (overview_req or tag_req) and translate_by_list:
                    for each in translate_by_list:
                        self.show_log_text(f" 🐙 请求 {each.capitalize()} 翻译演员信息...")
                        if each == 'youdao':                                                # 使用有道翻译
                            t, o, r = self.youdao_translate(tag_req, overview_req)
                        elif each == 'google':                                              # 使用 google 翻译
                            t, o, r = self.google_translate(tag_req, overview_req)
                        else:                                                               # 使用deepl翻译
                            t, o, r = self.deepl_translate(tag_req, overview_req)
                        if r:
                            self.show_log_text(f' 🔴 Translation failed!({each.capitalize()}) Error: {r}')
                        else:
                            if tag_req:
                                actor_js["Taglines"] = [t]
                            if overview_req:
                                overview = o
                                overview = overview.replace('\n= = = = = = = = = =个人资料\n', '\n===== 个人资料 =====\n')
                                overview = overview.replace('\n=====人物介绍\n', '\n===== 人物介绍 =====\n')
                                overview = overview.replace('\n= = = = =个人鉴定= = = = =\n', '\n===== 个人经历 =====\n')
                                overview = overview.replace('\n=====个人日历=====\n', '\n===== 个人经历 =====\n')
                                overview = overview.replace('\n=====个人费用=====\n', '\n===== 个人资料 =====\n')
                                overview = overview.replace('\n===== 个人协助 =====\n', '\n===== 人物介绍 =====\n')
                                overview = overview.replace('\n===== 个人经济学 =====\n', '\n===== 个人经历 =====\n')
                                overview = overview.replace('\n===== 个人信息 =====\n', '\n===== 个人资料 =====\n')
                                overview = overview.replace('\n===== 简介 =====\n', '\n===== 人物介绍 =====\n')
                                overview = overview.replace(':', ': ') + '\n'
                                if '=====\n' not in overview:
                                    overview = overview.replace(' ===== 个人资料 ===== ', '\n===== 个人资料 =====\n')
                                    overview = overview.replace(' ===== 人物介绍 ===== ', '\n===== 人物介绍 =====\n')
                                    overview = overview.replace(' ===== 个人经历 ===== ', '\n===== 个人经历 =====\n')
                            break
                    else:
                        self.show_log_text(f'\n 🔴 Translation failed! {each.capitalize()} 不可用！')

            # 外部链接
            temp_urls = actor_js.get("temp_urls")
            overview += f'\n===== 外部链接 =====\n{temp_urls}'
            actor_js["Overview"] = overview.replace('\n', '<br>').replace('这篇报道有多个问题。请协助改善和在笔记页上的讨论。', '').strip()

            # 语言替换和转换
            taglines = actor_js.get("Taglines")
            if 'actor_info_zh_cn' in emby_on:
                if not taglines:
                    if 'AV監督' in res:
                        actor_js["Taglines"] = ['日本成人影片导演']
                    elif '女優' in res or '女优' in res:
                        actor_js["Taglines"] = ['日本AV女优']
            elif 'actor_info_zh_tw' in emby_on:
                if overview_req:
                    overview = zhconv.convert(overview, 'zh-hant')
                if tag_req:
                    actor_js["Taglines"] = [zhconv.convert(actor_js["Taglines"][0], 'zh-hant')]
                elif 'AV監督' in res:
                    actor_js["Taglines"] = ['日本成人影片導演']
                elif '女優' in res or '女优' in res:
                    actor_js["Taglines"] = ['日本AV女優']

            elif 'actor_info_ja' in emby_on:
                overview = overview.replace('== 个人资料 ==', '== 個人情報 ==')
                overview = overview.replace('== 人物介绍 ==', '== 人物紹介 ==')
                overview = overview.replace('== 个人经历 ==', '== 個人略歴 ==')
                overview = overview.replace('== 外部链接 ==', '== 外部リンク ==')
                if not taglines:
                    if 'AV監督' in res:
                        actor_js["Taglines"] = ['日本のAV監督']
                    elif '女優' in res or '女优' in res:
                        actor_js["Taglines"] = ['日本のAV女優']

            # 显示信息
            actor_name = actor_js['Name']
            taglines = actor_js.get("Taglines")
            date = actor_js.get("PremiereDate")
            locations = actor_js.get("ProductionLocations")
            self.show_log_text(f"👩🏻 {actor_name}")
            if taglines:
                self.show_log_text(f"{taglines[0]}")
            if date and locations:
                self.show_log_text(f"出生: {date} 在 {locations[0]}")
            if overview:
                self.show_log_text(f"\n{overview}")

            # 更新 emby 演员信息
            actor_js.pop("temp_urls")
            actor_js.pop("Taglines_translate")
            result, res = post_html(update_url, json=actor_js, proxies=False)
            if result:
                self.show_log_text(f"\n ✅ 演员主页信息更新成功！\n 👩🏻 点击查看 {actor_name} 的 Emby 演员主页:")
                self.show_log_text(f" {actor_homepage}")
            else:
                self.show_log_text(f"\n 🔴 演员主页信息更新失败！\n    错误信息: {res}")
        except:
            self.show_log_text(traceback.format_exc())

    # ======================================================================================转换日志为html语句

    def add_html(self, text):
        # 特殊字符转义
        text = text.replace('=http', '🔮🧿⚔️')                                    # 例外不转换的

        # 替换链接为超链接
        url_list = re.findall(r'http[s]?://\S+', text)
        if url_list:
            url_list = list(set(url_list))
            url_list.sort(key=lambda i: len(i), reverse=True)
            for each_url in url_list:
                new_url = f'<a href="{each_url}">{each_url}</a>'
                text = text.replace(each_url, new_url)
        text = text.replace('🔮🧿⚔️', '=http')                                    # 还原不转换的

        # 链接放在span里，避免点击后普通文本变超链接，设置样式为pre-wrap（保留空格换行）
        return '<span style="white-space: pre-wrap;">%s</span>' % text

    # ======================================================================================日志页面显示详情日志内容

    def show_detail_log(self):
        text = cf.get_log()
        if text:
            self.main_req_logs_show.emit(self.add_html(text))
            if self.req_logs_counts < 10000:
                self.req_logs_counts += 1
            else:
                self.req_logs_counts = 0
                self.req_logs_clear.emit('')
                self.main_req_logs_show.emit(self.add_html(' 🗑️ 日志过多，已清屏！'))

    def show_traceback_log(self, text):
        print(text)
        cf.add_log((text))

    def test_html(self):
        a = '''有码\t<font color=\"#18385B\">▇▇▇▇▇▇▇▇▇</font> 90.22% （1230）<br>
无码\t<font color=\"#99CD5D\">▇</font> 8.22% （123）
            '''
        a = ' ⏸ 已连续刮削 4 个文件，将 1 分钟，在 <font color=\"red\">20:21:30</font> 继续刮削...\n'
        print_js({})
        self.main_logs_show.emit(a)
        self.show_log_text(a)

    # ======================================================================================日志页面显示内容

    def show_log_text(self, text):
        if not text:
            return
        text = str(text)
        if self.Ui.radioButton_log_on.isChecked():                              # 保存日志
            try:
                self.log_txt.write((text + '\n').encode('utf-8'))
            except:
                log_folder = os.path.join(self.main_path, 'Log')
                if not os.path.exists(log_folder):
                    os.makedirs(log_folder)
                log_name = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + '.txt'
                log_name = self.convert_path(os.path.join(log_folder, log_name))

                self.log_txt = open(log_name, "wb", buffering=0)
                self.show_log_text('Create log file: ' + log_name + '\n')
                self.show_log_text(text)
                return
        try:
            self.main_logs_show.emit(self.add_html(text))
            if self.logs_counts < 10000:
                self.logs_counts += 1
            else:
                self.logs_counts = 0
                self.main_logs_clear.emit('')
                self.main_logs_show.emit(self.add_html(' 🗑️ 日志过多，已清屏！'))
            # self.show_traceback_log(self.Ui.textBrowser_log_main.document().lineCount())

        except:
            self.show_traceback_log(traceback.format_exc())
            self.Ui.textBrowser_log_main.append(traceback.format_exc())

    # ======================================================================================检测网络界面日志显示

    def show_net_info(self, text):
        try:
            self.net_logs_show.emit(self.add_html(text))
        except:
            self.show_traceback_log(traceback.format_exc())
            self.Ui.textBrowser_net_main.append(traceback.format_exc())

    # ======================================================================================失败记录列表显示内容

    def failed_file_info_show(self, count, path, error_info):
        folder = os.path.dirname(path)
        info_str = "{:<3} {} \n    所在目录: {} \n    失败原因: {} \n".format('🔴 ' + count + '.', path, folder, error_info)
        if os.path.islink(path):
            real_path = read_link(path)
            real_folder = os.path.dirname(path)
            info_str = "{:<3} {} \n    指向文件: {} \n    所在目录: {} \n    失败原因: {} \n".format(count + '.', path, real_path, real_folder, error_info)
        self.logs_failed_show.emit(info_str)

    # ======================================================================================移动到失败文件夹

    def move_file_to_failed_folder(self, json_data, file_path, folder_old_path, file_ex):
        failed_folder = json_data['failed_folder']

        # 更新模式、读取模式，不移动失败文件；不移动文件-关时，不移动； 软硬链接开时，不移动
        main_mode = self.config.get('main_mode')
        if main_mode == 3 or main_mode == 4 or self.config.get('failed_file_move') == 0 or self.config.get('soft_link') != 0:
            json_data['logs'] += "\n 🙊 [Movie] %s" % file_path
            return file_path

        # 文件路径已经在失败路径内时不移动
        failed_folder_temp = failed_folder.replace('\\', '/') + '/'
        file_path_temp = file_path.replace('\\', '/')

        if failed_folder_temp in file_path_temp:
            json_data['logs'] += "\n 🙊 [Movie] %s" % file_path
            return file_path

        # 创建failed文件夹
        if not os.path.exists(failed_folder):
            self.creat_failed_folder(failed_folder)

        # 获取文件路径
        file_full_name = split_path(file_path)[1]
        file_name, file_ext = os.path.splitext(file_full_name)
        trailer_old_path_no_filename = self.convert_path(os.path.join(folder_old_path, 'trailers/trailer.mp4'))
        trailer_old_path_with_filename = file_path.replace(file_ext, '-trailer.mp4')

        # 重复改名
        file_new_path = self.convert_path(os.path.join(failed_folder, file_full_name))
        while os.path.exists(file_new_path) and file_new_path != self.convert_path(file_path):
            file_new_path = file_new_path.replace(file_ext, '@' + file_ext)

        # 移动
        try:
            move_file(file_path, file_new_path)
            json_data['logs'] += "\n 🔴 Move file to the failed folder!"
            json_data['logs'] += "\n 🙊 [Movie] %s" % file_new_path
            json_data['file_path'] = file_new_path
            json_data['error_info'] = json_data['error_info'].replace(file_path, file_new_path)

            # 同步移动预告片
            trailer_new_path = file_new_path.replace(file_ext, '-trailer.mp4')
            if not os.path.exists(trailer_new_path):
                try:
                    has_trailer = False
                    if os.path.exists(trailer_old_path_with_filename):
                        has_trailer = True
                        move_file(trailer_old_path_with_filename, trailer_new_path)
                    elif os.path.exists(trailer_old_path_no_filename):
                        has_trailer = True
                        move_file(trailer_old_path_no_filename, trailer_new_path)
                    if has_trailer:
                        json_data['logs'] += "\n 🔴 Move trailer to the failed folder!"
                        json_data['logs'] += "\n 🔴 [Trailer] %s" % trailer_new_path
                except Exception as e:
                    json_data['logs'] += "\n 🔴 Failed to move trailer to the failed folder! \n    " + str(e)

            # 同步移动字幕
            sub_type_list = self.config.get('sub_type').split('|')
            sub_type_new_list = []
            [sub_type_new_list.append('.chs' + i) for i in sub_type_list if '.chs' not in i]
            for sub in sub_type_new_list:
                sub_old_path = file_path.replace(os.path.splitext(file_path)[1], sub)
                sub_new_path = file_new_path.replace(os.path.splitext(file_new_path)[1], sub)
                if os.path.exists(sub_old_path) and not os.path.exists(sub_new_path):
                    result, error_info = move_file(sub_old_path, sub_new_path)
                    if not result:
                        json_data['logs'] += f"\n 🔴 Failed to move sub to the failed folder!\n     {error_info}"
                    else:
                        json_data['logs'] += "\n 💡 Move sub to the failed folder!"
                        json_data['logs'] += "\n 💡 [Sub] %s" % sub_new_path
            return file_new_path
        except Exception as e:
            json_data['logs'] += "\n 🔴 Failed to move the file to the failed folder! \n    " + str(e)

    # ======================================================================================下载文件

    def download_file_with_filepath(self, json_data, url, file_path, folder_new_path):
        if not url:
            return False

        if not os.path.exists(folder_new_path):
            os.makedirs(folder_new_path)
        try:
            if multi_download(url, file_path):
                return True
        except:
            pass
        json_data['logs'] += f"\n 🥺 Download failed! {url}"
        return False

    # ======================================================================================下载缩略图

    def thumb_download(self, json_data, folder_new_path, thumb_final_path):
        start_time = time.time()
        download_files = self.config.get('download_files')
        keep_files = self.config.get('keep_files')
        poster_path = json_data['poster_path']
        thumb_path = json_data['thumb_path']
        fanart_path = json_data['fanart_path']

        # 本地存在 thumb.jpg，且勾选保留旧文件时，不下载
        if thumb_path and 'thumb' in keep_files:
            json_data['logs'] += "\n 🍀 Thumb done! (old)(%ss) " % self.get_used_time(start_time)
            return True

        # 如果thumb不下载，看fanart、poster要不要下载，都不下载则返回
        if 'thumb' not in download_files:
            if 'poster' in download_files and ('poster' not in keep_files or not poster_path):
                pass
            elif 'fanart' in download_files and ('fanart' not in keep_files or not fanart_path):
                pass
            else:
                return True

        # 尝试复制其他分集。看分集有没有下载，如果下载完成则可以复制，否则就自行下载
        if json_data['cd_part']:
            done_thumb_path = self.file_done_dic.get(json_data['number']).get('thumb')
            if done_thumb_path and os.path.exists(done_thumb_path) and split_path(done_thumb_path)[0] == split_path(thumb_final_path)[0]:
                copy_file(done_thumb_path, thumb_final_path)
                json_data['logs'] += "\n 🍀 Thumb done! (copy cd-thumb)(%ss) " % self.get_used_time(start_time)
                json_data['cover_from'] = 'copy cd-thumb'
                json_data['thumb_path'] = thumb_final_path
                return True

        # 获取高清背景图
        json_data = self.get_big_thumb(json_data)

        # 下载图片
        cover_url = json_data.get('cover')
        cover_from = json_data.get('cover_from')
        if cover_url:
            cover_list = json_data['cover_list']
            while [cover_from, cover_url] in cover_list:
                cover_list.remove([cover_from, cover_url])
            cover_list.insert(0, [cover_from, cover_url])

            thumb_final_path_temp = thumb_final_path
            if os.path.exists(thumb_final_path):
                thumb_final_path_temp = thumb_final_path + '.[DOWNLOAD].jpg'
            for each in cover_list:
                if not each[1]:
                    continue
                cover_from, cover_url = each
                cover_url = check_url(cover_url)
                if not cover_url:
                    json_data['logs'] += "\n 🟠 检测到 Thumb 图片失效! 跳过！(%s)(%ss) " % (cover_from, self.get_used_time(start_time)) + each[1]
                    continue
                json_data['cover_from'] = cover_from
                if self.download_file_with_filepath(json_data, cover_url, thumb_final_path_temp, folder_new_path):
                    cover_size = check_pic(thumb_final_path_temp)
                    if cover_size:
                        if not cover_from.startswith('Google') or cover_size == json_data['cover_size'] or (cover_size[0] >= 800 and abs(cover_size[0] / cover_size[1] - json_data['cover_size'][0] / json_data['cover_size'][1]) <= 0.1):
                            # 图片下载正常，替换旧的 thumb.jpg
                            if thumb_final_path_temp != thumb_final_path:
                                move_file(thumb_final_path_temp, thumb_final_path)
                                delete_file(thumb_final_path_temp)
                            if json_data['cd_part']:
                                dic = {'thumb': thumb_final_path}
                                self.file_done_dic[json_data['number']].update(dic)
                            json_data['thumb_marked'] = False   # 表示还没有走加水印流程
                            json_data['logs'] += "\n 🍀 Thumb done! (%s)(%ss) " % (json_data['cover_from'], self.get_used_time(start_time))
                            json_data['thumb_path'] = thumb_final_path
                            return True
                        else:
                            delete_file(thumb_final_path_temp)
                            json_data['logs'] += "\n 🟠 检测到 Thumb 分辨率不对%s! 已删除 (%s)(%ss)" % (str(cover_size), cover_from, self.get_used_time(start_time))
                            continue
                    json_data['logs'] += f"\n 🟠 Thumb download failed! {cover_from}: {cover_url} "
        else:
            json_data['logs'] += "\n 🟠 Thumb url is empty! "

        # 下载失败，本地有图
        if thumb_path:
            json_data['logs'] += "\n 🟠 Thumb download failed! 将继续使用之前的图片！"
            json_data['logs'] += "\n 🍀 Thumb done! (old)(%ss) " % self.get_used_time(start_time)
            return True
        else:
            if 'ignore_pic_fail' in download_files:
                json_data['logs'] += "\n 🟠 Thumb download failed! (你已勾选「图片下载失败时，不视为失败！」) "
                json_data['logs'] += "\n 🍀 Thumb done! (none)(%ss)" % self.get_used_time(start_time)
                return True
            else:
                json_data['logs'] += "\n 🔴 Thumb download failed! 你可以到「设置」-「下载」，勾选「图片下载失败时，不视为失败！」 "
                json_data['error_info'] = 'Thumb download failed! 你可以到「设置」-「下载」，勾选「图片下载失败时，不视为失败！」'
                return False

    # ======================================================================================下载poster

    def poster_download(self, json_data, folder_new_path, poster_final_path):
        start_time = time.time()
        download_files = self.config.get('download_files')
        keep_files = self.config.get('keep_files')
        poster_path = json_data['poster_path']
        thumb_path = json_data['thumb_path']
        fanart_path = json_data['fanart_path']
        image_cut = ''

        # 不下载poster、不保留poster时，返回
        if 'poster' not in download_files and 'poster' not in keep_files:
            if poster_path:
                delete_file(poster_path)
            return True

        # 本地有poster时，且勾选保留旧文件时，不下载
        if poster_path and 'poster' in keep_files:
            json_data['logs'] += "\n 🍀 Poster done! (old)(%ss)" % self.get_used_time(start_time)
            return True

        # 不下载时返回
        if 'poster' not in download_files:
            return True

        # 尝试复制其他分集。看分集有没有下载，如果下载完成则可以复制，否则就自行下载
        if json_data['cd_part']:
            done_poster_path = self.file_done_dic.get(json_data['number']).get('poster')
            if done_poster_path and os.path.exists(done_poster_path) and split_path(done_poster_path)[0] == split_path(poster_final_path)[0]:
                copy_file(done_poster_path, poster_final_path)
                json_data['poster_from'] = 'copy cd-poster'
                json_data['poster_path'] = poster_final_path
                json_data['logs'] += "\n 🍀 Poster done! (copy cd-poster)(%ss)" % self.get_used_time(start_time)
                return True

        # 勾选复制 thumb时：国产，复制thumb；无码，勾选不裁剪时，也复制thumb
        if thumb_path:
            mosaic = json_data['mosaic']
            number = json_data['number']
            copy_flag = False
            if number.startswith('FC2'):
                image_cut = 'center'
                if 'ignore_fc2' in download_files:
                    copy_flag = True
            elif mosaic == '国产' or mosaic == '國產':
                image_cut = 'right'
                if 'ignore_guochan' in download_files:
                    copy_flag = True
            elif mosaic == '无码' or mosaic == '無碼' or mosaic == '無修正':
                image_cut = 'center'
                if 'ignore_wuma' in download_files:
                    copy_flag = True
            elif mosaic == '有码' or mosaic == '有碼':
                if 'ignore_youma' in download_files:
                    copy_flag = True
            if copy_flag:
                copy_file(thumb_path, poster_final_path)
                json_data['poster_marked'] = json_data['thumb_marked']
                json_data['poster_from'] = 'copy thumb'
                json_data['poster_path'] = poster_final_path
                json_data['logs'] += "\n 🍀 Poster done! (copy thumb)(%ss)" % self.get_used_time(start_time)
                return True

        # 获取高清 poster
        json_data = self.get_big_poster(json_data)

        # 下载图片
        poster_url = json_data.get('poster')
        poster_from = json_data.get('poster_from')
        poster_final_path_temp = poster_final_path
        if os.path.exists(poster_final_path):
            poster_final_path_temp = poster_final_path + '.[DOWNLOAD].jpg'
        if json_data['image_download']:
            start_time = time.time()
            if self.download_file_with_filepath(json_data, poster_url, poster_final_path_temp, folder_new_path):
                poster_size = check_pic(poster_final_path_temp)
                if poster_size:
                    if not poster_from.startswith('Google') or poster_size == json_data['poster_size'] or 'media-amazon.com' in poster_url:
                        if poster_final_path_temp != poster_final_path:
                            move_file(poster_final_path_temp, poster_final_path)
                            delete_file(poster_final_path_temp)
                        if json_data['cd_part']:
                            dic = {'poster': poster_final_path}
                            self.file_done_dic[json_data['number']].update(dic)
                        json_data['poster_marked'] = False  # 下载的图，还没加水印
                        json_data['poster_path'] = poster_final_path
                        json_data['logs'] += "\n 🍀 Poster done! (%s)(%ss)" % (poster_from, self.get_used_time(start_time))
                        return True
                    else:
                        delete_file(poster_final_path_temp)
                        json_data['logs'] += "\n 🟠 检测到 Poster 分辨率不对%s! 已删除 (%s)" % (str(poster_size), poster_from)

        # 判断之前有没有 poster 和 thumb
        if not poster_path and not thumb_path:
            json_data['poster_path'] = ''
            if 'ignore_pic_fail' in download_files:
                json_data['logs'] += "\n 🟠 Poster download failed! (你已勾选「图片下载失败时，不视为失败！」) "
                json_data['logs'] += "\n 🍀 Poster done! (none)(%ss)" % self.get_used_time(start_time)
                return True
            else:
                json_data['logs'] += "\n 🔴 Poster download failed! 你可以到「设置」-「下载」，勾选「图片下载失败时，不视为失败！」 "
                json_data['error_info'] = 'Poster download failed! 你可以到「设置」-「下载」，勾选「图片下载失败时，不视为失败！」'
                return False

        # 使用thumb裁剪
        poster_final_path_temp = poster_final_path + '.[CUT].jpg'
        if fanart_path:
            thumb_path = fanart_path
        if self.cut_thumb_to_poster(json_data, thumb_path, poster_final_path_temp, image_cut):
            # 裁剪成功，替换旧图
            move_file(poster_final_path_temp, poster_final_path)
            if json_data['cd_part']:
                dic = {'poster': poster_final_path}
                self.file_done_dic[json_data['number']].update(dic)
            json_data['poster_path'] = poster_final_path
            json_data['poster_marked'] = False
            return True

        # 裁剪失败，本地有图
        if poster_path:
            json_data['logs'] += "\n 🟠 Poster cut failed! 将继续使用之前的图片！"
            json_data['logs'] += "\n 🍀 Poster done! (old)(%ss) " % self.get_used_time(start_time)
            return True
        else:
            if 'ignore_pic_fail' in download_files:
                json_data['logs'] += "\n 🟠 Poster cut failed! (你已勾选「图片下载失败时，不视为失败！」) "
                json_data['logs'] += "\n 🍀 Poster done! (none)(%ss)" % self.get_used_time(start_time)
                return True
            else:
                json_data['logs'] += "\n 🔴 Poster cut failed! 你可以到「设置」-「下载」，勾选「图片下载失败时，不视为失败！」 "
                json_data['error_info'] = 'Poster failed！你可以到「设置」-「下载」，勾选「图片下载失败时，不视为失败！」'
                return False

    # ======================================================================================复制thumb为fanart

    def fanart_download(self, json_data, fanart_final_path):
        start_time = time.time()
        thumb_path = json_data['thumb_path']
        fanart_path = json_data['fanart_path']
        download_files = self.config.get('download_files')
        keep_files = self.config.get('keep_files')

        # 不保留不下载时删除返回
        if ',fanart' not in keep_files and ',fanart' not in download_files:
            if fanart_path and os.path.exists(fanart_path):
                delete_file(fanart_path)
            return True

        # 保留，并且本地存在 fanart.jpg，不下载返回
        if ',fanart' in keep_files and fanart_path:
            json_data['logs'] += "\n 🍀 Fanart done! (old)(%ss)" % self.get_used_time(start_time)
            return True

        # 不下载时，返回
        if ',fanart' not in download_files:
            return True

        # 尝试复制其他分集。看分集有没有下载，如果下载完成则可以复制，否则就自行下载
        if json_data['cd_part']:
            done_fanart_path = self.file_done_dic.get(json_data['number']).get('fanart')
            if done_fanart_path and os.path.exists(done_fanart_path) and split_path(done_fanart_path)[0] == split_path(fanart_final_path)[0]:
                if fanart_path:
                    delete_file(fanart_path)
                copy_file(done_fanart_path, fanart_final_path)
                json_data['fanart_from'] = 'copy cd-fanart'
                json_data['fanart_path'] = fanart_final_path
                json_data['logs'] += "\n 🍀 Fanart done! (copy cd-fanart)(%ss)" % self.get_used_time(start_time)
                return True

        # 复制thumb
        if thumb_path:
            if fanart_path:
                delete_file(fanart_path)
            copy_file(thumb_path, fanart_final_path)
            json_data['fanart_from'] = 'copy thumb'
            json_data['fanart_path'] = fanart_final_path
            json_data['fanart_marked'] = json_data['thumb_marked']
            json_data['logs'] += "\n 🍀 Fanart done! (copy thumb)(%ss)" % self.get_used_time(start_time)
            if json_data['cd_part']:
                dic = {'fanart': fanart_final_path}
                self.file_done_dic[json_data['number']].update(dic)
            return True
        else:
            # 本地有 fanart 时，不下载
            if fanart_path:
                json_data['logs'] += "\n 🟠 Fanart copy failed! 未找到 thumb 图片，将继续使用之前的图片！"
                json_data['logs'] += "\n 🍀 Fanart done! (old)(%ss)" % self.get_used_time(start_time)
                return True

            else:
                if 'ignore_pic_fail' in download_files:
                    json_data['logs'] += "\n 🟠 Fanart failed! (你已勾选「图片下载失败时，不视为失败！」) "
                    json_data['logs'] += "\n 🍀 Fanart done! (none)(%ss)" % self.get_used_time(start_time)
                    return True
                else:
                    json_data['logs'] += "\n 🔴 Fanart failed! 你可以到「设置」-「下载」，勾选「图片下载失败时，不视为失败！」 "
                    json_data['error_info'] = 'Fanart 下载失败！你可以到「设置」-「下载」，勾选「图片下载失败时，不视为失败！」'
                    return False

    # ======================================================================================下载剧照

    def extrafanart_download(self, json_data, folder_new_path):
        start_time = time.time()
        download_files = self.config.get('download_files')
        keep_files = self.config.get('keep_files')
        extrafanart_list = json_data.get('extrafanart')
        extrafanart_folder_path = os.path.join(folder_new_path, 'extrafanart')

        # 不下载不保留时删除返回
        if 'extrafanart' not in download_files and 'extrafanart' not in keep_files:
            if os.path.exists(extrafanart_folder_path):
                shutil.rmtree(extrafanart_folder_path, ignore_errors=True)
            return

        # 本地存在 extrafanart_folder，且勾选保留旧文件时，不下载
        if 'extrafanart' in keep_files and os.path.exists(extrafanart_folder_path):
            json_data['logs'] += "\n 🍀 Extrafanart done! (old)(%ss) " % self.get_used_time(start_time)
            return True

        # 如果 extrafanart 不下载
        if 'extrafanart' not in download_files:
            return True

        # 检测链接有效性
        if extrafanart_list and check_url(extrafanart_list[0]):
            extrafanart_folder_path_temp = extrafanart_folder_path
            if os.path.exists(extrafanart_folder_path_temp):
                extrafanart_folder_path_temp = extrafanart_folder_path + '[DOWNLOAD]'
                if not os.path.exists(extrafanart_folder_path_temp):
                    os.makedirs(extrafanart_folder_path_temp)
            else:
                os.makedirs(extrafanart_folder_path_temp)

            extrafanart_count = 0
            extrafanart_count_succ = 0
            task_list = []
            for extrafanart_url in extrafanart_list:
                extrafanart_count += 1
                extrafanart_name = 'fanart' + str(extrafanart_count) + '.jpg'
                extrafanart_file_path = os.path.join(extrafanart_folder_path_temp, extrafanart_name)
                task_list.append([json_data, extrafanart_url, extrafanart_file_path, extrafanart_folder_path_temp, extrafanart_name])

            result = self.extrafanart_pool.map(self.mutil_extrafanart_download_thread, task_list)
            for res in result:
                if res:
                    extrafanart_count_succ += 1
            if extrafanart_count_succ == extrafanart_count:
                if extrafanart_folder_path_temp != extrafanart_folder_path:
                    shutil.rmtree(extrafanart_folder_path)
                    os.rename(extrafanart_folder_path_temp, extrafanart_folder_path)
                json_data['logs'] += "\n 🍀 ExtraFanart done! (%s %s/%s)(%ss)" % (json_data['extrafanart_from'], extrafanart_count_succ, extrafanart_count, self.get_used_time(start_time))
                return True
            else:
                json_data['logs'] += "\n 🟠  ExtraFanart download failed! (%s %s/%s)(%ss)" % (json_data['extrafanart_from'], extrafanart_count_succ, extrafanart_count, self.get_used_time(start_time))
                if extrafanart_folder_path_temp != extrafanart_folder_path:
                    shutil.rmtree(extrafanart_folder_path_temp)
                else:
                    json_data['logs'] += "\n 🍀 ExtraFanart done! (incomplete)(%ss)" % self.get_used_time(start_time)
                    return False
            json_data['logs'] += "\n 🟠 ExtraFanart download failed! 将继续使用之前的本地文件！"
        if os.path.exists(extrafanart_folder_path): # 使用旧文件
            json_data['logs'] += "\n 🍀 ExtraFanart done! (old)(%ss)" % self.get_used_time(start_time)
            return True

    def mutil_extrafanart_download_thread(self, task):
        json_data, extrafanart_url, extrafanart_file_path, extrafanart_folder_path, extrafanart_name = task
        if self.download_file_with_filepath(json_data, extrafanart_url, extrafanart_file_path, extrafanart_folder_path):
            if check_pic(extrafanart_file_path):
                return True
        else:
            json_data['logs'] += "\n 💡 %s download failed! ( %s )" % (extrafanart_name, extrafanart_url)
            return False

    # ======================================================================================拷贝剧照为附加内容

    def extrafanart_extras_copy(self, json_data, folder_new_path):
        start_time = time.time()
        download_files = self.config.get('download_files')
        keep_files = self.config.get('keep_files')
        extrafanart_path = self.convert_path(os.path.join(folder_new_path, 'extrafanart'))
        extrafanart_extra_path = self.convert_path(os.path.join(folder_new_path, 'behind the scenes'))

        if 'extrafanart_extras' not in download_files and 'extrafanart_extras' not in keep_files:
            if os.path.exists(extrafanart_extra_path):
                shutil.rmtree(extrafanart_extra_path, ignore_errors=True)
            return True

        if 'extrafanart_extras' in keep_files and os.path.exists(extrafanart_extra_path):
            json_data['logs'] += "\n 🍀 Extrafanart_extras done! (old)(%ss)" % self.get_used_time(start_time)
            return True

        if 'extrafanart_extras' not in download_files:
            return True

        if not os.path.exists(extrafanart_path):
            return False

        if os.path.exists(extrafanart_extra_path):
            shutil.rmtree(extrafanart_extra_path)
        shutil.copytree(extrafanart_path, extrafanart_extra_path)
        filelist = os.listdir(extrafanart_extra_path)
        for each in filelist:
            file_new_name = each.replace('jpg', 'mp4')
            file_path = os.path.join(extrafanart_extra_path, each)
            file_new_path = os.path.join(extrafanart_extra_path, file_new_name)
            move_file(file_path, file_new_path)
        json_data['logs'] += "\n 🍀 Extrafanart_extras done! (copy extrafanart)(%ss)" % self.get_used_time(start_time)
        return True

    # =====================================================================================为所有视频中的创建/删除剧照附加内容

    def pushButton_add_all_extras_clicked(self):
        self.pushButton_show_log_clicked()                                      # 点按钮后跳转到日志页面
        try:
            t = threading.Thread(target=self.add_del_extras_clicked, args=('add', ))
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_log_text(traceback.format_exc())

    def pushButton_del_all_extras_clicked(self):
        self.pushButton_show_log_clicked()                                      # 点按钮后跳转到日志页面
        try:
            t = threading.Thread(target=self.add_del_extras_clicked, args=('del', ))
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_log_text(traceback.format_exc())

    def add_del_extras_clicked(self, mode):
        self.show_log_text('Start %s extrafanart extras! \n' % mode)

        movie_path, success_folder, failed_folder, escape_folder_list, extrafanart_folder, softlink_path = self.get_movie_path_setting()
        self.show_log_text(' 🖥 Movie path: %s \n 🔎 Checking all videos, Please wait...' % movie_path)
        movie_type = self.config.get('media_type')
        movie_list = self.movie_lists('', movie_type, movie_path)               # 获取所有需要刮削的影片列表

        extrafanart_folder_path_list = []
        for movie in movie_list:
            movie_file_folder_path = split_path(movie)[0]
            extrafanart_folder_path = os.path.join(movie_file_folder_path, 'extrafanart')
            if os.path.exists(extrafanart_folder_path):
                extrafanart_folder_path_list.append(movie_file_folder_path)
        extrafanart_folder_path_list = list(set(extrafanart_folder_path_list))
        extrafanart_folder_path_list.sort()
        total_count = len(extrafanart_folder_path_list)
        new_count = 0
        count = 0
        for each in extrafanart_folder_path_list:
            extrafanart_folder_path = os.path.join(each, 'extrafanart')
            extrafanart_copy_folder_path = os.path.join(each, 'behind the scenes')
            count += 1
            if mode == 'add':
                if not os.path.exists(extrafanart_copy_folder_path):
                    shutil.copytree(extrafanart_folder_path, extrafanart_copy_folder_path)
                    filelist = os.listdir(extrafanart_copy_folder_path)
                    for each in filelist:
                        file_new_name = each.replace('jpg', 'mp4')
                        file_path = os.path.join(extrafanart_copy_folder_path, each)
                        file_new_path = os.path.join(extrafanart_copy_folder_path, file_new_name)
                        move_file(file_path, file_new_path)
                    self.show_log_text(" %s new extras: \n  %s" % (count, extrafanart_copy_folder_path))
                    new_count += 1
                else:
                    self.show_log_text(" %s old extras: \n  %s" % (count, extrafanart_copy_folder_path))
            else:
                if os.path.exists(extrafanart_copy_folder_path):
                    shutil.rmtree(extrafanart_copy_folder_path, ignore_errors=True)
                    self.show_log_text(" %s del extras: \n  %s" % (count, extrafanart_copy_folder_path))
                    new_count += 1

        self.show_log_text('\nDone! \n Total: %s  %s copy: %s ' % (total_count, mode, new_count))
        self.show_log_text("================================================================================")

    # ======================================================================================拷贝剧照副本

    def extrafanart_copy2(self, json_data, folder_new_path):
        start_time = time.time()
        download_files = self.config.get('download_files')
        keep_files = self.config.get('keep_files')
        extrafanart_copy_folder = self.config.get('extrafanart_folder')
        extrafanart_path = self.convert_path(os.path.join(folder_new_path, 'extrafanart'))
        extrafanart_copy_path = self.convert_path(os.path.join(folder_new_path, extrafanart_copy_folder))

        # 如果不保留，不下载，删除返回
        if 'extrafanart_copy' not in keep_files and 'extrafanart_copy' not in download_files:
            if os.path.exists(extrafanart_copy_path):
                shutil.rmtree(extrafanart_copy_path, ignore_errors=True)
            return

        # 如果保留，并且存在，返回
        if 'extrafanart_copy' in keep_files and os.path.exists(extrafanart_copy_path):
            json_data['logs'] += "\n 🍀 Extrafanart_copy done! (old)(%ss) " % self.get_used_time(start_time)
            return

        # 如果不下载，返回
        if 'extrafanart_copy' not in download_files:
            return

        if not os.path.exists(extrafanart_path):
            return

        if os.path.exists(extrafanart_copy_path):
            shutil.rmtree(extrafanart_copy_path, ignore_errors=True)
        shutil.copytree(extrafanart_path, extrafanart_copy_path)

        filelist = os.listdir(extrafanart_copy_path)
        for each in filelist:
            file_new_name = each.replace('fanart', '')
            file_path = os.path.join(extrafanart_copy_path, each)
            file_new_path = os.path.join(extrafanart_copy_path, file_new_name)
            move_file(file_path, file_new_path)
        json_data['logs'] += "\n 🍀 ExtraFanart_copy done! (copy extrafanart)(%ss)" % (self.get_used_time(start_time))

    # =====================================================================================为所有视频中的创建/删除剧照副本

    def pushButton_add_all_extrafanart_copy_clicked(self):
        self.pushButton_show_log_clicked()                                      # 点按钮后跳转到日志页面
        try:
            t = threading.Thread(target=self.add_del_extrafanart_copy_clicked, args=('add', ))
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_log_text(traceback.format_exc())

    def pushButton_del_all_extrafanart_copy_clicked(self):
        self.pushButton_show_log_clicked()                                      # 点按钮后跳转到日志页面
        try:
            t = threading.Thread(target=self.add_del_extrafanart_copy_clicked, args=('del', ))
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_log_text(traceback.format_exc())

    def add_del_extrafanart_copy_clicked(self, mode):
        extrafanart_folder = self.Ui.lineEdit_extrafanart_dir.text().strip()
        extrafanart_folder_config = self.config.get('extrafanart_folder')
        if extrafanart_folder != extrafanart_folder_config:
            self.pushButton_save_config_clicked()
        self.show_log_text('Start %s extrafanart copy! \n' % mode)

        movie_path, success_folder, failed_folder, escape_folder_list, extrafanart_folder, softlink_path = self.get_movie_path_setting()
        self.show_log_text(' 🖥 Movie path: %s \n 🔎 Checking all videos, Please wait...' % movie_path)
        movie_type = self.config.get('media_type')
        movie_list = self.movie_lists('', movie_type, movie_path)               # 获取所有需要刮削的影片列表

        extrafanart_folder_path_list = []
        for movie in movie_list:
            movie_file_folder_path = split_path(movie)[0]
            extrafanart_folder_path = os.path.join(movie_file_folder_path, 'extrafanart')
            if os.path.exists(extrafanart_folder_path):
                extrafanart_folder_path_list.append(movie_file_folder_path)
        extrafanart_folder_path_list = list(set(extrafanart_folder_path_list))
        extrafanart_folder_path_list.sort()
        total_count = len(extrafanart_folder_path_list)
        new_count = 0
        count = 0
        for each in extrafanart_folder_path_list:
            extrafanart_folder_path = os.path.join(each, 'extrafanart')
            extrafanart_copy_folder_path = os.path.join(each, extrafanart_folder)
            count += 1
            if mode == 'add':
                if not os.path.exists(extrafanart_copy_folder_path):
                    shutil.copytree(extrafanart_folder_path, extrafanart_copy_folder_path)
                    self.show_log_text(" %s new copy: \n  %s" % (count, extrafanart_copy_folder_path))
                    new_count += 1
                else:
                    self.show_log_text(" %s old copy: \n  %s" % (count, extrafanart_copy_folder_path))
            else:
                if os.path.exists(extrafanart_copy_folder_path):
                    shutil.rmtree(extrafanart_copy_folder_path, ignore_errors=True)
                    self.show_log_text(" %s del copy: \n  %s" % (count, extrafanart_copy_folder_path))
                    new_count += 1

        self.show_log_text('\nDone! \n Total: %s  %s copy: %s ' % (total_count, mode, new_count))
        self.show_log_text("================================================================================")

    # =====================================================================================为所有视频中的创建/删除主题视频

    def pushButton_add_all_theme_videos_clicked(self):
        self.pushButton_show_log_clicked()                                      # 点按钮后跳转到日志页面
        try:
            t = threading.Thread(target=self.add_del_theme_videos_clicked, args=('add', ))
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_log_text(traceback.format_exc())

    def pushButton_del_all_theme_videos_clicked(self):
        self.pushButton_show_log_clicked()                                      # 点按钮后跳转到日志页面
        try:
            t = threading.Thread(target=self.add_del_theme_videos_clicked, args=('del', ))
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_log_text(traceback.format_exc())

    def add_del_theme_videos_clicked(self, mode):
        self.show_log_text('Start %s theme videos! \n' % mode)

        movie_path, success_folder, failed_folder, escape_folder_list, extrafanart_folder, softlink_path = self.get_movie_path_setting()
        self.show_log_text(' 🖥 Movie path: %s \n 🔎 Checking all videos, Please wait...' % movie_path)
        movie_type = self.config.get('media_type')
        movie_list = self.movie_lists('', movie_type, movie_path)               # 获取所有需要刮削的影片列表

        theme_videos_folder_path_dic = {}
        for movie in movie_list:
            movie_file_folder_path = split_path(movie)[0]
            movie_file_path_no_ext = os.path.splitext(movie)[0]
            trailer_file_path_with_filename = movie_file_path_no_ext + '-trailer.mp4'
            trailer_file_path_no_filename = os.path.join(movie_file_folder_path, 'trailers/trailer.mp4')
            if os.path.exists(trailer_file_path_with_filename):
                theme_videos_folder_path_dic[movie_file_folder_path] = trailer_file_path_with_filename
            elif os.path.exists(trailer_file_path_no_filename):
                theme_videos_folder_path_dic[movie_file_folder_path] = trailer_file_path_no_filename
        theme_videos_folder_path_list = sorted(theme_videos_folder_path_dic.keys())
        total_count = len(theme_videos_folder_path_list)
        new_count = 0
        count = 0
        for movie_file_folder_path in theme_videos_folder_path_list:
            trailer_file_path = theme_videos_folder_path_dic.get(movie_file_folder_path)
            theme_videos_folder_path = os.path.join(movie_file_folder_path, 'backdrops')
            theme_videos_file_path = os.path.join(movie_file_folder_path, 'backdrops/theme_video.mp4')
            count += 1
            if mode == 'add':
                if not os.path.exists(theme_videos_file_path):
                    if not os.path.exists(theme_videos_folder_path):
                        os.mkdir(theme_videos_folder_path)
                    copy_file(trailer_file_path, theme_videos_file_path)
                    self.show_log_text(" %s new theme video: \n  %s" % (count, theme_videos_file_path))
                    new_count += 1
                else:
                    self.show_log_text(" %s old theme video: \n  %s" % (count, theme_videos_file_path))
            else:
                if os.path.exists(theme_videos_folder_path):
                    shutil.rmtree(theme_videos_folder_path, ignore_errors=True)
                    self.show_log_text(" %s del theme video: \n  %s" % (count, theme_videos_folder_path))
                    new_count += 1

        self.show_log_text('\nDone! \n Total: %s  %s copy: %s ' % (total_count, mode, new_count))
        self.show_log_text("================================================================================")

    # ======================================================================================字段命名规则

    def deal_some_filed(self, json_data):
        fields_rule = self.config.get('fields_rule')
        actor = json_data['actor']
        title = json_data['title']
        originaltitle = json_data['originaltitle']
        number = json_data['number']

        # 演员处理
        if actor:
            # 去除演员名中的括号
            new_actor_list = []
            actor_list = []
            temp_actor_list = []
            for each_actor in actor.split(','):
                if each_actor and each_actor not in actor_list:
                    actor_list.append(each_actor)
                    new_actor = re.findall(r'[^\(\)\（\）]+', each_actor)
                    if new_actor[0] not in new_actor_list:
                        new_actor_list.append(new_actor[0])
                    temp_actor_list.extend(new_actor)
            if 'del_char' in fields_rule:
                json_data['actor'] = ','.join(new_actor_list)
            else:
                json_data['actor'] = ','.join(actor_list)

            # 去除标题后的演员名
            if 'del_actor' in fields_rule:
                new_all_actor_name_list = []
                for each_actor in json_data['actor_amazon'] + temp_actor_list:
                    actor_keyword_list = self.get_actor_data(each_actor).get('keyword') # 获取演员映射表的所有演员别名进行替换
                    new_all_actor_name_list.extend(actor_keyword_list)
                for each_actor in set(new_all_actor_name_list):
                    try:
                        end_actor = re.compile(r' %s$' % each_actor)
                        title = re.sub(end_actor, '', title)
                        originaltitle = re.sub(end_actor, '', originaltitle)
                    except:
                        pass
            json_data['title'] = title.strip()
            json_data['originaltitle'] = originaltitle.strip()

        # 去除标题中的番号
        if number != title and title.startswith(number):
            title = title.replace(number, '').strip()
            json_data['title'] = title
        if number != originaltitle and originaltitle.startswith(number):
            originaltitle = originaltitle.replace(number, '').strip()
            json_data['originaltitle'] = originaltitle

        # 去除标题中的/
        json_data['title'] = json_data['title'].replace('/', '#').strip(' -')
        json_data['originaltitle'] = json_data['originaltitle'].replace('/', '#').strip(' -')

        # 去除素人番号前缀数字
        if 'del_num' in fields_rule:
            temp_n = re.findall(r'\d{3,}([a-zA-Z]+-\d+)', number)
            if temp_n:
                json_data['number'] = temp_n[0]
                json_data['letters'] = get_number_letters(json_data['number'])

        if number.endswith('Z'):
            json_data['number'] = json_data['number'][:-1] + 'z'
        return json_data

    # ======================================================================================替换一些字符

    def convert_half(self, string):
        # 替换敏感词
        for key, value in self.special_word.items():
            string = string.replace(key, value)
        # 替换全角为半角
        for each in self.full_half_char:
            string = string.replace(each[0], each[1])
        # 去除空格等符号
        return re.sub(r'[\W_]', '', string).upper()

    def set_some_data(self):
        self.full_half_char = [
            (u"・", u"·"), (u"．", u"."), (u"，", u","), (u"！", u"!"), (u"？", u"?"), (u"”", u'"'), (u"’", u"'"), (u"‘", u"`"), (u"＠", u"@"), (u"＿", u"_"), (u"：", u":"), (u"；", u";"), (u"＃", u"#"), (u"＄", u"$"), (u"％", u"%"), (u"＆", u"&"), (u"（", u"("), (u"）", u")"), (u"‐", u"-"), (u"＝", u"="), (u"＊", u"*"), (u"＋", u"+"), (u"－", u"-"), (u"／", u"/"), (u"＜", u"<"), (u"＞", u">"), (u"［", u"["), (u"￥", u"\\"), (u"］", u"]"), (u"＾", u"^"), (u"｛", u"{"), (u"｜", u"|"), (u"｝", u"}"), (u"～", u"~"), (u"ａ", u"a"), (u"ｂ", u"b"), (u"ｃ", u"c"), (u"ｄ", u"d"), (u"ｅ", u"e"), (u"ｆ", u"f"), (u"ｇ", u"g"), (u"ｈ", u"h"), (u"ｉ", u"i"), (u"ｊ", u"j"), (u"ｋ", u"k"), (u"ｌ", u"l"), (u"ｍ", u"m"), (u"ｎ", u"n"), (u"ｏ", u"o"), (u"ｐ", u"p"), (u"ｑ", u"q"), (u"ｒ", u"r"), (u"ｓ", u"s"), (u"ｔ", u"t"), (u"ｕ", u"u"), (u"ｖ", u"v"),
            (u"ｗ", u"w"), (u"ｘ", u"x"), (u"ｙ", u"y"), (u"ｚ", u"z"), (u"Ａ", u"A"), (u"Ｂ", u"B"), (u"Ｃ", u"C"), (u"Ｄ", u"D"), (u"Ｅ", u"E"), (u"Ｆ", u"F"), (u"Ｇ", u"G"), (u"Ｈ", u"H"), (u"Ｉ", u"I"), (u"Ｊ", u"J"), (u"Ｋ", u"K"), (u"Ｌ", u"L"), (u"Ｍ", u"M"), (u"Ｎ", u"N"), (u"Ｏ", u"O"), (u"Ｐ", u"P"), (u"Ｑ", u"Q"), (u"Ｒ", u"R"), (u"Ｓ", u"S"), (u"Ｔ", u"T"), (u"Ｕ", u"U"), (u"Ｖ", u"V"), (u"Ｗ", u"W"), (u"Ｘ", u"X"), (u"Ｙ", u"Y"), (u"Ｚ", u"Z"), (u"０", u"0"), (u"１", u"1"), (u"２", u"2"), (u"３", u"3"), (u"４", u"4"), (u"５", u"5"), (u"６", u"6"), (u"７", u"7"), (u"８", u"8"), (u"９", u"9"), (u"　", u" ")
        ]
        self.special_word = {
            '強●': '強制',
            '犯●': '犯さ',
            '凌●': '凌辱',
            '折●': '折檻',
            '奴●': '奴隷',
            '輪●': '輪姦',
            '痴●': '痴漢',
            '近●': '近親',
            '小●生': '小学生',
            '中●生': '中学生',
            '女子●生': '女子校生',
            '強○': '強制',
            '犯○': '犯さ',
            '凌○': '凌辱',
            '折○': '折檻',
            '奴○': '奴隷',
            '輪○': '輪姦',
            '痴○': '痴漢',
            '近○': '近親',
            '小○生': '小学生',
            '中○生': '中学生',
            '女子○生': '女子校生',
            'ﾒｲﾄﾞ': 'メイド',
            'ﾎｰﾙﾄﾞ': 'ホールド',
        }

    def replace_special_word(self, json_data):
        # 常见字段替换的字符
        all_key_word = ['title', 'originaltitle', 'outline', 'originalplot', 'series', 'director', 'studio', 'publisher', 'tag']
        for key, value in self.special_word.items():
            for each in all_key_word:
                json_data[each] = json_data[each].replace(key, value)

    def replace_word(self, json_data):
        # 常见字段替换的字符
        all_key_word = ['title', 'originaltitle', 'outline', 'originalplot', 'series', 'director', 'studio', 'publisher']
        all_rep_word = {
            '&amp;': '＆',                                                       # 将网页中存在二次抓取的&amp;(实际意义为&)的字符全局替换成＆（大写的&，不会被emby误判，显示更美观）
            '&lt;': '<',                                                        # 将网页中存在二次抓取的&lt;(实际意义为<)的字符全局替换成<
            '&gt;': '>',                                                        # 将网页中存在二次抓取的&gt;(实际意义为>)的字符替全局换成>
            '&apos;': "'",                                                      # 将网页中存在二次抓取的&apos;(实际意义为')的字符全局替换成'
            '&quot;': '"',                                                      # 将网页中存在二次抓取的&quot;(实际意义为")的字符替全局换成"
            '&lsquo;': '「',                                                     # 将网页中存在二次抓取的&lsquo;(实际意义为「)的字符全局替换成「
            '&rsquo;': '」',                                                     # 将网页中存在二次抓取的&rsquo;(实际意义为」)的字符全局替换成」
            '&hellip;': '…',                                                    # 将网页中存在二次抓取的&hellip;(实际意义为…)的字符全局替换成…
            '&rarr;': '→',                                                      # 将网页中存在二次抓取的&rarr;(实际意义为→)的字符全局替换成→
            '<br/>': '',                                                        # 将网页中存在的隐藏换行符全局替换成空白
            '&': '＆',                                                           # 将网页本身抓取到的&全局替换成＆（大写的&，不会被emby误判，避免Emby的nfo读取错误，显示更美观）
            '&mdash;': '—',                                                     # 将网页中存在二次抓取的&mdash;(实际意义为—破折号)的字符全局替换成—，破折号”—“不等于数字“一”
            '<': '＜',                                                           # 将网页中存在二次抓取的<字符全局替换成＜（大写的＜，不会被emby误判，避免Emby的nfo读取错误，显示更美观）
            '>': '＞',                                                           # 将网页中存在二次抓取的>字符全局替换成＞（大写的＞，不会被emby误判，避免Emby的nfo读取错误，显示更美观）
            '・': '·',                                                           # 将网页本身的・（人名间隔号）全局替换成·
            '“': '「',                                                           # 将前双引号“全局替换为「，更美观
            '”': '」',                                                           # 将后双引号”全局替换为」，更美观
            '...': '…',                                                         # 将非标准省略号...全局替换成标准省略号…
            '……': '…',                                                          # 将并列的两个省略号……全局替换成单个省略号…  解决......替换成……后出现两个省略号
            '’s': "'s",                                                         # 将非标准英文单引号的’替换全局为标准英文单引号'，避免’s被以下规则替换成」s,例如：love’s替换成love's
            '‘': '「',                                                           # 将前单引号‘全局替换为「，更美观
            '’': '」',                                                           # 将后单引号’全局替换为」，更美观
            ',': '，',                                                           # 将英文逗号,全局替换成中文逗号，
            '?': '？',                                                           # 将英文问号?全局替换成中文问号？
            '! ': '！',                                                          # 去除感叹号后面不必要的空格
            '!': '！',                                                           # 将英文感叹号!全局替换成中文感叹号！
            'Ａ': 'A',                                                           # 将全角大写英文替换成半角大写英文
            'Ｂ': 'B',                                                           # 将全角大写英文替换成半角大写英文
            'Ｃ': 'C',                                                           # 将全角大写英文替换成半角大写英文
            'Ｄ': 'D',                                                           # 将全角大写英文替换成半角大写英文
            'Ｅ': 'E',                                                           # 将全角大写英文替换成半角大写英文
            'Ｆ': 'F',                                                           # 将全角大写英文替换成半角大写英文
            'Ｇ': 'G',                                                           # 将全角大写英文替换成半角大写英文
            'Ｈ': 'H',                                                           # 将全角大写英文替换成半角大写英文
            'Ｉ': 'I',                                                           # 将全角大写英文替换成半角大写英文
            'Ｊ': 'J',                                                           # 将全角大写英文替换成半角大写英文
            'Ｋ': 'K',                                                           # 将全角大写英文替换成半角大写英文
            'Ｌ': 'L',                                                           # 将全角大写英文替换成半角大写英文
            'Ｍ': 'M',                                                           # 将全角大写英文替换成半角大写英文
            'Ｎ': 'N',                                                           # 将全角大写英文替换成半角大写英文
            'Ｏ': 'O',                                                           # 将全角大写英文替换成半角大写英文
            'Ｐ': 'P',                                                           # 将全角大写英文替换成半角大写英文
            'Ｑ': 'Q',                                                           # 将全角大写英文替换成半角大写英文
            'Ｒ': 'R',                                                           # 将全角大写英文替换成半角大写英文
            'Ｓ': 'S',                                                           # 将全角大写英文替换成半角大写英文
            'Ｔ': 'T',                                                           # 将全角大写英文替换成半角大写英文
            'Ｕ': 'U',                                                           # 将全角大写英文替换成半角大写英文
            'Ｖ': 'V',                                                           # 将全角大写英文替换成半角大写英文
            'Ｗ': 'W',                                                           # 将全角大写英文替换成半角大写英文
            'Ｘ': 'X',                                                           # 将全角大写英文替换成半角大写英文
            'Ｙ': 'Y',                                                           # 将全角大写英文替换成半角大写英文
            'Ｚ': 'Z',                                                           # 将全角大写英文替换成半角大写英文
            'ａ': 'a',                                                           # 将全角小写英文替换成半角小写英文
            'ｂ': 'b',                                                           # 将全角小写英文替换成半角小写英文
            'ｃ': 'c',                                                           # 将全角小写英文替换成半角小写英文
            'ｄ': 'd',                                                           # 将全角小写英文替换成半角小写英文
            'ｅ': 'e',                                                           # 将全角小写英文替换成半角小写英文
            'ｆ': 'f',                                                           # 将全角小写英文替换成半角小写英文
            'ｇ': 'g',                                                           # 将全角小写英文替换成半角小写英文
            'ｈ': 'h',                                                           # 将全角小写英文替换成半角小写英文
            'ｉ': 'i',                                                           # 将全角小写英文替换成半角小写英文
            'ｊ': 'j',                                                           # 将全角小写英文替换成半角小写英文
            'ｋ': 'k',                                                           # 将全角小写英文替换成半角小写英文
            'ｌ': 'l',                                                           # 将全角小写英文替换成半角小写英文
            'ｍ': 'm',                                                           # 将全角小写英文替换成半角小写英文
            'ｎ': 'n',                                                           # 将全角小写英文替换成半角小写英文
            'ｏ': 'o',                                                           # 将全角小写英文替换成半角小写英文
            'ｐ': 'p',                                                           # 将全角小写英文替换成半角小写英文
            'ｑ': 'q',                                                           # 将全角小写英文替换成半角小写英文
            'ｒ': 'r',                                                           # 将全角小写英文替换成半角小写英文
            'ｓ': 's',                                                           # 将全角小写英文替换成半角小写英文
            'ｔ': 't',                                                           # 将全角小写英文替换成半角小写英文
            'ｕ': 'u',                                                           # 将全角小写英文替换成半角小写英文
            'ｖ': 'v',                                                           # 将全角小写英文替换成半角小写英文
            'ｗ': 'w',                                                           # 将全角小写英文替换成半角小写英文
            'ｘ': 'x',                                                           # 将全角小写英文替换成半角小写英文
            'ｙ': 'y',                                                           # 将全角小写英文替换成半角小写英文
            'ｚ': 'z',                                                           # 将全角小写英文替换成半角小写英文
            '１': '1',                                                           # 将全角数字替换成半角数字
            '２': '2',                                                           # 将全角数字替换成半角数字
            '３': '3',                                                           # 将全角数字替换成半角数字
            '４': '4',                                                           # 将全角数字替换成半角数字
            '５': '5',                                                           # 将全角数字替换成半角数字
            '６': '6',                                                           # 将全角数字替换成半角数字
            '７': '7',                                                           # 将全角数字替换成半角数字
            '８': '8',                                                           # 将全角数字替换成半角数字
            '９': '9',                                                           # 将全角数字替换成半角数字
            '０': '0',                                                           # 将全角数字替换成半角数字
            '\t': ' ',                                                           # 将制表符替换为空格
        }
        for key, value in all_rep_word.items():
            for each in all_key_word:
                json_data[each] = json_data[each].replace(key, value)

        # 简体时替换的字符
        key_word = []
        if self.config.get('title_language') == 'zh_cn':
            key_word.append('title')
        if self.config.get('outline_language') == 'zh_cn':
            key_word.append('outline')
        chinese_rep_word = {
            '姊': '姐',                                                           # 中文简体常见错字全局替换
            '著': '着',                                                           # 中文简体常见错字全局替换
            '慾': '欲',                                                           # 中文简体常见错字全局替换
            '肏': '操',                                                           # 中文简体常见错字全局替换
            '裡': '里',                                                           # 中文简体常见错字全局替换
            '係': '系',                                                           # 中文简体常见错字全局替换
            '繫': '联',                                                           # 中文简体常见错字全局替换
            '豔': '艳',                                                           # 中文简体常见错字全局替换
            '妳': '你',                                                           # 中文简体常见错字全局替换
            '歳': '岁',                                                           # 中文简体常见错字全局替换
            '廿': '二十',                                                          # 中文简体常见错字全局替换
            '卅': '三十',                                                          # 中文简体常见错字全局替换
            '卌': '四十',                                                          # 中文简体常见错字全局替换
        }
        for key, value in chinese_rep_word.items():
            for each in key_word:
                json_data[each] = json_data[each].replace(key, value)

        # 替换标题的上下集信息
        title_rep = ['第一集', '第二集', ' - 上', ' - 下', ' 上集', ' 下集', ' -上', ' -下', 'Part.1 (HD)', '(蓝光碟版)', '(蓝光版)', '(ブルーレイ版)']
        fields_word = ['title', 'originaltitle']
        for field in fields_word:
            for each in title_rep:
                json_data[field] = json_data[field].replace(each, '').strip(':， ').strip()

    # ======================================================================================打印NFO

    def write_nfo(self, json_data, nfo_new_path, folder_new_path, file_path, edit_mode=False):
        start_time = time.time()
        download_files = self.config.get('download_files')
        keep_files = self.config.get('keep_files')
        outline_show = self.config.get('outline_show')

        if not edit_mode:
            # 读取模式，有nfo，并且没有勾选更新 nfo 信息
            if not json_data['nfo_can_translate']:
                json_data['logs'] += "\n 🍀 Nfo done! (old)(%ss)" % self.get_used_time(start_time)
                return True

            # 不下载，不保留时
            if 'nfo' not in download_files:
                if 'nfo' not in keep_files and os.path.exists(nfo_new_path):
                    delete_file(nfo_new_path)
                return True

            # 保留时，返回
            if 'nfo' in keep_files and os.path.exists(nfo_new_path):
                json_data['logs'] += "\n 🍀 Nfo done! (old)(%ss)" % self.get_used_time(start_time)
                return True

        # 字符转义，避免emby无法解析
        json_data_nfo = json_data.copy()
        key_word = ['title', 'originaltitle', 'outline', 'originalplot', 'actor', 'series', 'director', 'studio', 'publisher', 'tag', 'website', 'cover', 'poster', 'trailer']
        rep_word = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&apos;': "'",
            '&quot;': '"',
            '&lsquo;': '「',
            '&rsquo;': '」',
            '&hellip;': '…',
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&apos;',
            '"': '&quot;',
        }
        for key, value in rep_word.items():
            for each in key_word:
                json_data_nfo[each] = str(json_data_nfo[each]).replace(key, value)
        # 获取字段
        nfo_include_new = self.config.get('nfo_include_new')
        c_word = json_data_nfo['c_word']
        cd_part = json_data_nfo['cd_part']
        originaltitle = json_data_nfo['originaltitle']
        originalplot = json_data_nfo['originalplot']
        title, originaltitle, studio, publisher, year, outline, runtime, director, actor_photo, actor, release, tag, number, cover, poster, website, series, mosaic, definition, trailer, letters = get_info(json_data_nfo)
        all_actor = json_data['all_actor']
        temp_release = self.get_new_release(release)
        file_full_name = split_path(file_path)[1]
        filename = os.path.splitext(file_full_name)[0]
        definition = json_data['definition']
        temp_4k = ''
        if definition == '8K' or definition == 'UHD8' or definition == '4K' or definition == 'UHD':
            temp_4k = definition.replace('UHD8', 'UHD')

        # 获取在媒体文件中显示的规则，不需要过滤Windows异常字符
        # 国产使用title作为number会出现重复，此处去除title，避免重复(需要注意titile繁体情况)
        nfo_title = self.config.get('naming_media')
        if not number:
            number = title
        if number == title and 'number' in nfo_title and 'title' in nfo_title:
            nfo_title = nfo_title.replace('originaltitle', '').replace('title', '')
        first_letter = get_number_first_letter(number)

        # 处理演员
        first_actor = actor.split(',').pop(0)
        temp_all_actor = self.deal_actor_more(json_data['all_actor'])
        temp_actor = self.deal_actor_more(actor)

        repl_list = [['4K', temp_4k], ['originaltitle', originaltitle], ['title', title], ['outline', outline], ['number', number], ['first_actor', first_actor], ['all_actor', temp_all_actor], ['actor', temp_actor], ['release', temp_release], ['year', year], ['runtime', runtime], ['director', director], ['series', series], ['studio', studio], ['publisher', publisher], ['mosaic', mosaic], ['definition', definition.replace('UHD8', 'UHD')], ['cnword', c_word], ['first_letter', first_letter], ['letters', letters], ['filename', filename], ['wanted', json_data['wanted']]]
        for each_key in repl_list:
            nfo_title = nfo_title.replace(each_key[0], each_key[1])

        tag = re.split(r'[,，]', tag)                                            # tag str转list

        try:
            if not os.path.exists(folder_new_path):
                os.makedirs(folder_new_path)
            delete_file(nfo_new_path)   # 避免115出现重复文件
            with open(nfo_new_path, "wt", encoding='UTF-8') as code:
                print('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', file=code)
                print("<movie>", file=code)

                # 输出剧情简介
                if outline:
                    outline = outline.replace('\n', '<br>')
                    if originalplot and originalplot != outline:
                        if 'show_zh_jp' in outline_show:
                            outline += f'<br>  <br>{originalplot}'
                        elif 'show_jp_zh' in outline_show:
                            outline = f'{originalplot}<br>  <br>{outline}'
                        outline_from = json_data['outline_from'].capitalize().replace('Youdao', '有道')
                        if 'show_from' in outline_show and outline_from:
                            outline += f'<br>  <br>由 {outline_from} 提供翻译'
                    if 'outline_no_cdata,' in nfo_include_new:
                        temp_outline = outline.replace('<br>', '')
                        if 'plot_,' in nfo_include_new:
                            print(f"  <plot>{temp_outline}</plot>", file=code)
                        if 'outline,' in nfo_include_new:
                            print(f"  <outline>{temp_outline}</outline>", file=code)
                    else:
                        if 'plot_,' in nfo_include_new:
                            print("  <plot><![CDATA[" + outline + "]]></plot>", file=code)
                        if 'outline,' in nfo_include_new:
                            print("  <outline><![CDATA[" + outline + "]]></outline>", file=code)

                # 输出日文剧情简介
                if originalplot and 'originalplot,' in nfo_include_new:
                    originalplot = originalplot.replace('\n', '<br>')
                    if 'outline_no_cdata,' in nfo_include_new:
                        temp_originalplot = originalplot.replace('<br>', '')
                        print(f"  <originalplot>{temp_originalplot}</originalplot>", file=code)
                    else:
                        print("  <originalplot><![CDATA[" + originalplot + "]]></originalplot>", file=code)

                # 输出发行日期
                if release:
                    nfo_tagline = self.config.get('nfo_tagline').replace('release', release)
                    if nfo_tagline:
                        print("  <tagline>" + nfo_tagline + "</tagline>", file=code)
                    if 'premiered,' in nfo_include_new:
                        print("  <premiered>" + release + "</premiered>", file=code)
                    if 'releasedate,' in nfo_include_new:
                        print("  <releasedate>" + release + "</releasedate>", file=code)
                    if 'release_,' in nfo_include_new:
                        print("  <release>" + release + "</release>", file=code)

                # 输出番号
                print("  <num>" + number + "</num>", file=code)

                # 输出标题
                if cd_part and 'title_cd,' in nfo_include_new:
                    nfo_title += ' ' + cd_part[1:].upper()
                print("  <title>" + nfo_title + "</title>", file=code)

                # 输出原标题
                if 'originaltitle,' in nfo_include_new:
                    if number != title:
                        print("  <originaltitle>" + number + ' ' + originaltitle + "</originaltitle>", file=code)
                    else:
                        print("  <originaltitle>" + originaltitle + "</originaltitle>", file=code)

                # 输出类标题
                if 'sorttitle,' in nfo_include_new:
                    if cd_part:
                        originaltitle += ' ' + cd_part[1:].upper()
                    if number != title:
                        print("  <sorttitle>" + number + ' ' + originaltitle + "</sorttitle>", file=code)
                    else:
                        print("  <sorttitle>" + number + "</sorttitle>", file=code)

                # 输出国家和分级
                try:
                    country = json_data['country']
                except:
                    if re.findall(r'\.\d{2}\.\d{2}\.\d{2}', number):
                        country = 'US'
                    else:
                        country = 'JP'

                # 输出家长分级
                if 'mpaa,' in nfo_include_new:
                    if country == 'JP':
                        print("  <mpaa>JP-18+</mpaa>", file=code)
                    else:
                        print("  <mpaa>NC-17</mpaa>", file=code)

                # 输出自定义分级
                if 'customrating,' in nfo_include_new:
                    if country == 'JP':
                        print("  <customrating>JP-18+</customrating>", file=code)
                    else:
                        print("  <customrating>NC-17</customrating>", file=code)

                # 输出国家
                if 'country,' in nfo_include_new:
                    print(f"  <countrycode>{country}</countrycode>", file=code)

                # 输出演员
                if 'actor_all,' in nfo_include_new:
                    actor = all_actor
                if actor and actor != '未知演员' and actor != '未知演員' and 'actor,' in nfo_include_new:
                    actor_list = actor.split(',')                                         # 字符串转列表
                    actor_list = [actor.strip() for actor in actor_list if actor.strip()] # 去除空白
                    if actor_list:
                        for each in actor_list:
                            print("  <actor>", file=code)
                            print("    <name>" + each + "</name>", file=code)
                            print("    <type>Actor</type>", file=code)
                            print("    <thumb>.actors/" + each + ".jpg</thumb>", file=code)
                            print("  </actor>", file=code)

                # 输出导演
                if director and 'director,' in nfo_include_new:
                    print("  <director>" + director + "</director>", file=code)

                # 输出公众评分、影评人评分
                try:
                    if json_data['score']:
                        score = float(json_data['score'])
                        if 'score,' in nfo_include_new:
                            print("  <rating>" + str(score) + "</rating>", file=code)
                        if 'criticrating,' in nfo_include_new:
                            print("  <criticrating>" + str(int(score * 10)) + "</criticrating>", file=code)
                except:
                    print(traceback.format_exc())

                # 输出我想看人数
                try:
                    if json_data['wanted'] and 'wanted,' in nfo_include_new:
                        print("  <votes>" + json_data['wanted'] + "</votes>", file=code)
                except:
                    pass

                # 输出年代
                if str(year) and 'year,' in nfo_include_new:
                    print("  <year>" + str(year) + "</year>", file=code)

                # 输出时长
                if str(runtime) and 'runtime,' in nfo_include_new:
                    print("  <runtime>" + str(runtime).replace(" ", "") + "</runtime>", file=code)

                # 输出合集(使用演员)
                if 'actor_set,' in nfo_include_new and actor and actor != '未知演员' and actor != '未知演員':
                    actor_list = actor.split(',')                                         # 字符串转列表
                    actor_list = [actor.strip() for actor in actor_list if actor.strip()] # 去除空白
                    if actor_list:
                        for each in actor_list:
                            print("  <set>", file=code)
                            print("    <name>" + each + "</name>", file=code)
                            print("  </set>", file=code)

                # 输出合集(使用系列)
                if 'series_set,' in nfo_include_new and series:
                    print("  <set>", file=code)
                    print("    <name>" + series + "</name>", file=code)
                    print("  </set>", file=code)

                # 输出系列
                if series:
                    if 'series,' in nfo_include_new:
                        print("  <series>" + series + "</series>", file=code)

                # 输出片商/制作商
                if studio:
                    if 'studio,' in nfo_include_new:
                        print("  <studio>" + studio + "</studio>", file=code)
                    if 'maker,' in nfo_include_new:
                        print("  <maker>" + studio + "</maker>", file=code)

                # 输出发行商 label（厂牌/唱片公司） publisher（发行商）
                if publisher:
                    if 'publisher,' in nfo_include_new:
                        print("  <publisher>" + publisher + "</publisher>", file=code)
                    if 'label,' in nfo_include_new:
                        print("  <label>" + publisher + "</label>", file=code)

                # 输出 tag
                if tag and 'tag,' in nfo_include_new:
                    try:
                        for i in tag:
                            if i:
                                print("  <tag>" + i + "</tag>", file=code)
                    except:
                        self.show_log_text(traceback.format_exc())

                # 输出 genre
                if tag and 'genre,' in nfo_include_new:
                    try:
                        for i in tag:
                            if i:
                                print("  <genre>" + i + "</genre>", file=code)
                    except:
                        self.show_log_text(traceback.format_exc())

                # 输出封面地址
                if poster and 'poster,' in nfo_include_new:
                    print("  <poster>" + poster + "</poster>", file=code)

                # 输出背景地址
                if cover and 'cover,' in nfo_include_new:
                    print("  <cover>" + cover + "</cover>", file=code)

                # 输出预告片
                if trailer and 'trailer,' in nfo_include_new:
                    print("  <trailer>" + trailer + "</trailer>", file=code)

                # 输出网页地址
                if website and 'website,' in nfo_include_new:
                    print("  <website>" + website + "</website>", file=code)
                print("</movie>", file=code)
                json_data['logs'] += "\n 🍀 Nfo done! (new)(%ss)" % self.get_used_time(start_time)
                return True
        except Exception as e:
            json_data['logs'] += '\n 🔴 Nfo failed! \n     %s' % str(e)
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())
            return False

    # ======================================================================================移动视频、字幕

    def move_movie(self, json_data, file_path, file_new_path):
        # 明确不需要移动的，直接返回
        if json_data['dont_move_movie']:
            json_data['logs'] += "\n 🍀 Movie done! \n 🙉 [Movie] %s" % file_path
            return True

        # 明确要删除自己的，删除后返回
        if json_data['del_file_path']:
            delete_file(file_path)
            json_data['logs'] += "\n 🍀 Movie done! \n 🙉 [Movie] %s" % file_new_path
            json_data['file_path'] = file_new_path
            return True

        # 软链接模式开时，先删除目标文件，再创建软链接(需考虑自身是软链接的情况)
        if self.config.get('soft_link') == 1:
            temp_path = file_path
            # 自身是软链接时，获取真实路径
            if os.path.islink(file_path):
                file_path = read_link(file_path)
                delete_file(temp_path)
            # 删除目标路径存在的文件，否则会创建失败，
            delete_file(file_new_path)
            try:
                os.symlink(file_path, file_new_path)
                json_data['file_path'] = file_new_path
                json_data['logs'] += f"\n 🍀 Softlink done! \n    Softlink file: {file_new_path} \n    Source file: {file_path}"
                return True
            except Exception as e:
                if self.is_windows:
                    json_data['logs'] += "\n 🥺 Softlink failed! (创建软连接失败！注意：Windows 平台输出目录必须是本地磁盘！不支持挂载的 NAS 盘或网盘！如果是本地磁盘，请尝试以管理员身份运行！)\n%s\n 🙉 [Movie] %s" % (str(e), temp_path)
                else:
                    json_data['logs'] += "\n 🥺 Softlink failed! (创建软连接失败！)\n%s\n 🙉 [Movie] %s" % (str(e), temp_path)
                self.show_traceback_log(traceback.format_exc())
                self.show_log_text(traceback.format_exc())
                return False

        # 硬链接模式开时，创建硬链接
        elif self.config.get('soft_link') == 2:
            try:
                delete_file(file_new_path)
                os.link(file_path, file_new_path)
                json_data['file_path'] = file_new_path
                json_data['logs'] += f"\n 🍀 HardLink done! \n    HadrLink file: {file_new_path} \n    Source file: {file_path}"
                return True
            except Exception as e:
                if self.is_mac:
                    json_data['logs'] += "\n 🥺 HardLink failed! (创建硬连接失败！注意：硬链接要求待刮削文件和输出目录必须是同盘，不支持跨卷！如要跨卷可以尝试软链接模式！另外，Mac 平台非本地磁盘不支持创建硬链接（权限问题），请选择软链接模式！)\n%s " % (str(e))
                else:
                    json_data['logs'] += "\n 🥺 HardLink failed! (创建硬连接失败！注意：硬链接要求待刮削文件和输出目录必须是同盘，不支持跨卷！如要跨卷可以尝试软链接模式！)\n%s " % (str(e))
                json_data['error_info'] = '创建硬连接失败！'
                self.show_traceback_log(traceback.format_exc())
                self.show_log_text(traceback.format_exc())
                return False

        # 其他情况，就移动文件
        result, error_info = move_file(file_path, file_new_path)
        if result:
            json_data['logs'] += "\n 🍀 Movie done! \n 🙉 [Movie] %s" % file_new_path
            if os.path.islink(file_new_path):
                json_data['logs'] += "\n    It's a symlink file! Source file: \n    %s" % read_link(file_new_path)  # win 不能用os.path.realpath()，返回的结果不准
            json_data['file_path'] = file_new_path
            return True
        else:
            if 'are the same file' in error_info.lower():                               # 大小写不同，win10 用raidrive 挂载 google drive 改名会出错
                if json_data['cd_part']:
                    temp_folder, temp_file = split_path(file_new_path)
                    if temp_file not in os.listdir(temp_folder):
                        move_file(file_path, file_new_path + '.MDCx.tmp')
                        move_file(file_new_path + '.MDCx.tmp', file_new_path)
                json_data['logs'] += "\n 🍀 Movie done! \n 🙉 [Movie] %s" % file_new_path
                json_data['file_path'] = file_new_path
                return True
            json_data['logs'] += f'\n 🔴 Failed to move movie file to success folder!\n    {error_info}'
            return False

    # ======================================================================================裁剪封面

    def cut_thumb_to_poster(self, json_data, thumb_path, poster_path, image_cut=''):
        start_time = time.time()
        if os.path.exists(poster_path):
            delete_file(poster_path)

        # 打开图片, 获取图片尺寸
        try:
            img = Image.open(thumb_path)                                        # 返回一个Image对象
        except:
            self.show_log_text(f"{traceback.format_exc()}\n Pic: {thumb_path}")
            return False

        w, h = img.size
        prop = h / w

        # 判断裁剪方式
        if not image_cut:
            if prop >= 1.4:
                image_cut = 'no'
            elif prop >= 1:
                image_cut = 'center'
            else:
                image_cut = 'right'
            json_data['image_cut'] = image_cut

        # 不裁剪
        if image_cut == 'no':
            copy_file(thumb_path, poster_path)
            json_data['logs'] += "\n 🍀 Poster done! (copy thumb)(%ss)" % self.get_used_time(start_time)
            json_data['poster_from'] = 'copy thumb'
            img.close()
            return True

        # 中间裁剪
        elif image_cut == 'center':
            json_data['poster_from'] = 'thumb center'
            ax = int((w - h / 1.5) / 2)
            ay = 0
            bx = ax + int(h / 1.5)
            by = int(h)

        # 右边裁剪
        else:
            json_data['poster_from'] = 'thumb right'
            ax, ay, bx, by = w / 1.9, 0, w, h
            if w == 800:
                if h == 439:
                    ax, ay, bx, by = 420, 0, w, h
                elif h >= 499 and h <= 503:
                    ax, ay, bx, by = 437, 0, w, h
                else:
                    ax, ay, bx, by = 421, 0, w, h
            elif w == 840:
                if h == 472:
                    ax, ay, bx, by = 473, 0, 788, h

        # 裁剪并保存
        try:
            img_new = img.convert('RGB')
            img_new_png = img_new.crop((ax, ay, bx, by))
            img_new_png.save(poster_path, quality=95, subsampling=0)
            img.close()
            if check_pic(poster_path):
                json_data['logs'] += "\n 🍀 Poster done! (%s)(%ss)" % (json_data['poster_from'], self.get_used_time(start_time))
                return True
            json_data['logs'] += '\n 🥺 Poster cut failed! (%s)(%ss)' % (json_data['poster_from'], self.get_used_time(start_time))
        except Exception as e:
            json_data['logs'] += '\n 🥺 Poster failed! (%s)(%ss)\n    %s' % (json_data['poster_from'], self.get_used_time(start_time), str(e))
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())
        return False

    def fix_size(self, path, naming_rule):
        try:
            poster_path = os.path.join(path, (naming_rule + '-poster.jpg'))
            if os.path.exists(poster_path):
                pic = Image.open(poster_path)
                (width, height) = pic.size
                if not 2 / 3 - 0.05 <= width / height <= 2 / 3 + 0.05:                # 仅处理会过度拉伸的图片
                    fixed_pic = pic.resize((int(width), int(3 / 2 * width)))          # 拉伸图片
                    fixed_pic = fixed_pic.filter(ImageFilter.GaussianBlur(radius=50)) # 高斯模糊
                    fixed_pic.paste(pic, (0, int((3 / 2 * width - height) / 2)))      # 粘贴原图
                    fixed_pic.save(poster_path, quality=95, subsampling=0)
                pic.close()
        except:
            self.show_log_text(f"{traceback.format_exc()}\n Pic: {poster_path}")

    # ======================================================================================添加水印
    # 判断要加哪些水印
    def add_mark(self, json_data, poster_marked=False, thumb_marked=False, fanart_marked=False):
        download_files = self.config.get('download_files')
        mark_type = self.config.get('mark_type').lower()
        has_sub = json_data['has_sub']
        mosaic = json_data['mosaic']
        definition = json_data['definition']
        mark_list = []
        if ('K' in definition or 'UHD' in definition) and 'hd' in mark_type:
            if '8' in definition:
                mark_list.append('8K')
            else:
                mark_list.append('4K')
        if has_sub and 'sub' in mark_type:
            mark_list.append('字幕')

        if mosaic == '有码' or mosaic == '有碼':
            if 'youma' in mark_type:
                mark_list.append('有码')
        elif mosaic == '无码破解' or mosaic == '無碼破解':
            if 'umr' in mark_type:
                mark_list.append('破解')
            elif 'uncensored' in mark_type:
                mark_list.append('无码')
        elif mosaic == '无码流出' or mosaic == '無碼流出':
            if 'leak' in mark_type:
                mark_list.append('流出')
            elif 'uncensored' in mark_type:
                mark_list.append('无码')
        elif mosaic == '无码' or mosaic == '無碼':
            if 'uncensored' in mark_type:
                mark_list.append('无码')

        if mark_list:
            download_files = self.config.get('download_files')
            mark_show_type = ','.join(mark_list)
            poster_path = json_data['poster_path']
            thumb_path = json_data['thumb_path']
            fanart_path = json_data['fanart_path']

            if self.config.get('thumb_mark') == 1 and 'thumb' in download_files and thumb_path and not thumb_marked:
                self.add_mark_thread(thumb_path, mark_list)
                json_data['logs'] += '\n 🍀 Thumb add watermark: %s!' % mark_show_type
            if self.config.get('poster_mark') == 1 and 'poster' in download_files and poster_path and not poster_marked:
                self.add_mark_thread(poster_path, mark_list)
                json_data['logs'] += '\n 🍀 Poster add watermark: %s!' % mark_show_type
            if self.config.get('fanart_mark') == 1 and ',fanart' in download_files and fanart_path and not fanart_marked:
                self.add_mark_thread(fanart_path, mark_list)
                json_data['logs'] += '\n 🍀 Fanart add watermark: %s!' % mark_show_type

    # 获取水印位置
    def add_mark_thread(self, pic_path, mark_list):
        mark_size = self.config.get('mark_size')
        mark_fixed = self.config.get('mark_fixed')
        mark_pos = self.config.get('mark_pos')
        mark_pos_hd = self.config.get('mark_pos_hd')
        mark_pos_sub = self.config.get('mark_pos_sub')
        mark_pos_mosaic = self.config.get('mark_pos_mosaic')
        mark_pos_corner = self.config.get('mark_pos_corner')
        try:
            img_pic = Image.open(pic_path)
        except:
            self.show_log_text(f"{traceback.format_exc()}\n Open Pic: {pic_path}")
            return

        if mark_fixed == 'corner':
            count = 0
            if 'left' not in mark_pos_corner:
                count = 3 - len(mark_list)
            for mark_name in mark_list:
                self.add_to_pic(pic_path, img_pic, mark_size, count, mark_name)
                count += 1
        else:
            pos = {
                'top_left': 0,
                'top_right': 1,
                'bottom_right': 2,
                'bottom_left': 3,
            }
            mark_pos_count = pos.get(mark_pos)                                                       # 获取自定义位置, 取余配合pos达到顺时针添加的效果
            count_hd = ''
            for mark_name in mark_list:
                if mark_name == '4K' or mark_name == '8K':                                           # 4K/8K使用固定位置
                    count_hd = pos.get(mark_pos_hd)
                    self.add_to_pic(pic_path, img_pic, mark_size, count_hd, mark_name)
                elif mark_fixed == 'on':                                                             # 固定位置
                    if mark_name == '字幕':
                        count = pos.get(mark_pos_sub)
                    else:
                        count = pos.get(mark_pos_mosaic)
                    self.add_to_pic(pic_path, img_pic, mark_size, count, mark_name)
                else:                                                                                # 不固定位置
                    if mark_pos_count % 4 == count_hd:
                        mark_pos_count += 1
                    if mark_name == '字幕':
                        self.add_to_pic(pic_path, img_pic, mark_size, mark_pos_count % 4, mark_name) # 添加字幕
                        mark_pos_count += 1
                    else:
                        self.add_to_pic(pic_path, img_pic, mark_size, mark_pos_count % 4, mark_name)
        img_pic.close()

    # 获取水印图片，生成水印
    def add_to_pic(self, pic_path, img_pic, mark_size, count, mark_name):
        mark_fixed = self.config.get('mark_fixed')
        mark_pos_corner = self.config.get('mark_pos_corner')
        mark_pic_path = ''
        if mark_name == '4K':
            mark_pic_path = self.icon_4k_path
        elif mark_name == '8K':
            mark_pic_path = self.icon_8k_path
        elif mark_name == '字幕':
            mark_pic_path = self.icon_sub_path
        elif mark_name == '有码':
            mark_pic_path = self.icon_youma_path
        elif mark_name == '破解':
            mark_pic_path = self.icon_umr_path
        elif mark_name == '流出':
            mark_pic_path = self.icon_leak_path
        elif mark_name == '无码':
            mark_pic_path = self.icon_wuma_path

        if mark_pic_path:
            try:
                img_subt = Image.open(mark_pic_path)
                img_subt = img_subt.convert('RGBA')
                scroll_high = int(img_pic.height * mark_size / 40)
                scroll_width = int(scroll_high * img_subt.width / img_subt.height)
                img_subt = img_subt.resize((scroll_width, scroll_high), Image.LANCZOS)
            except:
                self.show_log_text(f"{traceback.format_exc()}\n Open Pic: {mark_pic_path}")
                print(traceback.format_exc())
                return
            r, g, b, a = img_subt.split()                                       # 获取颜色通道, 保持png的透明性

            # 固定一个位置
            if mark_fixed == 'corner':
                corner_top_left = [(0, 0), (scroll_width, 0), (scroll_width * 2, 0)]
                corner_bottom_left = [(0, img_pic.height - scroll_high), (scroll_width, img_pic.height - scroll_high), (scroll_width * 2, img_pic.height - scroll_high)]
                corner_top_right = [(img_pic.width - scroll_width * 4, 0), (img_pic.width - scroll_width * 2, 0), (img_pic.width - scroll_width, 0)]
                corner_bottom_right = [(img_pic.width - scroll_width * 4, img_pic.height - scroll_high), (img_pic.width - scroll_width * 2, img_pic.height - scroll_high), (img_pic.width - scroll_width, img_pic.height - scroll_high)]
                corner_dic = {
                    'top_left': corner_top_left,
                    'bottom_left': corner_bottom_left,
                    'top_right': corner_top_right,
                    'bottom_right': corner_bottom_right,
                }
                mark_postion = corner_dic[mark_pos_corner][count]

            # 封面四个角的位置
            else:
                pos = [
                    {
                        'x': 0,
                        'y': 0
                    },
                    {
                        'x': img_pic.width - scroll_width,
                        'y': 0
                    },
                    {
                        'x': img_pic.width - scroll_width,
                        'y': img_pic.height - scroll_high
                    },
                    {
                        'x': 0,
                        'y': img_pic.height - scroll_high
                    },
                ]
                mark_postion = (pos[count]['x'], pos[count]['y'])
            try:                                                            # 图片如果下载不完整时，这里会崩溃，跳过
                img_pic.paste(img_subt, mark_postion, mask=a)
            except:
                self.show_log_text(traceback.format_exc())
            img_pic = img_pic.convert('RGB')
            temp_pic_path = pic_path + '.[MARK].jpg'
            try:
                img_pic.load()
                img_pic.save(temp_pic_path, quality=95, subsampling=0)
            except:
                self.show_log_text(traceback.format_exc())
            img_subt.close()
            if check_pic(temp_pic_path):
                move_file(temp_pic_path, pic_path)

    # ======================================================================================更新进度条

    def set_processbar(self, value):
        self.Ui.progressBar_scrape.setProperty("value", value)

    # ======================================================================================显示jsondata结果

    def show_data_result(self, json_data, start_time):
        if json_data['error_info'] or json_data['title'] == '':
            json_data['logs'] += '\n 🌐 [website] %s' % json_data['req_web'].strip('-> ') + '\n' + json_data['log_info'].strip(' ').strip('\n') + '\n' + ' 🔴 Data failed!(%ss)' % (self.get_used_time(start_time))
            return False
        else:
            self.show_debug_info(json_data)                                     # 调试模式打开时显示详细日志
            json_data['logs'] += '\n 🍀 Data done!(%ss)' % (self.get_used_time(start_time))
            return True

    # ======================================================================================输出调试信息

    def show_debug_info(self, json_data):
        if self.config.get('show_web_log') == 'on':                             # 字段刮削过程
            json_data['logs'] += '\n 🌐 [website] %s' % json_data['req_web'].strip('-> ')
            try:
                if json_data['log_info']:
                    json_data['logs'] += '\n' + json_data['log_info'].strip(' ').strip('\n')
            except:
                self.show_log_text(traceback.format_exc())
        if self.config.get('show_from_log') == 'on':                            # 字段来源信息
            if json_data['fields_info']:
                json_data['logs'] += '\n' + json_data['fields_info'].strip(' ').strip('\n')

    # ======================================================================================输出 Movie 信息

    def show_movie_info(self, json_data):
        if self.config.get('show_data_log') == 'off':                           # 调试模式打开时显示详细日志
            return
        show_key = [
            'number',
            'letters',
            'has_sub',
            'cd_part',
            'mosaic',
            'title',
            'originaltitle',
            'actor',
            'outline',
            'originalplot',
            'tag',
            'release',
            'year',
            'runtime',
            'score',
            'wanted',
            'series',
            'director',
            'studio',
            'publisher',
            'trailer',
            'website',
        ]
        for key in show_key:
            value = json_data.get(key)
            if not value:
                continue
            if key == 'outline' or key == 'originalplot' and len(value) > 100:
                value = str(value)[:98] + '……（略）'
            elif key == 'has_sub':
                value = '中文字幕'
            elif key == 'actor' and 'actor_all,' in self.config.get('nfo_include_new'):
                value = json_data['all_actor']
            json_data['logs'] += '\n     ' + "%-13s" % key + ': ' + str(value)

    # ======================================================================================获取输出文件夹名称

    def get_folder_path(self, file_path, success_folder, json_data):
        main_mode = self.config.get('main_mode')                                # 刮削模式
        update_mode = self.config.get('update_mode')                            # 更新模式
        update_a_folder = self.config.get('update_a_folder')                    # 更新模式a目录
        update_b_folder = self.config.get('update_b_folder')                    # 更新模式b目录
        update_d_folder = self.config.get('update_d_folder')                    # 更新模式d目录
        folder_name = self.config.get('folder_name').replace('\\', '/')         # 设置-命名-视频目录名
        folder_path, file_name = split_path(file_path)                          # 当前文件的目录和文件名
        filename = os.path.splitext(file_name)[0]

        # 更新模式 或 读取模式
        if main_mode == 3 or main_mode == 4:
            if update_mode == 'c':
                folder_name = split_path(folder_path)[1]
                json_data['folder_name'] = folder_name
                return folder_path
            elif 'bc' in update_mode:
                folder_name = update_b_folder
                success_folder = split_path(folder_path)[0]
                if 'a' in update_mode:
                    success_folder = split_path(success_folder)[0]
                    folder_name = os.path.join(update_a_folder, update_b_folder).replace('\\', '/').strip('/')
            elif update_mode == 'd':
                folder_name = update_d_folder
                success_folder = split_path(file_path)[0]

        # 正常模式 或 整理模式
        else:
            # 关闭软连接，并且成功后移动文件关时，使用原来文件夹
            if self.config.get('soft_link') == 0 and self.config.get('success_file_move') == 0:
                folder_path = split_path(file_path)[0]
                json_data['folder_name'] = folder_name
                return folder_path

        # 当根据刮削模式得到的视频目录名为空时，使用成功输出目录
        if not folder_name:
            json_data['folder_name'] = ''
            return success_folder

        # 获取文件信息
        destroyed = json_data['destroyed']
        leak = json_data['leak']
        wuma = json_data['wuma']
        youma = json_data['youma']
        m_word = destroyed + leak + wuma + youma
        c_word = json_data['c_word']
        title, originaltitle, studio, publisher, year, outline, runtime, director, actor_photo, actor, release, tag, number, cover, poster, website, series, mosaic, definition, trailer, letters = get_info(json_data)

        # 国产使用title作为number会出现重复，此处去除title，避免重复(需要注意titile繁体情况)
        if not number:
            number = title
        if number == title and 'number' in folder_name and 'title' in folder_name:
            folder_name = folder_name.replace('originaltitle', '').replace('title', '')

        # 是否勾选目录名添加字幕标识
        cnword = c_word
        if self.config.get('folder_cnword') != 'on':
            c_word = ''

        # 是否勾选目录名添加4k标识
        temp_4k = ''
        if 'folder' in self.config.get('show_4k'):
            definition = json_data['definition']
            if definition == '8K' or definition == 'UHD8' or definition == '4K' or definition == 'UHD':
                temp_definition = definition.replace('UHD8', 'UHD')
                temp_4k = f'-{temp_definition}'

        # 是否勾选目录名添加版本字符标识
        moword = m_word
        if 'folder' not in self.config.get('show_moword'):
            m_word = ''

        # 判断后缀字段顺序
        file_show_name = number + temp_4k
        suffix_sort_list = self.config.get('suffix_sort').split(',')
        for each in suffix_sort_list:
            if each == 'mosaic':
                file_show_name += m_word
            elif each == 'cnword':
                file_show_name += c_word

        # 生成number
        number = file_show_name
        first_letter = get_number_first_letter(number)

        # 特殊情况处理
        score = str(json_data['score'])
        if not series:
            series = '未知系列'
        if not actor:
            actor = self.config.get('actor_no_name')
        if not year:
            year = '0000'
        if not score:
            score = '0.0'
        release = self.get_new_release(release)

        # 获取演员
        first_actor = actor.split(',').pop(0)
        all_actor = self.deal_actor_more(json_data['all_actor'])
        actor = self.deal_actor_more(actor)

        # 替换字段里的文件夹分隔符
        fields = [originaltitle, title, number, director, actor, release, series, studio, publisher, cnword, outline]
        for i in range(len(fields)):
            fields[i] = fields[i].replace('/', '-').replace('\\', '-').strip('. ')
        originaltitle, title, number, director, actor, release, series, studio, publisher, cnword, outline = fields

        # 更新4k
        if definition == '8K' or definition == 'UHD8' or definition == '4K' or definition == 'UHD':
            temp_4k = definition.replace('UHD8', 'UHD')

        # 替换文件夹名称
        repl_list = [['4K', temp_4k.strip('-')], ['originaltitle', originaltitle], ['title', title], ['outline', outline], ['number', number], ['first_actor', first_actor], ['all_actor', all_actor], ['actor', actor], ['release', release], ['year', str(year)], ['runtime', str(runtime)], ['director', director], ['series', series], ['studio', studio], ['publisher', publisher], ['mosaic', mosaic], ['definition', definition.replace('UHD8', 'UHD')], ['cnword', cnword], ['moword', moword], ['first_letter', first_letter], ['letters', letters], ['filename', filename], ['wanted', str(json_data['wanted'])], ['score', str(score)]]
        folder_new_name = folder_name
        for each_key in repl_list:
            folder_new_name = folder_new_name.replace(each_key[0], each_key[1])

        # 去除各种乱七八糟字符后，文件夹名为空时，使用number显示
        folder_name_temp = re.sub(r'[\\/:*?"<>|\r\n]+', '', folder_new_name)
        folder_name_temp = folder_name_temp.replace('//', '/').replace('--', '-').strip('-')
        if not folder_name_temp:
            folder_new_name = number

        # 判断文件夹名长度，超出长度时，截短标题名
        folder_name_max = int(self.config.get('folder_name_max'))
        if len(folder_new_name) > folder_name_max:
            cut_index = folder_name_max - len(folder_new_name)
            if 'originaltitle' in folder_name:
                json_data['logs'] += '\n 💡 当前目录名长度：%s，最大允许长度：%s，目录命名时将去除原标题后%s个字符!' % (len(folder_new_name), folder_name_max, abs(cut_index))
                folder_new_name = folder_new_name.replace(originaltitle, originaltitle[0:cut_index])
            elif 'title' in folder_name:
                json_data['logs'] += '\n 💡 当前目录名长度：%s，最大允许长度：%s，目录命名时将去除标题后%s个字符!' % (len(folder_new_name), folder_name_max, abs(cut_index))
                folder_new_name = folder_new_name.replace(title, title[0:cut_index])
            elif 'outline' in folder_name:
                json_data['logs'] += '\n 💡 当前目录名长度：%s，最大允许长度：%s，目录命名时将去除简介后%s个字符!' % (len(folder_new_name), folder_name_max, abs(cut_index))
                folder_new_name = folder_new_name.replace(outline, outline[0:cut_index])

        # 替换一些字符
        folder_new_name = folder_new_name.replace('--', '-').strip('-').strip('- .')

        # 用在保存文件时的名字，需要过滤window异常字符 特殊字符
        folder_new_name = re.sub(r'[\\:*?"<>|\r\n]+', '', folder_new_name).strip(' /')

        # 过滤文件夹名字前后的空格
        folder_new_name = folder_new_name.replace(' /', '/').replace(' \\', '\\').replace('/ ', '/').replace('\\ ', '\\')

        # 日文浊音转换（mac的坑,osx10.12以下使用nfd）
        folder_new_name = self.nfd2c(folder_new_name)

        # 生成文件夹名
        folder_new_path = os.path.join(success_folder, folder_new_name)
        folder_new_path = self.convert_path(folder_new_path)
        folder_new_path = self.nfd2c(folder_new_path)

        json_data['folder_name'] = folder_new_name

        return folder_new_path.strip().replace(' /', '/')

    # ======================================================================================发行日期命名规则

    def get_new_release(self, release):
        release_rule = self.config.get('release_rule')
        if not release:
            release = '0000-00-00'
        if release_rule == 'YYYY-MM-DD':
            return release
        year, month, day = re.findall(r'(\d{4})-(\d{2})-(\d{2})', release)[0]
        return release_rule.replace('YYYY', year).replace('YY', year[-2:]).replace('MM', month).replace('DD', day)

    # ======================================================================================获取输出的本地文件名

    def get_naming_rule(self, file_path, json_data):
        file_full_name = split_path(file_path)[1]
        file_name, file_ex = os.path.splitext(file_full_name)
        filename = file_name

        # 如果成功后不重命名，则返回原来名字
        if self.config.get('success_file_rename') == 0:
            return file_name

        # 获取文件信息
        cd_part = json_data['cd_part']
        destroyed = json_data['destroyed']
        leak = json_data['leak']
        wuma = json_data['wuma']
        youma = json_data['youma']
        m_word = destroyed + leak + wuma + youma
        c_word = json_data['c_word']
        title, originaltitle, studio, publisher, year, outline, runtime, director, actor_photo, actor, release, tag, number, cover, poster, website, series, mosaic, definition, trailer, letters = get_info(json_data)

        # 国产使用title作为number会出现重复，此处去除title，避免重复(需要注意titile繁体情况)
        naming_file = self.config.get('naming_file')
        if not number:
            number = title
        if number == title and 'number' in naming_file and 'title' in naming_file:
            naming_file = naming_file.replace('originaltitle', '').replace('title', '')
        file_name = naming_file

        # 是否勾选文件名添加4k标识
        temp_4k = ''
        if 'file' in self.config.get('show_4k'):
            definition = json_data['definition']
            if definition == '8K' or definition == 'UHD8' or definition == '4K' or definition == 'UHD':
                temp_definition = definition.replace('UHD8', 'UHD')
                temp_4k = f'-{temp_definition}'

        # 判断是否勾选文件名添加字幕标识
        cnword = c_word
        if self.config.get('file_cnword') != 'on':
            c_word = ''

        # 判断是否勾选文件名添加版本标识
        moword = m_word
        if 'file' not in self.config.get('show_moword'):
            m_word = ''

        # 判断后缀字段顺序
        file_show_name = number + temp_4k
        suffix_sort_list = self.config.get('suffix_sort').split(',')
        for each in suffix_sort_list:
            if each == 'mosaic':
                file_show_name += m_word
            elif each == 'cnword':
                file_show_name += c_word

        # 生成number
        number = file_show_name
        first_letter = get_number_first_letter(number)

        # 处理异常情况
        score = json_data['score']
        if not series:
            series = '未知系列'
        if not actor:
            actor = self.config.get('actor_no_name')
        if not year:
            year = '0000'
        if not score:
            score = '0.0'
        release = self.get_new_release(release)

        # 获取演员
        first_actor = actor.split(',').pop(0)
        all_actor = self.deal_actor_more(json_data['all_actor'])
        actor = self.deal_actor_more(actor)

        # 替换字段里的文件夹分隔符
        fields = [originaltitle, title, number, director, actor, release, series, studio, publisher, cnword, outline]
        for i in range(len(fields)):
            fields[i] = fields[i].replace('/', '-').replace('\\', '-').strip('. ')
        originaltitle, title, number, director, actor, release, series, studio, publisher, cnword, outline = fields

        # 更新4k
        if definition == '8K' or definition == 'UHD8' or definition == '4K' or definition == 'UHD':
            temp_4k = definition.replace('UHD8', 'UHD')

        # 替换文件名
        repl_list = [['4K', temp_4k.strip('-')], ['originaltitle', originaltitle], ['title', title], ['outline', outline], ['number', number], ['first_actor', first_actor], ['all_actor', all_actor], ['actor', actor], ['release', release], ['year', str(year)], ['runtime', str(runtime)], ['director', director], ['series', series], ['studio', studio], ['publisher', publisher], ['mosaic', mosaic], ['definition', definition.replace('UHD8', 'UHD')], ['cnword', cnword], ['moword', moword], ['first_letter', first_letter], ['letters', letters], ['filename', filename], ['wanted', str(json_data['wanted'])], ['score', str(score)]]
        for each_key in repl_list:
            file_name = file_name.replace(each_key[0], each_key[1])
        file_name += cd_part

        # 去除各种乱七八糟字符后，文件名为空时，使用number显示
        file_name_temp = re.sub(r'[\\/:*?"<>|\r\n]+', '', file_name)
        file_name_temp = file_name_temp.replace('//', '/').replace('--', '-').strip('-')
        if not file_name_temp:
            file_name = number

        # 插入防屏蔽字符（115）
        prevent_char = self.config.get('prevent_char')
        if prevent_char:
            file_char_list = list(file_name)
            file_name = prevent_char.join(file_char_list)

        # 判断文件名长度，超出长度时，截短文件名
        file_name_max = int(self.config.get('file_name_max'))
        if len(file_name) > file_name_max:
            cut_index = file_name_max - len(file_name) - len(file_ex)

            # 如果没有防屏蔽字符，截短标题或者简介，这样不影响其他字段阅读
            if not prevent_char:
                if 'originaltitle' in naming_file:
                    json_data['logs'] += '\n 💡 当前文件名长度：%s，最大允许长度：%s，文件命名时将去除原标题后%s个字符!' % (len(file_name), file_name_max, abs(cut_index))
                    file_name = file_name.replace(originaltitle, originaltitle[:cut_index])
                elif 'title' in naming_file:
                    json_data['logs'] += '\n 💡 当前文件名长度：%s，最大允许长度：%s，文件命名时将去除标题后%s个字符!' % (len(file_name), file_name_max, abs(cut_index))
                    file_name = file_name.replace(title, title[:cut_index])
                elif 'outline' in naming_file:
                    json_data['logs'] += '\n 💡 当前文件名长度：%s，最大允许长度：%s，文件命名时将去除简介后%s个字符!' % (len(file_name), file_name_max, abs(cut_index))
                    file_name = file_name.replace(outline, outline[:cut_index])

            # 加了防屏蔽字符，直接截短
            else:
                file_name = file_name[:cut_index]

        # 替换一些字符
        file_name = file_name.replace('//', '/').replace('--', '-').strip('-')

        # 用在保存文件时的名字，需要过滤window异常字符 特殊字符
        file_name = re.sub(r'[\\/:*?"<>|\r\n]+', '', file_name).strip()

        # 过滤文件名字前后的空格
        file_name = file_name.replace(' /', '/').replace(' \\', '\\').replace('/ ', '/').replace('\\ ', '\\').strip()

        # 日文浊音转换（mac的坑,osx10.12以下使用nfd）
        file_name = self.nfd2c(file_name)

        return file_name

    # ======================================================================================windows 保留了一些文件名

    def deal_path_name(self, path):
        # Windows 保留文件名
        if self.is_windows:
            windows_keep_name = ['CON', 'PRN', 'NUL', 'AUX']
            temp_list = re.split(r'[/\\]', path)
            for i in range(len(temp_list)):
                if temp_list[i].upper() in windows_keep_name:
                    temp_list[i] += '☆'
            return self.convert_path('/'.join(temp_list))
        return path

    # ======================================================================================判断演员数量

    def deal_actor_more(self, actor):
        actor_name_max = int(self.config.get('actor_name_max'))
        actor_name_more = self.config.get('actor_name_more')
        actor_list = actor.split(',')
        if len(actor_list) > actor_name_max:                                    # 演员多于设置值时
            actor = ''
            for i in range(actor_name_max):
                actor = actor + actor_list[i] + ','
            actor = actor.strip(',') + actor_name_more
        return actor

    # ======================================================================================生成各种输出文件和文件夹的名字

    def get_output_name(self, json_data, file_path, success_folder, file_ex):
        # =====================================================================================更新输出文件夹名
        folder_new_path = self.get_folder_path(file_path, success_folder, json_data)
        folder_new_path = self.deal_path_name(folder_new_path)
        # =====================================================================================更新实体文件命名规则
        naming_rule = self.get_naming_rule(file_path, json_data)
        naming_rule = self.deal_path_name(naming_rule)
        # =====================================================================================生成文件和nfo新路径
        file_new_name = naming_rule + file_ex.lower()
        nfo_new_name = naming_rule + '.nfo'
        file_new_path = self.convert_path(os.path.join(folder_new_path, file_new_name))
        nfo_new_path = self.convert_path(os.path.join(folder_new_path, nfo_new_name))
        # =====================================================================================生成图片下载路径
        poster_new_name = naming_rule + '-poster.jpg'
        thumb_new_name = naming_rule + '-thumb.jpg'
        fanart_new_name = naming_rule + '-fanart.jpg'
        poster_new_path_with_filename = self.convert_path(os.path.join(folder_new_path, poster_new_name))
        thumb_new_path_with_filename = self.convert_path(os.path.join(folder_new_path, thumb_new_name))
        fanart_new_path_with_filename = self.convert_path(os.path.join(folder_new_path, fanart_new_name))
        # =====================================================================================生成图片最终路径
        # 如果图片命名规则不加文件名并且视频目录不为空
        if self.config.get('pic_name') == 1 and json_data['folder_name'].replace(' ', ''):
            poster_final_name = 'poster.jpg'
            thumb_final_name = 'thumb.jpg'
            fanart_final_name = 'fanart.jpg'
        else:
            poster_final_name = naming_rule + '-poster.jpg'
            thumb_final_name = naming_rule + '-thumb.jpg'
            fanart_final_name = naming_rule + '-fanart.jpg'
        poster_final_path = self.convert_path(os.path.join(folder_new_path, poster_final_name))
        thumb_final_path = self.convert_path(os.path.join(folder_new_path, thumb_final_name))
        fanart_final_path = self.convert_path(os.path.join(folder_new_path, fanart_final_name))

        return folder_new_path, file_new_path, nfo_new_path, poster_new_path_with_filename, thumb_new_path_with_filename, fanart_new_path_with_filename, naming_rule, poster_final_path, thumb_final_path, fanart_final_path

    # ======================================================================================获取刮削网站

    def get_website_name(self, json_data, file_mode):
        website_name = 'all'
        if file_mode == 'single_file':                                          # 刮削单文件（工具页面）
            website_name = self.Ui.comboBox_website.currentText()
        elif file_mode == 'search_again':                                       # 重新刮削
            website_temp = json_data['website_name']
            if website_temp:
                website_name = website_temp
        elif self.config.get('scrape_like') == 'single':
            website_name = self.config.get('website_single')

        return website_name

    # ======================================================================================从指定网站获取json_data

    def get_json_data(self, json_data, file_mode):
        website_name = self.get_website_name(json_data, file_mode)
        json_data = get_data_from_website(json_data, website_name)
        return self.deal_json_data(json_data)

    # ======================================================================================处理得到的json_data

    def deal_json_data(self, json_data):
        config = self.config

        # 标题为空返回
        title = json_data['title']
        if not title:
            return json_data

        # 演员
        json_data['actor'] = str(json_data['actor']).strip(" [ ]").replace("'", '').replace(', ', ',').replace('<', '(').replace('>', ')').strip(',') # 列表转字符串（避免个别网站刮削返回的是列表）

        # 标签
        tag = str(json_data['tag']).strip(" [ ]").replace("'", '').replace(', ', ',') # 列表转字符串（避免个别网站刮削返回的是列表）
        tag = re.sub(r',\d+[kKpP]', '', tag)
        tag_rep_word = [',HD高画质', ',HD高畫質', ',高画质', ',高畫質']
        for each in tag_rep_word:
            tag = tag.replace(each, '')
        json_data['tag'] = tag

        # poster图
        if not json_data.get('poster'):
            json_data['poster'] = ''

        # 发行日期
        release = json_data['release']
        if release:
            release = release.replace('/', '-').strip('. ')
            if len(release) < 10:
                release_list = re.findall(r'(\d{4})-(\d{1,2})-(\d{1,2})', release)
                if release_list:
                    r_year, r_month, r_day = release_list[0]
                    r_month = '0' + r_month if len(r_month) == 1 else r_month
                    r_day = '0' + r_day if len(r_day) == 1 else r_day
                    release = r_year + '-' + r_month + '-' + r_day
        json_data['release'] = release

        # 评分
        if json_data.get('score'):
            json_data['score'] = '%.1f' % float(json_data.get('score'))
        else:
            json_data['score'] = ''

        # originaltitle
        if not json_data.get('originaltitle'):
            json_data['originaltitle'] = ''

        # outline
        if not json_data.get('outline'):
            json_data['outline'] = ''

        # originalplot
        if not json_data.get('originalplot'):
            json_data['originalplot'] = ''

        # series
        if not json_data.get('series'):
            json_data['series'] = ''

        # series
        if not json_data.get('director'):
            json_data['director'] = ''

        # studio
        if not json_data.get('studio'):
            json_data['studio'] = ''

        # publisher
        if not json_data.get('publisher'):
            json_data['publisher'] = json_data['studio']

        # trailer
        if not json_data.get('trailer'):
            json_data['trailer'] = ''

        # wanted
        if not json_data.get('wanted'):
            json_data['wanted'] = ''

        # 字符转义，避免显示问题
        key_word = ['title', 'originaltitle', 'number', 'outline', 'originalplot', 'actor', 'tag', 'series', 'director', 'studio', 'publisher']
        rep_word = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&apos;': "'",
            '&quot;': '"',
            '&lsquo;': '「',
            '&rsquo;': '」',
            '&hellip;': '…',
            '<br/>': '',
            '・': '·',
            '“': '「',
            '”': '」',
            '...': '…',
            u'\xa0': '',
            u'\u3000': '',
            u'\u2800': '',
        }
        for each in key_word:
            for key, value in rep_word.items():
                json_data[each] = json_data[each].replace(key, value)

        # 命名规则
        naming_media = config.get('naming_media')
        naming_file = config.get('naming_file')
        folder_name = config.get('folder_name')
        json_data['naming_media'] = naming_media
        json_data['naming_file'] = naming_file
        json_data['folder_name'] = folder_name
        return json_data

    # ======================================================================================编辑nfo

    def show_nfo_info(self):
        try:
            json_data = self.json_array[self.show_name]
            self.now_show_name = json_data['show_name']
            title, originaltitle, studio, publisher, year, outline, runtime, director, actor_photo, actor, release, tag, number, cover, poster, website, series, mosaic, definition, trailer, letters = get_info(json_data)
            file_path = json_data.get('file_path')
            number = json_data.get('number')
            originalplot = json_data.get('originalplot')
            score = json_data.get('score')
            wanted = json_data.get('wanted')
            country = json_data.get('country')
            self.Ui.label_nfo.setText(file_path)
            self.Ui.lineEdit_nfo_number.setText(number)
            if json_data['all_actor'] and 'actor_all,' in self.config.get('nfo_include_new'):
                actor = str(json_data['all_actor'])
            self.Ui.lineEdit_nfo_actor.setText(actor)
            self.Ui.lineEdit_nfo_year.setText(year)
            self.Ui.lineEdit_nfo_title.setText(title)
            self.Ui.lineEdit_nfo_originaltitle.setText(originaltitle)
            self.Ui.textEdit_nfo_outline.setPlainText(outline)
            self.Ui.textEdit_nfo_originalplot.setPlainText(originalplot)
            self.Ui.textEdit_nfo_tag.setPlainText(tag)
            self.Ui.lineEdit_nfo_release.setText(release)
            self.Ui.lineEdit_nfo_runtime.setText(runtime)
            self.Ui.lineEdit_nfo_score.setText(score)
            self.Ui.lineEdit_nfo_wanted.setText(wanted)
            self.Ui.lineEdit_nfo_director.setText(director)
            self.Ui.lineEdit_nfo_series.setText(series)
            self.Ui.lineEdit_nfo_studio.setText(studio)
            self.Ui.lineEdit_nfo_publisher.setText(publisher)
            self.Ui.lineEdit_nfo_poster.setText(poster)
            self.Ui.lineEdit_nfo_cover.setText(cover)
            self.Ui.lineEdit_nfo_trailer.setText(trailer)
            self.Ui.lineEdit_nfo_website.setText(website)
            if not country:
                if '.' in number:
                    country = 'US'
                else:
                    country = 'JP'
            AllItems = [self.Ui.comboBox_nfo.itemText(i) for i in range(self.Ui.comboBox_nfo.count())]
            self.Ui.comboBox_nfo.setCurrentIndex(AllItems.index(country))
        except:
            if self.config:
                self.show_traceback_log(traceback.format_exc())

    def save_nfo_info(self):
        try:
            json_data = self.json_array[self.now_show_name]
            file_path = json_data['file_path']
            nfo_path = os.path.splitext(file_path)[0] + '.nfo'
            nfo_folder = split_path(file_path)[0]
            json_data['number'] = self.Ui.lineEdit_nfo_number.text()
            if 'actor_all,' in self.config.get('nfo_include_new'):
                json_data['all_actor'] = self.Ui.lineEdit_nfo_actor.text()
            json_data['actor'] = self.Ui.lineEdit_nfo_actor.text()
            json_data['year'] = self.Ui.lineEdit_nfo_year.text()
            json_data['title'] = self.Ui.lineEdit_nfo_title.text()
            json_data['originaltitle'] = self.Ui.lineEdit_nfo_originaltitle.text()
            json_data['outline'] = self.Ui.textEdit_nfo_outline.toPlainText()
            json_data['originalplot'] = self.Ui.textEdit_nfo_originalplot.toPlainText()
            json_data['tag'] = self.Ui.textEdit_nfo_tag.toPlainText()
            json_data['release'] = self.Ui.lineEdit_nfo_release.text()
            json_data['runtime'] = self.Ui.lineEdit_nfo_runtime.text()
            json_data['score'] = self.Ui.lineEdit_nfo_score.text()
            json_data['wanted'] = self.Ui.lineEdit_nfo_wanted.text()
            json_data['director'] = self.Ui.lineEdit_nfo_director.text()
            json_data['series'] = self.Ui.lineEdit_nfo_series.text()
            json_data['studio'] = self.Ui.lineEdit_nfo_studio.text()
            json_data['publisher'] = self.Ui.lineEdit_nfo_publisher.text()
            json_data['poster'] = self.Ui.lineEdit_nfo_poster.text()
            json_data['cover'] = self.Ui.lineEdit_nfo_cover.text()
            json_data['trailer'] = self.Ui.lineEdit_nfo_trailer.text()
            json_data['website'] = self.Ui.lineEdit_nfo_website.text()
            json_data['country'] = self.Ui.comboBox_nfo.currentText()
            if self.write_nfo(json_data, nfo_path, nfo_folder, file_path, edit_mode=True):
                self.Ui.label_save_tips.setText(f'已保存! {self.get_current_time()}')
                self.add_label_info(json_data)
            else:
                self.Ui.label_save_tips.setText(f'保存失败! {self.get_current_time()}')
        except:
            if self.config:
                self.show_traceback_log(traceback.format_exc())

    # ======================================================================================json_data添加到主界面

    def add_label_info(self, json_data):
        self.set_main_info.emit(json_data)

    def add_label_info_Thread(self, json_data):
        try:
            if not json_data:
                json_data = {
                    'number': '',
                    'actor': '',
                    'all_actor': '',
                    'source': '',
                    'website': '',
                    'title': '',
                    'outline': '',
                    'tag': '',
                    'release': '',
                    'year': '',
                    'runtime': '',
                    'director': '',
                    'series': '',
                    'studio': '',
                    'publisher': '',
                    'poster_path': '',
                    'thumb_path': '',
                    'fanart_path': '',
                    'img_path': '',
                    'has_sub': False,
                    'c_word': '',
                    'leak': '',
                    'cd_part': '',
                    'mosaic': '',
                    'destroyed': '',
                    'actor_href': '',
                    'definition': '',
                    'cover_from': '',
                    'poster_from': '',
                    'extrafanart_from': '',
                    'trailer_from': '',
                    'file_path': '',
                    'img_path': '',
                    'show_name': '',
                    'country': '',
                }
            self.again_json_data = json_data
            number = str(json_data['number'])
            self.Ui.label_number.setToolTip(number)
            if len(number) > 11:
                number = number[:10] + '……'
            self.Ui.label_number.setText(number)
            self.label_number_url = json_data['website']
            actor = str(json_data['actor'])
            if json_data['all_actor'] and 'actor_all,' in self.config.get('nfo_include_new'):
                actor = str(json_data['all_actor'])
            self.Ui.label_actor.setToolTip(actor)
            if number and not actor:
                actor = self.config.get('actor_no_name')
            if len(actor) > 10:
                actor = actor[:9] + '……'
            self.Ui.label_actor.setText(actor)
            self.label_actor_url = json_data['actor_href']
            self.file_main_open_path = json_data['file_path']                   # 文件路径
            self.show_name = json_data['show_name']
            if json_data.get('source'):
                self.Ui.label_source.setText('数据：' + json_data['source'].replace('.main', ''))
            else:
                self.Ui.label_source.setText('')
            self.Ui.label_source.setToolTip(json_data['website'])
            title = json_data['title'].split('\n')[0].strip(' :')
            self.Ui.label_title.setToolTip(title)
            if len(title) > 27:
                title = title[:25] + '……'
            self.Ui.label_title.setText(title)
            outline = str(json_data['outline'])
            self.Ui.label_outline.setToolTip(outline)
            if len(outline) > 38:
                outline = outline[:36] + '……'
            self.Ui.label_outline.setText(outline)
            tag = str(json_data['tag']).strip(" [',']").replace('\'', '')
            self.Ui.label_tag.setToolTip(tag)
            if len(tag) > 76:
                tag = tag[:75] + '……'
            self.Ui.label_tag.setText(tag)
            self.Ui.label_release.setText(str(json_data['release']))
            self.Ui.label_release.setToolTip(str(json_data['release']))
            if json_data['runtime']:
                self.Ui.label_runtime.setText(str(json_data['runtime']) + ' 分钟')
                self.Ui.label_runtime.setToolTip(str(json_data['runtime']) + ' 分钟')
            else:
                self.Ui.label_runtime.setText('')
            self.Ui.label_director.setText(str(json_data['director']))
            self.Ui.label_director.setToolTip(str(json_data['director']))
            series = str(json_data['series'])
            self.Ui.label_series.setToolTip(series)
            if len(series) > 32:
                series = series[:31] + '……'
            self.Ui.label_series.setText(series)
            self.Ui.label_studio.setText(str(json_data['studio']))
            self.Ui.label_studio.setToolTip(str(json_data['studio']))
            self.Ui.label_publish.setText(str(json_data['publisher']))
            self.Ui.label_publish.setToolTip(str(json_data['publisher']))
            self.Ui.label_poster.setToolTip('点击裁剪图片')
            self.Ui.label_thumb.setToolTip('点击裁剪图片')
            if os.path.isfile(json_data['fanart_path']):                        # 生成img_path，用来裁剪使用
                json_data['img_path'] = json_data['fanart_path']
            else:
                json_data['img_path'] = json_data['thumb_path']
            self.json_data = json_data
            self.img_path = json_data['img_path']
            if self.Ui.checkBox_cover.isChecked():                              # 主界面显示封面和缩略图
                poster_path = json_data['poster_path']
                thumb_path = json_data['thumb_path']
                fanart_path = json_data['fanart_path']
                if not os.path.exists(thumb_path):
                    if os.path.exists(fanart_path):
                        thumb_path = fanart_path

                poster_from = json_data['poster_from']
                cover_from = json_data['cover_from']

                self.set_pixmap_thread(poster_path, thumb_path, poster_from, cover_from)
        except:
            if self.config:
                self.show_traceback_log(traceback.format_exc())

    def set_pixmap_thread(self, poster_path='', thumb_path='', poster_from='', cover_from=''):
        t = threading.Thread(target=self.set_pixmap, args=(
            poster_path,
            thumb_path,
            poster_from,
            cover_from,
        ))
        t.start()

    def set_pixmap(self, poster_path='', thumb_path='', poster_from='', cover_from=''):
        poster_pix = [False, '', '暂无封面图', 156, 220]
        thumb_pix = [False, '', '暂无缩略图', 328, 220]
        if os.path.exists(poster_path):
            poster_pix = self.get_pixmap(poster_path, poster=True, pic_from=poster_from)
        if os.path.exists(thumb_path):
            thumb_pix = self.get_pixmap(thumb_path, poster=False, pic_from=cover_from)

        # self.Ui.label_poster_size.setText(poster_pix[2] + '  ' + thumb_pix[2])
        poster_text = poster_pix[2] if poster_pix[2] != '暂无封面图' else ''
        thumb_text = thumb_pix[2] if thumb_pix[2] != '暂无缩略图' else ''
        self.set_pic_text.emit((poster_text + ' ' + thumb_text).strip())
        self.set_pic_pixmap.emit(poster_pix, thumb_pix)

    def get_pixmap(self, pic_path, poster=True, pic_from=''):
        try:
            # 使用 QImageReader 加载，适合加载大文件，pixmap适合显示
            # 判断是否可读取
            img = QImageReader(pic_path)
            if img.canRead():
                img = img.read()
                pix = QPixmap(img)
                pic_width = img.size().width()
                pic_height = img.size().height()
                pic_file_size = int(os.path.getsize(pic_path) / 1024)
                if pic_width and pic_height:
                    if poster:
                        if pic_width / pic_height > 156 / 220:
                            w = 156
                            h = int(156 * pic_height / pic_width)
                        else:
                            w = int(220 * pic_width / pic_height)
                            h = 220
                    else:
                        if pic_width / pic_height > 328 / 220:
                            w = 328
                            h = int(328 * pic_height / pic_width)
                        else:
                            w = int(220 * pic_width / pic_height)
                            h = 220
                    msg = '%s: %s*%s/%sKB' % (pic_from.title(), pic_width, pic_height, pic_file_size)
                    return [True, pix, msg, w, h]
            delete_file(pic_path)
            if poster:
                return [False, '', '封面图损坏', 156, 220]
            return [False, '', '缩略图损坏', 328, 220]
        except:
            self.show_log_text(traceback.format_exc())
            return [False, '', '加载失败', 156, 220]

    def resize_label_and_setpixmap(self, poster_pix, thumb_pix):
        self.Ui.label_poster.resize(poster_pix[3], poster_pix[4])
        self.Ui.label_thumb.resize(thumb_pix[3], thumb_pix[4])

        if poster_pix[0]:
            self.Ui.label_poster.setPixmap(poster_pix[1])
        else:
            self.Ui.label_poster.setText(poster_pix[2])

        if thumb_pix[0]:
            self.Ui.label_thumb.setPixmap(thumb_pix[1])
        else:
            self.Ui.label_thumb.setText(thumb_pix[2])

    # ======================================================================================检测网络

    def ping_host(self, host_address):
        count = self.config.get('retry')
        result_list = [None] * count
        thread_list = [0] * count
        for i in range(count):
            thread_list[i] = threading.Thread(target=self.ping_host_thread, args=(host_address, result_list, i))
            thread_list[i].start()
        for i in range(count):
            thread_list[i].join()
        new_list = [each for each in result_list if each]
        return f'  ⏱ Ping {int(sum(new_list) / len(new_list))} ms ({len(new_list)}/{count})' if new_list else f'  🔴 Ping - ms (0/{count})'

    def ping_host_thread(self, host_address, result_list, i):
        response = ping(host_address, timeout=1)
        result_list[i] = int(response * 1000) if response else 0

    def show_netstatus(self, proxy_info):
        self.show_net_info(time.strftime('%Y-%m-%d %H:%M:%S').center(80, '='))
        proxy_type = ''
        retry_count = 0
        proxy = ''
        timeout = 0
        try:
            proxy_type, proxy, timeout, retry_count = proxy_info
        except:
            self.show_traceback_log(traceback.format_exc())
            self.show_net_info(traceback.format_exc())
        if proxy == '' or proxy_type == '' or proxy_type == 'no':
            self.show_net_info(' 当前网络状态：❌ 未启用代理\n   类型： ' + str(proxy_type) + '    地址：' + str(proxy) + '    超时时间：' + str(timeout) + '    重试次数：' + str(retry_count))
        else:
            self.show_net_info(' 当前网络状态：✅ 已启用代理\n   类型： ' + proxy_type + '    地址：' + proxy + '    超时时间：' + str(timeout) + '    重试次数：' + str(retry_count))
        self.show_net_info('=' * 80)

    def netResult(self):
        start_time = time.time()
        try:
            # 显示代理信息
            self.show_net_info('\n⛑ 开始检测网络....')
            self.show_netstatus(self.current_proxy)
            # 检测网络连通性
            self.show_net_info(' 开始检测网络连通性...')

            javbus_url = 'https://www.javbus.com'
            javdb_url = 'https://javdb.com'
            hdouban_url = 'https://hdouban.com'
            mdtv_url = 'https://www.mdpjzip.xyz'
            airavcc_url = 'https://airav5.fun'
            lulubar_url = 'https://lulubar.co'
            iqqtv_url = 'https://iqq5.xyz'
            avsex_url = 'https://paycalling.com'
            javlibrary_url = 'https://www.javlibrary.com'
            javbus_website = self.config.get('javbus_website')
            javdb_website = self.config.get('javdb_website')
            hdouban_website = self.config.get('hdouban_website')
            mdtv_website = self.config.get('mdtv_website')
            airavcc_website = self.config.get('airavcc_website')
            lulubar_website = self.config.get('lulubar_website')
            iqqtv_website = self.config.get('iqqtv_website')
            avsex_website = self.config.get('avsex_website')
            javlibrary_website = self.config.get('javlibrary_website')
            if javbus_website:
                javbus_url = javbus_website
            if javdb_website:
                javdb_url = javdb_website + '/v/D16Q5?locale=zh'
            else:
                javdb_url = javdb_url + '/v/D16Q5?locale=zh'
            if hdouban_website:
                hdouban_url = hdouban_website
            if mdtv_website:
                mdtv_url = mdtv_website
            if airavcc_website:
                airavcc_url = airavcc_website
            if lulubar_website:
                lulubar_url = lulubar_website
            if iqqtv_website:
                iqqtv_url = iqqtv_website
            if avsex_website:
                avsex_url = avsex_website
            if javlibrary_website:
                javlibrary_url = javlibrary_website
            net_info = [
                ['github', 'https://raw.githubusercontent.com', ''],
                ['airav_cc', airavcc_url + '/jp/playon.aspx?hid=44733', ''],
                ['iqqtv', iqqtv_url, ''],
                ['avsex', avsex_url, ''],
                ['freejavbt', 'https://freejavbt.com', ''],
                ['javbus', javbus_url, ''],
                ['javdb', javdb_url, ''],
                ['jav321', 'https://www.jav321.com', ''],
                ['javlibrary', javlibrary_url + '/cn/?v=javme2j2tu', ''],
                ['dmm', 'https://www.dmm.co.jp', ''],
                ['mgstage', 'https://www.mgstage.com', ''],
                ['getchu', 'http://www.getchu.com', ''],
                ['theporndb', 'https://api.metadataapi.net', ''],
                ['avsox', get_avsox_domain(), ''],
                ['7mmtv', 'https://7mmtv.tv', ''],
                ['xcity', 'https://xcity.jp', ''],
                ['hdouban', hdouban_url, ''],
                ['mdtv', mdtv_url, ''],
                ['madouqu', 'https://madouqu.com', ''],
                ['cnmdb', 'https://cnmdb.net', ''],
                ['lulubar', lulubar_url, ''],
                ['love6', 'https://love6.tv', ''],
                ['yesjav', 'http://www.yesjav.info', ''],
                ['fc2', 'https://adult.contents.fc2.com', ''],
                ['fc2club', 'https://fc2club.top', ''],
                ['fc2hub', 'https://fc2hub.com', ''],
                ['airav', 'https://www.airav.wiki', ''],
                ['av-wiki', 'https://av-wiki.net', ''],
                ['seesaawiki', 'https://seesaawiki.jp/av_neme/d/%C9%F1%A5%EF%A5%A4%A5%D5', ''],
                ['mywife', 'https://mywife.cc', ''],
                ['giga', 'https://www.giga-web.jp', ''],
                ['kin8', 'https://www.kin8tengoku.com/moviepages/3681/index.html', ''],
                ['fantastica', 'http://fantastica-vr.com', ''],
                ['faleno', 'https://faleno.jp', ''],
                ['dahlia', 'https://dahlia-av.jp', ''],
                ['prestige', 'https://www.prestige-av.com', ''],
                ['s1s1s1', 'https://s1s1s1.com', ''],
                ['moodyz', 'https://moodyz.com', ''],
                ['madonna', 'https://www.madonna-av.com', ''],
                ['wanz-factory', 'https://www.wanz-factory.com', ''],
                ['ideapocket', 'https://ideapocket.com', ''],
                ['kirakira', 'https://kirakira-av.com', ''],
                ['ebody', 'https://www.av-e-body.com', ''],
                ['bi-av', 'https://bi-av.com', ''],
                ['premium', 'https://premium-beauty.com', ''],
                ['miman', 'https://miman.jp', ''],
                ['tameikegoro', 'https://tameikegoro.jp', ''],
                ['fitch', 'https://fitch-av.com', ''],
                ['kawaiikawaii', 'https://kawaiikawaii.jp', ''],
                ['befreebe', 'https://befreebe.com', ''],
                ['muku', 'https://muku.tv', ''],
                ['attackers', 'https://attackers.net', ''],
                ['mko-labo', 'https://mko-labo.net', ''],
                ['dasdas', 'https://dasdas.jp', ''],
                ['mvg', 'https://mvg.jp', ''],
                ['opera', 'https://av-opera.jp', ''],
                ['oppai', 'https://oppai-av.com', ''],
                ['v-av', 'https://v-av.com', ''],
                ['to-satsu', 'https://to-satsu.com', ''],
                ['bibian', 'https://bibian-av.com', ''],
                ['honnaka', 'https://honnaka.jp', ''],
                ['rookie', 'https://rookie-av.jp', ''],
                ['nanpa', 'https://nanpa-japan.jp', ''],
                ['hajimekikaku', 'https://hajimekikaku.com', ''],
                ['hhh-av', 'https://hhh-av.com', ''],
            ]
            for each in net_info:
                host_address = each[1].replace('https://', '').replace('http://', '').split('/')[0]
                if each[0] == 'javdb':
                    res_javdb = self.check_javdb_cookie()
                    each[2] = res_javdb.replace('✅ 连接正常', f'✅ 连接正常{self.ping_host(host_address)}')
                elif each[0] == 'javbus':
                    res_javbus = self.check_javbus_cookie()
                    each[2] = res_javbus.replace('✅ 连接正常', f'✅ 连接正常{self.ping_host(host_address)}')
                elif each[0] == 'theporndb':
                    res_theporndb = self.check_theporndb_api_token()
                    each[2] = res_theporndb.replace('✅ 连接正常', f'✅ 连接正常{self.ping_host(host_address)}')
                elif each[0] == 'javlibrary':
                    proxies = True
                    if javlibrary_website:
                        proxies = False
                    result, html_info = scraper_html(each[1], proxies=proxies)
                    if not result:
                        each[2] = '❌ 连接失败 请检查网络或代理设置！ ' + html_info
                    elif 'Cloudflare' in html_info:
                        each[2] = '❌ 连接失败 (被 Cloudflare 5 秒盾拦截！)'
                    else:
                        each[2] = f'✅ 连接正常{self.ping_host(host_address)}'
                elif each[0] in ['avsex', 'freejavbt', 'airav_cc', 'airav', 'madouqu', '7mmtv']:
                    result, html_info = scraper_html(each[1])
                    if not result:
                        each[2] = '❌ 连接失败 请检查网络或代理设置！ ' + html_info
                    elif 'Cloudflare' in html_info:
                        each[2] = '❌ 连接失败 (被 Cloudflare 5 秒盾拦截！)'
                    else:
                        each[2] = f'✅ 连接正常{self.ping_host(host_address)}'
                else:
                    try:
                        result, html_content = get_html(each[1])
                        if not result:
                            each[2] = '❌ 连接失败 请检查网络或代理设置！ ' + str(html_content)
                        else:
                            if each[0] == 'dmm':
                                if re.findall('このページはお住まいの地域からご利用になれません', html_content):
                                    each[2] = '❌ 连接失败 地域限制, 请使用日本节点访问！'
                                else:
                                    each[2] = f'✅ 连接正常{self.ping_host(host_address)}'
                            elif each[0] == 'mgstage':
                                if not html_content.strip():
                                    each[2] = '❌ 连接失败 地域限制, 请使用日本节点访问！'
                                else:
                                    each[2] = f'✅ 连接正常{self.ping_host(host_address)}'
                            else:
                                each[2] = f'✅ 连接正常{self.ping_host(host_address)}'
                    except Exception as e:
                        each[2] = '测试连接时出现异常！信息:' + str(e)
                        self.show_traceback_log(traceback.format_exc())
                        self.show_net_info(traceback.format_exc())
                self.show_net_info('   ' + each[0].ljust(12) + each[2])
            self.show_net_info(f"\n🎉 网络检测已完成！用时 {self.get_used_time(start_time)} 秒！")
            self.show_net_info("================================================================================\n")
        except:
            if not self.config:
                self.show_net_info('\n⛔️ 当前有刮削任务正在停止中，请等待刮削停止后再进行检测！')
                self.show_net_info("================================================================================\n")
        self.Ui.pushButton_check_net.setEnabled(True)
        self.Ui.pushButton_check_net.setText('开始检测')
        self.Ui.pushButton_check_net.setStyleSheet('QPushButton#pushButton_check_net{background-color:#4C6EFF}QPushButton:hover#pushButton_check_net{background-color: rgba(76,110,255,240)}QPushButton:pressed#pushButton_check_net{#4C6EE0}')

    # ======================================================================================网络检查

    def pushButton_check_net_clicked(self):
        if self.Ui.pushButton_check_net.text() == '开始检测':
            self.Ui.pushButton_check_net.setText('停止检测')
            self.Ui.pushButton_check_net.setStyleSheet('QPushButton#pushButton_check_net{color: white;background-color: rgba(230, 36, 0, 250);}QPushButton:hover#pushButton_check_net{color: white;background-color: rgba(247, 36, 0, 250);}QPushButton:pressed#pushButton_check_net{color: white;background-color: rgba(180, 0, 0, 250);}')
            try:
                self.t_net = threading.Thread(target=self.netResult)
                self.t_net.start()                                              # 启动线程,即让线程开始执行
            except:
                self.show_traceback_log(traceback.format_exc())
                self.show_net_info(traceback.format_exc())
        elif self.Ui.pushButton_check_net.text() == '停止检测':
            self.Ui.pushButton_check_net.setText(' 停止检测 ')
            self.Ui.pushButton_check_net.setText(' 停止检测 ')
            t = threading.Thread(target=self.kill_a_thread, args=(self.t_net, ))
            t.start()
            self.show_net_info('\n⛔️ 网络检测已手动停止！')
            self.show_net_info("================================================================================\n")
            self.Ui.pushButton_check_net.setStyleSheet('QPushButton#pushButton_check_net{color: white;background-color:#4C6EFF;}QPushButton:hover#pushButton_check_net{color: white;background-color: rgba(76,110,255,240)}QPushButton:pressed#pushButton_check_net{color: white;background-color:#4C6EE0}')
            self.Ui.pushButton_check_net.setText('开始检测')
        else:
            try:
                self._async_raise(self.t_net.ident, SystemExit)
            except Exception as e:
                self.show_traceback_log(str(e))
                self.show_traceback_log(traceback.format_exc())

    # ======================================================================================检查javdb cookie

    def pushButton_check_javdb_cookie_clicked(self):
        input_cookie = self.Ui.plainTextEdit_cookie_javdb.toPlainText()
        if not input_cookie:
            self.Ui.label_javdb_cookie_result.setText('❌ 未填写 Cookie，影响 FC2 刮削！')
            self.show_log_text(' ❌ JavDb 未填写 Cookie，影响 FC2 刮削！可在「设置」-「网络」添加！')
            return
        self.Ui.label_javdb_cookie_result.setText('⏳ 正在检测中...')
        try:
            t = threading.Thread(target=self.check_javdb_cookie)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())

    # ======================================================================================检查javdb cookie

    def check_javdb_cookie(self):
        tips = '❌ 未填写 Cookie，影响 FC2 刮削！'
        input_cookie = self.Ui.plainTextEdit_cookie_javdb.toPlainText()
        if not input_cookie:
            self.Ui.label_javdb_cookie_result.setText(tips)
            return tips
        # self.Ui.pushButton_check_javdb_cookie.setEnabled(False)
        tips = '✅ 连接正常！'
        new_cookie = {'cookie': input_cookie}
        cookies = self.config.get('javdb')
        javdb_website = self.config.get('javdb_website')
        if javdb_website:
            javdb_url = javdb_website + '/v/D16Q5?locale=zh'
        else:
            javdb_url = 'https://javdb.com/v/D16Q5?locale=zh'

        try:
            result, response = scraper_html(javdb_url, cookies=new_cookie)
            if not result:
                if 'Cookie' in response:
                    if cookies != input_cookie:
                        tips = '❌ Cookie 已过期！'
                    else:
                        tips = '❌ Cookie 已过期！已清理！(不清理无法访问)'
                        self.set_javdb_cookie.emit('')
                        self.pushButton_save_config_clicked()
                else:
                    tips = f'❌ 连接失败！请检查网络或代理设置！ {response}'
            else:
                if "The owner of this website has banned your access based on your browser's behaving" in response:
                    ip_adress = re.findall(r'(\d+\.\d+\.\d+\.\d+)', response)
                    ip_adress = ip_adress[0] + ' ' if ip_adress else ''
                    tips = f'❌ 你的 IP {ip_adress}被 JavDb 封了！'
                elif 'Due to copyright restrictions' in response or 'Access denied' in response:
                    tips = '❌ 当前 IP 被禁止访问！请使用非日本节点！'
                elif 'ray-id' in response:
                    tips = '❌ 访问被 CloudFlare 拦截！'
                elif '/logout' in response:                                         # 已登录，有登出按钮
                    vip_info = '未开通 VIP'
                    tips = f'✅ 连接正常！（{vip_info}）'
                    if input_cookie:
                        if 'icon-diamond' in response or '/v/D16Q5' in response:    # 有钻石图标或者跳到详情页表示已开通
                            vip_info = '已开通 VIP'
                        if cookies != input_cookie:    # 保存cookie
                            tips = f'✅ 连接正常！（{vip_info}）Cookie 已保存！'
                            self.pushButton_save_config_clicked()
                        else:
                            tips = f'✅ 连接正常！（{vip_info}）'

                else:
                    if cookies != input_cookie:
                        tips = '❌ Cookie 无效！请重新填写！'
                    else:
                        tips = '❌ Cookie 无效！已清理！'
                        self.set_javdb_cookie.emit('')
                        self.pushButton_save_config_clicked()

        except Exception as e:
            tips = f'❌ 连接失败！请检查网络或代理设置！ {e}'

        if input_cookie:
            self.Ui.label_javdb_cookie_result.setText(tips)
        # self.Ui.pushButton_check_javdb_cookie.setEnabled(True)
        self.show_log_text(tips.replace('❌', ' ❌ JavDb').replace('✅', ' ✅ JavDb'))
        return tips

    # ======================================================================================检查javbus cookie

    def pushButton_check_javbus_cookie_clicked(self):
        try:
            t = threading.Thread(target=self.check_javbus_cookie)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())

    # ======================================================================================检查javbus cookie

    def check_javbus_cookie(self):
        self.set_javbus_status.emit('⏳ 正在检测中...')

        # self.Ui.pushButton_check_javbus_cookie.setEnabled(False)
        tips = '✅ 连接正常！'
        input_cookie = self.Ui.plainTextEdit_cookie_javbus.toPlainText()
        new_cookie = {'cookie': input_cookie}
        cookies = self.config.get('javbus')
        headers_o = self.config.get('headers')
        headers = {
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
        }
        headers.update(headers_o)
        javbus_website = self.config.get('javbus_website')
        if javbus_website:
            javbus_url = javbus_website + '/FSDSS-660'
        else:
            javbus_url = 'https://javbus.com/FSDSS-660'

        try:
            result, response = get_html(javbus_url, headers=headers, cookies=new_cookie)

            if not result:
                tips = f'❌ 连接失败！请检查网络或代理设置！ {response}'
            elif 'lostpasswd' in response:
                if input_cookie:
                    tips = '❌ Cookie 无效！'
                else:
                    tips = '❌ 当前节点需要 Cookie 才能刮削！请填写 Cookie 或更换节点！'
            elif cookies != input_cookie:
                self.pushButton_save_config_clicked()
                tips = '✅ 连接正常！Cookie 已保存！  '

        except Exception as e:
            tips = f'❌ 连接失败！请检查网络或代理设置！ {e}'

        self.show_log_text(tips.replace('❌', ' ❌ JavBus').replace('✅', ' ✅ JavBus'))
        self.set_javbus_status.emit(tips)
        # self.Ui.pushButton_check_javbus_cookie.setEnabled(True)
        return tips

    # =====================================================================================检测api token
    def check_theporndb_api_token_thread(self):
        try:
            t = threading.Thread(target=self.check_theporndb_api_token)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())

    # ======================================================================================检测api token

    def check_theporndb_api_token(self):
        tips = '✅ 连接正常！'
        headers = self.config.get('headers')
        proxies = self.config.get('proxies')
        timeout = self.config.get('timeout')
        api_token = self.config.get('theporndb_api_token')
        url = 'https://api.metadataapi.net/scenes/hash/8679fcbdd29fa735'
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': get_user_agent(),
        }
        if not api_token:
            tips = '❌ 未填写 API Token，影响欧美刮削！可在「设置」-「网络」添加！'
        else:
            try:
                response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout, verify=False)
                if response.status_code == 401 and 'Unauthenticated' in str(response.text):
                    tips = '❌ API Token 错误！影响欧美刮削！请到「设置」-「网络」中修改。'
                elif response.status_code == 200:
                    if response.json().get('data'):
                        tips = '✅ 连接正常！'
                    else:
                        tips = '❌ 返回数据异常！'
                else:
                    tips = f'❌ 连接失败！请检查网络或代理设置！ {response.status_code} {response.text}'
            except Exception as e:
                tips = f'❌ 连接失败!请检查网络或代理设置！ {e}'
        self.show_log_text(tips.replace('❌', ' ❌ ThePornDB').replace('✅', ' ✅ ThePornDB'))
        return tips

    # ======================================================================================显示正在刮削的文件路径

    def showFilePath(self, file_path):
        if len(file_path) > 55:
            show_file_path = file_path[-50:]
            show_file_path = '..' + show_file_path[show_file_path.find('/'):]
            if len(show_file_path) < 25:
                show_file_path = '..' + file_path[-40:]
        else:
            show_file_path = file_path
        return show_file_path

    # ======================================================================================新建失败输出文件夹

    def creat_failed_folder(self, failed_folder):
        if self.config.get('failed_file_move') == 1 and not os.path.exists(failed_folder):
            try:
                os.makedirs(failed_folder)
            except:
                self.show_traceback_log(traceback.format_exc())
                self.show_log_text(traceback.format_exc())

    # ======================================================================================删除空目录

    def CEF(self, path, file_mode):
        start_time = time.time()
        del_empty_folder = self.config.get('del_empty_folder')
        if del_empty_folder == 0 or file_mode == 'single_file':
            return
        self.set_label_file_path.emit('🗑 正在清理空文件夹，请等待...')
        self.show_log_text(' ⏳ Cleaning empty folders...')
        if 'folder' in self.config.get('no_escape'):
            escape_folder_list = ''
        else:
            escape_folder_list = self.get_movie_path_setting()[3]
        if os.path.exists(path):
            all_info = os.walk(path, topdown=True)
            all_folder_list = []
            for root, dirs, files in all_info:
                if os.path.exists(os.path.join(root, 'skip')):                  # 是否有skip文件
                    dirs[:] = []                                                # 忽略当前文件夹子目录
                    continue
                root = os.path.join(root, '').replace('\\', '/')                # 是否在排除目录
                if root in escape_folder_list:
                    dirs[:] = []                                                # 忽略当前文件夹子目录
                    continue
                dirs_list = [os.path.join(root, dir) for dir in dirs]
                all_folder_list.extend(dirs_list)
            all_folder_list.sort(reverse=True)
            for folder in all_folder_list:
                hidden_file_mac = os.path.join(folder, '.DS_Store')
                hidden_file_windows = os.path.join(folder, 'Thumbs.db')
                if os.path.exists(hidden_file_mac):
                    delete_file(hidden_file_mac)                                # 删除隐藏文件
                if os.path.exists(hidden_file_windows):
                    delete_file(hidden_file_windows)                            # 删除隐藏文件
                try:
                    if not os.listdir(folder):
                        os.rmdir(folder)
                        self.show_log_text(' 🗑 Clean empty folder: ' + self.convert_path(folder))
                except Exception as e:
                    self.show_traceback_log(traceback.format_exc())
                    self.show_log_text(' 🔴 Delete empty folder error: %s' % str(e))

        self.show_log_text(' 🍀 Clean done!(%ss)' % (self.get_used_time(start_time)))
        self.show_log_text('=' * 80)

    def addTreeChild(self, result, filename):
        node = QTreeWidgetItem()
        node.setText(0, filename)
        if result == 'succ':
            self.item_succ.addChild(node)
        else:
            self.item_fail.addChild(node)
        # self.Ui.treeWidget_number.verticalScrollBar().setValue(self.Ui.treeWidget_number.verticalScrollBar().maximum())
        # self.Ui.treeWidget_number.setCurrentItem(node)
        # self.Ui.treeWidget_number.scrollToItem(node)

    def show_list_name(self, filename, result, json_data, real_number=''):
        # 添加树状节点
        self.set_tree_child.emit(result, filename)

        # 解析json_data，以在主界面左侧显示
        if not json_data.get('number'):
            json_data['number'] = real_number
        if not json_data.get('actor'):
            json_data['actor'] = ''
        if not json_data.get('title') or result == 'fail':
            json_data['title'] = json_data['error_info']
        if not json_data.get('outline'):
            json_data['outline'] = ''
        if not json_data.get('tag'):
            json_data['tag'] = ''
        if not json_data.get('release'):
            json_data['release'] = ''
        if not json_data.get('runtime'):
            json_data['runtime'] = ''
        if not json_data.get('director'):
            json_data['director'] = ''
        if not json_data.get('series'):
            json_data['series'] = ''
        if not json_data.get('publisher'):
            json_data['publisher'] = ''
        if not json_data.get('studio'):
            json_data['studio'] = ''
        if not json_data.get('poster_path'):
            json_data['poster_path'] = ''
        if not json_data.get('thumb_path'):
            json_data['thumb_path'] = ''
        if not json_data.get('fanart_path'):
            json_data['fanart_path'] = ''
        if not json_data.get('website'):
            json_data['website'] = ''
        if not json_data.get('source'):
            json_data['source'] = ''
        if not json_data.get('c_word'):
            json_data['c_word'] = ''
        if not json_data.get('cd_part'):
            json_data['cd_part'] = ''
        if not json_data.get('leak'):
            json_data['leak'] = ''
        if not json_data.get('mosaic'):
            json_data['mosaic'] = ''
        if not json_data.get('actor_href'):
            json_data['actor_href'] = ''
        json_data['show_name'] = filename
        self.show_name = filename
        self.add_label_info(json_data)
        self.json_array[filename] = json_data

    # =====================================================================================获取视频文件列表（区分文件夹刮削或单文件刮削）

    def get_movie_list(self, file_mode, movie_path, escape_folder_list):
        movie_list = []
        self.appoint_url = ''
        movie_type = self.config.get('media_type')
        main_mode = self.config.get('main_mode')
        if file_mode == 'default_folder':                                                     # 刮削默认视频目录的文件
            movie_path = self.convert_path(movie_path)
            if not os.path.exists(movie_path):
                self.show_log_text('\n 🔴 Movie folder does not exist!')
            else:
                self.show_log_text(' 🖥 Movie path: ' + movie_path)
                self.show_log_text(' 🔎 Searching all videos, Please wait...')
                self.set_label_file_path.emit('正在遍历待刮削视频目录中的所有视频，请等待...\n %s' % movie_path)
                if 'folder' in self.config.get('no_escape'):
                    escape_folder_list = []
                elif main_mode == 3 or main_mode == 4:
                    escape_folder_list = []
                try:
                    movie_list = self.movie_lists(escape_folder_list, movie_type, movie_path) # 获取所有需要刮削的影片列表
                except:
                    self.show_traceback_log(traceback.format_exc())
                    self.show_log_text(traceback.format_exc())
                count_all = len(movie_list)
                self.show_log_text(' 📺 Find ' + str(count_all) + ' movies')

        elif file_mode == 'single_file':                                        # 刮削单文件（工具页面）
            file_path = self.single_file_path.strip()
            self.appoint_url = self.Ui.lineEdit_appoint_url.text().strip()
            if not os.path.exists(file_path):
                self.show_log_text(' 🔴 Movie file does not exist!')
            else:
                movie_list.append(file_path)                                    # 把文件路径添加到movie_list
                self.show_log_text(' 🖥 File path: ' + file_path)
                if self.appoint_url:
                    self.show_log_text(' 🌐 File url: ' + self.appoint_url)

        return movie_list

    # =====================================================================================获取视频路径设置

    def get_path(self, movie_path, path):
        # 如果没有:并且首字母没有/，这样的目录视为包含在媒体目录下，需要拼接
        if ':' not in path and not re.search('^/', path):                       # 示例：abc 或 aaa/a，这种目录在Windows和mac都视为包含在媒体目录中
            path = os.path.join(movie_path, path).replace('\\', '/')

        # 首字母是/时(不是//)，需要判断Windows路径
        elif re.search('^/[^/]', path):                                         # 示例：/abc/a
            if ':' in movie_path or '//' in movie_path:                         # movie_path有“:”或者“//”表示是windows，/abc这种目录视为包含在媒体目录下
                path = path.strip('/')
                path = os.path.join(movie_path, path).replace('\\', '/')
        if path and path[-1] == '/':
            path = path[:-1]
        return path                                                             # path是路径的情况有 路径包含: 或者开头是//，或者非windows平台开头是/

    # ===================================================================================== 获取平台信息

    def get_platform_info(self):
        self.is_windows = True
        self.is_mac = False
        self.is_nfc = True
        if platform.system() != 'Windows':
            self.is_windows = False
            mac_ver = platform.mac_ver()[0]
            if platform.system() == 'Darwin' and mac_ver:
                self.is_mac = True
                ver_list = mac_ver.split('.')
                if float(ver_list[0] + '.' + ver_list[1]) < 10.12:
                    self.is_nfc = False

    # ===================================================================================== nfd转换nfc

    def nfd2c(self, path):
        # 转换 NFC(mac nfc和nfd都能访问到文件，但是显示的是nfd，这里统一使用nfc，避免各种问题。
        # 日文浊音转换（mac的坑，osx10.12以下使用nfd，以上兼容nfc和nfd，只是显示成了nfd）
        if self.is_nfc:
            new_path = unicodedata.normalize('NFC', path)         # Mac 会拆成两个字符，即 NFD，windwos是 NFC
        else:
            new_path = unicodedata.normalize('NFD', path)         # Mac 会拆成两个字符，即 NFD，windwos是 NFC
        return new_path

    # =====================================================================================获取视频路径设置

    def get_movie_path_setting(self, file_path=''):
        # 先把'\'转成'/'以便判断是路径还是目录
        movie_path = self.config.get('media_path').replace('\\', '/')                                   # 用户设置的扫描媒体路径
        if movie_path == '':                                                                            # 未设置为空时，使用主程序目录
            movie_path = self.main_path
        movie_path = self.nfd2c(movie_path)
        end_folder_name = split_path(movie_path)[1]
        # 用户设置的软链接输出目录
        softlink_path = self.config.get('softlink_path').replace('\\', '/').replace('end_folder_name', end_folder_name)
        # 用户设置的成功输出目录
        success_folder = self.config.get('success_output_folder').replace('\\', '/').replace('end_folder_name', end_folder_name)
        # 用户设置的失败输出目录
        failed_folder = self.config.get('failed_output_folder').replace('\\', '/').replace('end_folder_name', end_folder_name)
        # 用户设置的排除目录
        escape_folder_list = self.config.get('folders').replace('\\', '/').replace('end_folder_name', end_folder_name).replace('，', ',').split(',')
        # 用户设置的剧照副本目录
        extrafanart_folder = self.config.get('extrafanart_folder').replace('\\', '/')

        # 获取路径
        softlink_path = self.convert_path(self.get_path(movie_path, softlink_path))
        success_folder = self.convert_path(self.get_path(movie_path, success_folder))
        failed_folder = self.convert_path(self.get_path(movie_path, failed_folder))
        softlink_path = self.nfd2c(softlink_path)
        success_folder = self.nfd2c(success_folder)
        failed_folder = self.nfd2c(failed_folder)
        extrafanart_folder = self.nfd2c(extrafanart_folder)

        # 获取排除目录完整路径（尾巴添加/）
        escape_folder_new_list = []
        for es in escape_folder_list:                                           # 排除目录可以多个，以，,分割
            es = es.strip(' ')
            if es:
                es = self.get_path(movie_path, es).replace('\\', '/')
                if es[-1] != '/':                                               # 路径尾部添加“/”，方便后面move_list查找时匹配路径
                    es += '/'
                es = self.nfd2c(es)
                escape_folder_new_list.append(es)

        if file_path:
            temp_path = movie_path
            if self.config.get('scrape_softlink_path'):
                temp_path = softlink_path
            if 'first_folder_name' in success_folder or 'first_folder_name' in failed_folder:
                first_folder_name = re.findall(r'^/?([^/]+)/', file_path[len(temp_path):].replace('\\', '/'))
                first_folder_name = first_folder_name[0] if first_folder_name else ''
                success_folder = success_folder.replace('first_folder_name', first_folder_name)
                failed_folder = failed_folder.replace('first_folder_name', first_folder_name)

        return self.convert_path(movie_path), success_folder, failed_folder, escape_folder_new_list, extrafanart_folder, softlink_path

    # =====================================================================================获取文件的相关信息

    def get_file_info(self, file_path, copy_sub=True):
        json_data = {}
        json_data['version'] = self.localversion
        json_data['logs'] = ''
        json_data['req_web'] = ''
        json_data['image_download'] = ''
        json_data['outline_from'] = ''
        json_data['cover_from'] = ''
        json_data['poster_from'] = ''
        json_data['extrafanart_from'] = ''
        json_data['trailer_from'] = ''
        json_data['short_number'] = ''
        json_data['appoint_number'] = ''
        json_data['appoint_url'] = ''
        json_data['website_name'] = ''
        json_data['fields_info'] = ''
        json_data['poster_path'] = ''
        json_data['thumb_path'] = ''
        json_data['fanart_path'] = ''
        json_data['cover_list'] = []
        movie_number = ''
        has_sub = False
        c_word = ''
        cd_part = ''
        destroyed = ''
        leak = ''
        wuma = ''
        youma = ''
        mosaic = ''
        sub_list = []
        cnword_style = str(self.config.get('cnword_style'))

        if self.file_mode == 'search_again':
            temp_number, temp_url, temp_website = self.new_again_dic.get(file_path)
            if temp_number:                                                     # 如果指定了番号，则使用指定番号
                movie_number = temp_number
                json_data['appoint_number'] = temp_number
            if temp_url:
                json_data['appoint_url'] = temp_url
                json_data['website_name'] = temp_website
        elif self.file_mode == 'single_file':                                   # 刮削单文件（工具页面）
            json_data['appoint_url'] = self.appoint_url

        # 获取显示路径
        file_path = file_path.replace('\\', '/')
        file_show_path = self.showFilePath(file_path)

        # 获取文件名
        folder_path, file_full_name = split_path(file_path)                     # 获取去掉文件名的路径、完整文件名（含扩展名）
        file_name, file_ex = os.path.splitext(file_full_name)                   # 获取文件名（不含扩展名）、扩展名(含有.)
        file_name_temp = file_name + '.'
        nfo_old_name = file_name + '.nfo'
        nfo_old_path = os.path.join(folder_path, nfo_old_name)
        file_show_name = file_name

        # 软链接时，获取原身路径(用来查询原身文件目录是否有字幕)
        file_ori_path_no_ex = ''
        if os.path.islink(file_path):
            file_ori_path = read_link(file_path)
            file_ori_path_no_ex = os.path.splitext(file_ori_path)[0]

        try:
            # 清除防屏蔽字符
            prevent_char = self.config.get('prevent_char')
            if prevent_char:
                file_path = file_path.replace(prevent_char, '')
                file_name = file_name.replace(prevent_char, '')

            # 获取番号
            if not movie_number:
                movie_number = get_file_number(file_path)

            # 259LUXU-1111, 非mgstage、avsex去除前面的数字前缀
            temp_n = re.findall(r'\d{3,}([a-zA-Z]+-\d+)', movie_number)
            json_data['short_number'] = temp_n[0] if temp_n else ''

            # 去掉各种乱七八糟的字符
            file_name_cd = remove_escape_string(file_name, '-').replace(movie_number, '-').replace('--', '-').strip()

            # 替换分隔符为-
            cd_char = self.config.get('cd_char')
            if 'underline' in cd_char:
                file_name_cd = file_name_cd.replace('_', '-')
            if 'space' in cd_char:
                file_name_cd = file_name_cd.replace(' ', '-')
            if 'point' in cd_char:
                file_name_cd = file_name_cd.replace('.', '-')
            file_name_cd = file_name_cd.lower() + '.'   # .作为结尾

            # 获取分集(排除‘番号-C’和‘番号C’作为字幕标识的情况)
            # if '-C' in self.config.get('cnword_char') or cnword_style == '-C':
            #     file_name_cd = file_name_cd.replace('-c.', '.')
            # elif 'letter' in cd_char:
            #     file_name_cd = file_name_cd.replace('-c.', '-cd3.')
            # if 'C.' in self.config.get('cnword_char') and file_name_cd.endswith('c.'):
            #     file_name_cd = file_name_cd[:-2] + '.'

            temp_cd = re.compile(r'(vol|case|no|cwp|cwpbd|act)[-\.]?\d+')
            temp_cd_filename = re.sub(temp_cd, '', file_name_cd)
            cd_path_1 = re.findall(r'[-_ .]{1}(cd|part|hd)([0-9]{1,2})', temp_cd_filename)
            cd_path_2 = re.findall(r'-([0-9]{1,2})\.?$', temp_cd_filename)
            cd_path_3 = re.findall(r'(-|\d{2,}|\.)([a-o]{1})\.?$', temp_cd_filename)
            cd_path_4 = re.findall(r'-([0-9]{1})[^a-z0-9]', temp_cd_filename)
            if cd_path_1 and int(cd_path_1[0][1]) > 0:
                cd_part = cd_path_1[0][1]
            elif cd_path_2:
                if len(cd_path_2[0]) == 1 or 'digital' in cd_char:
                    cd_part = str(int(cd_path_2[0]))
            elif cd_path_3 and 'letter' in cd_char:
                letter_list = ['', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
                if cd_path_3[0][1] != 'c' or 'endc' in cd_char:
                    cd_part = letter_list.index(cd_path_3[0][1])
            elif cd_path_4 and 'middle_number' in cd_char:
                cd_part = str(int(cd_path_4[0]))

            # 判断分集命名规则是
            if cd_part:
                cd_name = self.config.get('cd_name')
                if int(cd_part) == 0:
                    cd_part = ''
                elif cd_name == 0:
                    cd_part = '-cd' + str(cd_part)
                elif cd_name == 1:
                    cd_part = '-CD' + str(cd_part)
                else:
                    cd_part = '-' + str(cd_part)

            # 判断是否是马赛克破坏版
            umr_style = str(self.config.get('umr_style'))
            if '-uncensored.' in file_path.lower() or 'umr.' in file_path.lower() or '破解' in file_path or '克破' in file_path or (umr_style and umr_style in file_path) or '-u.' in file_path.lower() or '-uc.' in file_path.lower():
                destroyed = umr_style
                mosaic = '无码破解'

            # 判断是否国产
            if not mosaic:
                if '国产' in file_path or '麻豆' in file_path or '國產' in file_path:
                    mosaic = '国产'
                else:
                    md_list = ['国产', '國產', '麻豆', '传媒', '傳媒', '皇家华人', '皇家華人', '精东', '精東', '猫爪影像', '貓爪影像', '91CM', '91MS', '导演系列', '導演系列', 'MDWP', 'MMZ', 'MLT', 'MSM', 'LAA', 'MXJ', 'SWAG']
                    for each in md_list:
                        if each in file_path:
                            mosaic = '国产'

            # 判断是否流出
            leak_style = str(self.config.get('leak_style'))
            if not mosaic:
                if '流出' in file_path or 'leaked' in file_path.lower() or (leak_style and leak_style in file_path):
                    leak = leak_style
                    mosaic = '无码流出'

            # 判断是否无码
            wuma_style = str(self.config.get('wuma_style'))
            if not mosaic:
                if '无码' in file_path or '無碼' in file_path or '無修正' in file_path or 'uncensored' in file_path.lower() or is_uncensored(movie_number):
                    wuma = wuma_style
                    mosaic = '无码'

            # 判断是否有码
            youma_style = str(self.config.get('youma_style'))
            if not mosaic:
                if '有码' in file_path or '有碼' in file_path:
                    youma = youma_style
                    mosaic = '有码'

            # 查找本地字幕文件
            cnword_list = self.config.get('cnword_char').replace('，', ',').split(',')
            if '-C.' in str(cnword_list).upper():
                cnword_list.append('-C ')
            sub_type_list = self.config.get('sub_type').split('|')              # 本地字幕后缀
            for sub_type in sub_type_list:                                      # 查找本地字幕, 可能多个
                sub_type_chs = '.chs' + sub_type
                sub_path_chs = os.path.join(folder_path, (file_name + sub_type_chs))
                sub_path = os.path.join(folder_path, (file_name + sub_type))
                if os.path.exists(sub_path_chs):
                    sub_list.append(sub_type_chs)
                    c_word = cnword_style                                       # 中文字幕影片后缀
                    has_sub = True
                if os.path.exists(sub_path):
                    sub_list.append(sub_type)
                    c_word = cnword_style                                       # 中文字幕影片后缀
                    has_sub = True
                if file_ori_path_no_ex:                                         # 原身路径
                    sub_path2 = file_ori_path_no_ex + sub_type
                    if os.path.exists(sub_path2):
                        c_word = cnword_style                                   # 中文字幕影片后缀
                        has_sub = True

            # 判断路径名是否有中文字幕字符
            if not has_sub:
                cnword_list.append('-uc.')
                file_name_temp = file_name_temp.upper().replace('CD', '').replace('CARIB', '') # 去掉cd/carib，避免-c误判
                if 'letter' in cd_char and 'endc' in cd_char:
                    file_name_temp = re.sub(r'(-|\d{2,}|\.)C\.$', '.', file_name_temp)

                for each in cnword_list:
                    if each.upper() in file_name_temp:
                        if '無字幕' not in file_path and '无字幕' not in file_path:
                            c_word = cnword_style                                         # 中文字幕影片后缀
                            has_sub = True
                            break

            # 判断nfo中是否有中文字幕、马赛克
            if (not has_sub or not mosaic) and os.path.exists(nfo_old_path):
                try:
                    with open(nfo_old_path, 'r', encoding='utf-8') as f:
                        nfo_content = f.read()
                    if not has_sub:
                        if '>中文字幕</' in nfo_content:
                            c_word = cnword_style                               # 中文字幕影片后缀
                            has_sub = True
                    if not mosaic:
                        if '>无码流出</' in nfo_content or '>無碼流出</' in nfo_content:
                            leak = leak_style
                            mosaic = '无码流出'
                        elif '>无码破解</' in nfo_content or '>無碼破解</' in nfo_content:
                            destroyed = umr_style
                            mosaic = '无码破解'
                        elif '>无码</' in nfo_content or '>無碼</' in nfo_content:
                            wuma = wuma_style
                            mosaic = '无码'
                        elif '>有碼</' in nfo_content or '>有碼</' in nfo_content:
                            youma = youma_style
                            mosaic = '有码'
                        elif '>国产</' in nfo_content or '>國產</' in nfo_content:
                            youma = youma_style
                            mosaic = '国产'
                        elif '>里番</' in nfo_content or '>裏番</' in nfo_content:
                            youma = youma_style
                            mosaic = '里番'
                        elif '>动漫</' in nfo_content or '>動漫</' in nfo_content:
                            youma = youma_style
                            mosaic = '动漫'
                except:
                    pass

            if not has_sub and os.path.exists(nfo_old_path):
                try:
                    with open(nfo_old_path, 'r', encoding='utf-8') as f:
                        nfo_content = f.read()
                    if '<genre>中文字幕</genre>' in nfo_content or '<tag>中文字幕</tag>' in nfo_content:
                        c_word = cnword_style                                   # 中文字幕影片后缀
                        has_sub = True
                except:
                    pass

            # 查找字幕包目录字幕文件
            subtitle_add = self.config.get('subtitle_add')
            if not has_sub and copy_sub and subtitle_add == 'on':
                subtitle_folder = self.config.get('subtitle_folder')
                subtitle_add = self.config.get('subtitle_add')
                if subtitle_add == 'on' and subtitle_folder:                    # 复制字幕开
                    for sub_type in sub_type_list:
                        sub_path_1 = os.path.join(subtitle_folder, (movie_number + cd_part + sub_type))
                        sub_path_2 = os.path.join(subtitle_folder, file_name + sub_type)
                        sub_path_list = [sub_path_1, sub_path_2]
                        sub_file_name = file_name + sub_type
                        if self.config.get('subtitle_add_chs') == 'on':
                            sub_file_name = file_name + '.chs' + sub_type
                            sub_type = '.chs' + sub_type
                        sub_new_path = os.path.join(folder_path, sub_file_name)
                        for sub_path in sub_path_list:
                            if os.path.exists(sub_path):
                                copy_file(sub_path, sub_new_path)
                                json_data['logs'] += "\n\n 🍉 Sub file '%s' copied successfully! " % sub_file_name
                                sub_list.append(sub_type)
                                c_word = cnword_style                               # 中文字幕影片后缀
                                has_sub = True
                                break

            file_show_name = movie_number
            suffix_sort_list = self.config.get('suffix_sort').split(',')
            for each in suffix_sort_list:
                if each == 'mosaic':
                    file_show_name += destroyed + leak + wuma + youma
                elif each == 'cnword':
                    file_show_name += c_word
            file_show_name += cd_part

        except:
            self.show_traceback_log(file_path)
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())
            json_data['logs'] += "\n" + file_path
            json_data['logs'] += "\n" + traceback.format_exc()

        # 车牌前缀
        letters = get_number_letters(movie_number)

        json_data['number'] = movie_number
        json_data['letters'] = letters
        json_data['has_sub'] = has_sub
        json_data['c_word'] = c_word
        json_data['cd_part'] = cd_part
        json_data['destroyed'] = destroyed
        json_data['leak'] = leak
        json_data['wuma'] = wuma
        json_data['youma'] = youma
        json_data['mosaic'] = mosaic
        json_data['4K'] = ''
        json_data['tag'] = ''
        json_data['actor_href'] = ''
        json_data['all_actor'] = ''
        json_data['definition'] = ''
        json_data['file_path'] = self.convert_path(file_path)

        return (json_data, movie_number, folder_path, file_name, file_ex, sub_list, file_show_name, file_show_path)

    # =====================================================================================deepl翻译
    def deepl_trans_thread(self, ls, title, outline, json_data):
        result = ''
        try:
            if title:
                title = deepl.translate(source_language=ls, target_language="ZH", text=title)
            if outline:
                outline = deepl.translate(source_language=ls, target_language="ZH", text=outline)
        except Exception as e:
            result = f'网页接口请求失败! 错误：{e}'
            print(title, outline, f'网页接口请求失败! 错误：{e}')
        self.deepl_result[json_data['file_path']] = (title, outline, result)

    def deepl_translate(self, title, outline, ls='JA', json_data=None):
        deepl_key = self.config.get('deepl_key')
        if not deepl_key:
            if json_data:
                t_deepl = threading.Thread(target=self.deepl_trans_thread, args=(ls, title, outline, json_data))
                t_deepl.setDaemon(True)
                t_deepl.start()
                t_deepl.join(timeout=self.config.get('timeout'))
                t, o, r = title, outline, '翻译失败或超时！'
                if self.deepl_result.get(json_data['file_path']):
                    t, o, r = self.deepl_result[json_data['file_path']]
                return t, o, r
            else:
                try:
                    if title:
                        title = deepl.translate(source_language=ls, target_language="ZH", text=title)
                    if outline:
                        outline = deepl.translate(source_language=ls, target_language="ZH", text=outline)
                    return title, outline, ''
                except Exception as e:
                    return title, outline, f'网页接口请求失败! 错误：{e}'

        deepl_url = 'https://api-free.deepl.com' if ':fx' in deepl_key else 'https://api.deepl.com'
        url = f'{deepl_url}/v2/translate?auth_key={deepl_key}&source_lang={ls}&target_lang=ZH'
        params_title = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'text': title,
        }
        params_outline = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'text': outline,
        }

        if title:
            result, res = post_html(url, data=params_title, json_data=True)
            if not result:
                return title, outline, f'API 接口请求失败！错误：{res}'
            else:
                if 'translations' in res:
                    title = res["translations"][0]["text"]
                else:
                    return title, outline, f'API 接口返回数据异常！返回内容：{res}'
        if outline:
            result, res = post_html(url, data=params_outline, json_data=True)
            if not result:
                return title, outline, f'API 接口请求失败！错误：{res}'
            else:
                if 'translations' in res:
                    outline = res["translations"][0]["text"]
                else:
                    return title, outline, f'API 接口返回数据异常！返回内容：{res}'
        return title, outline, ''

    # =====================================================================================有道翻译

    def youdao_translate(self, title, outline):
        url = 'https://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
        msg = '%s\n%s' % (title, outline)
        lts = str(int(time.time() * 1000))
        salt = lts + str(random.randint(0, 10))
        sign = hashlib.md5(("fanyideskweb" + msg + salt + self.youdaokey).encode('utf-8')).hexdigest()

        data = {
            'i': msg,
            'from': 'AUTO',
            'to': 'zh-CHS',
            'smartresult': 'dict',
            'client': 'fanyideskweb',
            'salt': salt,
            'sign': sign,
            'lts': lts,
            'bv': 'c6b8c998b2cbaa29bd94afc223bc106c',
            'doctype': 'json',
            'version': '2.1',
            'keyfrom': 'fanyi.web',
            'ue': 'UTF-8',
            'typoResult': 'true',
            'action': 'FY_BY_CLICKBUTTION',
        }
        headers = {
            'Cookie': random.choice([
                "OUTFOX_SEARCH_USER_ID=833904829@10.169.0.84",
                "OUTFOX_SEARCH_USER_ID=-10218418@11.136.67.24;",
                "OUTFOX_SEARCH_USER_ID=1989505748@10.108.160.19;",
                "OUTFOX_SEARCH_USER_ID=2072418438@218.82.240.196;",
                "OUTFOX_SEARCH_USER_ID=1768574849@220.181.76.83;",
                "OUTFOX_SEARCH_USER_ID=-2153895048@10.168.8.76;",
            ]),
            'Referer': 'https://fanyi.youdao.com/?keyfrom=dict2.top',
        }
        headers_o = self.config.get('headers')
        headers.update(headers_o)
        result, res = post_html(url, data=data, headers=headers, json_data=True)
        if not result:
            return title, outline, f'请求失败！可能是被封了，可尝试更换代理！错误：{res}'
        else:
            translateResult = res.get('translateResult')
            if not translateResult:
                return title, outline, f'返回数据未找到翻译结果！返回内容：{res}'
            else:
                list_count = len(translateResult)
                if list_count:
                    i = 0
                    if title:
                        i = 1
                        title_result_list = translateResult[0]
                        title_list = [a.get('tgt') for a in title_result_list]
                        title_temp = ''.join(title_list)
                        if title_temp:
                            title = title_temp
                    if outline:
                        outline_temp = ''
                        for j in range(i, list_count):
                            outline_result_list = translateResult[j]
                            outline_list = [a.get('tgt') for a in outline_result_list]
                            outline_temp += ''.join(outline_list) + '\n'
                        outline_temp = outline_temp.strip('\n')
                        if outline_temp:
                            outline = outline_temp
        return title, outline.strip('\n'), ''

    # ===================================================================================== google 翻译

    def google_translate(self, title, outline):
        msg = '%s\n%s' % (title, outline)
        msg_unquote = urllib.parse.unquote(msg)
        url = f'https://translate.google.com/translate_a/single?client=gtx&sl=auto&tl=zh-CN&dt=t&q={msg_unquote}'
        # url = f'https://translate.google.com/translate_a/single?client=at&sl=auto&tl=zh-CN&dt=t&q={msg_unquote}'
        result, response = get_html(url, json_data=True)
        if not result:
            return title, outline, f'请求失败！可能是被封了，可尝试更换代理！错误：{response}'
        else:
            try:
                result = []
                original = []
                for each in response[0]:
                    result.append(each[0])
                    original.append(each[1])
                if not title:
                    outline = ''.join(result)
                elif not outline:
                    title = ''.join(result)
                else:
                    for i in range(len(original)):
                        if len(''.join(original[:i + 1])) > len(title):
                            break
                    title = ''.join(result[:i])
                    outline = ''.join(result[i:])
                return title.strip(), outline.strip(), ''
            except Exception as e:
                return title, outline, f'返回数据格式异常！返回内容：{response} 错误：{e}'

    # =====================================================================================后台加载langid

    def load_langid(self):
        try:
            t = threading.Thread(target=self.load_langid_thread)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())

    def load_langid_thread(self):
        langid.classify('ok')

    # =====================================================================================获取有道翻译key

    def get_youdao_key(self):
        try:
            t = threading.Thread(target=self.get_youdao_key_thread)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())

    def get_youdao_key_thread(self):
        # 获取 js url
        js_url = ''
        youdao_url = 'https://fanyi.youdao.com'
        result, req = get_html(youdao_url)
        if result:
            # https://shared.ydstatic.com/fanyi/newweb/v1.1.11/scripts/newweb/fanyi.min.js
            url_temp = re.search(r'(https://shared.ydstatic.com/fanyi/newweb/.+/scripts/newweb/fanyi.min.js)', req)
            if url_temp:
                js_url = url_temp.group(1)
        if not js_url:
            self.show_log_text(' ⚠️ youdao js url get failed!!!')
            self.show_traceback_log('youdao js url get failed!!!')
            return

        # 请求 js url ，获取 youdao key
        result, req = get_html(js_url)
        try:
            self.youdaokey = re.search(r'(?<="fanyideskweb" \+ e \+ i \+ ")[^"]+', req).group(0)
            # sign: n.md5("fanyideskweb" + e + i + "Ygy_4c=r#e#4EX^NUGUc5")
        except:
            try:
                self.youdaokey = re.search(r'(?<="fanyideskweb"\+e\+i\+")[^"]+', req).group(0)
            except Exception as e:
                self.youdaokey = "Ygy_4c=r#e#4EX^NUGUc5"
                self.show_traceback_log(traceback.format_exc())
                self.show_traceback_log('🔴 有道翻译接口key获取失败！' + str(e))
                self.show_log_text(traceback.format_exc())
                self.show_log_text(' 🔴 有道翻译接口key获取失败！请检查网页版有道是否正常！%s' % str(e))
        return self.youdaokey

    # =====================================================================================创建成功输出目录

    def creat_folder(self, json_data, folder_new_path, file_path, file_new_path, thumb_new_path_with_filename, poster_new_path_with_filename):
        '''判断是否创建文件夹，目标文件是否有重复文件。file_new_path是最终路径'''

        soft_link = self.config.get('soft_link')
        main_mode = self.config.get('main_mode')
        json_data['dont_move_movie'] = False        # 不需要移动和重命名视频
        json_data['del_file_path'] = False          # 在 move movie 时需要删除自己，自己是软链接，目标是原始文件
        dont_creat_folder = False                   # 不需要创建文件夹

        # 正常模式、视频模式时，软连接关，成功后不移动文件开时，这时不创建文件夹
        if main_mode < 3 and soft_link == 0 and self.config.get('success_file_move') == 0:
            dont_creat_folder = True

        # 更新模式、读取模式，选择更新c文件时，不创建文件夹
        if self.config.get('main_mode') > 2 and self.config.get('update_mode') == 'c':
            dont_creat_folder = True

        # 如果不需要创建文件夹，当不重命名时，直接返回
        if dont_creat_folder:
            if self.config.get('success_file_rename') == 0:
                json_data['dont_move_movie'] = True
                return True

        # 如果不存在目标文件夹，则创建文件夹
        elif not os.path.isdir(folder_new_path):
            try:
                os.makedirs(folder_new_path)
                json_data['logs'] += "\n 🍀 Folder done! (new)"
                return True
            except Exception as e:
                if not os.path.exists(folder_new_path):
                    json_data['logs'] += '\n 🔴 Failed to create folder! \n    ' + str(e)
                    if len(folder_new_path) > 250:
                        json_data['logs'] += '\n    可能是目录名过长！！！建议限制目录名长度！！！越小越好！！！'
                        json_data['error_info'] = '创建文件夹失败！可能是目录名过长！'
                    else:
                        json_data['logs'] += '\n    请检查是否有写入权限！'
                        json_data['error_info'] = '创建文件夹失败！请检查是否有写入权限！'
                    return False

        # 判断是否有重复文件（Windows、Mac大小写不敏感）
        convert_file_path = self.convert_path(file_path).lower()
        convert_file_new_path = self.convert_path(file_new_path).lower()

        # 当目标文件存在，是软链接时
        if os.path.islink(file_new_path):
            # 路径相同，是自己
            if convert_file_path == convert_file_new_path:
                json_data['dont_move_movie'] = True
            # 路径不同，删掉目标文件即可（不验证是否真实路径了，太麻烦）
            else:
                # 在移动时删除即可。delete_file(file_new_path)
                # 创建软链接前需要删除目标路径文件
                pass
            return True

        # 当目标文件存在，不是软链接时
        elif os.path.exists(file_new_path):
            # 待刮削的文件不是软链接
            if not os.path.islink(file_path):
                # 如果路径相同，则代表已经在成功文件夹里，不是重复文件（大小写不敏感）
                if convert_file_path == convert_file_new_path:
                    json_data['dont_move_movie'] = True
                    if os.path.exists(thumb_new_path_with_filename):
                        json_data['thumb_path'] = thumb_new_path_with_filename
                    if os.path.exists(poster_new_path_with_filename):
                        json_data['poster_path'] = poster_new_path_with_filename
                    return True

                # 路径不同
                else:
                    try:
                        # 当都指向同一个文件时(此处路径不能用小写，因为Linux大小写敏感)
                        if os.stat(file_path).st_ino == os.stat(file_new_path).st_ino:
                            # 硬链接开时，不需要处理
                            if self.config.get('soft_link') == 2:
                                json_data['dont_move_movie'] = True
                            # 非硬链接模式，删除目标文件
                            else:
                                # 在移动时删除即可。delete_file(file_new_path)
                                pass
                            return True
                    except:
                        pass

                    # 路径不同，当指向不同文件时
                    json_data['title'] = "Success folder already exists a same name file!"
                    json_data['error_info'] = f"Success folder already exists a same name file! \n ❗️ Current file: {file_path} \n ❗️ Success folder already exists file: {file_new_path} "
                    return False

            # 待刮削文件是软链接
            else:
                # 看待刮削文件真实路径，路径相同，是同一个文件
                real_file_path = read_link(file_path)
                if self.convert_path(real_file_path).lower() == convert_file_new_path:
                    # 非软硬链接时，标记删除待刮削文件自身
                    if self.config.get('soft_link') == 0:
                        json_data['del_file_path'] = True
                    # 软硬链接时，标记不处理
                    else:
                        json_data['dont_move_movie'] = True
                    return True
                # 路径不同，是两个文件
                else:
                    json_data['title'] = "Success folder already exists a same name file!"
                    json_data['error_info'] = f"Success folder already exists a same name file! \n ❗️ Current file is symlink file: {file_path} \n ❗️ real file: {real_file_path} \n ❗️ Success folder already exists another real file: {file_new_path} "
                    return False

        # 目标文件不存在时
        return True

    # =====================================================================================处理翻译

    def get_yesjav_title(self, json_data, movie_number):
        yesjav_url = 'http://www.yesjav.info/search.asp?q=%s&' % movie_number
        movie_title = ''
        result, response = get_html(yesjav_url)
        if result and response:
            parser = etree.HTMLParser(encoding="utf-8")
            html = etree.HTML(response, parser)
            movie_title = html.xpath('//dl[@id="zi"]/p/font/a/b[contains(text(), $number)]/../../a[contains(text(), "中文字幕")]/text()', number=movie_number)
            if movie_title:
                movie_title = movie_title[0]
                char_list = [
                    '[高清] (中文字幕)',
                    '[高清 (中文字幕)',
                    ' (中文字幕)',
                    ' (中文字幕)',
                    '[高清中文字幕]',
                    '[高清中文字幕',
                    '高清中文字幕]',
                    '【高清中文字幕】',
                    '[高清]',
                    '无码流出版',
                    '无码流出',
                    '无码破解版',
                    '无码破解',
                    'TOKYO-HOT-',
                    '韩文转译版',
                    '独家听译版',
                    '完整版',
                    '特别版',
                    '完全版',
                    '时间轴修复版',
                    '导演剪辑最终版',
                    '堂友',
                ]
                for each in char_list:
                    movie_title = movie_title.replace(each, '')
                movie_title = movie_title.strip()
        return movie_title

    # =====================================================================================处理翻译

    def translate_title_outline(self, json_data, movie_number):
        title_language = self.config.get('title_language')
        title_translate = self.config.get('title_translate')
        outline_language = self.config.get('outline_language')
        outline_translate = self.config.get('outline_translate')
        translate_by = self.config.get('translate_by')
        if title_language == 'jp' and outline_language == 'jp':
            return
        trans_title = ''
        trans_outline = ''
        title_sehua = self.config.get('title_sehua')
        title_sehua_zh = self.config.get('title_sehua_zh')
        title_yesjav = self.config.get('title_yesjav')
        json_data_title_language = langid.classify(json_data['title'])[0]

        # 处理title
        if title_language != 'jp':
            movie_title = ''

            # 匹配本地高质量标题(色花标题数据)
            if title_sehua_zh == 'on' or (json_data_title_language == 'ja' and title_sehua == 'on'):
                start_time = time.time()
                try:
                    movie_title = self.sehua_title_data.get(movie_number)
                except:
                    self.show_traceback_log(traceback.format_exc())
                    self.show_log_text(traceback.format_exc())
                if movie_title:
                    json_data['title'] = movie_title
                    json_data['logs'] += '\n 🌸 Sehua title done!(%ss)' % (self.get_used_time(start_time))

            # 匹配网络高质量标题（yesjav， 可在线更新）
            if not movie_title and title_yesjav == 'on' and json_data_title_language == 'ja':
                start_time = time.time()
                movie_title = self.get_yesjav_title(json_data, movie_number)
                if movie_title and langid.classify(movie_title)[0] != 'ja':
                    json_data['title'] = movie_title
                    json_data['logs'] += '\n 🆈 Yesjav title done!(%ss)' % (self.get_used_time(start_time))

            # 使用json_data数据
            if not movie_title and title_translate == 'on' and json_data_title_language == 'ja':
                trans_title = json_data['title']

        # 处理outline
        if json_data['outline'] and outline_language != 'jp':
            if outline_translate == 'on' and langid.classify(json_data['outline'])[0] == 'ja':
                trans_outline = json_data['outline']

        # 翻译
        if self.translate_by_list:
            if (trans_title and title_translate == 'on') or (trans_outline and outline_translate == 'on'):
                start_time = time.time()
                translate_by_list = self.translate_by_list.copy()
                if not json_data['cd_part']:
                    random.shuffle(translate_by_list)
                for each in translate_by_list:
                    if each == 'youdao':                                                # 使用有道翻译
                        t, o, r = self.youdao_translate(trans_title, trans_outline)
                    elif each == 'google':                                              # 使用 google 翻译
                        t, o, r = self.google_translate(trans_title, trans_outline)
                    else:                                                               # 使用deepl翻译
                        t, o, r = self.deepl_translate(trans_title, trans_outline, 'JA', json_data)
                    if r:
                        json_data['logs'] += f'\n 🔴 Translation failed!({each.capitalize()})({self.get_used_time(start_time)}s) Error: {r}'
                    else:
                        if t:
                            json_data['title'] = t
                        if o:
                            json_data['outline'] = o
                        json_data['logs'] += f'\n 🍀 Translation done!({each.capitalize()})({self.get_used_time(start_time)}s)'
                        json_data['outline_from'] = each
                        break
                else:
                    translate_by = translate_by.strip(',').capitalize()
                    json_data['logs'] += f'\n 🔴 Translation failed! {translate_by} 不可用！({self.get_used_time(start_time)}s)'

        # 简繁转换
        if title_language == 'zh_cn':
            json_data['title'] = zhconv.convert(json_data['title'], 'zh-cn')
        elif title_language == 'zh_tw':
            json_data['title'] = zhconv.convert(json_data['title'], 'zh-hant')
            json_data['mosaic'] = zhconv.convert(json_data['mosaic'], 'zh-hant')

        if outline_language == 'zh_cn':
            json_data['outline'] = zhconv.convert(json_data['outline'], 'zh-cn')
        elif outline_language == 'zh_tw':
            json_data['outline'] = zhconv.convert(json_data['outline'], 'zh-hant')

        return json_data

    # =====================================================================================thumb、poster、fanart 删除冗余的图片
    def pic_some_deal(self, json_data, thumb_final_path, fanart_final_path):
        # 不保存thumb时，清理 thumb
        if 'thumb' not in self.config.get('download_files') and 'thumb' not in self.config.get('keep_files'):
            if os.path.exists(fanart_final_path):
                self.file_done_dic[json_data['number']].update({'thumb': fanart_final_path})
            else:
                self.file_done_dic[json_data['number']].update({'thumb': ''})
            if os.path.exists(thumb_final_path):
                delete_file(thumb_final_path)
                json_data['logs'] += "\n 🍀 Thumb delete done!"

    # =====================================================================================处理本地已存在的thumb、poster、fanart、nfo

    def deal_old_files(self, json_data, folder_old_path, folder_new_path, file_path, file_new_path, thumb_new_path_with_filename, poster_new_path_with_filename, fanart_new_path_with_filename, nfo_new_path, file_ex, poster_final_path, thumb_final_path, fanart_final_path):
        # 转换文件路径
        file_path = self.convert_path(file_path)
        nfo_old_path = file_path.replace(file_ex, '.nfo')
        nfo_new_path = self.convert_path(nfo_new_path)
        folder_old_path = self.convert_path(folder_old_path)
        folder_new_path = self.convert_path(folder_new_path)
        extrafanart_old_path = self.convert_path(os.path.join(folder_old_path, 'extrafanart'))
        extrafanart_new_path = self.convert_path(os.path.join(folder_new_path, 'extrafanart'))
        extrafanart_folder = self.config.get('extrafanart_folder')
        extrafanart_copy_old_path = self.convert_path(os.path.join(folder_old_path, extrafanart_folder))
        extrafanart_copy_new_path = self.convert_path(os.path.join(folder_new_path, extrafanart_folder))
        trailer_name = self.config.get('trailer_name')
        trailer_old_folder_path = self.convert_path(os.path.join(folder_old_path, 'trailers'))
        trailer_new_folder_path = self.convert_path(os.path.join(folder_new_path, 'trailers'))
        trailer_old_file_path = self.convert_path(os.path.join(trailer_old_folder_path, 'trailer.mp4'))
        trailer_new_file_path = self.convert_path(os.path.join(trailer_new_folder_path, 'trailer.mp4'))
        trailer_old_file_path_with_filename = self.convert_path(nfo_old_path.replace('.nfo', '-trailer.mp4'))
        trailer_new_file_path_with_filename = self.convert_path(nfo_new_path.replace('.nfo', '-trailer.mp4'))
        theme_videos_old_path = self.convert_path(os.path.join(folder_old_path, 'backdrops'))
        theme_videos_new_path = self.convert_path(os.path.join(folder_new_path, 'backdrops'))
        extrafanart_extra_old_path = self.convert_path(os.path.join(folder_old_path, 'behind the scenes'))
        extrafanart_extra_new_path = self.convert_path(os.path.join(folder_new_path, 'behind the scenes'))

        # 图片旧路径转换路径
        poster_old_path_with_filename = file_path.replace(file_ex, '-poster.jpg')
        thumb_old_path_with_filename = file_path.replace(file_ex, '-thumb.jpg')
        fanart_old_path_with_filename = file_path.replace(file_ex, '-fanart.jpg')
        poster_old_path_no_filename = self.convert_path(os.path.join(folder_old_path, 'poster.jpg'))
        thumb_old_path_no_filename = self.convert_path(os.path.join(folder_old_path, 'thumb.jpg'))
        fanart_old_path_no_filename = self.convert_path(os.path.join(folder_old_path, 'fanart.jpg'))
        file_path_list = set([nfo_old_path, nfo_new_path, thumb_old_path_with_filename, thumb_old_path_no_filename, thumb_new_path_with_filename, thumb_final_path, poster_old_path_with_filename, poster_old_path_no_filename, poster_new_path_with_filename, poster_final_path, fanart_old_path_with_filename, fanart_old_path_no_filename, fanart_new_path_with_filename, fanart_final_path, trailer_old_file_path_with_filename, trailer_new_file_path_with_filename])
        folder_path_list = set([extrafanart_old_path, extrafanart_new_path, extrafanart_copy_old_path, extrafanart_copy_new_path, trailer_old_folder_path, trailer_new_folder_path, theme_videos_old_path, theme_videos_new_path, extrafanart_extra_old_path, extrafanart_extra_new_path])

        # 视频模式进行清理
        main_mode = self.config.get('main_mode')
        if main_mode == 2 and 'sort_del' in self.config.get('switch_on'):
            for each in file_path_list:
                if os.path.exists(each):
                    delete_file(each)
            for each in folder_path_list:
                if os.path.isdir(each):
                    shutil.rmtree(each, ignore_errors=True)
            return

        # 非视频模式，将本地已有的图片、剧照等文件，按照命名规则，重新命名和移动。这个环节仅应用设置-命名设置，没有应用设置-下载的设置
        # 抢占图片的处理权
        single_folder_catched = False                                        # 剧照、剧照副本、主题视频 这些单文件夹的处理权，他们只需要处理一次
        pic_final_catched = False                                            # 最终图片（poster、thumb、fanart）的处理权
        with self.lock:
            if thumb_new_path_with_filename not in self.pic_catch_set:
                if thumb_final_path != thumb_new_path_with_filename:
                    if thumb_final_path not in self.pic_catch_set:           # 不带文件名的图片的下载权利（下载权利只给它一个）
                        self.pic_catch_set.add(thumb_final_path)
                        pic_final_catched = True
                else:
                    pic_final_catched = True                                 # 带文件名的图片，下载权利给每一个。（如果有一个下载好了，未下载的可以直接复制）
            # 处理 extrafanart、extrafanart副本、主题视频、附加视频
            if pic_final_catched and extrafanart_new_path not in self.extrafanart_deal_set:
                self.extrafanart_deal_set.add(extrafanart_new_path)
                single_folder_catched = True
        '''
        需要考虑旧文件分集情况（带文件名、不带文件名）、旧文件不同扩展名情况，他们如何清理或保留
        需要考虑新文件分集情况（带文件名、不带文件名）
        需要考虑分集同时刮削如何节省流量
        需要考虑分集带文件名图片是否会有重复水印问题
        '''

        # poster_marked True 不加水印，避免二次加水印,；poster_exists 是不是存在本地图片
        json_data['poster_marked'] = True
        json_data['thumb_marked'] = True
        json_data['fanart_marked'] = True
        poster_exists = True
        thumb_exists = True
        fanart_exists = True
        trailer_exists = True

        # 软硬链接模式，不处理旧的图片
        if self.config.get('soft_link') != 0:
            return pic_final_catched, single_folder_catched

        '''
        保留图片或删除图片说明：
        图片保留的前提条件：非整理模式，并且满足（在保留名单 或 读取模式 或 图片已下载）。此时不清理 poster.jpg thumb.jpg fanart.jpg（在del_noname_pic中清理）。
        图片保留的命名方式：保留时会保留为最终路径 和 文件名-thumb.jpg (thumb 需要复制一份为 文件名-thumb.jpg，避免 poster 没有，要用 thumb 裁剪，或者 fanart 要复制 thumb)
        图片下载的命名方式：新下载的则都保存为 文件名-thumb.jpg（因为多分集同时下载为 thumb.jpg 时会冲突）
        图片下载的下载条件：如果最终路径有内容，则不下载。如果 文件名-thumb.jpg 有内容，也不下载。
        图片下载的复制条件：如果不存在 文件名-thumb.jpg，但是存在 thumb.jpg，则复制 thumb.jpg 为 文件名-thumb.jpg
        最终的图片处理：在最终的 rename pic 环节，如果最终路径有内容，则删除非最终路径的内容；如果最终路径没内容，表示图片是刚下载的，要改成最终路径。
        '''

        # poster 处理：寻找对应文件放到最终路径上。这样避免刮削失败时，旧的图片被删除
        done_poster_path = self.file_done_dic.get(json_data['number']).get('poster')
        done_poster_path_copy = True
        try:
            # 图片最终路径等于已下载路径时，图片是已下载的，不需要处理
            if done_poster_path and os.path.exists(done_poster_path) and split_path(done_poster_path)[0] == split_path(poster_final_path)[0]:          # 如果存在已下载完成的文件，尝试复制
                done_poster_path_copy = False   # 标记未复制！此处不复制，在poster download中复制
            elif os.path.exists(poster_final_path):
                pass    # windows、mac大小写不敏感，暂不解决
            elif poster_new_path_with_filename != poster_final_path and os.path.exists(poster_new_path_with_filename):
                move_file(poster_new_path_with_filename, poster_final_path)
            elif poster_old_path_with_filename != poster_final_path and os.path.exists(poster_old_path_with_filename):
                move_file(poster_old_path_with_filename, poster_final_path)
            elif poster_old_path_no_filename != poster_final_path and os.path.exists(poster_old_path_no_filename):
                move_file(poster_old_path_no_filename, poster_final_path)
            else:
                poster_exists = False

            if poster_exists:
                self.file_done_dic[json_data['number']].update({'local_poster': poster_final_path})
                # 清理旧图片
                if poster_old_path_with_filename.lower() != poster_final_path.lower() and os.path.exists(poster_old_path_with_filename):
                    delete_file(poster_old_path_with_filename)
                if poster_old_path_no_filename.lower() != poster_final_path.lower() and os.path.exists(poster_old_path_no_filename):
                    delete_file(poster_old_path_no_filename)
                if poster_new_path_with_filename.lower() != poster_final_path.lower() and os.path.exists(poster_new_path_with_filename):
                    delete_file(poster_new_path_with_filename)
            elif self.file_done_dic[json_data['number']]['local_poster']:
                copy_file(self.file_done_dic[json_data['number']]['local_poster'], poster_final_path)

        except:
            self.show_log_text(traceback.format_exc())

        # thumb 处理：寻找对应文件放到最终路径上。这样避免刮削失败时，旧的图片被删除
        done_thumb_path = self.file_done_dic.get(json_data['number']).get('thumb')
        done_thumb_path_copy = True
        try:
            # 图片最终路径等于已下载路径时，图片是已下载的，不需要处理
            if done_thumb_path and os.path.exists(done_thumb_path) and split_path(done_thumb_path)[0] == split_path(thumb_final_path)[0]:
                done_thumb_path_copy = False # 标记未复制！此处不复制，在 thumb download中复制
            elif os.path.exists(thumb_final_path):
                pass
            elif thumb_new_path_with_filename != thumb_final_path and os.path.exists(thumb_new_path_with_filename):
                move_file(thumb_new_path_with_filename, thumb_final_path)
            elif thumb_old_path_with_filename != thumb_final_path and os.path.exists(thumb_old_path_with_filename):
                move_file(thumb_old_path_with_filename, thumb_final_path)
            elif thumb_old_path_no_filename != thumb_final_path and os.path.exists(thumb_old_path_no_filename):
                move_file(thumb_old_path_no_filename, thumb_final_path)
            else:
                thumb_exists = False

            if thumb_exists:
                self.file_done_dic[json_data['number']].update({'local_thumb': thumb_final_path})
                # 清理旧图片
                if thumb_old_path_with_filename.lower() != thumb_final_path.lower() and os.path.exists(thumb_old_path_with_filename):
                    delete_file(thumb_old_path_with_filename)
                if thumb_old_path_no_filename.lower() != thumb_final_path.lower() and os.path.exists(thumb_old_path_no_filename):
                    delete_file(thumb_old_path_no_filename)
                if thumb_new_path_with_filename.lower() != thumb_final_path.lower() and os.path.exists(thumb_new_path_with_filename):
                    delete_file(thumb_new_path_with_filename)
            elif self.file_done_dic[json_data['number']]['local_thumb']:
                copy_file(self.file_done_dic[json_data['number']]['local_thumb'], thumb_final_path)

        except:
            self.show_log_text(traceback.format_exc())

        # fanart 处理：寻找对应文件放到最终路径上。这样避免刮削失败时，旧的图片被删除
        done_fanart_path = self.file_done_dic.get(json_data['number']).get('fanart')
        done_fanart_path_copy = True
        try:
            # 图片最终路径等于已下载路径时，图片是已下载的，不需要处理
            if done_fanart_path and os.path.exists(done_fanart_path) and split_path(done_fanart_path)[0] == split_path(fanart_final_path)[0]:
                done_fanart_path_copy = False # 标记未复制！此处不复制，在 fanart download中复制
            elif os.path.exists(fanart_final_path):
                pass
            elif fanart_new_path_with_filename != fanart_final_path and os.path.exists(fanart_new_path_with_filename):
                move_file(fanart_new_path_with_filename, fanart_final_path)
            elif fanart_old_path_with_filename != fanart_final_path and os.path.exists(fanart_old_path_with_filename):
                move_file(fanart_old_path_with_filename, fanart_final_path)
            elif fanart_old_path_no_filename != fanart_final_path and os.path.exists(fanart_old_path_no_filename):
                move_file(fanart_old_path_no_filename, fanart_final_path)
            else:
                fanart_exists = False

            if fanart_exists:
                self.file_done_dic[json_data['number']].update({'local_fanart': fanart_final_path})
                # 清理旧图片
                if fanart_old_path_with_filename.lower() != fanart_final_path.lower() and os.path.exists(fanart_old_path_with_filename):
                    delete_file(fanart_old_path_with_filename)
                if fanart_old_path_no_filename.lower() != fanart_final_path.lower() and os.path.exists(fanart_old_path_no_filename):
                    delete_file(fanart_old_path_no_filename)
                if fanart_new_path_with_filename.lower() != fanart_final_path.lower() and os.path.exists(fanart_new_path_with_filename):
                    delete_file(fanart_new_path_with_filename)
            elif self.file_done_dic[json_data['number']]['local_fanart']:
                copy_file(self.file_done_dic[json_data['number']]['local_fanart'], fanart_final_path)

        except:
            self.show_log_text(traceback.format_exc())

        # 更新图片地址
        json_data['poster_path'] = poster_final_path if poster_exists and done_poster_path_copy else ''
        json_data['thumb_path'] = thumb_final_path if thumb_exists and done_thumb_path_copy else ''
        json_data['fanart_path'] = fanart_final_path if fanart_exists and done_fanart_path_copy else ''

        # nfo 处理
        try:
            if os.path.exists(nfo_new_path):
                if nfo_old_path.lower() != nfo_new_path.lower() and os.path.exists(nfo_old_path):
                    delete_file(nfo_old_path)
            elif nfo_old_path != nfo_new_path and os.path.exists(nfo_old_path):
                move_file(nfo_old_path, nfo_new_path)
        except:
            self.show_log_text(traceback.format_exc())

        # trailer
        if trailer_name == 1:                                               # 预告片名字不含视频文件名
            # trailer最终路径等于已下载路径时，trailer是已下载的，不需要处理
            if os.path.exists(trailer_new_file_path):
                if os.path.exists(trailer_old_file_path_with_filename):
                    delete_file(trailer_old_file_path_with_filename)
                elif os.path.exists(trailer_new_file_path_with_filename):
                    delete_file(trailer_new_file_path_with_filename)
            elif trailer_old_file_path != trailer_new_file_path and os.path.exists(trailer_old_file_path):
                if not os.path.exists(trailer_new_folder_path):
                    os.makedirs(trailer_new_folder_path)
                move_file(trailer_old_file_path, trailer_new_file_path)
            elif os.path.exists(trailer_new_file_path_with_filename):
                if not os.path.exists(trailer_new_folder_path):
                    os.makedirs(trailer_new_folder_path)
                move_file(trailer_new_file_path_with_filename, trailer_new_file_path)
            elif os.path.exists(trailer_old_file_path_with_filename):
                if not os.path.exists(trailer_new_folder_path):
                    os.makedirs(trailer_new_folder_path)
                move_file(trailer_old_file_path_with_filename, trailer_new_file_path)

            # 删除旧文件夹，用不到了
            if trailer_old_folder_path != trailer_new_folder_path and os.path.exists(trailer_old_folder_path):
                shutil.rmtree(trailer_old_folder_path, ignore_errors=True)
            # 删除带文件名文件，用不到了
            if os.path.exists(trailer_old_file_path_with_filename):
                delete_file(trailer_old_file_path_with_filename)
            if trailer_new_file_path_with_filename != trailer_old_file_path_with_filename and os.path.exists(trailer_new_file_path_with_filename):
                delete_file(trailer_new_file_path_with_filename)
        else:
            # 目标文件带文件名
            if os.path.exists(trailer_new_file_path_with_filename):
                if trailer_old_file_path_with_filename != trailer_new_file_path_with_filename and os.path.exists(trailer_old_file_path_with_filename):
                    delete_file(trailer_old_file_path_with_filename)
            elif trailer_old_file_path_with_filename != trailer_new_file_path_with_filename and os.path.exists(trailer_old_file_path_with_filename):
                move_file(trailer_old_file_path_with_filename, trailer_new_file_path_with_filename)
            elif os.path.exists(trailer_old_file_path):
                move_file(trailer_old_file_path, trailer_new_file_path_with_filename)
            elif trailer_new_file_path != trailer_old_file_path and os.path.exists(trailer_new_file_path):
                move_file(trailer_new_file_path, trailer_new_file_path_with_filename)
            else:
                trailer_exists = False

            if trailer_exists:
                self.file_done_dic[json_data['number']].update({'local_trailer': trailer_new_file_path_with_filename})
                # 删除旧、新文件夹，用不到了(分集使用local trailer复制即可)
                if os.path.exists(trailer_old_folder_path):
                    shutil.rmtree(trailer_old_folder_path, ignore_errors=True)
                if trailer_new_folder_path != trailer_old_folder_path and os.path.exists(trailer_new_folder_path):
                    shutil.rmtree(trailer_new_folder_path, ignore_errors=True)
                # 删除带文件名旧文件，用不到了
                if trailer_old_file_path_with_filename != trailer_new_file_path_with_filename and os.path.exists(trailer_old_file_path_with_filename):
                    delete_file(trailer_old_file_path_with_filename)
            else:
                local_trailer = self.file_done_dic.get(json_data['number']).get('local_trailer')
                if local_trailer and os.path.exists(local_trailer):
                    copy_file(local_trailer, trailer_new_file_path_with_filename)

        # 处理 extrafanart、extrafanart副本、主题视频、附加视频
        if single_folder_catched:
            # 处理 extrafanart
            try:
                if os.path.exists(extrafanart_new_path):
                    if extrafanart_old_path.lower() != extrafanart_new_path.lower() and os.path.exists(extrafanart_old_path):
                        shutil.rmtree(extrafanart_old_path, ignore_errors=True)
                elif os.path.exists(extrafanart_old_path):
                    move_file(extrafanart_old_path, extrafanart_new_path)
            except:
                self.show_log_text(traceback.format_exc())

            # extrafanart副本
            try:
                if os.path.exists(extrafanart_copy_new_path):
                    if extrafanart_copy_old_path.lower() != extrafanart_copy_new_path.lower() and os.path.exists(extrafanart_copy_old_path):
                        shutil.rmtree(extrafanart_copy_old_path, ignore_errors=True)
                elif os.path.exists(extrafanart_copy_old_path):
                    move_file(extrafanart_copy_old_path, extrafanart_copy_new_path)
            except:
                self.show_log_text(traceback.format_exc())

            # 主题视频
            if os.path.exists(theme_videos_new_path):
                if theme_videos_old_path.lower() != theme_videos_new_path.lower() and os.path.exists(theme_videos_old_path):
                    shutil.rmtree(theme_videos_old_path, ignore_errors=True)
            elif os.path.exists(theme_videos_old_path):
                move_file(theme_videos_old_path, theme_videos_new_path)

            # 附加视频
            if os.path.exists(extrafanart_extra_new_path):
                if extrafanart_extra_old_path.lower() != extrafanart_extra_new_path.lower() and os.path.exists(extrafanart_extra_old_path):
                    shutil.rmtree(extrafanart_extra_old_path, ignore_errors=True)
            elif os.path.exists(extrafanart_extra_old_path):
                move_file(extrafanart_extra_old_path, extrafanart_extra_new_path)

        return pic_final_catched, single_folder_catched

    # =====================================================================================获取VR高清封面图片
    def get_big_pic_by_google(self, pic_url, poster=False):
        url, pic_size, big_pic = self.get_pic_by_google(pic_url)
        if not poster:
            if big_pic or (pic_size and int(pic_size[0]) > 800 and int(pic_size[1]) > 539):   # cover 有大图时或者图片高度 > 800 时使用该图片
                return url, pic_size
            return '', ''
        if url and int(pic_size[1]) < 1000:                                                 # poster，图片高度小于 1500，重新搜索一次
            url, pic_size, big_pic = self.get_pic_by_google(url)
        if pic_size and (big_pic or 'blogger.googleusercontent.com' in url or int(pic_size[1]) > 560):     # poster，大图或高度 > 560 时，使用该图片
            return url, pic_size
        else:
            return '', ''

    def get_pic_by_google(self, pic_url):
        google_keyused = self.config.get('google_keyused')
        google_keyword = self.config.get('google_keyword')
        req_url = f'https://www.google.com/searchbyimage?sbisrc=2&image_url={pic_url}'
        # req_url = f'https://lens.google.com/uploadbyurl?url={pic_url}&hl=zh-CN&re=df&ep=gisbubu'
        result, response = get_html(req_url, keep=False)

        big_pic = True
        if result:
            url_list = re.findall(r'a href="([^"]+isz:l[^"]+)">', response)
            url_list_middle = re.findall(r'a href="([^"]+isz:m[^"]+)">', response)
            if not url_list and url_list_middle:
                url_list = url_list_middle
                big_pic = False
            if url_list:
                req_url = 'https://www.google.com' + url_list[0].replace('amp;', '')
                result, response = get_html(req_url, keep=False)
                if result:
                    url_list = re.findall(r'\["(http[^"]+)",(\d{3,4}),(\d{3,4})\],[^[]', response)
                    # 优先下载放前面
                    new_url_list = []
                    for each_url in url_list.copy():
                        if int(each_url[2]) < 800:
                            url_list.remove(each_url)

                    for each_key in google_keyused:
                        for each_url in url_list.copy():
                            if each_key in each_url[0]:
                                new_url_list.append(each_url)
                                url_list.remove(each_url)
                    # 只下载关时，追加剩余地址
                    if 'goo_only' not in self.config.get('download_hd_pics'):
                        new_url_list += url_list
                    # 解析地址
                    for each in new_url_list:
                        temp_url = each[0]
                        for temp_keyword in google_keyword:
                            if temp_keyword in temp_url:
                                break
                        else:
                            h = int(each[1])
                            w = int(each[2])
                            if w > h and w / h < 1.4:                           # thumb 被拉高时跳过
                                continue

                            p_url = temp_url.encode('utf-8').decode('unicode_escape') # url中的Unicode字符转义，不转义，url请求会失败
                            if 'm.media-amazon.com' in p_url:
                                p_url = re.sub(r'\._[_]?AC_[^\.]+\.', '.', p_url)
                                pic_size = get_imgsize(p_url)
                                if pic_size[0]:
                                    return p_url, pic_size, big_pic
                            else:
                                url = check_url(p_url)
                                if url:
                                    pic_size = (w, h)
                                    return url, pic_size, big_pic
        return '', '', ''

    # =====================================================================================获取高清封面图片 amazon

    def get_big_pic_by_amazon(self, json_data, originaltitle_amazon, actor_amazon):
        if not originaltitle_amazon or not actor_amazon:
            return ''
        hd_pic_url = ''
        originaltitle_amazon = re.sub(r'【.*】', '', originaltitle_amazon)
        originaltitle_amazon_list = [originaltitle_amazon]
        for originaltitle_amazon in originaltitle_amazon_list:
            # 需要两次urlencode，nb_sb_noss表示无推荐来源
            url_search = 'https://www.amazon.co.jp/black-curtain/save-eligibility/black-curtain?returnUrl=/s?k=' + urllib.parse.quote_plus(urllib.parse.quote_plus(originaltitle_amazon.replace('&', ' ') + ' [DVD]')) + '&ref=nb_sb_noss'
            result, html_search = get_amazon_data(url_search)

            # 没有结果，尝试拆词，重新搜索
            if 'キーワードが正しく入力されていても一致する商品がない場合は、別の言葉をお試しください。' in html_search and len(originaltitle_amazon_list) < 2:
                for each_name in originaltitle_amazon.split(' '):
                    if each_name not in originaltitle_amazon_list:
                        if len(each_name) > 8 or (not each_name.encode('utf-8').isalnum() and len(each_name) > 4) and each_name not in actor_amazon:
                            originaltitle_amazon_list.append(each_name)
                continue

            # 有结果时，检查结果
            if result and html_search:
                html = etree.fromstring(html_search, etree.HTMLParser())
                originaltitle_amazon_half = self.convert_half(originaltitle_amazon)
                originaltitle_amazon_half_no_actor = originaltitle_amazon_half

                # 标题缩短匹配（如无结果，则使用缩小标题再次搜索）
                if '検索に一致する商品はありませんでした。' in html_search and len(originaltitle_amazon_list) < 2:
                    short_originaltitle_amazon = html.xpath('//div[@class="a-section a-spacing-base a-spacing-top-base"]/span[@class="a-size-base a-color-base"]/text()')
                    if short_originaltitle_amazon:
                        short_originaltitle_amazon = short_originaltitle_amazon[0].upper().replace(' DVD', '')
                        if short_originaltitle_amazon in originaltitle_amazon.upper():
                            originaltitle_amazon_list.append(short_originaltitle_amazon)
                            short_originaltitle_amazon = self.convert_half(short_originaltitle_amazon)
                            if short_originaltitle_amazon in originaltitle_amazon_half:
                                originaltitle_amazon_half = short_originaltitle_amazon
                    for each_name in originaltitle_amazon.split(' '):
                        if each_name not in originaltitle_amazon_list:
                            if len(each_name) > 8 or (not each_name.encode('utf-8').isalnum() and len(each_name) > 4) and each_name not in actor_amazon:
                                originaltitle_amazon_list.append(each_name)

                # 标题不带演员名匹配
                for each_actor in actor_amazon:
                    originaltitle_amazon_half_no_actor = originaltitle_amazon_half_no_actor.replace(each_actor.upper(), '')

                # 检查搜索结果
                actor_result_list = set()
                title_result_list = []
                # s-card-container s-overflow-hidden aok-relative puis-wide-grid-style puis-wide-grid-style-t2 puis-expand-height puis-include-content-margin puis s-latency-cf-section s-card-border
                pic_card = html.xpath('//div[@class="a-section a-spacing-base"]')
                for each in pic_card:   # tek-077
                    pic_ver_list = each.xpath('div//a[@class="a-size-base a-link-normal s-underline-text s-underline-link-text s-link-style a-text-bold"]/text()')
                    pic_title_list = each.xpath('div//span[@class="a-size-base-plus a-color-base a-text-normal"]/text()')
                    pic_url_list = each.xpath('div//div[@class="a-section aok-relative s-image-square-aspect"]/img/@src')
                    detail_url_list = each.xpath('div//a[@class="a-link-normal s-no-outline"]/@href')
                    if len(pic_ver_list) and len(pic_url_list) and (len(pic_title_list) and len(detail_url_list)):
                        pic_ver = pic_ver_list[0]                                            # 图片版本
                        pic_title = pic_title_list[0]                                        # 图片标题
                        pic_url = pic_url_list[0]                                            # 图片链接
                        detail_url = detail_url_list[0]                                      # 详情页链接（有时带有演员名）
                        if pic_ver in ['DVD', 'Software Download'] and '.jpg' in pic_url:      # 无图时是.gif
                            pic_title_half = self.convert_half(re.sub(r'【.*】', '', pic_title))
                            pic_title_half_no_actor = pic_title_half
                            for each_actor in actor_amazon:
                                pic_title_half_no_actor = pic_title_half_no_actor.replace(each_actor, '')

                            # 判断标题是否命中
                            if originaltitle_amazon_half[:15] in pic_title_half or originaltitle_amazon_half_no_actor[:15] in pic_title_half_no_actor:
                                detail_url = urllib.parse.unquote_plus(detail_url)
                                temp_title = re.findall(r'(.+)keywords=', detail_url)
                                temp_detail_url = temp_title[0] + pic_title_half if temp_title else detail_url + pic_title_half
                                url = re.sub(r'\._[_]?AC_[^\.]+\.', '.', pic_url)

                                # 判断演员是否在标题里，避免同名标题误匹配 MOPP-023
                                for each_actor in actor_amazon:
                                    if each_actor in temp_detail_url:
                                        actor_result_list.add(url)
                                        if '写真付き' not in pic_title:     # NACR-206
                                            w, h = get_imgsize(url)
                                            if w > 600 or not w:
                                                hd_pic_url = url
                                                return hd_pic_url
                                            else:
                                                json_data['poster'] = pic_url    # 用于 Google 搜图
                                                json_data['poster_from'] = 'Amazon'
                                        break
                                else:
                                    title_result_list.append([url, 'https://www.amazon.co.jp' + detail_url])

                # 命中演员有多个结果时返回最大的（不等于1759/1758）
                if len(actor_result_list):
                    pic_w = 0
                    for each in actor_result_list:
                        new_pic_w = get_imgsize(each)[0]
                        if new_pic_w > pic_w:
                            if new_pic_w >= 1770 or (new_pic_w < 1750 and new_pic_w > 600):    # 不要小图 FCDSS-001，截短的图（1758/1759）
                                pic_w = new_pic_w
                                hd_pic_url = each
                            else:
                                json_data['poster'] = each    # 用于 Google 搜图
                                json_data['poster_from'] = 'Amazon'

                    if hd_pic_url:
                        return hd_pic_url

                # 当搜索结果命中了标题，没有命中演员时，尝试去详情页获取演员信息
                elif len(title_result_list) <= 20 and 's-pagination-item s-pagination-next s-pagination-button s-pagination-separator' not in html_search:
                    for each in title_result_list[:4]:
                        try:
                            url_new = 'https://www.amazon.co.jp' + re.findall(r'(/dp/[^/]+)', each[1])[0]
                        except:
                            url_new = each[1]
                        result, html_detail = get_amazon_data(url_new)
                        if result and html_detail:
                            html = etree.fromstring(html_detail, etree.HTMLParser())
                            detail_actor = str(html.xpath('//span[@class="author notFaded"]/a/text()')).replace(' ', '')
                            detail_info_1 = str(html.xpath('//ul[@class="a-unordered-list a-vertical a-spacing-mini"]//text()')).replace(' ', '')
                            detail_info_2 = str(html.xpath('//div[@id="detailBulletsWrapper_feature_div"]//text()')).replace(' ', '')
                            detail_info_3 = str(html.xpath('//div[@id="productDescription"]//text()')).replace(' ', '')
                            all_info = detail_actor + detail_info_1 + detail_info_2 + detail_info_3
                            for each_actor in actor_amazon:
                                if each_actor in all_info:
                                    w, h = get_imgsize(each[0])
                                    if w > 720 or not w:
                                        return each[0]
                                    else:
                                        json_data['poster'] = each[0]    # 用于 Google 搜图
                                        json_data['poster_from'] = 'Amazon'

                # 有很多结果时（有下一页按钮），加演员名字重新搜索
                if 's-pagination-item s-pagination-next s-pagination-button s-pagination-separator' in html_search or len(title_result_list) > 5:
                    amazon_orginaltitle_actor = json_data.get('amazon_orginaltitle_actor')
                    if amazon_orginaltitle_actor and amazon_orginaltitle_actor not in originaltitle_amazon:
                        originaltitle_amazon_list.append(f'{originaltitle_amazon} {amazon_orginaltitle_actor}')

        return hd_pic_url

    # =====================================================================================获取高清封面图片

    def get_big_poster(self, json_data):
        start_time = time.time()

        # 未勾选下载高清图poster时，返回
        download_hd_pics = self.config.get('download_hd_pics')
        if 'poster' not in download_hd_pics:
            return json_data

        # 如果有大图时，直接下载
        if json_data.get('poster_big') and get_imgsize(json_data['poster'])[1] > 600:
            json_data['image_download'] = True
            json_data['logs'] += f"\n 🖼 HD Poster found! ({json_data['poster_from']})({self.get_used_time(start_time)}s)"
            return json_data

        # 初始化数据
        number = json_data.get('number')
        poster_url = json_data.get('poster')
        hd_pic_url = ''
        poster_width = 0

        # 通过原标题去 amazon 查询
        if 'amazon' in download_hd_pics and json_data['mosaic'] in ['有码', '有碼', '流出', '无码破解', '無碼破解', '里番', '裏番', '动漫', '動漫']:
            hd_pic_url = self.get_big_pic_by_amazon(json_data, json_data['originaltitle_amazon'], json_data['actor_amazon'])
            if hd_pic_url:
                json_data['poster'] = hd_pic_url
                json_data['poster_from'] = 'Amazon'
            if json_data['poster_from'] == 'Amazon':
                json_data['image_download'] = True

        # 通过番号去 官网 查询获取稍微大一些的封面图，以便去 Google 搜索
        if not hd_pic_url and 'official' in download_hd_pics and 'official' not in self.config.get('website_set') and json_data['poster_from'] != 'Amazon':
            letters = json_data['letters'].upper()
            official_url = self.config.get('official_websites').get(letters)
            if official_url:
                url_search = official_url + '/search/list?keyword=' + number.replace('-', '')
                result, html_search = get_html(url_search)
                if result:
                    poster_url_list = re.findall(r'img class="c-main-bg lazyload" data-src="([^"]+)"', html_search)
                    if poster_url_list:
                        # 使用官网图作为封面去 google 搜索
                        poster_url = poster_url_list[0]
                        json_data['poster'] = poster_url
                        json_data['poster_from'] = official_url.split('.')[-2].replace('https://', '')
                        # vr作品或者官网图片高度大于500时，下载封面图开
                        if 'VR' in number.upper() or get_imgsize(poster_url)[1] > 500:
                            json_data['image_download'] = True

        # 使用google以图搜图，放在最后是因为有时有错误，比如 kawd-943
        poster_url = json_data.get('poster')
        if not hd_pic_url and poster_url and 'google' in download_hd_pics and json_data['poster_from'] != 'theporndb':
            hd_pic_url, poster_size = self.get_big_pic_by_google(poster_url, poster=True)
            if hd_pic_url:
                if 'prestige' in json_data['poster'] or json_data['poster_from'] == 'Amazon':
                    poster_width = get_imgsize(poster_url)[0]
                if poster_size[0] > poster_width:
                    json_data['poster'] = hd_pic_url
                    json_data['poster_size'] = poster_size
                    pic_domain = re.findall(r'://([^/]+)', hd_pic_url)[0]
                    json_data['poster_from'] = f'Google({pic_domain})'

        # 如果找到了高清链接，则替换
        if hd_pic_url:
            json_data['image_download'] = True
            json_data['logs'] += "\n 🖼 HD Poster found! (%s)(%ss)" % (json_data['poster_from'], self.get_used_time(start_time))

        return json_data

    # =====================================================================================获取高清背景图

    def get_big_thumb(self, json_data):
        '''
        获取背景大图：
        1，官网图片
        2，Amazon 图片
        3，Google 搜图
        '''
        start_time = time.time()
        download_hd_pics = self.config.get('download_hd_pics')
        if 'thumb' not in download_hd_pics:
            return json_data
        number = json_data['number']
        letters = json_data['letters']
        number_lower_line = number.lower()
        number_lower_no_line = number_lower_line.replace('-', '')
        thumb_width = 0

        # faleno.jp 番号检查，都是大图，返回即可
        if json_data['cover_from'] in ['faleno', 'dahlia']:
            if json_data['cover']:
                json_data['logs'] += "\n 🖼 HD Thumb found! (%s)(%ss)" % (json_data['cover_from'], self.get_used_time(start_time))
            json_data['poster_big'] = True
            return json_data

        # prestige 图片有的是大图，需要检测图片分辨率
        elif json_data['cover_from'] in ['prestige', 'mgstage']:
            if json_data['cover']:
                thumb_width, h = get_imgsize(json_data['cover'])

        # 片商官网查询
        elif 'official' in download_hd_pics:
            # faleno.jp 番号检查
            if re.findall(r'F[A-Z]{2}SS', number):
                req_url = 'https://faleno.jp/top/works/%s/' % number_lower_no_line
                result, response = get_html(req_url)
                if result:
                    temp_url = re.findall(r'src="((https://cdn.faleno.net/top/wp-content/uploads/[^_]+_)([^?]+))\?output-quality=', response)
                    if temp_url:
                        json_data['cover'] = temp_url[0][0]
                        json_data['poster'] = temp_url[0][1] + '2125.jpg'
                        json_data['cover_from'] = 'faleno'
                        json_data['poster_from'] = 'faleno'
                        json_data['poster_big'] = True
                        trailer_temp = re.findall(r'class="btn09"><a class="pop_sample" href="([^"]+)', response)
                        if trailer_temp:
                            json_data['trailer'] = trailer_temp[0]
                            json_data['trailer_from'] = 'faleno'
                        json_data['logs'] += "\n 🖼 HD Thumb found! (faleno)(%ss)" % self.get_used_time(start_time)
                        return json_data

            # km-produce.com 番号检查
            number_letter = letters.lower()
            kmp_key = ['vrkm', 'mdtm', 'mkmp', 'savr', 'bibivr', 'scvr', 'slvr', 'averv', 'kbvr', 'cbikmv']
            prestige_key = ['abp', 'abw', 'aka', 'prdvr', 'pvrbst', 'sdvr', 'docvr']
            if number_letter in kmp_key:
                req_url = f'https://km-produce.com/img/title1/{number_lower_line}.jpg'
                real_url = check_url(req_url)
                if real_url:
                    json_data['cover'] = real_url
                    json_data['cover_from'] = 'km-produce'
                    json_data['logs'] += "\n 🖼 HD Thumb found! (km-produce)(%ss)" % (self.get_used_time(start_time))
                    return json_data

            # www.prestige-av.com 番号检查
            elif number_letter in prestige_key:
                number_num = re.findall(r'\d+', number)[0]
                if number_letter == 'abw' and int(number_num) > 280:
                    pass
                else:
                    req_url = f'https://www.prestige-av.com/api/media/goods/prestige/{number_letter}/{number_num}/pb_{number_lower_line}.jpg'
                    if number_letter == 'docvr':
                        req_url = f'https://www.prestige-av.com/api/media/goods/doc/{number_letter}/{number_num}/pb_{number_lower_line}.jpg'
                    if get_imgsize(req_url)[0] >= 800:
                        json_data['cover'] = req_url
                        json_data['poster'] = req_url.replace('/pb_', '/pf_')
                        json_data['cover_from'] = 'prestige'
                        json_data['poster_from'] = 'prestige'
                        json_data['poster_big'] = True
                        json_data['logs'] += "\n 🖼 HD Thumb found! (prestige)(%ss)" % (self.get_used_time(start_time))
                        return json_data

        # 使用google以图搜图
        pic_url = json_data.get('cover')
        if 'google' in download_hd_pics:
            if pic_url and json_data['cover_from'] != 'theporndb':
                thumb_url, cover_size = self.get_big_pic_by_google(pic_url)
                if thumb_url and cover_size[0] > thumb_width:
                    json_data['cover_size'] = cover_size
                    pic_domain = re.findall(r'://([^/]+)', thumb_url)[0]
                    json_data['cover_from'] = f'Google({pic_domain})'
                    json_data['cover'] = thumb_url
                    json_data['logs'] += "\n 🖼 HD Thumb found! (%s)(%ss)" % (json_data['cover_from'], self.get_used_time(start_time))

        return json_data

    # =====================================================================================演员名映射输出处理

    def get_actor_data(self, actor):
        # 初始化数据
        actor_data = {
            'zh_cn': actor,
            'zh_tw': actor,
            'jp': actor,
            'keyword': [actor],
            'href': '',
            'has_name': False,
        }

        # 查询映射表
        xml_actor = self.get_actor_mapping_data()
        if len(xml_actor):
            actor_name = ',%s,' % actor.upper()
            for each in self.full_half_char:
                actor_name = actor_name.replace(each[0], each[1])
            actor_ob = xml_actor.xpath('//a[contains(translate(@keyword, "abcdefghijklmnopqrstuvwxyzａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ・", "ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ·"), $name)]', name=actor_name)
            if actor_ob:
                actor_ob = actor_ob[0]
                actor_data['zh_cn'] = actor_ob.get('zh_cn')
                actor_data['zh_tw'] = actor_ob.get('zh_tw')
                actor_data['jp'] = actor_ob.get('jp')
                actor_data['keyword'] = actor_ob.get('keyword').strip(',').split(',')
                actor_data['href'] = actor_ob.get('href')
                actor_data['has_name'] = True
        return actor_data

    # =====================================================================================信息名映射输出处理

    def get_info_data(self, info):
        # 初始化数据
        info_data = {
            'zh_cn': info,
            'zh_tw': info,
            'jp': info,
            'keyword': [info],
            'has_name': False,
        }

        # 查询映射表
        xml_info = self.get_info_mapping_data()
        if len(xml_info):
            info_name = ',%s,' % info.upper()
            for each in self.full_half_char:
                info_name = info_name.replace(each[0], each[1])
            info_ob = xml_info.xpath('//a[contains(translate(@keyword, "abcdefghijklmnopqrstuvwxyzａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ・", "ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ·"), $name)]', name=info_name)
            if info_ob:
                info_ob = info_ob[0]
                info_data['zh_cn'] = info_ob.get('zh_cn').replace('删除', '')
                info_data['zh_tw'] = info_ob.get('zh_tw').replace('删除', '')
                info_data['jp'] = info_ob.get('jp').replace('删除', '')
                info_data['keyword'] = info_ob.get('keyword').strip(',').split(',')
                info_data['has_name'] = True
        return info_data

    # =====================================================================================演员名映射输出处理

    def translate_actor(self, json_data):
        # 网络请求真实的演员名字
        actor_realname = self.config.get('actor_realname')
        mosaic = json_data['mosaic']
        number = json_data['number']

        # 非读取模式，勾选了使用真实名字时; 读取模式，勾选了允许更新真实名字时
        if actor_realname == 'on':
            start_time = time.time()
            if mosaic != '国产' and (number.startswith('FC2') or number.startswith('SIRO') or re.search(r'\d{3,}[A-Z]{3,}-', number)):
                result, temp_actor = get_actorname(json_data['number'])
                if result:
                    json_data['actor'] = temp_actor
                    json_data['logs'] += f"\n 👩🏻 Av-wiki done! Actor's real Japanese name is '{temp_actor}' ({self.get_used_time(start_time)}s)"
                else:
                    json_data['logs'] += f"\n 🔴 Av-wiki failed! {temp_actor} ({self.get_used_time(start_time)}s)"

        # 如果不映射，返回
        if self.config.get('actor_translate') == 'off':
            return json_data

        # 映射表数据加载失败，返回
        xml_actor = self.get_actor_mapping_data()
        if len(xml_actor) == 0:
            return json_data

        # 未知演员，返回
        actor = json_data['actor']
        if actor == self.config.get('actor_no_name'):
            return json_data

        # 查询映射表
        actor_list = actor.split(',')
        actor_new_list = []
        actor_href_list = []
        actor_language = self.config.get('actor_language')
        for each_actor in actor_list:
            if each_actor:
                actor_data = self.get_actor_data(each_actor)
                new_actor = actor_data.get(actor_language)
                if actor_language == 'zh_cn':
                    new_actor = zhconv.convert(new_actor, 'zh-cn')
                elif actor_language == 'zh_tw':
                    new_actor = zhconv.convert(new_actor, 'zh-hant')
                if new_actor not in actor_new_list:
                    actor_new_list.append(new_actor)
                    if actor_data.get('href'):
                        actor_href_list.append(actor_data.get('href'))
        json_data['actor'] = ','.join(actor_new_list)

        # 演员主页
        if actor_href_list:
            json_data['actor_href'] = actor_href_list[0]
        elif json_data['actor']:
            json_data['actor_href'] = 'https://javdb.com/search?f=actor&q=' + \
                urllib.parse.quote(
                    json_data['actor'].split(',')[0])  # url转码，避免乱码

        return json_data

    # =====================================================================================标签去重去空

    def remove_repeat(self, a: str):
        if a:                                                                   # 转列表去空去重
            list1 = a.split(',')                                                # 转列表
            list2 = list(set(list1))                                            # 去重
            list3 = [each for each in list2 if each]                            # 去空
            list3.sort(key=list1.index)                                         # 排序（保持原顺序）
            a = ','.join(map(str, list3))                                       # 转字符串
        return a

    # =====================================================================================信息（tag、series、studio、publisher、director）映射输出处理

    def translate_info(self, json_data):
        xml_info = self.info_mapping_data
        if len(xml_info) == 0:
            return json_data
        tag_translate = self.config.get('tag_translate')
        series_translate = self.config.get('series_translate')
        studio_translate = self.config.get('studio_translate')
        publisher_translate = self.config.get('publisher_translate')
        director_translate = self.config.get('director_translate')
        tag_language = self.config.get('tag_language')
        series_language = self.config.get('series_language')
        studio_language = self.config.get('studio_language')
        publisher_language = self.config.get('publisher_language')
        director_language = self.config.get('director_language')
        fields_rule = self.config.get('fields_rule')

        tag_include = self.config.get('tag_include')
        tag = json_data['tag']
        remove_key = ['HD高画质', 'HD高畫質', '高画质', '高畫質', '無碼流出', '无码流出', '無碼破解', '无码破解', '無碼片', '无码片', '有碼片', '有码片', '無碼', '无码', '有碼', '有码', '流出', '国产', '國產']
        for each_key in remove_key:
            tag = tag.replace(each_key, '')

        # 映射tag并且存在xml_info时，处理tag映射
        if tag_translate == 'on':
            tag_list = re.split(r'[,，]', tag)
            tag_new = []
            for each_info in tag_list:
                if each_info:                                                   # 为空时会多出来一个
                    info_data = self.get_info_data(each_info)
                    each_info = info_data.get(tag_language)
                    if each_info and each_info not in tag_new:
                        tag_new.append(each_info)
            tag = ','.join(tag_new)

        # tag去重/去空/排序
        tag = self.remove_repeat(tag)

        # 添加演员
        if 'actor' in tag_include and json_data['actor']:
            tag = json_data['actor'] + ',' + tag
            tag = tag.strip(',')

        # 添加番号前缀
        letters = json_data['letters']
        if 'letters' in tag_include and letters and letters != '未知车牌':
            # 去除素人番号前缀数字
            if 'del_num' in fields_rule:
                temp_n = re.findall(r'\d{3,}([a-zA-Z]+-\d+)', json_data['number'])
                if temp_n:
                    letters = get_number_letters(temp_n[0])
                    json_data['letters'] = letters
                    json_data['number'] = temp_n[0]
            tag = letters + ',' + tag
            tag = tag.strip(',')

        # 添加字幕、马赛克信息到tag中
        has_sub = json_data['has_sub']
        mosaic = json_data['mosaic']
        if has_sub and 'cnword' in tag_include:
            tag += ',中文字幕'
        if mosaic and 'mosaic' in tag_include:
            tag += ',' + mosaic

        # 添加系列、制作、发行信息到tag中
        series = json_data['series']
        studio = json_data['studio']
        publisher = json_data['publisher']
        director = json_data['director']
        if not studio and publisher:
            studio = publisher
        if not publisher and studio:
            publisher = studio

        # 系列
        if series:                                                              # 为空时会匹配所有
            if series_translate == 'on':                                        # 映射
                info_data = self.get_info_data(series)
                series = info_data.get(series_language)
            if series and 'series' in tag_include:                              # 写nfo
                nfo_tag_series = self.config.get('nfo_tag_series').replace('series', series)
                if nfo_tag_series:
                    tag += f',{nfo_tag_series}'

        # 片商
        if studio:
            if studio_translate == 'on':
                info_data = self.get_info_data(studio)
                studio = info_data.get(studio_language)
            if studio and 'studio' in tag_include:
                nfo_tag_studio = self.config.get('nfo_tag_studio').replace('studio', studio)
                if nfo_tag_studio:
                    tag += f',{nfo_tag_studio}'

        # 发行
        if publisher:
            if publisher_translate == 'on':
                info_data = self.get_info_data(publisher)
                publisher = info_data.get(publisher_language)
            if publisher and 'publisher' in tag_include:
                nfo_tag_publisher = self.config.get('nfo_tag_publisher').replace('publisher', publisher)
                if nfo_tag_publisher:
                    tag += f',{nfo_tag_publisher}'

        # 导演
        if director:
            if director_translate == 'on':
                info_data = self.get_info_data(director)
                director = info_data.get(director_language)

        if tag_language == 'zh_cn':
            tag = zhconv.convert(tag, 'zh-cn')
        else:
            tag = zhconv.convert(tag, 'zh-hant')

        # tag去重/去空/排序
        tag = self.remove_repeat(tag)

        json_data['tag'] = tag.strip(',')
        json_data['series'] = series
        json_data['studio'] = studio
        json_data['publisher'] = publisher
        json_data['director'] = director
        return json_data

    # =====================================================================================读取nfo

    def get_nfo_data(self, json_data, file_path, movie_number):
        local_nfo_path = os.path.splitext(file_path)[0] + '.nfo'
        local_nfo_name = split_path(local_nfo_path)[1]
        file_folder = split_path(file_path)[0]
        json_data['title'] = ''
        json_data['originaltitle'] = ''
        json_data['originaltitle_amazon'] = ''
        # json_data['number'] = ''
        json_data['actor'] = ''
        json_data['actor_amazon'] = []
        json_data['outline'] = ''
        json_data['originalplot'] = ''
        json_data['tag'] = ''
        json_data['release'] = ''
        json_data['year'] = ''
        json_data['runtime'] = ''
        json_data['score'] = ''
        json_data['series'] = ''
        json_data['director'] = ''
        json_data['publisher'] = ''
        json_data['studio'] = ''
        json_data['source'] = 'nfo'
        json_data['website'] = ''
        json_data['cover'] = ''
        json_data['poster'] = ''
        json_data['extrafanart'] = ''
        json_data['trailer'] = ''
        json_data['image_download'] = ''
        json_data['image_cut'] = ''
        json_data['log_info'] = ''
        json_data['error_info'] = ''
        json_data['req_web'] = local_nfo_path
        json_data['fields_info'] = ''
        json_data['poster_from'] = 'local'
        json_data['cover_from'] = 'local'
        json_data['fanart_from'] = 'local'
        json_data['extrafanart_from'] = 'local'
        json_data['trailer_from'] = 'local'
        # json_data['mosaic'] = ''
        json_data['poster_path'] = ''
        json_data['thumb_path'] = ''
        json_data['fanart_path'] = ''
        json_data['only_tag_list'] = ''
        json_data['wanted'] = ''
        json_data['cover_list'] = []

        if not os.path.exists(local_nfo_path):
            json_data['error_info'] = 'nfo文件不存在'
            json_data['req_web'] = 'do_not_update_json_data_dic'
            json_data['outline'] = split_path(file_path)[1]
            json_data['tag'] = file_path
            return False, json_data

        with open(local_nfo_path, 'r', encoding='utf-8') as f:
            content = f.read().replace('<![CDATA[', '').replace(']]>', '')

        parser = etree.HTMLParser(encoding="utf-8")
        xml_nfo = etree.HTML(content.encode('utf-8'), parser)

        title = ''.join(xml_nfo.xpath('//title/text()'))
        # 获取不到标题，表示xml错误，重新刮削
        if not title:
            json_data['error_info'] = 'nfo文件损坏'
            json_data['req_web'] = 'do_not_update_json_data_dic'
            json_data['outline'] = split_path(file_path)[1]
            json_data['tag'] = file_path
            return False, json_data
        title = re.sub(r' (CD)?\d{1}$', '', title)

        # 获取其他数据
        originaltitle = ''.join(xml_nfo.xpath('//originaltitle/text()'))
        if json_data['appoint_number']:
            number = json_data['appoint_number']
        else:
            number = ''.join(xml_nfo.xpath('//num/text()'))
            if not number:
                number = movie_number
        letters = get_number_letters(number)
        title = title.replace(number + ' ', '').strip()
        originaltitle = originaltitle.replace(number + ' ', '').strip()
        originaltitle_amazon = originaltitle
        if originaltitle:
            for key, value in self.special_word.items():
                originaltitle_amazon = originaltitle_amazon.replace(value, key)
        actor = ','.join(xml_nfo.xpath('//actor/name/text()'))
        originalplot = ''.join(xml_nfo.xpath('//originalplot/text()'))
        outline = ''
        temp_outline = re.findall(r'<plot>(.+)</plot>', content)
        if not temp_outline:
            temp_outline = re.findall(r'<outline>(.+)</outline>', content)
        if temp_outline:
            outline = temp_outline[0]
            if '<br>  <br>' in outline:
                temp_from = re.findall(r'<br>  <br>由 .+ 提供翻译', outline)
                if temp_from:
                    outline = outline.replace(temp_from[0], '')
                    json_data['outline_from'] = temp_from[0].replace('<br>  <br>由 ', '').replace(' 提供翻译', '')
                outline = outline.replace(originalplot, '').replace('<br>  <br>', '')
        tag = ','.join(xml_nfo.xpath('//tag/text()'))
        release = ''.join(xml_nfo.xpath('//release/text()'))
        if not release:
            release = ''.join(xml_nfo.xpath('//releasedate/text()'))
        if not release:
            release = ''.join(xml_nfo.xpath('//premiered/text()'))
        if release:
            release = release.replace('/', '-').strip('. ')
            if len(release) < 10:
                release_list = re.findall(r'(\d{4})-(\d{1,2})-(\d{1,2})', release)
                if release_list:
                    r_year, r_month, r_day = release_list[0]
                    r_month = '0' + r_month if len(r_month) == 1 else r_month
                    r_day = '0' + r_day if len(r_day) == 1 else r_day
                    release = r_year + '-' + r_month + '-' + r_day
        json_data['release'] = release
        year = ''.join(xml_nfo.xpath('//year/text()'))
        runtime = ''.join(xml_nfo.xpath('//runtime/text()'))
        score = ''.join(xml_nfo.xpath('//rating/text()'))
        if not score:
            score = ''.join(xml_nfo.xpath('//rating/text()'))
            if score:
                score = str(int(score) / 10)
        series = ''.join(xml_nfo.xpath('//series/text()'))
        director = ''.join(xml_nfo.xpath('//director/text()'))
        studio = ''.join(xml_nfo.xpath('//studio/text()'))
        if not studio:
            studio = ''.join(xml_nfo.xpath('//maker/text()'))
        publisher = ''.join(xml_nfo.xpath('//publisher/text()'))
        if not publisher:
            publisher = ''.join(xml_nfo.xpath('//label/text()'))
        cover = ''.join(xml_nfo.xpath('//cover/text()')).replace('&amp;', '&')
        poster = ''.join(xml_nfo.xpath('//poster/text()')).replace('&amp;', '&')
        trailer = ''.join(xml_nfo.xpath('//trailer/text()')).replace('&amp;', '&')
        website = ''.join(xml_nfo.xpath('//website/text()')).replace('&amp;', '&')
        wanted = ''.join(xml_nfo.xpath('//votes/text()'))

        # 判断马赛克
        if '国产' in tag or '國產' in tag:
            json_data['mosaic'] = '国产'
        elif '破解' in tag:
            json_data['mosaic'] = '无码破解'
        elif '有码' in tag or '有碼' in tag:
            json_data['mosaic'] = '有码'
        elif '流出' in tag:
            json_data['mosaic'] = '流出'
        elif '无码' in tag or '無碼' in tag or '無修正' in tag:
            json_data['mosaic'] = '无码'
        elif '里番' in tag or '裏番' in tag:
            json_data['mosaic'] = '里番'
        elif '动漫' in tag or '動漫' in tag:
            json_data['mosaic'] = '动漫'

        # 获取只有标签的标签（因为启用字段翻译后，会再次重复添加字幕、演员、发行、系列等字段）
        replace_keys = set(filter(None, ['：', ':'] + re.split(r'[,，]', actor)))
        temp_tag_list = list(filter(None, re.split(r'[,，]', tag.replace('中文字幕', ''))))
        only_tag_list = temp_tag_list.copy()
        for each_tag in temp_tag_list:
            for each_key in replace_keys:
                if each_key in each_tag:
                    only_tag_list.remove(each_tag)
                    break
        json_data['tag_only'] = ','.join(only_tag_list)

        # 获取本地图片路径
        poster_path_1 = self.convert_path(os.path.splitext(file_path)[0] + '-poster.jpg')
        poster_path_2 = self.convert_path(os.path.join(file_folder, 'poster.jpg'))
        thumb_path_1 = self.convert_path(os.path.splitext(file_path)[0] + '-thumb.jpg')
        thumb_path_2 = self.convert_path(os.path.join(file_folder, 'thumb.jpg'))
        fanart_path_1 = self.convert_path(os.path.splitext(file_path)[0] + '-fanart.jpg')
        fanart_path_2 = self.convert_path(os.path.join(file_folder, 'fanart.jpg'))
        if os.path.isfile(poster_path_1):
            poster_path = poster_path_1
        elif os.path.isfile(poster_path_2):
            poster_path = poster_path_2
        else:
            poster_path = ''
        if os.path.isfile(thumb_path_1):
            thumb_path = thumb_path_1
        elif os.path.isfile(thumb_path_2):
            thumb_path = thumb_path_2
        else:
            thumb_path = ''
        if os.path.isfile(fanart_path_1):
            fanart_path = fanart_path_1
        elif os.path.isfile(fanart_path_2):
            fanart_path = fanart_path_2
        else:
            fanart_path = ''

        # 返回数据
        json_data['title'] = title
        if self.config.get('title_language') == 'jp' and 'read_translate_again' in self.config.get('read_mode') and originaltitle:
            json_data['title'] = originaltitle
        json_data['originaltitle'] = originaltitle
        if originaltitle and langid.classify(originaltitle)[0] == 'ja':
            json_data['originaltitle_amazon'] = originaltitle
            if actor:
                json_data['actor_amazon'] = json_data['actor'].split(',')
        json_data['number'] = number
        json_data['letters'] = letters
        json_data['actor'] = actor
        json_data['all_actor'] = actor
        json_data['outline'] = outline
        if self.config.get('outline_language') == 'jp' and 'read_translate_again' in self.config.get('read_mode') and originalplot:
            json_data['outline'] = originalplot
        json_data['originalplot'] = originalplot
        json_data['tag'] = tag
        json_data['release'] = release
        json_data['year'] = year
        json_data['runtime'] = runtime
        json_data['score'] = score
        json_data['director'] = director
        json_data['series'] = series
        json_data['studio'] = studio
        json_data['publisher'] = publisher
        json_data['website'] = website
        json_data['cover'] = cover
        if cover:
            json_data['cover_list'].append(['local', cover])
        json_data['poster'] = poster
        json_data['trailer'] = trailer
        json_data['wanted'] = wanted
        json_data['poster_path'] = poster_path
        json_data['thumb_path'] = thumb_path
        json_data['fanart_path'] = fanart_path
        json_data['logs'] += "\n 📄 [NFO] %s" % local_nfo_name
        self.show_traceback_log(f"{number} {json_data['mosaic']}")
        return True, json_data

    # =====================================================================================检查文件

    def check_file(self, json_data, file_path, file_escape_size):

        if os.path.islink(file_path):
            file_path = read_link(file_path)
            if 'check_symlink' not in self.config.get('no_escape'):
                return True, json_data

        if not os.path.exists(file_path):
            json_data['error_info'] = '文件不存在'
            json_data['req_web'] = 'do_not_update_json_data_dic'
            json_data['outline'] = split_path(file_path)[1]
            json_data['tag'] = file_path
            return False, json_data
        if 'no_skip_small_file' not in self.config.get('no_escape'):
            file_size = os.path.getsize(file_path) / float(1024 * 1024)
            if file_size < file_escape_size:
                json_data['error_info'] = '文件小于 %s MB 被过滤!（实际大小 %s MB）已跳过刮削！' % (file_escape_size, round(file_size, 2))
                json_data['req_web'] = 'do_not_update_json_data_dic'
                json_data['outline'] = split_path(file_path)[1]
                json_data['tag'] = file_path
                return False, json_data
        return True, json_data

    # =====================================================================================获取视频分辨率

    def get_video_size(self, json_data, file_path):
        # 获取本地分辨率
        definition = ''
        height = 0
        hd_get = self.config.get('hd_get')
        if os.path.islink(file_path):
            if 'symlink_definition' in self.config.get('no_escape'):
                file_path = read_link(file_path)
            else:
                hd_get = 'path'
        if hd_get == 'video':
            try:
                cap = cv2.VideoCapture(file_path)
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            except Exception as e:
                self.show_traceback_log(traceback.format_exc())
                self.show_traceback_log(str(e))
                self.show_log_text(traceback.format_exc())
                self.show_log_text(f' 🔴 无法获取视频分辨率！ 文件地址: {file_path}  错误信息: {e}')
        elif hd_get == 'path':
            file_path_temp = file_path.upper()
            if '8K' in file_path_temp:
                height = 4000
            elif '4K' in file_path_temp or 'UHD' in file_path_temp:
                height = 2000
            elif '1440P' in file_path_temp or 'QHD' in file_path_temp:
                height = 1440
            elif '1080P' in file_path_temp or 'FHD' in file_path_temp:
                height = 1080
            elif '960P' in file_path_temp:
                height = 960
            elif '720P' in file_path_temp or 'HD' in file_path_temp:
                height = 720

        hd_name = self.config.get('hd_name')
        if not height:
            pass
        elif height >= 4000:
            definition = '8K' if hd_name == 'height' else 'UHD8'
        elif height >= 2000:
            definition = '4K' if hd_name == 'height' else 'UHD'
        elif height >= 1400:
            definition = '1440P' if hd_name == 'height' else 'QHD'
        elif height >= 1000:
            definition = '1080P' if hd_name == 'height' else 'FHD'
        elif height >= 900:
            definition = '960P' if hd_name == 'height' else 'HD'
        elif height >= 700:
            definition = '720P' if hd_name == 'height' else 'HD'
        elif height >= 500:
            definition = '540P' if hd_name == 'height' else 'qHD'
        elif height >= 400:
            definition = '480P'
        elif height >= 300:
            definition = '360P'
        elif height >= 100:
            definition = '144P'
        json_data['definition'] = definition

        if definition in ['4K', '8K', 'UHD', 'UHD8']:
            json_data['4K'] = '-' + definition

        # 去除标签中的分辨率率，使用本地读取的实际分辨率
        remove_key = ['144P', '360P', '480P', '540P', '720P', '960P', '1080P', '1440P', '2160P', '4K', '8K']
        tag = json_data['tag']
        for each_key in remove_key:
            tag = tag.replace(each_key, '').replace(each_key.lower(), '')
        tag_list = re.split(r'[,，]', tag)
        new_tag_list = []
        [new_tag_list.append(i) for i in tag_list if i]
        if definition and 'definition' in self.config.get('tag_include'):
            new_tag_list.insert(0, definition)
        json_data['tag'] = '，'.join(new_tag_list)
        return json_data

    # ========================================================================清理文件

    def pushButton_check_and_clean_files_clicked(self):
        if not self.config.get('can_clean'):
            self.pushButton_save_config_clicked()
        self.pushButton_show_log_clicked()
        try:
            t = threading.Thread(target=self.check_and_clean_files)
            self.threads_list.append(t)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())

    def check_and_clean_files(self):
        self.change_buttons_status()
        start_time = time.time()
        movie_path = self.get_movie_path_setting()[0]
        self.show_log_text('🍯 🍯 🍯 NOTE: START CHECKING AND CLEAN FILE NOW!!!')
        self.show_log_text('\n ⏰ Start time: ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        self.show_log_text(' 🖥 Movie path: %s \n ⏳ Checking all videos and cleaning, Please wait...' % movie_path)
        total = 0
        succ = 0
        fail = 0
        for root, dirs, files in os.walk(movie_path, topdown=True):
            for f in files:
                # 判断清理文件
                path = os.path.join(root, f)
                file_type_current = os.path.splitext(f)[1]
                if need_clean(path, f, file_type_current):
                    total += 1
                    result, error_info = delete_file(path)
                    if result:
                        succ += 1
                        self.show_log_text(' 🗑 Clean: %s ' % path)
                    else:
                        fail += 1
                        self.show_log_text(' 🗑 Clean error: %s ' % error_info)
        self.show_log_text(' 🍀 Clean done!(%ss)' % (self.get_used_time(start_time)))
        self.show_log_text('================================================================================')
        self.CEF(movie_path, '')
        self.set_label_file_path.emit('🗑 清理完成！')
        self.show_log_text(" 🎉🎉🎉 All finished!!!(%ss) Total %s , Success %s , Failed %s " % (self.get_used_time(start_time), total, succ, fail))
        self.show_log_text('================================================================================')
        self.reset_buttons_status()

    # =====================================================================================为所有视频中的无字幕视频添加字幕

    def pushButton_add_sub_for_all_video_clicked(self):
        self.pushButton_show_log_clicked()                                      # 点按钮后跳转到日志页面
        try:
            t = threading.Thread(target=self.add_sub_for_all_video)
            self.threads_list.append(t)
            t.start()                                                           # 启动线程,即让线程开始执行
        except:
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())

    def add_sub_for_all_video(self):
        self.change_buttons_status()
        sub_add = True
        self.show_log_text('Start check no subtitle video and add subtitles for them!\n')
        subtitle_folder = self.config.get('subtitle_folder')
        subtitle_add_chs = self.config.get('subtitle_add_chs')
        if subtitle_folder == '' or not os.path.exists(subtitle_folder):
            sub_add = False
            self.show_log_text("Subtitle folder does not exist!\nNow can only check no subtitle video, can't add subtitles for them！")
            self.show_log_text("================================================================================")

        movie_path, success_folder, failed_folder, escape_folder_list, extrafanart_folder, softlink_path = self.get_movie_path_setting()
        self.show_log_text(' 🖥 Movie path: %s \n 🔎 Checking all videos, Please wait...' % movie_path)
        if subtitle_add_chs == 'on':
            self.show_log_text(" If the subtitle file does not end with '.chs', '.chs' will be add automatically!\n")
        else:
            self.show_log_text(" If the subtitle file end with '.chs', '.chs' will be delete automatically!\n")
        movie_type = self.config.get('media_type')
        movie_list = self.movie_lists('', movie_type, movie_path)               # 获取所有需要刮削的影片列表
        sub_type_list = self.config.get('sub_type').split('|')                  # 本地字幕文件后缀

        add_count = 0
        no_sub_count = 0
        new_sub_movie_list = []
        for movie in movie_list:
            file_info = self.get_file_info(movie, copy_sub=False)
            json_data, number, folder_old_path, file_name, file_ex, sub_list, file_show_name, file_show_path = file_info
            has_sub = json_data['has_sub']                                      # 视频中文字幕标识
            if not has_sub:
                no_sub_count += 1
                self.show_log_text(" No sub:'%s' " % movie)
                cd_part = json_data['cd_part']
                if sub_add:
                    add_succ = False
                    for sub_type in sub_type_list:
                        sub_path = os.path.join(subtitle_folder, (number + cd_part + sub_type))
                        sub_file_name = file_name + sub_type
                        if subtitle_add_chs == 'on':
                            sub_file_name = file_name + '.chs' + sub_type
                        sub_new_path = os.path.join(folder_old_path, sub_file_name)

                        if os.path.exists(sub_path):
                            copy_file(sub_path, sub_new_path)
                            self.show_log_text(" 🍀 Sub file '%s' copied successfully! " % sub_file_name)
                            new_sub_movie_list.append(movie)
                            add_succ = True
                    if add_succ:
                        add_count += 1
            elif sub_list:
                for sub_type in sub_list:
                    sub_old_path = os.path.join(folder_old_path, (file_name + sub_type))
                    sub_new_path = os.path.join(folder_old_path, (file_name + '.chs' + sub_type))
                    if subtitle_add_chs == 'on':
                        if '.chs' not in sub_old_path and not os.path.exists(sub_new_path):
                            move_file(sub_old_path, sub_new_path)
                            self.show_log_text(" 🍀 Sub file:'%s' is renamed to:'%s' " % (file_name + sub_type, file_name + '.chs' + sub_type))
                    else:
                        sub_old_path_no_chs = sub_old_path.replace('.chs', '')
                        if '.chs' in sub_old_path and not os.path.exists(sub_old_path_no_chs):
                            move_file(sub_old_path, sub_old_path_no_chs)
                            self.show_log_text(" 🍀 Sub file:'%s' is renamed to:'%s' " % (file_name + sub_type, split_path(sub_old_path_no_chs)[1]))

                    cnword_style = self.config.get('cnword_style')
                    if cnword_style and cnword_style not in sub_new_path:
                        folder_cnword = self.config.get('folder_cnword')
                        file_cnword = self.config.get('file_cnword')
                        folder_name = self.config.get('folder_name')
                        naming_file = self.config.get('naming_file')
                        if folder_cnword == 'on' or file_cnword == 'on' or 'cnword' in folder_name or 'cnword' in naming_file:
                            new_sub_movie_list.append(movie)

        self.show_log_text('\nDone! \nMovies add sub successfully: %s \nMovies still without sub: %s ' % (add_count, no_sub_count - add_count))
        self.show_log_text("================================================================================")
        self.search_for_sub_video(new_sub_movie_list)

    def search_for_sub_video(self, movie_list):
        subtitle_add_rescrape = self.config.get('subtitle_add_rescrape')
        list2 = list(set(movie_list))                                            # 去重
        list3 = [each for each in list2 if each]                                 # 去空
        list3.sort(key=movie_list.index)                                         # 排序（保持原顺序）

        if list3 and subtitle_add_rescrape == 'on':
            self.show_log_text('开始对新添加字幕的视频重新刮削...')
            self.start_new_scrape('default_folder', movie_list=list3)
        else:
            self.reset_buttons_status()

    # =====================================================================================移动字幕

    def move_sub(self, json_data, folder_old_path, folder_new_path, file_name, sub_list, naming_rule):
        main_mode = self.config.get('main_mode')                                # 刮削模式
        update_mode = self.config.get('update_mode')                            # 更新模式
        has_sub = json_data['has_sub']                                          # 视频中文字幕标识
        copy_flag = False

        # 没有字幕，返回
        if not has_sub:
            return

        # 更新模式 或 读取模式
        if main_mode > 2:
            if update_mode == 'c' and self.config.get('success_file_rename') == 0:
                return

        # 软硬链接开时，复制字幕（EMBY 显示字幕）
        elif self.config.get('soft_link') > 0:
            copy_flag = True

        # 成功移动关、成功重命名关时，返回
        elif self.config.get('success_file_move') == 0 and self.config.get('success_file_rename') == 0:
            return

        for sub in sub_list:
            sub_old_path = os.path.join(folder_old_path, (file_name + sub))
            sub_new_path = os.path.join(folder_new_path, (naming_rule + sub))
            sub_new_path_chs = os.path.join(folder_new_path, (naming_rule + '.chs' + sub))
            if self.config.get('subtitle_add_chs') == 'on':
                if '.chs' not in sub:
                    sub_new_path = sub_new_path_chs
            if os.path.exists(sub_old_path) and not os.path.exists(sub_new_path):
                if copy_flag:
                    if not copy_file(sub_old_path, sub_new_path):
                        json_data['logs'] += "\n 🔴 Sub copy failed!"
                        return
                elif not move_file(sub_old_path, sub_new_path):
                    json_data['logs'] += "\n 🔴 Sub move failed!"
                    return
            json_data['logs'] += "\n 🍀 Sub done!"

    # =====================================================================================移动种子

    def move_torrent(self, json_data, folder_old_path, folder_new_path, file_name, movie_number, naming_rule):
        main_mode = self.config.get('main_mode')                                # 刮削模式
        update_mode = self.config.get('update_mode')                            # 更新模式

        # 更新模式 或 读取模式
        if main_mode == 3 or main_mode == 4:
            if update_mode == 'c' and self.config.get('success_file_rename') == 0:
                return

        # 软硬链接开时，不移动
        elif self.config.get('soft_link') != 0:
            return

        elif self.config.get('success_file_move') == 0 and self.config.get('success_file_rename') == 0:
            return
        torrent_file1 = os.path.join(folder_old_path, (file_name + '.torrent'))
        torrent_file2 = os.path.join(folder_old_path, (movie_number + '.torrent'))
        torrent_file1_new_path = os.path.join(folder_new_path, (naming_rule + '.torrent'))
        torrent_file2_new_path = os.path.join(folder_new_path, (movie_number + '.torrent'))
        if os.path.exists(torrent_file1) and torrent_file1 != torrent_file1_new_path and not os.path.exists(torrent_file1_new_path):
            move_file(torrent_file1, torrent_file1_new_path)
            json_data['logs'] += "\n 🍀 Torrent done!"

        if torrent_file2 != torrent_file1:
            if os.path.exists(torrent_file2) and torrent_file2 != torrent_file2_new_path and not os.path.exists(torrent_file2_new_path):
                move_file(torrent_file2, torrent_file2_new_path)
                json_data['logs'] += "\n 🍀 Torrent done!"

    # =====================================================================================移动bif缩略图

    def move_bif(self, json_data, folder_old_path, folder_new_path, file_name, naming_rule):
        main_mode = self.config.get('main_mode')                                # 刮削模式
        update_mode = self.config.get('update_mode')                            # 更新模式

        # 更新模式 或 读取模式
        if main_mode == 3 or main_mode == 4:
            if update_mode == 'c' and self.config.get('success_file_rename') == 0:
                return

        elif self.config.get('success_file_move') == 0 and self.config.get('success_file_rename') == 0:
            return
        bif_old_path = os.path.join(folder_old_path, (file_name + '-320-10.bif'))
        bif_new_path = os.path.join(folder_new_path, (naming_rule + '-320-10.bif'))
        if bif_old_path != bif_new_path and os.path.exists(bif_old_path) and not os.path.exists(bif_new_path):
            move_file(bif_old_path, bif_new_path)
            json_data['logs'] += "\n 🍀 Bif done!"

    # =====================================================================================移动其他旧文件（旧文件不改名）

    def move_other_file(self, json_data, folder_old_path, folder_new_path, file_name, naming_rule):
        main_mode = self.config.get('main_mode')                                # 刮削模式
        update_mode = self.config.get('update_mode')                            # 更新模式
        movie_type = self.config.get('media_type')                              # 视频格式

        # 软硬链接模式不移动
        if self.config.get('soft_link') != 0:
            return

        # 目录相同不移动
        if self.convert_path(folder_new_path).lower() == self.convert_path(folder_old_path).lower():
            return

        # 更新模式 或 读取模式
        if main_mode == 3 or main_mode == 4:
            if update_mode == 'c' and self.config.get('success_file_rename') == 0:
                return

        elif self.config.get('success_file_move') == 0 and self.config.get('success_file_rename') == 0:
            return

        files = os.listdir(folder_old_path)
        for old_file in files:
            if os.path.splitext(old_file)[1].lower() in movie_type:
                continue
            if json_data['number'] in old_file or file_name in old_file or naming_rule in old_file:
                if '-cd' not in old_file.lower():                               # 避免多分集时，其他分级的内容被移走
                    old_file_old_path = os.path.join(folder_old_path, old_file)
                    old_file_new_path = os.path.join(folder_new_path, old_file)
                    if old_file_old_path != old_file_new_path and os.path.exists(old_file_old_path) and not os.path.exists(old_file_new_path):
                        move_file(old_file_old_path, old_file_new_path)
                        json_data['logs'] += "\n 🍀 Move %s done!" % old_file

    # =====================================================================================移动预览视频

    def move_trailer_video(self, json_data, folder_old_path, folder_new_path, file_name, naming_rule):
        if self.config.get('main_mode') < 2:
            if self.config.get('success_file_move') == 0 and self.config.get('success_file_rename') == 0:
                return
        if self.config.get('main_mode') > 2:
            update_mode = self.config.get('update_mode')
            if update_mode == 'c' and self.config.get('success_file_rename') == 0:
                return

        media_type_list = self.config.get('media_type').split('|')
        for media_type in media_type_list:
            trailer_old_path = os.path.join(folder_old_path, (file_name + '-trailer' + media_type))
            trailer_new_path = os.path.join(folder_new_path, (naming_rule + '-trailer' + media_type))
            if os.path.exists(trailer_old_path) and not os.path.exists(trailer_new_path):
                move_file(trailer_old_path, trailer_new_path)
                json_data['logs'] += "\n 🍀 Trailer done!"

    # =====================================================================================下载预览视频

    def trailer_download(self, json_data, folder_new_path, folder_old_path, naming_rule):
        start_time = time.time()
        download_files = self.config.get('download_files')
        keep_files = self.config.get('keep_files')
        trailer_name = self.config.get('trailer_name')
        trailer_url = json_data['trailer']
        trailer_old_folder_path = os.path.join(folder_old_path, 'trailers')
        trailer_new_folder_path = os.path.join(folder_new_path, 'trailers')

        # 预告片名字不含视频文件名（只让一个视频去下载即可）
        if trailer_name == 1:
            trailer_folder_path = os.path.join(folder_new_path, 'trailers')
            trailer_file_name = 'trailer.mp4'
            trailer_file_path = os.path.join(trailer_folder_path, trailer_file_name)

            # 预告片文件夹已在已处理列表时，返回（这时只需要下载一个，其他分集不需要下载）
            if trailer_folder_path in self.trailer_deal_set:
                return
            self.trailer_deal_set.add(trailer_folder_path)

            # 不下载不保留时删除返回
            if 'trailer' not in download_files and 'trailer' not in keep_files:
                # 删除目标文件夹即可，其他文件夹和文件已经删除了
                if os.path.exists(trailer_folder_path):
                    shutil.rmtree(trailer_folder_path, ignore_errors=True)
                return

        else:
            # 预告片带文件名（每个视频都有机会下载，如果已有下载好的，则使用已下载的）
            trailer_file_name = naming_rule + '-trailer.mp4'
            trailer_folder_path = folder_new_path
            trailer_file_path = os.path.join(trailer_folder_path, trailer_file_name)

            # 不下载不保留时删除返回
            if 'trailer' not in download_files and 'trailer' not in keep_files:
                # 删除目标文件，删除预告片旧文件夹、新文件夹（deal old file时没删除）
                if os.path.exists(trailer_file_path):
                    delete_file(trailer_file_path)
                if os.path.exists(trailer_old_folder_path):
                    shutil.rmtree(trailer_old_folder_path, ignore_errors=True)
                if trailer_new_folder_path != trailer_old_folder_path and os.path.exists(trailer_new_folder_path):
                    shutil.rmtree(trailer_new_folder_path, ignore_errors=True)
                return

        # 选择保留文件，当存在文件时，不下载。（done trailer path 未设置时，把当前文件设置为 done trailer path，以便其他分集复制）
        if 'trailer' in keep_files and os.path.exists(trailer_file_path):
            if not self.file_done_dic.get(json_data['number']).get('trailer'):
                self.file_done_dic[json_data['number']].update({'trailer': trailer_file_path})
                # 带文件名时，删除掉新、旧文件夹，用不到了。（其他分集如果没有，可以复制第一个文件的预告片。此时不删，没机会删除了）
                if trailer_name == 0:
                    if os.path.exists(trailer_old_folder_path):
                        shutil.rmtree(trailer_old_folder_path, ignore_errors=True)
                    if trailer_new_folder_path != trailer_old_folder_path and os.path.exists(trailer_new_folder_path):
                        shutil.rmtree(trailer_new_folder_path, ignore_errors=True)
            json_data['logs'] += "\n 🍀 Trailer done! (old)(%ss) " % self.get_used_time(start_time)
            return True

        # 带文件名时，选择下载不保留，或者选择保留但没有预告片，检查是否有其他分集已下载或本地预告片
        # 选择下载不保留，当没有下载成功时，不会删除不保留的文件
        done_trailer_path = self.file_done_dic.get(json_data['number']).get('trailer')
        if trailer_name == 0 and done_trailer_path and os.path.exists(done_trailer_path):
            if os.path.exists(trailer_file_path):
                delete_file(trailer_file_path)
            copy_file(done_trailer_path, trailer_file_path)
            json_data['logs'] += '\n 🍀 Trailer done! (copy trailer)(%ss)' % self.get_used_time(start_time)
            return

        # 不下载时返回（选择不下载保留，但本地并不存在，此时返回）
        if 'trailer,' not in download_files:
            return

        # 下载预告片,检测链接有效性
        content_length = check_url(trailer_url, length=True)
        if content_length:
            # 创建文件夹
            if trailer_name == 1 and not os.path.exists(trailer_folder_path):
                os.makedirs(trailer_folder_path)

            # 开始下载
            download_files = self.config.get('download_files')
            self.show_traceback_log(f"🍔 {json_data['number']} download trailer... {trailer_url}")
            trailer_file_path_temp = trailer_file_path
            if os.path.exists(trailer_file_path):
                trailer_file_path_temp = trailer_file_path + '.[DOWNLOAD].mp4'
            if self.download_file_with_filepath(json_data, trailer_url, trailer_file_path_temp, trailer_folder_path):
                file_size = os.path.getsize(trailer_file_path_temp)
                if file_size >= content_length or 'ignore_size' in download_files:
                    json_data['logs'] += "\n 🍀 Trailer done! (%s %s/%s)(%ss) " % (json_data['trailer_from'], file_size, content_length, self.get_used_time(start_time))
                    self.show_traceback_log(f"✅ {json_data['number']} trailer done!")
                    if trailer_file_path_temp != trailer_file_path:
                        move_file(trailer_file_path_temp, trailer_file_path)
                        delete_file(trailer_file_path_temp)
                    done_trailer_path = self.file_done_dic.get(json_data['number']).get('trailer')
                    if not done_trailer_path:
                        self.file_done_dic[json_data['number']].update({'trailer': trailer_file_path})
                        if trailer_name == 0:   # 带文件名，已下载成功，删除掉那些不用的文件夹即可
                            if os.path.exists(trailer_old_folder_path):
                                shutil.rmtree(trailer_old_folder_path, ignore_errors=True)
                            if trailer_new_folder_path != trailer_old_folder_path and os.path.exists(trailer_new_folder_path):
                                shutil.rmtree(trailer_new_folder_path, ignore_errors=True)
                    return True
                else:
                    json_data['logs'] += "\n 🟠 Trailer size is incorrect! delete it! (%s %s/%s) " % (json_data['trailer_from'], file_size, content_length)
            # 删除下载失败的文件
            delete_file(trailer_file_path_temp)
            json_data['logs'] += "\n 🟠 Trailer download failed! (%s) " % trailer_url

        if os.path.exists(trailer_file_path): # 使用旧文件
            done_trailer_path = self.file_done_dic.get(json_data['number']).get('trailer')
            if not done_trailer_path:
                self.file_done_dic[json_data['number']].update({'trailer': trailer_file_path})
                if trailer_name == 0:   # 带文件名，已下载成功，删除掉那些不用的文件夹即可
                    if os.path.exists(trailer_old_folder_path):
                        shutil.rmtree(trailer_old_folder_path, ignore_errors=True)
                    if trailer_new_folder_path != trailer_old_folder_path and os.path.exists(trailer_new_folder_path):
                        shutil.rmtree(trailer_new_folder_path, ignore_errors=True)
            json_data['logs'] += "\n 🟠 Trailer download failed! 将继续使用之前的本地文件！"
            json_data['logs'] += "\n 🍀 Trailer done! (old)(%ss)" % self.get_used_time(start_time)
            return True

    # ======================================================================================拷贝主题视频

    def copy_trailer_to_theme_videos(self, json_data, folder_new_path, naming_rule):
        start_time = time.time()
        download_files = self.config.get('download_files')
        keep_files = self.config.get('keep_files')
        theme_videos_folder_path = os.path.join(folder_new_path, 'backdrops')
        theme_videos_new_path = os.path.join(theme_videos_folder_path, 'theme_video.mp4')

        # 不保留不下载主题视频时，删除
        if 'theme_videos' not in download_files and 'theme_videos' not in keep_files:
            if os.path.exists(theme_videos_folder_path):
                shutil.rmtree(theme_videos_folder_path, ignore_errors=True)
            return

        # 保留主题视频并存在时返回
        if 'theme_videos' in keep_files and os.path.exists(theme_videos_folder_path):
            json_data['logs'] += "\n 🍀 Theme video done! (old)(%ss) " % self.get_used_time(start_time)
            return

        # 不下载主题视频时返回
        if 'theme_videos' not in download_files:
            return

        # 不存在预告片时返回
        trailer_name = self.config.get('trailer_name')
        if trailer_name == 1:
            trailer_folder = os.path.join(folder_new_path, 'trailers')
            trailer_file_path = os.path.join(trailer_folder, 'trailer.mp4')
        else:
            trailer_file_path = os.path.join(folder_new_path, naming_rule + '-trailer.mp4')
        if not os.path.exists(trailer_file_path):
            return

        # 存在预告片时复制
        if not os.path.exists(theme_videos_folder_path):
            os.makedirs(theme_videos_folder_path)
        if os.path.exists(theme_videos_new_path):
            delete_file(theme_videos_new_path)
        copy_file(trailer_file_path, theme_videos_new_path)
        json_data['logs'] += "\n 🍀 Theme video done! (copy trailer)"

        # 不下载并且不保留预告片时，删除预告片
        if 'trailer' not in download_files and 'trailer' not in self.config.get('keep_files'):
            delete_file(trailer_file_path)
            if trailer_name == 1:
                shutil.rmtree(trailer_folder, ignore_errors=True)
            json_data['logs'] += "\n 🍀 Trailer delete done!"

    # =====================================================================================载入本地数据

    def get_actor_mapping_data(self):
        if len(self.actor_mapping_data):
            return self.actor_mapping_data

        # 读取本地数据
        actor_map_local_path = self.actor_map_local_path
        if not os.path.exists(actor_map_local_path):
            if not copy_file(self.actor_map_backup_path, actor_map_local_path):
                actor_map_local_path = self.actor_map_backup_path
        try:
            with open(actor_map_local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            parser = etree.HTMLParser(encoding="utf-8")
            self.actor_mapping_data = etree.HTML(content.encode('utf-8'), parser=parser)
        except Exception as e:
            self.show_log_text(' %s 读取失败！请检查该文件是否存在问题！如需重置请删除该文件！错误信息：\n%s' % (actor_map_local_path, str(e)))
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())
            self.actor_mapping_data = {}

        return self.actor_mapping_data

    def get_info_mapping_data(self):
        if len(self.info_mapping_data):
            return self.info_mapping_data

        # 读取本地数据
        info_map_local_path = self.info_map_local_path
        if not os.path.exists(info_map_local_path):
            if not copy_file(self.info_map_backup_path, info_map_local_path):
                info_map_local_path = self.info_map_backup_path
        try:
            with open(info_map_local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            parser = etree.HTMLParser(encoding="utf-8")
            self.info_mapping_data = etree.HTML(content.encode('utf-8'), parser=parser)
        except Exception as e:
            self.show_log_text(' %s 读取失败！请检查该文件是否存在问题！如需重置请删除该文件！错误信息：\n%s' % (info_map_local_path, str(e)))
            self.info_mapping_data = {}
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())
        return self.info_mapping_data

    def get_local_data(self):
        # 载入c_numuber.json数据
        with open(self.sehua_title_path, 'r', encoding='UTF-8') as data:
            self.sehua_title_data = json.load(data)

        # 载入mapping_actor.xml数据
        self.get_actor_mapping_data()

        # 载入mapping_info.xml数据
        self.get_info_mapping_data()

    def deal_tag_data(self, tag):
        for each in ['中文字幕', '无码流出', '無碼流出', '无码破解', '無碼破解', '无码', '無碼', '有码', '有碼', '国产', '國產', '里番', '裏番', '动漫', '動漫']:
            tag = tag.replace(each, '')
        return tag.replace(',,', ',')

    # =====================================================================================处理单个文件刮削

    def coreMain(self, file_path, file_info, file_mode):
        # =====================================================================================初始化所需变量
        start_time = time.time()
        sub_list = []
        read_mode = self.config.get('read_mode')
        file_escape_size = float(self.config.get('file_size'))
        file_path = self.convert_path(file_path)

        # =====================================================================================获取文件信息
        json_data, movie_number, folder_old_path, file_name, file_ex, sub_list, file_show_name, file_show_path = file_info

        # =====================================================================================获取设置的媒体目录、失败目录、成功目录
        movie_path, success_folder, failed_folder, escape_folder_list, extrafanart_folder, softlink_path = self.get_movie_path_setting(file_path)
        json_data['failed_folder'] = failed_folder

        # =====================================================================================检查文件大小
        result, json_data = self.check_file(json_data, file_path, file_escape_size)
        if not result:
            return False, json_data

        # =====================================================================================读取模式
        json_data['file_can_download'] = True
        json_data['nfo_can_translate'] = True
        json_data['nfo_update'] = False
        if self.config.get('main_mode') == 4:
            result, json_data = self.get_nfo_data(json_data, file_path, movie_number)
            if result:                                                          # 有nfo
                movie_number = json_data['number']
                json_data['nfo_update'] = True
                if 'has_nfo_update' not in read_mode:                           # 不更新并返回
                    self.show_data_result(json_data, start_time)
                    self.show_movie_info(json_data)
                    json_data['logs'] += "\n 🙉 [Movie] %s" % file_path
                    self.save_success_list(file_path, file_path)     # 保存成功列表
                    return True, json_data

                # 读取模式要不要下载
                if 'read_download_again' not in read_mode:
                    json_data['file_can_download'] = False

                # 读取模式要不要翻译
                if 'read_translate_again' not in read_mode:
                    json_data['nfo_can_translate'] = False
                else:
                    # 启用翻译时，tag使用纯tag的内容
                    json_data['tag'] = json_data['tag_only']
            else:
                if 'no_nfo_scrape' not in read_mode:                            # 无nfo，没有勾选「无nfo时，刮削并执行更新模式」
                    return False, json_data

        # =====================================================================================刮削json_data
        # =====================================================================================获取已刮削的json_data
        if '.' in movie_number or json_data['mosaic'] in ['国产']:
            pass
        elif movie_number not in self.json_get_set:
            self.json_get_set.add(movie_number)
        elif not self.json_data_dic.get(movie_number):
            while not self.json_data_dic.get(movie_number):
                time.sleep(1)

        json_data_old = self.json_data_dic.get(movie_number)
        if json_data_old and '.' not in movie_number and json_data['mosaic'] not in ['国产']:      # 已存在该番号数据时直接使用该数据
            json_data_new = {}
            json_data_new.update(json_data_old)
            json_data_new['cd_part'] = json_data['cd_part']
            json_data_new['has_sub'] = json_data['has_sub']
            json_data_new['c_word'] = json_data['c_word']
            json_data_new['destroyed'] = json_data['destroyed']
            json_data_new['leak'] = json_data['leak']
            json_data_new['wuma'] = json_data['wuma']
            json_data_new['youma'] = json_data['youma']
            json_data_new['4K'] = ''
            json_data_new['tag'] = self.deal_tag_data(json_data_old['tag'])
            json_data_new['logs'] = json_data['logs']
            json_data_new['file_path'] = json_data['file_path']
            if '破解' in json_data_old['mosaic'] or '流出' in json_data_old['mosaic']:
                json_data_new['mosaic'] = json_data['mosaic'] if json_data['mosaic'] else '有码'
            elif '破解' in json_data['mosaic'] or '流出' in json_data['mosaic']:
                json_data_new['mosaic'] = json_data['mosaic']
            json_data.update(json_data_new)
        elif not json_data['nfo_update']:
            json_data = self.get_json_data(json_data, file_mode)

        # =====================================================================================显示json_data结果或日志
        json_data['failed_folder'] = failed_folder
        if not self.show_data_result(json_data, start_time):
            return False, json_data                                             # 返回MDCx1_1main, 继续处理下一个文件

        # =====================================================================================映射或翻译
        # 当不存在已刮削数据，或者读取模式允许翻译映射时才进行映射翻译
        if not json_data_old and json_data['nfo_can_translate']:
            self.deal_some_filed(json_data)                                     # 处理字段
            self.replace_special_word(json_data)                                # 替换特殊字符
            self.translate_title_outline(json_data, movie_number)               # 翻译json_data（标题/介绍）
            self.deal_some_filed(json_data)                                     # 再处理一遍字段，翻译后可能出现要去除的内容
            self.translate_actor(json_data)                                     # 映射输出演员名/信息
            self.translate_info(json_data)                                      # 映射输出标签等信息
            self.replace_word(json_data)

        # =====================================================================================更新视频分辨率
        self.get_video_size(json_data, file_path)

        # =====================================================================================显示json_data内容
        self.show_movie_info(json_data)

        # =====================================================================================生成输出文件夹和输出文件的路径
        folder_new_path, file_new_path, nfo_new_path, poster_new_path_with_filename, thumb_new_path_with_filename, fanart_new_path_with_filename, naming_rule, poster_final_path, thumb_final_path, fanart_final_path = self.get_output_name(json_data, file_path, success_folder, file_ex)

        # =====================================================================================判断输出文件的路径是否重复
        if self.config.get('soft_link') == 0:
            done_file_new_path_list = self.file_new_path_dic.get(file_new_path)
            if not done_file_new_path_list:                                     # 如果字典中不存在同名的情况，存入列表，继续刮削
                self.file_new_path_dic[file_new_path] = [file_path]
            else:
                done_file_new_path_list.append(file_path)                       # 已存在时，添加到列表，停止刮削
                done_file_new_path_list.sort(reverse=True)
                json_data['error_info'] = '存在重复文件（指刮削后的文件路径相同！），请检查:\n    🍁 %s' % '\n    🍁 '.join(done_file_new_path_list)
                # json_data['req_web'] = 'do_not_update_json_data_dic'            # do_not_update_json_data_dic 是不要更新json_data的标识，表示这个文件的数据有问题
                json_data['outline'] = split_path(file_path)[1]
                json_data['tag'] = file_path
                return False, json_data

        # =====================================================================================判断输出文件夹和文件是否已存在，如无则创建输出文件夹
        if not self.creat_folder(json_data, folder_new_path, file_path, file_new_path, thumb_new_path_with_filename, poster_new_path_with_filename):
            return False, json_data                                             # 返回MDCx1_1main, 继续处理下一个文件

        # =====================================================================================初始化图片已下载地址的字典
        if not self.file_done_dic.get(json_data['number']):
            self.file_done_dic[json_data['number']] = {
                'poster': '',
                'thumb': '',
                'fanart': '',
                'trailer': '',
                'local_poster': '',
                'local_thumb': '',
                'local_fanart': '',
                'local_trailer': '',
            }

        # =====================================================================================视频模式（原来叫整理模式）
        # 视频模式（仅根据刮削数据把电影命名为番号并分类到对应目录名称的文件夹下）
        if self.config.get('main_mode') == 2:
            # 移动文件
            if self.move_movie(json_data, file_path, file_new_path):
                if 'sort_del' in self.config.get('switch_on'):
                    self.deal_old_files(json_data, folder_old_path, folder_new_path, file_path, file_new_path, thumb_new_path_with_filename, poster_new_path_with_filename, fanart_new_path_with_filename, nfo_new_path, file_ex, poster_final_path, thumb_final_path, fanart_final_path) # 清理旧的thumb、poster、fanart、nfo
                self.save_success_list(file_path, file_new_path)                    # 保存成功列表
                return True, json_data
            else:

                # 返回MDCx1_1main, 继续处理下一个文件
                return False, json_data

        # =====================================================================================清理旧的thumb、poster、fanart、extrafanart、nfo
        pic_final_catched, single_folder_catched = self.deal_old_files(json_data, folder_old_path, folder_new_path, file_path, file_new_path, thumb_new_path_with_filename, poster_new_path_with_filename, fanart_new_path_with_filename, nfo_new_path, file_ex, poster_final_path, thumb_final_path, fanart_final_path)

        # 如果 final_pic_path 没处理过，这时才需要下载和加水印
        if pic_final_catched:
            if json_data['file_can_download']:
                # =====================================================================================下载thumb
                if not self.thumb_download(json_data, folder_new_path, thumb_final_path):
                    return False, json_data                                         # 返回MDCx1_1main, 继续处理下一个文件

                # =====================================================================================下载艺术图
                self.fanart_download(json_data, fanart_final_path)

                # =====================================================================================下载poster
                if not self.poster_download(json_data, folder_new_path, poster_final_path):
                    return False, json_data                                         # 返回MDCx1_1main, 继续处理下一个文件

                # =====================================================================================清理冗余图片
                self.pic_some_deal(json_data, thumb_final_path, fanart_final_path)

                # =====================================================================================加水印
                self.add_mark(json_data, json_data['poster_marked'], json_data['thumb_marked'], json_data['fanart_marked'])

                # =====================================================================================下载剧照和剧照副本
                if single_folder_catched:
                    self.extrafanart_download(json_data, folder_new_path)
                    self.extrafanart_copy2(json_data, folder_new_path)
                    self.extrafanart_extras_copy(json_data, folder_new_path)

                # =====================================================================================下载trailer、复制主题视频
                # 因为 trailer也有带文件名，不带文件名两种情况，不能使用pic_final_catched。比如图片不带文件名，trailer带文件名这种场景需要支持每个分集去下载trailer
                self.trailer_download(json_data, folder_new_path, folder_old_path, naming_rule)
                self.copy_trailer_to_theme_videos(json_data, folder_new_path, naming_rule)

        # =====================================================================================生成nfo文件
        self.write_nfo(json_data, nfo_new_path, folder_new_path, file_path)

        # =====================================================================================移动字幕、种子、bif、trailer、其他文件
        self.move_sub(json_data, folder_old_path, folder_new_path, file_name, sub_list, naming_rule)
        self.move_torrent(json_data, folder_old_path, folder_new_path, file_name, movie_number, naming_rule)
        self.move_bif(json_data, folder_old_path, folder_new_path, file_name, naming_rule)
        # self.move_trailer_video(json_data, folder_old_path, folder_new_path, file_name, naming_rule)
        self.move_other_file(json_data, folder_old_path, folder_new_path, file_name, naming_rule)

        # =====================================================================================移动文件
        if not self.move_movie(json_data, file_path, file_new_path):
            return False, json_data                                             # 返回MDCx1_1main, 继续处理下一个文件
        self.save_success_list(file_path, file_new_path)                        # 保存成功列表

        # =====================================================================================json添加封面缩略图路径
        # json_data['number'] = movie_number
        json_data['poster_path'] = poster_final_path
        json_data['thumb_path'] = thumb_final_path
        json_data['fanart_path'] = fanart_final_path
        if not os.path.exists(thumb_final_path) and os.path.exists(fanart_final_path):
            json_data['thumb_path'] = fanart_final_path

        return True, json_data

    # =====================================================================================主界面左下角显示信息

    def show_scrape_info(self, before_info=''):
        try:
            if self.file_mode == 'single_file':
                scrape_info = '💡 单文件刮削\n💠 %s · %s' % (self.main_mode, self.Ui.comboBox_website.currentText())
            else:
                scrape_info = '💠 %s · %s' % (self.main_mode, self.scrape_like)
                if self.config.get('scrape_like') == 'single':
                    scrape_info = f"💡 {self.config.get('website_single')} 刮削\n" + scrape_info
            if self.config.get('soft_link') == 1:
                scrape_info = '🍯 软链接 · 开\n' + scrape_info
            elif self.config.get('soft_link') == 2:
                scrape_info = '🍯 硬链接 · 开\n' + scrape_info
            after_info = '\n%s\n🛠 %s\n🐰 MDCx %s' % (scrape_info, self.config_file, self.localversion)
            self.label_show_version.emit(before_info + after_info + self.new_version)
        except:
            pass

    # =====================================================================================主功能函数

    def MDCx_main(self, file_mode, movie_list=[]):
        self.scrape_start_time = time.time()                                    # 开始刮削时间
        self.stop_other = False
        self.file_mode = file_mode                                              # 刮削模式（工具单文件或主界面/日志点开始正常刮削）
        self.failed_list = []                                                   # 失败文件和错误原因记录
        self.failed_file_list = []                                              # 失败文件记录
        self.show_scrape_info('🔎 正在刮削中...')

        # =====================================================================================初始化所需变量
        self.counting_order = 0                                                 # 刮削顺序
        self.total_count = 0                                                    # 总数
        self.rest_now_begin_count = 0                                           # 本轮刮削开始统计的线程序号（实际-1）
        self.rest_sleepping = False                                             # 是否休眠中
        self.scrape_starting = 0                                                # 已进入过刮削流程的数量
        self.scrape_started = 0                                                 # 已进入过刮削流程并开始的数量
        self.scrape_done = 0                                                    # 已完成刮削数量
        self.succ_count = 0                                                     # 成功数量
        self.fail_count = 0                                                     # 失败数量
        self.file_new_path_dic = {}                                             # 所有文件最终输出路径的字典（如已存在，则视为重复文件，直接跳过）
        self.pic_catch_set = set()                                              # 当前文件的图片最终输出路径的字典（如已存在，则最终图片文件视为已处理过）
        self.file_done_dic = {}                                                 # 当前番号的图片已下载完成的标识（如已存在，视为图片已下载完成）
        self.extrafanart_deal_set = set()                                       # 当前文件夹剧照已处理的标识（如已存在，视为剧照已处理过）
        self.extrafanart_copy_deal_set = set()                                  # 当前文件夹剧照副本已下载的标识（如已存在，视为剧照已处理过）
        self.trailer_deal_set = set()                                           # 当前文件trailer已处理的标识（如已存在，视为剧照已处理过）
        self.theme_videos_deal_set = set()                                      # 当前文件夹剧照已下载的标识（如已存在，视为剧照已处理过）
        self.nfo_deal_set = set()                                               # 当前文件nfo已处理的标识（如已存在，视为剧照已处理过）
        json_data = {}
        self.json_get_set = set()                                               # 去获取json的番号列表
        self.json_data_dic = {}                                                 # 获取成功的json
        self.img_path = ''
        self.deepl_result = {}                                                  # deep 翻译结果（当没有填写api时，使用第三方翻译模块，作用是实现超时自动退出，避免卡死）
        self.add_label_info(json_data)                                          # 清空主界面显示信息
        thread_number = self.config.get('thread_number')                        # 线程数量
        thread_time = self.config.get('thread_time')                            # 线程延时
        self.stop_flag = False                                                  # 线程停止标识
        self.label_result.emit(' 刮削中：%s 成功：%s 失败：%s' % (0, self.succ_count, self.fail_count))
        self.Ui.pushButton_view_failed_list.setText('失败 0')                    # 重置按钮文案
        self.logs_failed_settext.emit('\n\n\n')
        self.Ui.pushButton_scraper_failed_list.setText('请等待刮削完成后，点击可以一键刮削当前失败列表')

        # 日志页面显示开始时间
        self.start_time = time.time()
        if file_mode == 'single_file':
            self.show_log_text('🍯 🍯 🍯 NOTE: 当前是单文件刮削模式！')
        elif file_mode == 'search_again':
            self.show_log_text(f'🍯 🍯 🍯 NOTE: 开始重新刮削！！！ 刮削文件数量（{len(movie_list)})')
            n = 0
            for each_f, each_i in self.new_again_dic.items():
                n += 1
                if each_i[0]:
                    self.show_log_text(f'{n} 🖥 File path: {each_f}\n 🚘 File number: {each_i[0]}')
                else:
                    self.show_log_text(f'{n} 🖥 File path: {each_f}\n 🌐 File url: {each_i[1]}')

        # 获取设置的媒体目录、失败目录、成功目录
        movie_path, success_folder, failed_folder, escape_folder_list, extrafanart_folder, softlink_path = self.get_movie_path_setting()

        # 获取待刮削文件列表的相关信息
        if not movie_list:
            if self.config.get('scrape_softlink_path'):
                self.newtdisk_creat_symlink(bool(self.Ui.checkBox_copy_netdisk_nfo.isChecked()), movie_path, softlink_path)
                movie_path = softlink_path
            self.show_log_text('\n ⏰ Start time: ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            movie_list = self.get_movie_list(file_mode, movie_path, escape_folder_list)
        else:
            self.show_log_text('\n ⏰ Start time: ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        self.remain_list = movie_list
        self.can_save_remain = True

        count_all = len(movie_list)
        self.total_count = count_all

        task_list = []
        i = 0
        for each in movie_list:
            i += 1
            task_list.append((each, i, count_all))

        if count_all:
            self.count_claw += 1
            if self.config.get('main_mode') == 4:
                # thread_number = 1
                self.show_log_text(' 🕷 当前为读取模式，线程数量（%s），线程延时（0）秒...' % thread_number)
            else:
                if count_all < thread_number:
                    thread_number = count_all
                self.show_log_text(' 🕷 开启多线程，线程数量（%s），线程延时（%s）秒...' % (thread_number, thread_time))
            self.thread_final_number = thread_number
            if self.rest_scrape and self.config.get('main_mode') != 4:
                self.show_log_text(f'<font color=\"brown\"> 🍯 间歇刮削 已启用，连续刮削 {self.rest_count} 个文件后，将自动休息 {self.rest_time_convert} 秒...</font>')

            # 在启动前点了停止按钮
            if self.stop_flag:
                return

            # 创建线程锁，避免多分集删除或操作相同图片文件的问题
            self.lock = threading.Lock()

            # 创建线程池
            self.next_start_time = time.time()
            self.pool = Pool(thread_number, 'MDCx-Pool')
            self.pool.map(self.MDCx_main2, task_list)

            # self.extrafanart_pool.shutdown(wait=True)
            self.pool.shutdown(wait=True)
            self.label_result.emit(' 刮削中：%s 成功：%s 失败：%s' % (0, self.succ_count, self.fail_count))
            self.save_success_list()     # 保存成功列表
            if not self.config:
                return

        self.show_log_text("================================================================================")
        self.CEF(movie_path, file_mode)
        end_time = time.time()
        used_time = str(round((end_time - self.start_time), 2))
        if count_all:
            average_time = str(round((end_time - self.start_time) / count_all, 2))
        else:
            average_time = used_time
        self.progressBarValue.emit(0)
        self.set_label_file_path.emit('🎉 恭喜！全部刮削完成！共 %s 个文件！用时 %s 秒' % (count_all, used_time))
        self.show_traceback_log("🎉 All finished!!! Total %s , Success %s , Failed %s " % (count_all, self.succ_count, self.fail_count))
        self.show_log_text(" 🎉🎉🎉 All finished!!! Total %s , Success %s , Failed %s " % (count_all, self.succ_count, self.fail_count))
        self.show_log_text("================================================================================")
        if self.failed_list:
            self.show_log_text("    *** Failed results ****")
            for i in range(len(self.failed_list)):
                fail_path, fail_reson = self.failed_list[i]
                self.show_log_text(" 🔴 %s %s\n    %s" % (i + 1, fail_path, fail_reson))
                self.show_log_text("================================================================================")
        self.show_log_text(' ⏰ Start time'.ljust(15) + ': ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)))
        self.show_log_text(' 🏁 End time'.ljust(15) + ': ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)))
        self.show_log_text(' ⏱ Used time'.ljust(15) + ': %sS' % used_time)
        self.show_log_text(' 📺 Movies num'.ljust(15) + ': %s' % count_all)
        self.show_log_text(' 🍕 Per time'.ljust(15) + ': %sS' % average_time)
        self.show_log_text("================================================================================")
        self.show_scrape_info('🎉 刮削完成 %s/%s' % (count_all, count_all))
        if 'actor_photo_auto' in self.config.get('emby_on'):
            self.update_emby_actor_photo()
        else:
            self.reset_buttons_status()
        if len(self.again_dic):
            self.again_search()
        self.auto_exit()

    def auto_scrape(self):
        if 'timed_scrape' in self.config.get('switch_on') and self.Ui.pushButton_start_cap.text() == '开始':
            time.sleep(0.1)
            timed_interval = self.config.get('timed_interval')
            self.atuo_scrape_count += 1
            self.show_log_text(f'\n\n 🍔 已启用「循环刮削」！间隔时间：{timed_interval}！即将开始第 {self.atuo_scrape_count} 次循环刮削！')
            if self.scrape_start_time:
                self.show_log_text(' ⏰ 上次刮削时间: ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.scrape_start_time)))
            self.start_new_scrape('default_folder')

    def auto_start(self):
        if 'auto_start' in self.config.get('switch_on'):
            self.show_log_text('\n\n 🍔 已启用「软件启动后自动刮削」！即将开始自动刮削！')
            self.pushButton_start_cap_clicked()

    def auto_exit(self):
        if 'auto_exit' in self.config.get('switch_on'):
            self.show_log_text('\n\n 🍔 已启用「刮削后自动退出软件」！')
            count = 5
            for i in range(count):
                self.show_log_text(f' {count-i} 秒后将自动退出！')
                time.sleep(1)
            self.exit_app()

    def again_search(self):
        self.new_again_dic = self.again_dic.copy()
        new_movie_list = list(self.new_again_dic.keys())
        self.again_dic.clear()
        self.start_new_scrape('search_again', new_movie_list)

    def change_buttons_status(self):
        self.stop_other = True
        self.Ui.pushButton_start_cap.setText('■ 停止')
        self.Ui.pushButton_start_cap2.setText('■ 停止')
        self.Ui.pushButton_select_media_folder.setVisible(False)
        self.Ui.pushButton_start_single_file.setEnabled(False)
        self.Ui.pushButton_start_single_file.setText('正在刮削中...')
        self.Ui.pushButton_add_sub_for_all_video.setEnabled(False)
        self.Ui.pushButton_add_sub_for_all_video.setText('正在刮削中...')
        self.Ui.pushButton_show_pic_actor.setEnabled(False)
        self.Ui.pushButton_show_pic_actor.setText('刮削中...')
        self.Ui.pushButton_add_actor_info.setEnabled(False)
        self.Ui.pushButton_add_actor_info.setText('正在刮削中...')
        self.Ui.pushButton_add_actor_pic.setEnabled(False)
        self.Ui.pushButton_add_actor_pic.setText('正在刮削中...')
        self.Ui.pushButton_add_actor_pic_kodi.setEnabled(False)
        self.Ui.pushButton_add_actor_pic_kodi.setText('正在刮削中...')
        self.Ui.pushButton_del_actor_folder.setEnabled(False)
        self.Ui.pushButton_del_actor_folder.setText('正在刮削中...')
        # self.Ui.pushButton_check_and_clean_files.setEnabled(False)
        self.Ui.pushButton_check_and_clean_files.setText('正在刮削中...')
        self.Ui.pushButton_move_mp4.setEnabled(False)
        self.Ui.pushButton_move_mp4.setText('正在刮削中...')
        self.Ui.pushButton_find_missing_number.setEnabled(False)
        self.Ui.pushButton_find_missing_number.setText('正在刮削中...')
        self.Ui.pushButton_start_cap.setStyleSheet('QPushButton#pushButton_start_cap{color: white;background-color: rgba(230, 66, 30, 255);}QPushButton:hover#pushButton_start_cap{color: white;background-color: rgba(247, 36, 0, 250);}QPushButton:pressed#pushButton_start_cap{color: white;background-color: rgba(180, 0, 0, 250);}')
        self.Ui.pushButton_start_cap2.setStyleSheet('QPushButton#pushButton_start_cap2{color: white;background-color: rgba(230, 66, 30, 255);}QPushButton:hover#pushButton_start_cap2{color: white;background-color: rgba(247, 36, 0, 250);}QPushButton:pressed#pushButton_start_cap2{color: white;background-color: rgba(180, 0, 0, 250);}')

    def reset_buttons_status(self):
        self.Ui.pushButton_start_cap.setEnabled(True)
        self.Ui.pushButton_start_cap2.setEnabled(True)
        self.pushButton_start_cap.emit('开始')
        self.pushButton_start_cap2.emit('开始')
        self.Ui.pushButton_select_media_folder.setVisible(True)
        self.Ui.pushButton_start_single_file.setEnabled(True)
        self.pushButton_start_single_file.emit('刮削')
        self.Ui.pushButton_add_sub_for_all_video.setEnabled(True)
        self.pushButton_add_sub_for_all_video.emit('点击检查所有视频的字幕情况并为无字幕视频添加字幕')

        self.Ui.pushButton_show_pic_actor.setEnabled(True)
        self.pushButton_show_pic_actor.emit('查看')
        self.Ui.pushButton_add_actor_info.setEnabled(True)
        self.pushButton_add_actor_info.emit('开始补全')
        self.Ui.pushButton_add_actor_pic.setEnabled(True)
        self.pushButton_add_actor_pic.emit('开始补全')
        self.Ui.pushButton_add_actor_pic_kodi.setEnabled(True)
        self.pushButton_add_actor_pic_kodi.emit('开始补全')
        self.Ui.pushButton_del_actor_folder.setEnabled(True)
        self.pushButton_del_actor_folder.emit('清除所有.actors文件夹')
        self.Ui.pushButton_check_and_clean_files.setEnabled(True)
        self.pushButton_check_and_clean_files.emit('点击检查待刮削目录并清理文件')
        self.Ui.pushButton_move_mp4.setEnabled(True)
        self.pushButton_move_mp4.emit('开始移动')
        self.Ui.pushButton_find_missing_number.setEnabled(True)
        self.pushButton_find_missing_number.emit('检查缺失番号')

        self.Ui.pushButton_start_cap.setStyleSheet('QPushButton#pushButton_start_cap{color: white;background-color:#4C6EFF;}QPushButton:hover#pushButton_start_cap{color: white;background-color: rgba(76,110,255,240)}QPushButton:pressed#pushButton_start_cap{color: white;background-color:#4C6EE0}')
        self.Ui.pushButton_start_cap2.setStyleSheet('QPushButton#pushButton_start_cap2{color: white;background-color:#4C6EFF;}QPushButton:hover#pushButton_start_cap2{color: white;background-color: rgba(76,110,255,240)}QPushButton:pressed#pushButton_start_cap2{color: white;background-color:#4C6EE0}')
        self.file_mode = 'default_folder'
        self.threads_list = []
        if len(self.failed_list):
            self.Ui.pushButton_scraper_failed_list.setText(f'一键重新刮削当前 {len(self.failed_list)} 个失败文件')
        else:
            self.Ui.pushButton_scraper_failed_list.setText('当有失败任务时，点击可以一键刮削当前失败列表')

    def check_stop(self, file_name_temp):
        if not self.config:
            self.now_kill += 1
            self.show_log_text(' 🕷 %s 已停止刮削：%s/%s %s' % (self.get_current_time(), self.now_kill, self.total_kills, file_name_temp))
            self.set_label_file_path.emit(f'⛔️ 正在停止刮削...\n   正在停止已在运行的任务线程（{self.now_kill}/{self.total_kills}）...')
            raise '手动停止刮削'

    def MDCx_main2(self, task):
        # 获取顺序
        with self.lock:
            file_path, count, count_all = task
            self.counting_order += 1
            count = self.counting_order

        # 名字缩写
        file_name_temp = split_path(file_path)[1]
        if len(file_name_temp) > 40:
            file_name_temp = file_name_temp[:40] + '...'

        # 处理间歇任务
        while self.config.get('main_mode') != 4 and self.rest_scrape and count - self.rest_now_begin_count > self.rest_count:
            self.check_stop(file_name_temp)
            time.sleep(1)

        # 非第一个加延时
        self.scrape_starting += 1
        count = self.scrape_starting
        thread_time = self.config.get('thread_time')
        if count == 1 or thread_time == 0 or self.config.get('main_mode') == 4:
            self.next_start_time = time.time()
            self.show_log_text(' 🕷 %s 开始刮削：%s/%s %s' % (self.get_current_time(), self.scrape_starting, count_all, file_name_temp))
            thread_time = 0
        else:
            self.next_start_time += thread_time

        # 计算本线程开始剩余时间, 休眠并定时检查是否手动停止
        remain_time = int(self.next_start_time - time.time())
        if remain_time > 0:
            self.show_log_text(' ⏱ %s（%s）秒后开始刮削：%s/%s %s' % (self.get_current_time(), remain_time, count, count_all, file_name_temp))
            for i in range(remain_time):
                self.check_stop(file_name_temp)
                time.sleep(1)

        self.scrape_started += 1
        if count > 1 and thread_time != 0:
            self.show_log_text(' 🕷 %s 开始刮削：%s/%s %s' % (self.get_current_time(), self.scrape_started, count_all, file_name_temp))

        start_time = time.time()
        file_mode = self.file_mode

        # 获取文件基础信息
        file_info = self.get_file_info(file_path)
        json_data, movie_number, folder_old_path, file_name, file_ex, sub_list, file_show_name, file_show_path = file_info

        # 显示刮削信息
        progress_value = self.scrape_started / count_all * 100
        progress_percentage = '%.2f' % progress_value + '%'
        self.progressBarValue.emit(int(progress_value))
        self.set_label_file_path.emit('正在刮削： %s/%s %s \n %s' % (self.scrape_started, count_all, progress_percentage, self.convert_path(file_show_path)))
        self.label_result.emit(' 刮削中：%s 成功：%s 失败：%s' % (self.scrape_started - self.succ_count - self.fail_count, self.succ_count, self.fail_count))
        json_data['logs'] += '\n' + '=' * 80
        json_data['logs'] += "\n 🙈 [Movie] " + self.convert_path(file_path)
        json_data['logs'] += "\n 🚘 [Number] " + movie_number

        # 如果指定了单一网站，进行提示
        website_single = self.config.get('website_single')
        if self.config.get('scrape_like') == 'single' and file_mode != 'single_file' and self.config.get('main_mode') != 4:
            json_data['logs'] += "\n 😸 [Note] You specified 「 %s 」, some videos may not have results! " % website_single

        # 获取刮削数据
        try:
            result, json_data = self.coreMain(file_path, file_info, file_mode)
            if json_data['req_web'] != 'do_not_update_json_data_dic':
                self.json_data_dic.update({movie_number: json_data})
        except Exception as e:
            self.check_stop(file_name_temp)
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())
            json_data['error_info'] = 'c1oreMain error: ' + str(e)
            json_data['logs'] += "\n" + traceback.format_exc()
            result = False

        # 显示刮削数据
        try:
            if result:
                self.succ_count += 1
                succ_show_name = str(self.count_claw) + '-' + str(self.succ_count) + '.' + file_show_name.replace(movie_number, json_data['number']) + json_data['4K']
                self.show_list_name(succ_show_name, 'succ', json_data, movie_number)
            else:
                self.fail_count += 1
                fail_show_name = str(self.count_claw) + '-' + str(self.fail_count) + '.' + file_show_name.replace(movie_number, json_data['number']) + json_data['4K']
                self.show_list_name(fail_show_name, 'fail', json_data, movie_number)
                if json_data['error_info']:
                    json_data['logs'] += '\n 🔴 [Failed] Reason: %s' % json_data['error_info']
                    if 'WinError 5' in json_data['error_info']:
                        json_data['logs'] += '\n 🔴 该问题为权限问题：请尝试以管理员身份运行，同时关闭其他正在运行的Python脚本！'
                fail_file_path = self.move_file_to_failed_folder(json_data, file_path, folder_old_path, file_ex)
                self.failed_list.append([fail_file_path, json_data['error_info']])
                self.failed_file_list.append(fail_file_path)
                self.failed_file_info_show(str(self.fail_count), fail_file_path, json_data['error_info'])
                self.Ui.pushButton_view_failed_list.setText(f'失败 {self.fail_count}')
        except Exception as e:
            self.check_stop(file_name_temp)
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())
            self.show_log_text(str(e))

        # 显示刮削结果
        with self.lock:
            try:
                self.scrape_done += 1
                count = self.scrape_done
                progress_value = count / count_all * 100
                progress_percentage = '%.2f' % progress_value + '%'
                used_time = self.get_used_time(start_time)
                scrape_info_begin = '\n%d/%d (%s) round(%s) %s' % (count, count_all, progress_percentage, self.count_claw, split_path(file_path)[1])
                scrape_info_after = '\n%s\n 🕷 %s %s/%s %s 刮削完成！用时 %s 秒！' % ('=' * 80, time.strftime("%H:%M:%S", time.localtime()), count, count_all, split_path(file_path)[1], used_time)
                json_data['logs'] = scrape_info_begin + json_data['logs'] + scrape_info_after
                self.show_log_text(json_data['logs'])
                remain_count = self.scrape_started - count
                if self.scrape_started == count_all:
                    self.show_log_text(f' 🕷 剩余正在刮削的线程：{remain_count}')
                self.label_result.emit(' 刮削中：%s 成功：%s 失败：%s' % (remain_count, self.succ_count, self.fail_count))
                self.show_scrape_info('🔎 已刮削 %s/%s' % (count, count_all))
            except Exception as e:
                self.check_stop(file_name_temp)
                self.show_traceback_log(traceback.format_exc())
                self.show_log_text(traceback.format_exc())
                self.show_log_text(str(e))

            # 更新剩余任务
            try:
                self.update_remain_list(file_path)
            except Exception as e:
                self.check_stop(file_name_temp)
                self.show_traceback_log(traceback.format_exc())
                self.show_log_text(traceback.format_exc())
                self.show_log_text(str(e))

        # 处理间歇刮削
        try:
            if self.config.get('main_mode') != 4 and self.rest_scrape:
                time_note = f' 🏖 已累计刮削 {count}/{count_all}，已连续刮削 {count - self.rest_now_begin_count}/{self.rest_count}...'
                self.show_log_text(time_note)
                if count - self.rest_now_begin_count >= self.rest_count:
                    if self.scrape_starting > count:
                        time_note = f' 🏖 当前还存在 {self.scrape_starting - count} 个已经在刮削的任务，等待这些任务结束将进入休息状态...\n'
                        self.show_log_text(time_note)
                        while not self.rest_sleepping:
                            time.sleep(1)
                    elif not self.rest_sleepping and count < count_all:
                        self.rest_sleepping = True                              # 开始休眠
                        self.rest_next_begin_time = time.time()                 # 下一轮倒计时开始时间
                        time_note = f'\n ⏸ 休息 {self.rest_time_convert} 秒，将在 <font color=\"red\">{self.get_real_time(self.rest_next_begin_time + self.rest_time_convert)}</font> 继续刮削剩余的 {count_all - count} 个任务...\n'
                        self.show_log_text(time_note)
                        while self.rest_scrape and time.time() - self.rest_next_begin_time < self.rest_time_convert:
                            if self.scrape_starting > count:                    # 如果突然调大了文件数量，这时跳出休眠
                                break
                            time.sleep(1)
                        self.rest_now_begin_count = count
                        self.rest_sleepping = False                             # 休眠结束，下一轮开始
                        self.next_start_time = time.time() - self.config.get('thread_time')
                    else:
                        while self.rest_sleepping:
                            time.sleep(1)

        except Exception as e:
            self.check_stop(file_name_temp)
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())
            self.show_log_text(str(e))

    # =====================================================================================停止刮削

    def show_stop_info(self):
        self.reset_buttons_status()
        try:
            self.rest_time_convert = self.rest_time_convert_
            if self.stop_other:
                self.show_scrape_info('⛔️ 已手动停止！')
                self.show_log_text("⛔️ 已手动停止！\n================================================================================")
                self.set_label_file_path.emit('⛔️ 已手动停止！')
                return
            self.progressBarValue.emit(0)
            end_time = time.time()
            used_time = str(round((end_time - self.start_time), 2))
            if self.scrape_done:
                average_time = str(round((end_time - self.start_time) / self.scrape_done, 2))
            else:
                average_time = used_time
            self.show_scrape_info('⛔️ 刮削已手动停止！')
            self.set_label_file_path.emit('⛔️ 刮削已手动停止！\n   已刮削 %s 个视频，还剩余 %s 个！刮削用时 %s 秒' % (self.scrape_done, (self.total_count - self.scrape_done), used_time))
            self.show_log_text('\n ⛔️ 刮削已手动停止！\n 😊 已刮削 %s 个视频，还剩余 %s 个！刮削用时 %s 秒，停止用时 %s 秒' % (self.scrape_done, (self.total_count - self.scrape_done), used_time, self.stop_used_time))
            self.show_log_text("================================================================================")
            self.show_log_text(' ⏰ Start time'.ljust(13) + ': ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)))
            self.show_log_text(' 🏁 End time'.ljust(13) + ': ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)))
            self.show_log_text(' ⏱ Used time'.ljust(13) + ': %sS' % used_time)
            self.show_log_text(' 🍕 Per time'.ljust(13) + ': %sS' % average_time)
            self.show_log_text("================================================================================")
            self.again_dic.clear()
        except:
            self.show_traceback_log(traceback.format_exc())
            self.show_log_text(traceback.format_exc())
        print(threading.enumerate())

    # =====================================================================================关闭某个线程

    def kill_a_thread(self, t):
        try:
            while t.is_alive():
                self._async_raise(t.ident, SystemExit)
        except:
            print(traceback.format_exc())
            self._async_raise(t.ident, SystemExit)

    def _async_raise(self, tid, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = 1
        while res == 1:
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            # raise ValueError("invalid thread id")
            pass
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    # =====================================================================================关闭线程池和扫描线程

    def kill_threads(self, ):
        thread_list = threading.enumerate()
        new_thread_list = []
        [new_thread_list.append(i) for i in thread_list if 'MDCx-Pool' in i.getName()] # 线程池的线程
        [new_thread_list.append(i) for i in self.threads_list]                         # 其他开启的线程
        other_name = new_thread_list[-1].getName()
        self.total_kills = len(new_thread_list)
        self.now_kill = 0
        start_time = time.time()
        self.set_label_file_path.emit(f'⛔️ 正在停止刮削...\n   正在停止已在运行的任务线程（1/{self.total_kills}）...')
        self.show_log_text(f'\n ⛔️ {self.get_current_time()} 已停止添加新的刮削任务，正在停止已在运行的任务线程（{self.total_kills}）...')
        self.show_traceback_log(f"⛔️ 正在停止正在运行的任务线程 ({self.total_kills}) ...")
        i = 0
        for each in new_thread_list:
            i += 1
            self.show_traceback_log(f'正在停止线程: {i}/{self.total_kills} {each.getName()} ...')
        self.show_traceback_log('线程正在停止中，请稍后...\n 🍯 停止时间与线程数量及线程正在执行的任务有关，比如正在执行网络请求、文件下载等IO操作时，需要等待其释放资源。。。\n')
        self.config = cf.set_stop(True)
        for each in new_thread_list:                                                   # 线程池的线程
            if 'MDCx-Pool' not in each.getName():
                self.kill_a_thread(each)
            while each.is_alive():
                pass

        self.config = cf.set_stop(False)
        self.stop_used_time = self.get_used_time(start_time)
        self.show_log_text(' 🕷 %s 已停止线程：%s/%s %s' % (self.get_current_time(), self.total_kills, self.total_kills, other_name))
        self.show_traceback_log(f'所有线程已停止！！！({self.stop_used_time}s)\n ⛔️ 刮削已手动停止！\n')
        self.show_log_text(f' ⛔️ {self.get_current_time()} 所有线程已停止！({self.stop_used_time}s)')
        thread_remain_list = []
        [thread_remain_list.append(i.getName()) for i in threading.enumerate()] # 剩余线程名字列表
        thread_remain = ', '.join(thread_remain_list)
        print(f"✅ 剩余线程 ({len(thread_remain_list)}): {thread_remain}")
        self.show_stop_info_thread()

    # =====================================================================================显示停止信息

    def show_stop_info_thread(self, ):
        t = threading.Thread(target=self.show_stop_info)
        t.start()

    # =====================================================================================获取当前时间、已用时间

    def get_current_time(self):
        return time.strftime("%H:%M:%S", time.localtime())

    def get_real_time(self, t):
        return time.strftime("%H:%M:%S", time.localtime(t))

    def get_used_time(self, start_time):
        return round((time.time() - start_time), )


class DraggableButton(QPushButton):

    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.iniDragCor = [0, 0]

    def mousePressEvent(self, e):
        # self.show_traceback_log("ppp",e.pos())
        self.iniDragCor[0] = e.x()
        self.iniDragCor[1] = e.y()

    def mouseMoveEvent(self, e):
        x = e.x() - self.iniDragCor[0]
        y = e.y() - self.iniDragCor[1]
        # 判断水平移动或竖直移动
        if newWin2.pic_h_w_ratio <= 1.5:
            y = 0
        else:
            x = 0

        cor = QPoint(x, y)
        self.move(self.mapToParent(cor))                                        # 需要maptoparent一下才可以的,否则只是相对位置。

        # self.show_traceback_log('drag button event,',time.time(),e.pos(),e.x(),e.y())

        # 计算实际裁剪位置
        c_x, c_y, c_x2, c_y2 = newWin2.getRealPos()
        # self.show_traceback_log('拖动：%s %s %s %s' % (str(c_x), str(c_y), str(c_x2), str(c_y2)))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.m_drag = False
        # 计算实际裁剪位置
        c_x, c_y, c_x2, c_y2 = newWin2.getRealPos()
        # self.show_traceback_log('松开：%s %s %s %s' % (str(c_x), str(c_y), str(c_x2), str(c_y2)))


class CutWindow(QDialog, Ui_Dialog_cut_poster):

    def __init__(self, parent=None):
        super(CutWindow, self).__init__(parent)
        self.Ui = Ui_Dialog_cut_poster()                                        # 实例化 Ui
        self.Ui.setupUi(self)                                                   # 初始化Ui
        self.m_drag = True                                                      # 允许拖动
        self.m_DragPosition = 0                                                 # 拖动位置
        self.show_w = self.Ui.label_backgroud_pic.width()                       # 图片显示区域的宽高
        self.show_h = self.Ui.label_backgroud_pic.height()                      # 图片显示区域的宽高
        self.keep_side = 'height'
        self.pic_new_w = self.show_w
        self.pic_new_h = self.show_h
        self.pic_w = self.show_w
        self.pic_h = self.show_h
        self.Ui.pushButton_select_cutrange = DraggableButton('拖动选择裁剪范围', self.Ui.label_backgroud_pic)
        self.Ui.pushButton_select_cutrange.setObjectName(u"pushButton_select_cutrange")
        self.Ui.pushButton_select_cutrange.setGeometry(QRect(420, 0, 379, 539))
        self.Ui.pushButton_select_cutrange.setCursor(QCursor(Qt.OpenHandCursor))
        self.Ui.pushButton_select_cutrange.setAcceptDrops(True)
        self.Ui.pushButton_select_cutrange.setStyleSheet(u"background-color: rgba(200, 200, 200, 80);\n" "font-size:13px;\n" "font-weight:normal;" "color: rgba(0, 0, 0, 255);\n" "border:2px solid rgba(0, 55, 255, 255);\n")
        self.set_style()
        self.Ui.horizontalSlider_left.valueChanged.connect(self.change_postion_left)
        self.Ui.horizontalSlider_right.valueChanged.connect(self.change_postion_right)
        self.Ui.pushButton_open_pic.clicked.connect(self.open_image)
        self.Ui.pushButton_cut_close.clicked.connect(self.to_cut_and_close)
        self.Ui.pushButton_cut.clicked.connect(self.to_cut)
        self.Ui.pushButton_close.clicked.connect(self.close)
        self.showimage()

    def set_style(self):
        # 控件美化 裁剪弹窗
        self.Ui.widget.setStyleSheet(
            '''
            * {
                font-family: Consolas, 'PingFang SC', 'Microsoft YaHei UI', 'Noto Color Emoji', 'Segoe UI Emoji';
            }
            QPushButton{
                color:black;
                font-size:14px;
                background-color:#CCCCCC;
                border-radius:20px;
                padding: 2px, 2px;
            }
            QPushButton:hover{
                color: white;
                background-color:#4C6EFF;
                font-weight:bold;
            }
            QPushButton:pressed{
                background-color:#4C6EE0;
                border-color:black;
                border-width:12px;
                font-weight:bold;
            }
            QPushButton#pushButton_cut_close{
                color: white;
                font-size:14px;
                background-color:#5E95CC;
                border-radius:25px;
                padding: 2px, 2px;
            }
            QPushButton:hover#pushButton_cut_close{
                color: white;
                background-color:#4C6EFF;
                font-weight:bold;
            }
            QPushButton:pressed#pushButton_cut_close{
                background-color:#4C6EE0;
                border-color:black;
                border-width:14px;
                font-weight:bold;
            }
            '''
        )

    def change_postion_left(self):
        abc = self.Ui.horizontalSlider_left.value()
        self.Ui.horizontalSlider_right.valueChanged.disconnect(self.change_postion_right)
        self.Ui.horizontalSlider_right.setValue(10000 - abc)
        self.Ui.horizontalSlider_right.valueChanged.connect(self.change_postion_right)

        self.rect_x, self.rect_y, self.rect_w, self.rect_h = self.Ui.pushButton_select_cutrange.geometry().getRect()
        self.rect_h_w_ratio = 1 + abc / 10000                                   # 更新高宽比
        self.Ui.label_cut_ratio.setText(str('%.2f' % self.rect_h_w_ratio))

        # 计算裁剪框大小
        if self.pic_h_w_ratio <= 1.5:                                                                             # 如果高宽比小时，固定高度，右边水平移动
            self.rect_w1 = int(self.rect_h / self.rect_h_w_ratio)
            self.rect_x = self.rect_x + self.rect_w - self.rect_w1
            self.rect_w = self.rect_w1
        else:
            self.rect_h1 = int(self.rect_w * self.rect_h_w_ratio)
            self.rect_y = self.rect_y + self.rect_h - self.rect_h1
            self.rect_h = self.rect_h1
        self.Ui.pushButton_select_cutrange.setGeometry(QRect(self.rect_x, self.rect_y, self.rect_w, self.rect_h)) # 显示裁剪框
        self.getRealPos()                                                                                         # 显示裁剪框实际位置

    def change_postion_right(self):
        abc = self.Ui.horizontalSlider_right.value()
        self.Ui.horizontalSlider_left.valueChanged.disconnect(self.change_postion_left)
        self.Ui.horizontalSlider_left.setValue(10000 - abc)
        self.Ui.horizontalSlider_left.valueChanged.connect(self.change_postion_left)

        self.rect_x, self.rect_y, self.rect_w, self.rect_h = self.Ui.pushButton_select_cutrange.geometry().getRect()
        self.rect_h_w_ratio = 2 - abc / 10000                                   # 更新高宽比
        self.Ui.label_cut_ratio.setText(str('%.2f' % self.rect_h_w_ratio))

        # 计算裁剪框大小
        if self.pic_h_w_ratio <= 1.5:                                                                             # 如果高宽比小时，固定高度，右边水平移动
            self.rect_w = int(self.rect_h / self.rect_h_w_ratio)
        else:
            self.rect_h = int(self.rect_w * self.rect_h_w_ratio)
        self.Ui.pushButton_select_cutrange.setGeometry(QRect(self.rect_x, self.rect_y, self.rect_w, self.rect_h)) # 显示裁剪框
        self.getRealPos()                                                                                         # 显示裁剪框实际位置

    # 打开图片选择框
    def open_image(self):
        img_path, img_type = QFileDialog.getOpenFileName(None, "打开图片", "", "*.jpg *.png;;All Files(*)", options=ui.options)
        if img_path:
            self.showimage(img_path)

    # 显示要裁剪的图片
    def showimage(self, img_path='', json_data={}):
        # self.Ui.Dialog_cut_poster.setText(' ')                                # 清空背景
        self.Ui.label_backgroud_pic.setText(' ')                                # 清空背景

        # 初始化数据
        self.Ui.checkBox_add_sub.setChecked(False)
        self.Ui.radioButton_add_no.setChecked(True)
        self.Ui.radioButton_add_no_2.setChecked(True)
        self.pic_h_w_ratio = 1.5
        self.rect_h_w_ratio = 536.6 / 379                                                     # 裁剪框默认高宽比
        self.show_image_path = img_path
        self.cut_thumb_path = ''                                                              # 裁剪后的thumb路径
        self.cut_poster_path = ''                                                             # 裁剪后的poster路径
        self.cut_fanart_path = ''                                                             # 裁剪后的fanart路径
        self.Ui.label_origin_size.setText(str('%s, %s' % (str(self.pic_w), str(self.pic_h)))) # 显示原图尺寸

        # 获取水印设置
        self.config = cf.get_config()
        poster_mark = self.config.get('poster_mark')
        mark_type = self.config.get('mark_type')
        pic_name = self.config.get('pic_name')

        # 显示图片及水印情况
        if img_path and os.path.exists(img_path):
            # 显示背景
            pic = QPixmap(img_path)
            self.pic_w = pic.width()
            self.pic_h = pic.height()
            self.Ui.label_origin_size.setText(str('%s, %s' % (str(self.pic_w), str(self.pic_h)))) # 显示原图尺寸
            self.pic_h_w_ratio = self.pic_h / self.pic_w                                          # 原图高宽比
            abc = int((self.rect_h_w_ratio - 1) * 10000)
            self.Ui.horizontalSlider_left.setValue(abc)                                           # 裁剪框左侧调整条的值（最大10000）
            self.Ui.horizontalSlider_right.setValue(10000 - abc)                                  # 裁剪框右侧调整条的值（最大10000）和左侧的值反过来

            # 背景图片等比缩放并显示
            if self.pic_h_w_ratio <= self.show_h / self.show_w:                 # 水平撑满（图片高/宽 <= 显示区域高/显示区域宽）
                self.pic_new_w = self.show_w                                    # 图片显示的宽度=显示区域宽度
                self.pic_new_h = int(self.pic_new_w * self.pic_h / self.pic_w)  # 计算出图片显示的高度
            else:                                                               # 垂直撑满
                self.pic_new_h = self.show_h                                    # 图片显示的高度=显示区域高度
                self.pic_new_w = int(self.pic_new_h * self.pic_w / self.pic_h)  # 计算出图片显示的宽度

            pic = QPixmap.scaled(pic, self.pic_new_w, self.pic_new_h, aspectRatioMode=Qt.KeepAspectRatio) # 图片缩放
            self.Ui.label_backgroud_pic.setGeometry(0, 0, self.pic_new_w, self.pic_new_h)                 # 背景区域大小位置设置
            self.Ui.label_backgroud_pic.setPixmap(pic)                                                    # 背景区域显示缩放后的图片

            # 获取nfo文件名，用来设置裁剪后图片名称和裁剪时的水印状态
            img_folder, img_fullname = split_path(img_path)
            img_name, img_ex = os.path.splitext(img_fullname)

            # 如果没有json_data，则通过图片文件名或nfo文件名获取，目的是用来获取水印
            if not json_data:
                # 根据图片文件名获取获取水印情况
                temp_path = img_path
                # 如果图片没有番号信息，则根据nfo文件名获取水印情况
                if '-' not in img_name:
                    file_list = os.listdir(img_folder)
                    for each in file_list:
                        if '.nfo' in each:
                            temp_path = os.path.join(img_folder, each)
                            break
                json_data, movie_number, folder_old_path, file_name, file_ex, sub_list, file_show_name, file_show_path = ui.get_file_info(temp_path, copy_sub=False)

            self.setWindowTitle(json_data.get('number') + ' 封面图片裁剪')            # 设置窗口标题

            # 获取水印信息
            has_sub = json_data['has_sub']
            mosaic = json_data['mosaic']
            definition = json_data['definition']

            # 获取裁剪后的的poster和thumb路径
            poster_path = os.path.join(img_folder, 'poster.jpg')
            if pic_name == 0:                                                   # 文件名-poster.jpg
                if '-' in img_name:
                    poster_path = img_path.replace('-fanart', '').replace('-thumb', '').replace('-poster', '').replace(img_ex, '') + '-poster.jpg'
            thumb_path = poster_path.replace('poster.', 'thumb.')
            fanart_path = poster_path.replace('poster.', 'fanart.')
            self.cut_thumb_path = thumb_path                                    # 裁剪后的thumb路径
            self.cut_poster_path = poster_path                                  # 裁剪后的poster路径
            self.cut_fanart_path = fanart_path                                  # 裁剪后的fanart路径

            # poster添加水印
            if poster_mark:
                if definition and 'hd' in mark_type:
                    if definition == '4K' or definition == 'UHD':
                        self.Ui.radioButton_add_4k.setChecked(True)
                    elif definition == '8K' or definition == 'UHD8':
                        self.Ui.radioButton_add_8k.setChecked(True)
                if has_sub and 'sub' in mark_type:
                    self.Ui.checkBox_add_sub.setChecked(True)
                if mosaic == '有码' or mosaic == '有碼':
                    if 'youma' in mark_type:
                        self.Ui.radioButton_add_censored.setChecked(True)
                elif '破解' in mosaic:
                    if 'umr' in mark_type:
                        self.Ui.radioButton_add_umr.setChecked(True)
                    elif 'uncensored' in mark_type:
                        self.Ui.radioButton_add_uncensored.setChecked(True)
                elif '流出' in mosaic:
                    if 'leak' in mark_type:
                        self.Ui.radioButton_add_leak.setChecked(True)
                    elif 'uncensored' in mark_type:
                        self.Ui.radioButton_add_uncensored.setChecked(True)
                elif mosaic == '无码' or mosaic == '無碼':
                    self.Ui.radioButton_add_uncensored.setChecked(True)
        # 显示裁剪框
        # 计算裁剪框大小
        if self.pic_h_w_ratio <= 1.5:                                                                             # 高宽比小时，固定高度，水平移动
            self.keep_side = 'height'
            self.rect_h = self.pic_new_h                                                                          # 裁剪框的高度 = 图片缩放显示的高度
            self.rect_w = int(self.rect_h / self.rect_h_w_ratio)                                                  # 计算裁剪框的宽度
            self.rect_x = self.pic_new_w - self.rect_w                                                            # 裁剪框左上角位置的x值
            self.rect_y = 0                                                                                       # 裁剪框左上角位置的y值
        else:                                                                                                     # 高宽比大时，固定宽度，竖向移动
            self.keep_side = 'width'
            self.rect_w = self.pic_new_w                                                                          # 裁剪框的宽度 = 图片缩放显示的宽度
            self.rect_h = int(self.rect_w * self.rect_h_w_ratio)                                                  # 计算裁剪框的高度
            self.rect_x = 0                                                                                       # 裁剪框左上角的x值
            self.rect_y = int((self.pic_new_h - self.rect_h) / 2)                                                 # 裁剪框左上角的y值（默认垂直居中）
        self.Ui.pushButton_select_cutrange.setGeometry(QRect(self.rect_x, self.rect_y, self.rect_w, self.rect_h)) # 显示裁剪框
        self.getRealPos()                                                                                         # 显示裁剪框实际位置

    # 计算在原图的裁剪位置
    def getRealPos(self):
        # 边界处理
        pic_new_w = self.pic_new_w
        pic_new_h = self.pic_new_h
        px, py, pw, ph = self.Ui.pushButton_select_cutrange.geometry().getRect() # 获取裁剪框大小位置
        pw1 = int(pw / 2)                                                        # 裁剪框一半的宽度
        ph1 = int(ph / 2)                                                        # 裁剪框一半的高度
        if px <= -pw1:                                                           # 左边出去一半
            px = -pw1
        elif px >= pic_new_w - pw1:                                              # x右边出去一半
            px = pic_new_w - pw1
        if py <= -ph1:                                                           # 上面出去一半
            py = -ph1
        elif py >= pic_new_h - ph1:                                              # 下面出去一半
            py = pic_new_h - ph1

        # 更新显示裁剪框
        self.Ui.pushButton_select_cutrange.setGeometry(QRect(px, py, pw, ph))

        # 计算实际裁剪位置(裁剪时用的是左上角和右下角的坐标)
        if self.keep_side == 'height':
            self.c_h = self.pic_h
            self.c_w = self.pic_w * pw / self.pic_new_w
            self.c_x = self.pic_w * px / self.pic_new_w                         # 左上角坐标x
            self.c_y = self.pic_w * py / self.pic_new_w                         # 左上角坐标y
        else:
            self.c_w = self.pic_w
            self.c_h = self.pic_h * ph / self.pic_new_h
            self.c_x = self.pic_h * px / self.pic_new_h
            self.c_y = self.pic_h * py / self.pic_new_h
        self.c_x2 = self.c_x + self.c_w                                         # 右下角坐标x
        self.c_y2 = self.c_y + self.c_h                                         # 右下角坐标y

        # 在原图以外的区域不裁剪
        if self.c_x < 0:
            self.c_w += self.c_x
            self.c_x = 0
        if self.c_y < 0:
            self.c_h += self.c_y
            self.c_y = 0
        if self.c_x2 > self.pic_w:
            self.c_w += self.pic_w - self.c_x2
            self.c_x2 = self.pic_w
        if self.c_y2 > self.pic_h:
            self.c_h += self.pic_h - self.c_y2
            self.c_y2 = self.pic_h

        self.c_x = int(self.c_x)
        self.c_y = int(self.c_y)
        self.c_x2 = int(self.c_x2)
        self.c_y2 = int(self.c_y2)
        self.c_w = int(self.c_w)
        self.c_y = int(self.c_y)

        # 显示实际裁剪位置
        self.Ui.label_cut_postion.setText('%s, %s, %s, %s' % (str(self.c_x), str(self.c_y), str(self.c_x2), str(self.c_y2)))

        # self.show_traceback_log('选择位置： %s, %s, %s, %s' % (str(self.c_x), str(self.c_y), str(self.c_x2), str(self.c_y2)))
        # 显示实际裁剪尺寸
        self.Ui.label_cut_size.setText('%s, %s' % (str(self.c_w), str(self.c_h)))

        return self.c_x, self.c_y, self.c_x2, self.c_y2

    def to_cut_and_close(self):
        t = threading.Thread(target=self.to_cut)
        t.start()
        self.close()

    def to_cut(self):
        img_path = self.show_image_path                                         # 被裁剪的图片

        # 路径为空时，跳过
        if not img_path or not os.path.exists(img_path):
            return
        thumb_path = self.cut_thumb_path                                        # 裁剪后的thumb路径
        poster_path = self.cut_poster_path                                      # 裁剪后的poster路径
        fanart_path = self.cut_fanart_path                                      # 裁剪后的fanart路径
        ui.img_path = img_path                                                  # 裁剪后更新图片url，这样再次点击时才可以重新加载并裁剪

        # 读取配置信息
        mark_list = []
        self.config = cf.get_config()
        download_files = self.config.get('download_files')
        poster_mark = self.config.get('poster_mark')
        thumb_mark = self.config.get('thumb_mark')
        fanart_mark = self.config.get('fanart_mark')
        if self.Ui.radioButton_add_4k.isChecked():
            mark_list.append('4K')
        elif self.Ui.radioButton_add_8k.isChecked():
            mark_list.append('8K')
        if self.Ui.checkBox_add_sub.isChecked():
            mark_list.append('字幕')
        if self.Ui.radioButton_add_censored.isChecked():
            mark_list.append('有码')
        elif self.Ui.radioButton_add_umr.isChecked():
            mark_list.append('破解')
        elif self.Ui.radioButton_add_leak.isChecked():
            mark_list.append('流出')
        elif self.Ui.radioButton_add_uncensored.isChecked():
            mark_list.append('无码')

        # 裁剪poster
        try:
            img = Image.open(img_path)
        except:
            ui.show_log_text(f"{traceback.format_exc()}\n Open Pic: {img_path}")
            return False
        img = img.convert('RGB')
        img_new_png = img.crop((self.c_x, self.c_y, self.c_x2, self.c_y2))
        try:
            if os.path.exists(poster_path):
                delete_file(poster_path)
        except Exception as e:
            ui.show_log_text(" 🔴 Failed to remove old poster!\n    " + str(e))
            return False
        img_new_png.save(poster_path, quality=95, subsampling=0)
        img.close()
        # poster加水印
        if poster_mark == 1:
            ui.add_mark_thread(poster_path, mark_list)

        # 清理旧的thumb
        if 'thumb' in download_files:
            if thumb_path != img_path:
                if os.path.exists(thumb_path):
                    delete_file(thumb_path)
                copy_file(img_path, thumb_path)
            # thumb加水印
            if thumb_mark == 1:
                ui.add_mark_thread(thumb_path, mark_list)
        else:
            thumb_path = img_path

        # 清理旧的fanart
        if ',fanart' in download_files:
            if fanart_path != img_path:
                if os.path.exists(fanart_path):
                    delete_file(fanart_path)
                copy_file(img_path, fanart_path)
            # fanart加水印
            if fanart_mark == 1:
                ui.add_mark_thread(fanart_path, mark_list)

        # 在主界面显示预览
        ui.set_pixmap_thread(poster_path, thumb_path, poster_from='cut', cover_from='local')
        ui.change_to_mainpage.emit('')
        return True

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.m_drag = True
            self.m_DragPosition = e.globalPos() - self.pos()
            self.setCursor(QCursor(Qt.OpenHandCursor))                          # 按下左键改变鼠标指针样式为手掌

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.m_drag = False
            self.setCursor(QCursor(Qt.ArrowCursor))                             # 释放左键改变鼠标指针样式为箭头

    def mouseMoveEvent(self, e):
        if Qt.LeftButton and self.m_drag:
            if self.m_DragPosition:
                self.move(e.globalPos() - self.m_DragPosition)
                e.accept()
        # self.show_traceback_log('main',e.x(),e.y())


if __name__ == '__main__':
    '''
    主函数
    '''
    if platform.system() != 'Windows':
        import faulthandler
        faulthandler.enable()
        if os.path.isfile('Img/1'):
            try:
                import AppKit
                info = AppKit.NSBundle.mainBundle().infoDictionary()
                info["LSUIElement"] = True
            except:
                pass
        if os.path.isfile('highdpi_passthrough'):
            # 解决不同电脑不同缩放比例问题，非整数倍缩放，如系统中设置了150%的缩放，QT程序的缩放将是两倍，QT 5.14中增加了非整数倍的支持，需要加入下面的代码才能使用150%的缩放
            # 默认是 Qt.HighDpiScaleFactorRoundingPolicy.Round，会将150%缩放变成200%
            QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    # 适应高DPI设备
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    # 解决图片在不同分辨率显示模糊问题
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    if platform.system() != 'Windows':
        app.setWindowIcon(QIcon('Img/MDCx.ico'))                                # 设置任务栏图标
    ui = MyMAinWindow()
    ui.show()
    app.installEventFilter(ui)
    newWin2 = CutWindow()
    sys.exit(app.exec_())
