# coding : utf-8
import os
import re
import sys
import shutil
from urllib.request import urlopen, urlretrieve
from urllib.parse import quote_plus

ROOT_DIR = os.path.realpath(os.path.dirname(__file__))
INPUT_REGEX = "^(?:SB\s?\:\s?)?(\d+)\s(?:\[([A-Z]{3})\])?\s?([\w\-\s]*?)(?:/+[\w\s]*)?$"
ONLINE_REGEX = "(http://magiccards\.info/scans/en/\w{3}/\d{1,3}\w?\.jpg)"

# TODO: use getopts
output_dir = os.path.join(ROOT_DIR, "Proxy")
scans_dir = os.path.join(ROOT_DIR, "ref")
not_found_file = os.path.join(ROOT_DIR, "not_found.txt")
input_file = os.path.join(ROOT_DIR, 'Proxy.txt')
online_mode = True

# TODO: support special-encoded character, like 'æ'
# encoding_map = {u'æ': u'ae'}
# def normalize(to_norm):
#     print(to_norm.translate(encoding_map))
#     return to_norm.translate(encoding_map)

# TODO: support double-faced cards

# TODO: generate PDF files


def findcard(loc, name):
    regex = name.lower()
    # print("regex : '{}' ".format(regex))
    for root, dirs, files in os.walk(loc):
        for file in files:
            if re.match(regex, file, re.IGNORECASE) and os.path.getsize(os.path.join(root, file)) > 0:
                # print(os.path.getsize(os.path.join(root, file)))
                return os.path.join(root, file)


def card_not_found(name):
    mode = 'a'
    if not os.path.isfile(not_found_file):
        mode = 'w'
    with open(not_found_file, mode) as nfd:
        nfd.write(name + '\n')


def init():
    if not os.path.isfile(input_file):
        sys.exit("Provided input file is not valid")
    if online_mode is False and not os.path.isdir(scans_dir):
        sys.exit("Offline mode requires valid scans folder")
    if os.path.isdir(output_dir):
        # Delete previous work and init current one
        for filename in os.listdir(output_dir):
            os.unlink(os.path.join(output_dir, filename))
    else:
        # Create output dir if necessary
        os.makedirs(output_dir)


if __name__ == '__main__':
    init()
    placeholderid = 0
    # Process input file
    with open(input_file, 'r', encoding='utf8') as fd:
        for line in fd:
            if re.match(INPUT_REGEX, line, re.M | re.I) is not None:
                quantity, cardset, cardname = re.findall(INPUT_REGEX, line, re.M | re.I)[0]
                # print("quantity : " + quantity)
                # print("cardset : " + cardset)
                if online_mode is False:
                    location = scans_dir
                    if cardset != '':
                        location = os.path.join(scans_dir, cardset)
                    filepath = findcard(location, cardname)
                    if filepath is not None:
                        print("Create {} {}".format(quantity, os.path.basename(filepath)))
                        for i in range(0, int(quantity)):
                            placeholderid += 1
                            shutil.copy(filepath, os.path.join(output_dir, str(placeholderid) + ".jpg"))
                    else:
                        card_not_found(cardname)
                elif online_mode is True:
                    searchurl = ''
                    if cardset == '':
                        searchurl = "http://magiccards.info/query?q={}&v=card&s=cname".format(
                            quote_plus(cardname.lower()))
                    else:
                        searchurl = "http://magiccards.info/query?q={}+e%3A{}%2Fen&v=card&s=cname".format(
                            quote_plus(cardname.lower()),
                            quote_plus(cardset.lower()))
                    with urlopen(searchurl) as response:
                        httpcontent = response.readlines()
                    # urlretrieve(searchurl, cardname+".txt")
                    if re.search(ONLINE_REGEX, str(httpcontent)):
                        imageurl = re.findall(ONLINE_REGEX, str(httpcontent))[0]
                        print(imageurl)
                        print("Create {} {}".format(quantity, os.path.basename(cardname)))
                        tmpfile = urlretrieve(imageurl)[0]
                        for i in range(0, int(quantity)):
                            placeholderid += 1
                            shutil.copy(tmpfile, os.path.join(output_dir, str(placeholderid) + ".jpg"))
                    else:
                        card_not_found(cardname)
