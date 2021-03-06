#! /bin/env python
# -*- coding: utf-8 -*-
"""
泛读模式，提供点赞数最多并且差评数较少的回答
修改版
"""
import sys
import requests
from bs4 import BeautifulSoup
import jieba
import urllib
from tqdm import *
import time, threading
import random
import get_weather
from selenium import webdriver
from time import ctime
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
sys.setrecursionlimit(1000000) # 递归深度，默认只有900

stopwords = ['是', '的', '谁', '什么', '和', '了', '我', '你', '知道', '哪', '？', '?', '，', ',', '.', '。', '：', ':']


def clean_question(question):
    ques = list(jieba.cut(question))
    for w in stopwords:
        if w in ques: ques.remove(w)
    return ques


def match_key_words(main_ques, other):
    # if len(other) < 8:
    #    return True
    for word in main_ques:
        if word in other:
            return True
    return False


def parse_subweb(url, ques):
    badwords = []
    with open("./badwords.txt", 'r', encoding='utf-8') as b:
        for line in b.readlines():
            badwords.append(line.strip('\n'))
    url_sub = url.get('href')
    wb_data_sub = requests.get(url_sub)
    wb_data_sub.encoding = ('gbk')
    soup_sub = BeautifulSoup(wb_data_sub.content, 'lxml')
    best_answer = soup_sub.find('div', class_="best-text mb-10")
    agree_point_p = soup_sub.find('span', class_="iknow-qb_home_icons evaluate evaluate-32 ")
    disagree_point_p = soup_sub.find('span', class_="iknow-qb_home_icons evaluate evaluate-bad evaluate-32 ")
    agree_point = 0
    disagree_point = 0
    if agree_point_p != None and disagree_point_p != None:
        agree_point = int(agree_point_p.get('data-evaluate'))
        disagree_point = int(disagree_point_p.get('data-evaluate'))
        # print(agree_point, disagree_point)

    if best_answer != None:
        best = best_answer.get_text(strip=True)
        # 如果问题的关键词，出现在了答案中，则判断是好的回答，改进，可以根据点赞比判断
        # 长度小于100,过滤“展开全部”
        contain_badword = [badword for badword in badwords if badword in best]
        if match_key_words(ques, best) and len(best) < 1000 \
                and len(contain_badword) == 0:
            best = best.strip("展开全部")
            best = best.strip("展开")
            return best
    else:
        better_answer = soup_sub.find_all('div', class_="answer-text mb-10 line")

        if better_answer != None:
            for i_better, better_answer_sub in enumerate(better_answer):
                better = better_answer_sub.get_text(strip=True)
                contain_badword = [badword for badword in badwords if badword in better]
                if match_key_words(ques, better) and len(better) < 1000 \
                        and len(contain_badword) == 0:
                    better = better.strip("展开全部")
                    better = better.strip("展开")
                    return better

def get_top_page(ques, one, url):
    evidences = []
    page_question_No = 1 + one
    # print("url: " + url)
    wb_data = requests.get(url)
    wb_data.encoding = ('gbk')
    soup = BeautifulSoup(wb_data.content, 'lxml')
    webdata = soup.select('a.ti')
    # import multiprocessing
    # pool = multiprocessing.Pool(processes=4)
    for title, url in zip(webdata, webdata):
        # evidence = pool.apply_async(parse_subweb, (url, ques, ))
        # if evidence.get() != None:
        #     evidences.append(evidence.get())
        evidence = parse_subweb(url, ques)
        if evidence != None:
            evidences.append(evidence)
            break
        page_question_No += 1
    # pool.close()
    # pool.join()
    return evidences


def get_page(ques, one, url):
    evidences = []
    page_question_No = 1 + one
    # print("url: " + url)
    wb_data = requests.get(url)
    wb_data.encoding = ('gbk')
    soup = BeautifulSoup(wb_data.content, 'lxml')
    webdata = soup.select('a.ti')
    # import multiprocessing
    # pool = multiprocessing.Pool(processes=4)
    for title, url in zip(webdata, webdata):
        # evidence = pool.apply_async(parse_subweb, (url, ques, ))
        # if evidence.get() != None:
        #     evidences.append(evidence.get())
        evidence = parse_subweb(url, ques)
        if evidence != None:
            evidences.append(evidence)
        page_question_No += 1
    # pool.close()
    # pool.join()
    return evidences


evidencess = []


def get_evidences(question, pages=2):
    print('Getting eivdences from baiduzhidao....')
    url = "https://zhidao.baidu.com/search?word=" + urllib.parse.quote(question) + "&pn="
    ques = clean_question(question)
    evidences_list = []
    for one in range(0, pages, 1):
        evidencess = []
        # evidences = get_multi_thread_page(ques, one, url + str(one))
        # evidences = pool.apply_async(get_page, (ques, one, url + str(one), ))
        # evidences = get_page(ques, one, url + str(one))
        evidences = get_top_page(ques, one, url + str(one))
        if evidences != []:
            evidences_list.extend(evidences)
        #time.sleep(1)
    # pool.close()
    # pool.join()
    print('evidences: ', len(evidences_list))
    # evidences_list = rank(evidneces_list)
    return evidences_list


# ---------------------------------
def rule_engine(input):
    """
    目前是比较简单的规则（随机数）
    :param input:
    :return:
    """
    random.shuffle(input)
    return input[0]


# evidencess = []
lock = threading.Lock()


def get_href(ques, title, url):
    url_sub = url.get('href')
    wb_data_sub = requests.get(url_sub)
    wb_data_sub.encoding = ('gbk')
    soup_sub = BeautifulSoup(wb_data_sub.content, 'lxml')
    best_answer = soup_sub.find('pre', class_="best-text mb-10")

    evidences = ['no_answer']
    if best_answer != None:
        best = best_answer.get_text(strip=True)
        if match_key_words(ques, best):
            if lock.acquire():
                evidencess.append(best)
                lock.release()
                # print(evidencess)
    else:
        better_answer = soup_sub.find_all('div', class_="answer-text line")

        if better_answer != None:
            for i_better, better_answer_sub in enumerate(better_answer):
                better = better_answer_sub.get_text(strip=True)
                if match_key_words(ques, better):
                    if lock.acquire():
                        evidencess.append(better)
                        lock.release()
                        # print(evidencess)
                        # return 1 #evidences


def get_multi_thread_page(ques, one, url):
    threads = []
    # evidences = []

    page_question_No = 1 + one
    wb_data = requests.get(url)
    wb_data.encoding = ('gbk')
    soup = BeautifulSoup(wb_data.content, 'lxml')
    webdata = soup.select('a.ti')
    nb_thread = len(webdata)

    for i in range(nb_thread):
        t = threading.Thread(target=get_href(ques, webdata[i], webdata[i]), name='LoopThread')
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
        # href_evidences = t.get_result()
        # evidneces.extend(href_evidences)

    return evidencess


if __name__ == '__main__':
    start = time.time()
    wq = get_weather.weather_query()
    # question = '三生三世十里桃花女主角是谁？'
    # question = "海南有哪些美食"
    # question = "我要去海南旅游，有什么可以建议的吗？"
    question = "海南的著名景点有哪些？"
    # question = "海南夏天的天气一般怎么样？"
    # question = "最近三亚的天气怎么样？"
    # question = "我想吃龙虾"
    # question = "海南冬天的天气一般怎么样？"
    # question = "三亚的机场在哪里？"
    # question = "你好啊"
    # question = str(sys.argv[1])
    flag = 0
    weather_words = ["天气", "气温", "风速", "风向", "温度"]
    for item in weather_words:
        if item in question:
            flag = 1
    if flag:
        date, city_name = wq.match_rule(question)
        info = wq.go(city_name, date)
        print(info)
        if info == "这个城市没有查不到..." or info == "抱歉,您查找的天气信息暂时没有哦~":
            evidences = get_evidences(question)
            # 规则模块
            rule_rank = rule_engine(list(range(len(evidences))))
            print(evidences[rule_rank])

    else:
        evidences = get_evidences(question)
        # 规则模块
        rule_rank = rule_engine(list(range(len(evidences))))
        print(evidences[rule_rank])
    end = time.time()
    print("cost time: " + str(end-start))
    # for item in range(len(evidences)):
    #     print(evidences[item])
    #     print("")