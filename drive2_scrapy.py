# -*- coding: utf-8 -*-
import scrapy
import requests
import json
import sys
import argparse
import datetime


requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser(description="Crowler for drive2.ru - show new cars and car_dairy records")
parser.add_argument("--init", help="Get current state of all cars for next comparison")
parser.add_argument("--d2_car_model_id", help="Drive2.ru car model id, for example Lada Vesta have id = m_2853, by default value is m_2853", default="m_2853")

const = dict(
    DRIVE_URL="https://www.drive2.ru",
    SEARCH_URL="https://www.drive2.ru/ajax/carsearch.cshtml?context={0}&sort=Date&start=",
    DB_FILE="db_{0}.json"
)


def saver(obj, file):
    obj.update(count=str(len(obj)))
    obj.update(last_update=str(datetime.datetime.today()))
    with open(file, "w") as f:
        f.write(json.dumps(obj))


def loader(file):
    with open(file, "r") as f:
        return json.loads(f.read())


def comparer(new, saved):
    for k,v in new.iteritems():
        if k in saved:
            if new[k]["entries"] != saved[k]["entries"]:
                print "We have one new(or more|or less) record in '{0}' entry! Old was {1}. New is {2}. See it here {3}{4}".format(k, saved[k]["entries"], new[k]["entries"], const['DRIVE_URL'], new[k]["page_link"]) 
        else:
            print "We have new one car from {0}. See it here {1}{2}".format(k, const['DRIVE_URL'], new[k]["page_link"])
    saver(new, const['DB_FILE'])


def get_all_cars(url):
    all_html = ""
    start = 0
    while True:
        u = "{}{}".format(url, start)
        print u
        resp = requests.get(u)
        resp_json = json.loads(resp.text)
        all_html += resp_json["html"]
        if "start" in resp_json:
            start = resp_json["start"]
        else:
            break 
    return all_html


def get_elems_by_xpath(html, xpath):
    sel = scrapy.Selector(text=html)
    return sel.xpath(xpath).extract()


def prepare_dict():
    html = get_all_cars(const['SEARCH_URL'])
    titles = get_elems_by_xpath(html, '//span[contains(@class,"uname uname-color")]/text()')
    entries = get_elems_by_xpath(html, u'//span[@data-tt="Записей в бортжурнале"]/text()')
    hrefs = get_elems_by_xpath(html, '//div[@class="carcard-caption"]/a/@href')
    
    saved = {}
    for t, e, p  in zip(titles, entries, hrefs):
        saved[t] = {"entries": e, "page_link": p}

    return saved


def main():
    saved = prepare_dict()
    comparer(saved, loader(const["DB_FILE"]))


if __name__ == "__main__":
    args = parser.parse_args()
    const.update(DB_FILE=const["DB_FILE"].format(args.d2_car_model_id))
    const.update(SEARCH_URL=const["SEARCH_URL"].format(args.d2_car_model_id))
    if args.init:
        print "Get latest state for model {0}".format(args.d2_car_model_id)
        saved = prepare_dict()
        saver(saved, const["DB_FILE"])

    main()
