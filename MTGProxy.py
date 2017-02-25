# coding : utf-8
import os
import re
import sys
import shutil
from urllib.request import urlopen, urlretrieve
from urllib.parse import quote_plus
import configparser

ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
INPUT_REGEX = "^(?:SB\s?\:\s?)?(\d+)\s+(?:\[(.{2}.?)\])?\s?([\w\,\'\-\s]*?)(?:/+[\w\,\'\-\s]*)?$"
ONLINE_REGEX = "(http://magiccards\.info/scans/en/\w{2,3}/\d{1,3}\w?\.jpg)"

output_dir = os.path.join(ROOT_DIR, "output", "Proxy")
not_found_file = os.path.join(ROOT_DIR, "input", "not_found.txt")
input_file = os.path.join(ROOT_DIR, "input", "Proxy.txt")
edition_file = os.path.join(ROOT_DIR, "conf", "Edition.txt")
scans_dir = ''
online_mode = True

# TODO: support special-encoded character, like 'æ'
# encoding_map = {u'æ': u'ae'}
# def normalize(to_norm):
#     print(to_norm.translate(encoding_map))
#     return to_norm.translate(encoding_map)

# TODO: support double-faced cards

# TODO: generate PDF files


def findcard(loc, name, searchdir=None):
    regex = name.lower()
    found = ''
    # print("regex : '{}' ".format(regex))
    with open(edition_file, 'r', encoding='utf8') as filedesc:
        edition_lines = reversed(filedesc.readlines())
    for edition_line in edition_lines:
        # print(edition_line)
        if re.match("\d{8}\t(.{3})\t", edition_line):
            trigram = re.findall("\d{8}\t(.{3})\t", edition_line)[0]
            # print(trigram)
            edition_scan_path = os.path.join(loc, trigram)
            # print(edition_scan_path + " test")
            if os.path.exists(edition_scan_path):
                for filename in os.listdir(edition_scan_path):
                    edition_file_path = os.path.join(edition_scan_path, filename)
                    if re.match(regex, filename, re.IGNORECASE) and os.path.getsize(edition_file_path) > 0:
                        print(edition_file_path)
                        found = edition_file_path
                        if not searchdir or os.path.basename(edition_scan_path) == searchdir:
                            return found
    if found:
        return found


def card_not_found(name):
    mode = 'a'
    if not os.path.isfile(not_found_file):
        mode = 'w'
    with open(not_found_file, mode) as nfd:
        nfd.write(name)
        # nfd.write(name + '\n')


def init():
    if not os.path.isfile(input_file):
        sys.exit("Provided input file is not valid")
    if online_mode is False:
        if not scans_dir:
            print("Ref option is mandatory in offline mode")
            usage()
            sys.exit(1)
        elif not os.path.isdir(scans_dir):
            sys.exit("Offline mode requires valid scans folder")
    print("output_dir is : " + output_dir)
    # All is OK !
    if os.path.isdir(output_dir):
        # Delete previous work and init current one
        for filename in os.listdir(output_dir):
            os.unlink(os.path.join(output_dir, filename))
    else:
        # Create output dir if necessary
        os.makedirs(output_dir)
    open(not_found_file, 'w').close()


# TODO: usage function
def usage():
    print("Usage: {} [-h] [-m (online|offline)] [-r scansDir] [inputFile [outputDir]]"
          .format(os.path.basename(sys.argv[0])))


def process_param():
    config = configparser.ConfigParser()
    config.read(os.path.join(ROOT_DIR, 'conf', 'global.ini'))
    global input_file
    global output_dir
    global online_mode
    global scans_dir

    input_file = config.get('input', 'proxy_list')
    if not os.path.isabs(input_file):
        input_file = os.path.realpath(os.path.join(ROOT_DIR, input_file))

    output_path = config.get('output', 'output_path')
    output_dir = output_path
    if not os.path.isabs(output_dir):
        output_dir = os.path.realpath(os.path.join(ROOT_DIR, output_dir, 'Proxy'))
    # config.getboolean('mode', 'online_mode')
    if config.get('mode', 'mode') == "online":
        online_mode = True
    elif config.get('mode', 'mode') == "offline":
        online_mode = False

    scans_dir = config.get('input', 'scans_directory')
    if not os.path.isabs(scans_dir):
        scans_dir = os.path.realpath(os.path.join(ROOT_DIR, scans_dir))


if __name__ == '__main__':
    # process_opts()
    process_param()

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
                    filepath = findcard(location, cardname, searchdir=cardset)
                    # print(filepath)
                    if filepath is not None:
                        print("Create {} {}".format(quantity, os.path.basename(filepath)))
                        for i in range(0, int(quantity)):
                            placeholderid += 1
                            shutil.copy(filepath, os.path.join(output_dir, str(placeholderid) + ".jpg"))
                    else:
                        print("Not found : {}".format(cardname))
                        card_not_found(line)
                elif online_mode is True:
                    searchurl = ''
                    if cardset == '':
                        searchurl = "http://magiccards.info/query?q=!{}&v=card&s=cname".format(
                            quote_plus(cardname.lower()))
                    else:
                        searchurl = "http://magiccards.info/query?q=!{}+e%3A{}&v=card&s=cname".format(
                            # searchurl = "http://magiccards.info/query?q=!{}+e%3A{}%2Fen&v=card&s=cname".format(
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
                        print(cardname + " not found with : " + searchurl)
                        card_not_found(line)
