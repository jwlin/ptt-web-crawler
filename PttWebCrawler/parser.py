import json
import csv
import argparse
# import re

__version__ = '1.0'
# __ITEM_NAME__ = '物品內容 '
# __ITEM_PRICE__ = '交易價格 '
# __ITEM_DETAIL__ = '詳細說明 '

class JsonPaser:
    def __init__(self, cmdline=None, as_lib=False):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='''
            Parsing data from ptt
        ''')
        parser.add_argument('-i', metavar='IN_FILE', help='Inpyt file', required=True)
        parser.add_argument('-o', metavar='OUT_FILE', help='Output file', required=True)
        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

        args = parser.parse_args(cmdline)
        self.IN_FILE = args.i
        self.OUT_FILE = args.o
        # self.draw_data()
        self.get_info()

    def draw_data(self):
        print("self.IN_FILE=" + self.IN_FILE)
        input_file = open(self.IN_FILE, "r", encoding='utf-8')
        json_array = json.load(input_file)

        with open('output.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # writer.writerow(['Title', 'Conetnt'])

            for item in json_array:
                writer.writerow([item['article_title'], item['content']])
    
    def get_info(self):
        __ITEM_NAME__ = '物品內容 '
        __ITEM_PRICE__ = '交易價格 '
        __ITEM_PRICE_NOTE__ = '(請務必填寫，成交後嚴禁刪修價格) '
        __ITEM_DETAIL__ = '詳細說明 '
        data = []

        with open(self.IN_FILE, newline='') as csvfile:
            rows = csv.reader(csvfile)
            fo = open(self.OUT_FILE, 'w')

            for row in rows:
                content_data = ''.join(row[1])
                data.clear()
                
                #Item Content
                startIndex = content_data.find(__ITEM_NAME__) + 5
                endIndex = content_data.find(__ITEM_PRICE__)
                itemName = content_data[startIndex:endIndex]
                data.append(itemName)
                # print(itemName)

                #Item Price
                startIndex = content_data.find(__ITEM_PRICE__) + 5
                endIndex = content_data.find(__ITEM_DETAIL__)
                itemPrice = content_data[startIndex:endIndex]
                noteIndex = itemPrice.find(__ITEM_PRICE_NOTE__)
                if -1 != noteIndex:
                    itemPrice = itemPrice[noteIndex+18:]
                data.append(itemPrice)
                # print(itemPrice)

                #Item Detail
                itemDetail = content_data[endIndex:]
                data.append(itemDetail)
                # print(itemDetail)

                # Write to another csv file
                for item in data:
                    fo.write(item + ',')
                fo.write('\n')
        fo.close()


if __name__ == '__main__':
    c = JsonPaser()