import scrapy
import pandas as pd
from scrapy import Selector
from collections import defaultdict
import re

MY_URL_BASE = "en.wikipedia.org/wiki/"
DEFAULT_PROPS = ['born',
                 'education',
                 'alma_mater',
                 'spouse',
                 'parents',
                 'occupation',
                 'relatives']
EDUCATION_TYPE = ["education", "college", "alma mater"]
# NBSP = "&nbsp;"
NBSP = "\xa0"

"""Regular Expressions"""
VCARD_TABLE_CLASS = re.compile(r'infobox.*vcard')
DEGREE_RGX = re.compile(r'"\s(".*>.*</a>.*).*</')


class PeopleSpider(scrapy.Spider):
    name = 'people'
    allowed_domains = ['en.wikipedia.org']
    # start_urls = pd.read_csv('people_wikis.csv')

    start_urls = ['http://en.wikipedia.org/wiki/Robert_Reich',
                  'http://en.wikipedia.org/wiki/Yuval_Noah_Harari',
                  'http://en.wikipedia.org/wiki/Barack_Obama',
                  'http://en.wikipedia.org/wiki/Warren_Buffet',
                  'http://en.wikipedia.org/wiki/John_Kerry']

    def parse(self, response):
        spouses_dict = defaultdict()
        # print(response.xpath('//table[contains(@class,"vcard"]'))
        table_classes = response.css('.vcard').xpath("@class").extract()
        for cls in table_classes:
            match = re.search(VCARD_TABLE_CLASS, cls)
            if match:
                print("Class = {}".format(match.group(0)))
                table_cls = match.group(0)
            else:
                print("No Table Classes match vcard.")

        table_cls_str = "//table[@class='{}']/tbody/tr".format(table_cls)
        print(table_cls_str)
        my_infobox_trs = response.xpath(table_cls_str)

        people_dict = defaultdict()
        people_dict['schools'] = []
        people_dict['degrees'] = []
        people_dict['name'] = my_infobox_trs[0].xpath('th/div/text()').get()

        print("======== NEXT PERSON ========")
        for tr in my_infobox_trs:
            if tr.xpath('th'):
                if tr.xpath('th/descendant-or-self::*/text()').get() not in [None, '']:
                    label_raw = tr.xpath('th/descendant-or-self::*/text()').get().lower()
                    label = label_raw.replace(NBSP, " ")
                    print(label)
                    if label in EDUCATION_TYPE:
                        print("####### EDUCATION LIST #######")
                        my_odd_tags = tr.xpath('td//child::a[position() mod 2 = 1]')
                        my_odd_list = [x.xpath('text()').get() for x in my_odd_tags]
                        my_even_tags = tr.xpath('td//child::a[position() mod 2 = 0]')
                        my_even_list = [x.xpath('text()').get() for x in my_even_tags]
                        # print(my_list)
                        schools, degrees = self.get_education_data(my_odd_list, my_even_list)
                        people_dict['schools'] += schools
                        people_dict['degrees'] += degrees
                        continue
                    if label == 'spouse(s)':
                        print("======== SPOUSE(S) =======")
                        people_dict, spouses_dict = self.get_spouse_data(tr, people_dict, spouses_dict)
                        continue
                    if tr.xpath('th/a/text()').get():
                        label2 = tr.xpath('th/a/text()').get()
                        label += label2
                if tr.xpath('td'):
                    # print(tr.xpath('td/text()').get())
                    if tr.xpath('td/a/text()'):
                        val = tr.xpath('td/a/text()').get()
                        # print(tr.getAttribute('href'))
                    else:
                        val = tr.xpath('td/text()').get()
                    people_dict[label] = val
        print(people_dict)
        print(spouses_dict)

    def get_education_data(self, my_list1, my_list2):
        schools_list = []
        degrees_list = []
        for list_item in [my_list1, my_list2]:
            for item in list_item:
                if len(item) > 3:
                    schools_list.append(item)
                else:
                    degrees_list.append(item)

        return schools_list, degrees_list

    def get_spouse_data(self, my_spouse_data, my_people_dict, my_spouses_dict):
        spouse_list = []
        # if my_spouse_data.xpath('td/descendant-or-self::*/@href').get() not in [None, '']:
        if my_spouse_data.xpath('td//@href').get() not in [None, '']:
            spouse_href = my_spouse_data.xpath('td//@href')
            print(len(spouse_href))
            for wiki in spouse_href:
                spouse_name = wiki.get().split('/')[-1].replace('_', ' ')
                spouse_list.append(spouse_name)
                my_spouses_dict[spouse_name] = wiki.get()
                print(spouse_name)
                print(f"wiki: {wiki.get()}")
            my_people_dict['spouses'] = spouse_list
        # elif my_spouse_data.xpath('td/descendant-or-self::*/div/text()').get() not in [None, '']:
        elif my_spouse_data.xpath('td//text()').get() not in [None, '']:
            spouse_name = my_spouse_data.xpath('td//text()').get()
            my_people_dict['spouses'] = spouse_name
            print(spouse_name)
        else:
            my_people_dict['spouse'] += 'unknown'
            print(f"Spouse cannot be retrieved from {my_spouse_data}")

        return my_people_dict, my_spouses_dict
