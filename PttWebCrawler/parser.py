import json
import csv
import argparse

__version__ = '1.0'

class JsonPaser:
    def __init__(self, cmdline=None, as_lib=False):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='''
            Parsing data from ptt
        ''')
        parser.add_argument('-f', metavar='FILE_NAME', help='File name', required=True)
        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

        args = parser.parse_args(cmdline)
        self.FILENAME = args.f
        self.draw_data()

    def draw_data(self):
        print("self.FILENAME=" + self.FILENAME)
        input_file = open (self.FILENAME, "r", encoding='utf-8')
        json_array = json.load(input_file)

        with open('output.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Title', 'Conetnt'])

            for item in json_array:
                writer.writerow([item['article_title'], item['content']])

if __name__ == '__main__':
    c = JsonPaser()