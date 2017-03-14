# coding : utf-8
import os
import re
import sys
import shutil
from urllib.request import urlopen, urlretrieve
from urllib.parse import quote_plus
import configparser

ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__)))
CONF_DIR = os.path.realpath(os.path.join(ROOT_DIR, 'conf'))
INPUT_DIR = os.path.realpath(os.path.join(ROOT_DIR, 'input'))
OUTPUT_DIR = os.path.realpath(os.path.join(ROOT_DIR, 'output'))
SCANS_DIR = os.path.realpath(os.path.join(ROOT_DIR, 'scans'))

INPUT_REGEX = "^(?:SB\s?\:\s?)?(\d+)\s+(?:\[(.{2}.?)\])?\s?([\w\,\'\-\s\(\)\.]*?)(?:/+[\w\,\'\-\s]*)?$"
ONLINE_REGEX = "(http://magiccards\.info/scans/en/\w{2,3}/\d{1,3}\w?\.jpg)"
LAND_VERSION_REGEX = '\s?\(v\.?\s?([0-9]*)\)'
EDITION_REGEX = '\d{8}\t(.*)\t'

current_proxy_id = 1
output_path = os.path.join(OUTPUT_DIR, "Proxy")
output_dir = output_path
not_found_file = os.path.join(INPUT_DIR, "not_found.txt")
proxy_file = os.path.join(INPUT_DIR, "Proxy.txt")
edition_file = os.path.join(CONF_DIR, "Edition.txt")
scans_dir = SCANS_DIR
online_mode = True
offline_mode = True
mode_priority = "online"
edition_lines = []

# TODO: support special-encoded character, like 'æ'
# encoding_map = {u'æ': u'ae'}
# def normalize(to_norm):
#     print(to_norm.translate(encoding_map))
#     return to_norm.translate(encoding_map)

# TODO: support double-faced cards

# TODO: generate PDF files


def findcardoffline(name, searchdir=None):
    regex = name.lower()
    reg = re.compile(LAND_VERSION_REGEX, re.IGNORECASE)
    if reg.search(name):
        # print(reg.findall(name))
        land_version = reg.findall(name)[0]
        name = reg.sub('', name)
        regex = re.escape(name)
        regex += '\s?\(v\.\s?' + land_version + '\)'
    elif name in ['plains', 'island', 'swamp', 'mountain', 'forest']:
        regex += '\s?\(v\.\s?1\)'
    regex += '(?! )\.'  # not followed by a space, but followed by a dot
    found = ''
    # print("regex : '{}' ".format(regex))
    for edition_line in edition_lines:
        # print(edition_line)
        if re.match(EDITION_REGEX, edition_line):
            trigram = re.findall(EDITION_REGEX, edition_line)[0]
            # print(trigram)
            edition_scan_path = os.path.join(scans_dir, trigram)
            # print(edition_scan_path + " test")
            if os.path.exists(edition_scan_path):
                for filename in os.listdir(edition_scan_path):
                    if re.match(regex, filename, re.IGNORECASE):
                        edition_file_path = os.path.join(edition_scan_path, filename)
                        if os.path.getsize(edition_file_path) > 0:
                            # print(edition_file_path)
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

    # All is OK !
    if os.path.isdir(output_dir):
        # Delete previous work and init current one
        for filename in os.listdir(output_dir):
            os.unlink(os.path.join(output_dir, filename))
    else:
        # Create output dir if necessary
        os.makedirs(output_dir)
    shutil.copy(os.path.join(CONF_DIR, "Proxy.sla"), os.path.join(OUTPUT_DIR))
    open(not_found_file, 'w').close()


# TODO: usage function
def usage():
    print("Usage: {} [-h] [-m (online|offline)] [-r scansDir] [inputFile [outputDir]]"
          .format(os.path.basename(sys.argv[0])))


def get_program_param():
    config = configparser.ConfigParser()
    config.read(os.path.join(ROOT_DIR, 'conf', 'global.ini'))
    global proxy_file
    global output_dir
    global output_path
    global online_mode
    global scans_dir
    global offline_mode
    global mode_priority
    # Proxy input file
    proxy_file = config.get('input', 'proxy_list')
    if not os.path.isabs(proxy_file):
        proxy_file = os.path.realpath(os.path.join(ROOT_DIR, proxy_file))
    if not os.path.isfile(proxy_file):
        sys.exit(proxy_file + "is not a valid file")
    # Output directory
    output_path = config.get('output', 'output_path')
    output_dir = output_path
    if not os.path.isabs(output_dir):
        output_dir = os.path.realpath(os.path.join(ROOT_DIR, output_dir, 'Proxy'))
    # Search modes
    offline_mode = config.getboolean('mode', 'offline_mode')
    online_mode = config.getboolean('mode', 'online_mode')
    mode_priority = config.get('mode', 'mode_priority')
    # Scans directory (offline mode)
    scans_dir = config.get('input', 'scans_directory')
    if not os.path.isabs(scans_dir):
        scans_dir = os.path.realpath(os.path.join(ROOT_DIR, scans_dir))
    if offline_mode and (not scans_dir or not os.path.isdir(scans_dir)):
        print("Scans directory muste be defined and valid for offline mode")
    global edition_lines
    with open(edition_file, 'r', encoding='utf8') as filedesc:
        edition_lines = list(reversed(filedesc.readlines()))


def copy_card(path, quantity):
    global current_proxy_id
    for i in range(0, int(quantity)):
        shutil.copy(path, os.path.join(output_dir, str(current_proxy_id) + ".jpg"))
        current_proxy_id += 1


def create_proxy_online(quantity, cardname, cardset=''):
    global current_proxy_id

    # print("quantity : " + quantity)
    # print("cardset : " + cardset)
    if cardset == '':
        searchurl = "http://magiccards.info/query?q=!{}&v=card&s=cname".format(
            quote_plus(cardname.lower()))
    else:
        searchurl = "http://magiccards.info/query?q={}+e%3A{}&v=card&s=cname".format(
            quote_plus(cardname.lower()),
            quote_plus(cardset.lower()))
    # print("Search with : {}".format(searchurl))
    with urlopen(searchurl) as response:
        httpcontent = response.readlines()
    if re.search(ONLINE_REGEX, str(httpcontent)):
        imageurl = re.findall(ONLINE_REGEX, str(httpcontent))[0]
        print("--> {} '{}' created using {}".format(quantity, cardname, imageurl))
        tmpfile = urlretrieve(imageurl)[0]
        copy_card(tmpfile, quantity)
        for i in range(0, int(quantity)):
            current_proxy_id += 1
            shutil.copy(tmpfile, os.path.join(output_dir, str(current_proxy_id) + ".jpg"))
        return 1
    else:
        print("--> '" + cardname + "' not found online with URL " + searchurl)
        return 0


def create_proxy_offline(quantity, cardname, cardset=''):
    filepath = findcardoffline(cardname, cardset)
    # print(filepath)
    if filepath is not None:
        print("--> {} '{}' created using file {}".format(quantity, cardname, filepath))
        copy_card(filepath, quantity)
        return 1
    else:
        print("'{}' not found in scans directory ".format(cardname))
        return 0


def process_input_file(input_file):
    with open(input_file, 'r', encoding='utf8') as fd:
        for line in fd:
            # Test line format
            if re.match(INPUT_REGEX, line, re.M | re.I) is not None:
                quantity, cardset, cardname = re.findall(INPUT_REGEX, line, re.M | re.I)[0]
                quantity = quantity.strip()
                cardset = cardset.strip()
                cardname = cardname.strip()
                # print("quantity : " + quantity)
                # print("cardset : " + cardset)
                if cardset == '':
                    print("Searching for '{}' in the most recent edition".format(cardname))
                else:
                    print("Searching for '{}' in [{}] edition".format(cardname, cardset))
                if online_mode and offline_mode:
                    if mode_priority.lower() == "online":
                        if not create_proxy_online(quantity, cardname, cardset):
                            if not create_proxy_offline(quantity, cardname, cardset):
                                card_not_found(line)
                    elif mode_priority.lower() == 'offline':
                        if not create_proxy_offline(quantity, cardname, cardset):
                            if not create_proxy_online(quantity, cardname, cardset):
                                card_not_found(line)
                    else:
                        print("No mode priority defined, exiting...")
                        sys.exit(2)
                elif online_mode:
                    if not create_proxy_online(quantity, cardname, cardset):
                        card_not_found(line)
                elif offline_mode:
                    if not create_proxy_offline(quantity, cardname, cardset):
                        card_not_found(line)
                else:
                    print("No mode selected, exiting...")
                    sys.exit(2)


if __name__ == '__main__':
    get_program_param()
    init()
    # Process input file
    process_input_file(proxy_file)
