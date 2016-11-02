#! /usr/bin/env python
# -*- coding:utf-8 -*-

import requests
from bs4 import BeautifulSoup as bs
import os
import hashlib
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import json
import sys
import time
reload(sys)
sys.setdefaultencoding('utf-8')
from subprocess import call

h = {"Accept-Encoding": "gzip, deflate, sdch", "user_agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36"}

def _lst(page = 1, retry = 10):
  
  print "page %s" % (page, )
  #h["Accept"] = "application/json, text/javascript, */*; q=0.01"
  h["X-Requested-With"] = "XMLHttpRequest"
  if page > 1:
    h["Referer"] = "http://www.flaticon.com/packs/%s?order_by=2" % (page-1, )
    url = "http://www.flaticon.com/ajax/packs/search/%s?order_by=2" % (page, )
  else:
    h["Referer"] = "http://www.flaticon.com/packs?order_by=2"
    url = "http://www.flaticon.com/ajax/packs/search?order_by=2"
  while retry > 0:
    try:
      r = requests.get(url, headers = h)
      j = json.loads(r.text)
      print len(j["items"])
    except Exception as e:
      print "page %s: retry %s" % (page, retry)
      retry -= 1
      print e
      time.sleep(5)
      continue
    break
  if retry == 0:
    return ""  
  return r.text

def get_lst(total = 100):
  pool = ThreadPool(16)
  r = pool.map(_lst, range(1, total+1))
  pool.close() 
  pool.join()
  items = []
  for i in r:
    if i == "":
      continue
    try:
      j = json.loads(i)
      items += j["items"]
    except:
      print i
      continue
  return items
#  items = []
#  for i in range(1, total + 1):
#    r = _lst(i)
#    time.sleep(5)
#    try:
#      j = json.loads(r)
#      items += j["items"]
#    except:
#      print r
#      continue
#  return items
    
    

def _save(content, filename, path):
  try:
    if not os.path.isdir(path):
      _mkdir(path)
    with open(path + filename, "w") as f:
      f.write(content.encode("utf-8"))
    return True
  except Exception as e:
    print e
    return False

def _mkdir(path):
  try:
    p = path.split("/")
    p = ["/".join(p[:i+1]) for i in range(len(p))][1:]
    for i in p:
      if not os.path.isdir(i):
        os.mkdir(i)
    return True
  except Exception as e:
    print e
    return False

def _download_link(url, retry = 3):
  link = ""
  while retry > 0:
    try:
      r = requests.get(url, headers = h)
      soup = bs(r.text)
      link = soup.select("a.btn-download-pack")[0]["href"]
    except Exception as e:
      retry -= 1
      print e
    break
  print link
  return link

def _category_lst():
  url = "http://www.flaticon.com/categories/"
  cate = []
  try:
    r = requests.get(url, h)
    soup = bs(r.text)
    c = soup.select("article.box")
    for i in c:
      name = i.select("a")[0]["title"]
      url = i.select("a")[0]["href"]
      cate.append((name, url))
  except Exception as e:
    print e
  return cate

def _icon_lst(c):
  icons = []
  url = c[1]
  try:
    r = requests.get(url, h)
    soup = bs(r.text)
    total = soup.select("#pagination-total")[0].text
    cid = soup.find("meta", {"property":"og:image"})['content'].split("/")[-1].split("-")[0]
    p = []
    for page in range(1, int(total) + 1):
      i = {}
      i["name"] = c[0]
      i["url"] = c[1]
      i["cid"] = cid
      if page != 1:
        i["page"] = page
      else:
        i["page"] = ""
      p.append(i)
    pool = ThreadPool(16)
    items = pool.map(_get_icon_info, p)
    pool.close() 
    pool.join()
    for i in items:
      icons += i
    print len(icons)
  except Exception as e:
    print e
  return icons

def _get_icon_info(i):
  print i
  url = "http://www.flaticon.com/ajax/category/%s/%s" % (i["cid"], i["page"])
  if i["page"] == "" or i == 2:
    h["Referer"] = "%s/%s" % (i["url"], "")
  else:
    h["Referer"] = "%s/%s" % (i["url"], i["page"]-1)
  h["X-Requested-With"] = "XMLHttpRequest"
  h["Accept"] = "application/json, text/javascript, */*; q=0.01"
  h["Host"] = "www.flaticon.com"
  h["Connection"] = "keep-alive"
  print url
  try:
    r = requests.get(url, headers = h)
    j = json.loads(r.text)
    print len(j["items"])
    return j["items"]
  except Exception as e:
    print e
    return []

if __name__ == "__main__":
  data_path = "./data/"
  lst_file = "lst.json"
  lst_file_path = "%s%s" % (data_path, lst_file)
  if not os.path.isfile(lst_file_path):
    lst = get_lst(171)
    print "lst done"
    _save(json.dumps(lst), lst_file, data_path)
  else:
    with open(lst_file_path, "r") as f:
      lst = json.loads(f.read())


  _mkdir(data_path + "icons")
  links = []
  for i in lst:
    links.append(i["link"])
  if not os.path.isfile("%s%s" % (data_path, "download.txt")):
    pool = ThreadPool(16)
    download_link = pool.map(_download_link, links)
    pool.close() 
    pool.join()
  else:
    with open("%s%s" % (data_path, "download.txt"), "r") as f:
      download_link = [i for i in f.read().split("\n") if i != ""]

  with open("%s%s" % (data_path, "download.txt"), "w") as f:
    for l in download_link:
      if not os.path.isfile("%s%s%s" % (data_path, "icons/", l.split("/")[-1])):
        f.write(l + "\n")
      else:
        print "skip %s" % (l, )
    
  call(["./download.sh"])

  cates = _category_lst()
  pool = ThreadPool(16)
  icons = pool.map(_icon_lst, cates)
  pool.close() 
  pool.join()

  cate_dir = "%s%s" % (data_path, "category")
  _mkdir(cate_dir)
  for i in range(len(cates)):
    if not os.path.isfile("%s/%s" % (cate_dir, cates[i][0])):
      with open("%s/%s" % (cate_dir, cates[i][0]), "w") as f:
        c = {}
        c["icons"] = icons[i]
        c["info"] = cates[i]
        f.write(json.dumps(c))


