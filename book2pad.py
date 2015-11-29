#!/usr/bin/env python
#-*- coding: utf8 -*-
#
# Copyright (C) 2012 Ruikai Liu <lrk700@gmail.com>
#
# This file is part of rbook.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import os
import sys
import shutil
import hashlib
import xml.etree.ElementTree as et
import zipfile


def new_plist():
    root = et.Element('plist', {'version':'1.0'})
    root.text = '\n'
    dic = et.Element('dict')
    dic.text = '\n\t'
    dic.tail = '\n'
    root.append(dic)
    key = et.Element('key')
    key.text = 'Books'
    key.tail = '\n\t'
    dic.append(key)
    array = et.Element('array')
    array.text = '\n\t\t'
    array.tail = '\n'
    dic.append(array)
    return et.ElementTree(root)

def parse_plist(plist):
    if os.path.exists(plist):
        tree = et.parse(plist)
    else:
        if not os.path.isdir(os.path.dirname(plist)):
            os.makedirs(os.path.dirname(plist))
        tree = new_plist()
    try:
        if not tree.getroot()[0][1].tag == 'array':
            raise IndexError
    except:
        tree = new_plist()
    finally:
        return (tree, tree.getroot()[0][1])

class Book(et.Element):
    def __init__(self,book):
        et.Element.__init__(self, 'dict')
        self.text = '\n\t\t\t'
        self.tail = '\n\t\t'
        self.add_attrib('Name', os.path.splitext(os.path.basename(book))[0])
        md5 = hashlib.md5()
        md5.update(open(book,'rb').read())
        self.add_attrib('Package Hash', md5.hexdigest().upper())
        self.add_attrib('Path', os.path.basename(book))
        self[-1].tail = '\n\t\t'

    def add_attrib(self, key, value):
        key_ele = et.Element('key')
        key_ele.text = key
        key_ele.tail = '\n\t\t\t'
        self.append(key_ele)
        value_ele = et.Element('string')
        value_ele.text = value
        value_ele.tail = '\n\t\t\t'
        self.append(value_ele)
        
def optimizedEntry(book):
    md5 = hashlib.md5()
    md5.update(open(book,'rb').read())
    fileHash = md5.hexdigest().upper()
    output = { 'Name': os.path.splitext(os.path.basename(book))[0],
               'Package Hash': fileHash,
               'Path': os.path.basename(book) }
    return output

def addbooks(root_dir, books):
    book_num = len(books)
    if book_num == 0:
        raise IndexError
    else:
        plist = os.path.join(root_dir, 'Books/Purchases/Purchases.plist')
        try:
            tree, array = parse_plist(plist)
            #Non-optimized is a plain xml file
            optimized = False
        except et.ParseError:
            import biplist
            #A completely different format! Not plain xml.
            tree = biplist.readPlist(plist)
            assert tree.items()[0][0] == 'Books'
            array = tree.items()[0][1]
            optimized = True #biplist optimized.
            print "Optimized plist"
        dest = os.path.dirname(plist)
        fail_list = []

        bar_len = int(int(os.popen('stty size', 'r').read().split()[1])*.75)
        step_len = 0
        print('Start transferring...')
        sys.stdout.write("[%s]" % (" " * (bar_len+1)))
        sys.stdout.flush()
        sys.stdout.write('%s%s' % ("\b" * (bar_len+2),'>'))
        sys.stdout.flush()

        if not optimized and len(array) > 0:
            array[-1].tail = '\n\t\t'
        for book in books:
            if not os.path.exists(book):
                fail_list.append(book)
            else:
                ext = os.path.splitext(book)[1].upper()
                if '.PDF' == ext:
                    if optimized:
                        array.append( optimizedEntry(book) )
                    else:
                        array.append(Book(book))
                    shutil.copyfile(book, os.path.join(dest, os.path.basename(book)))
                elif '.EPUB' == ext:
                    if optimized:
                        array.append( optimizedEntry(book) )
                    else:
                        array.append(Book(book))
                    folder = os.path.join(dest, os.path.basename(book))
                    os.mkdir(folder)
                    with zipfile.ZipFile(book, "r") as z:
                            z.extractall(folder)
                else:
                    fail_list.append(book)
            step_len += bar_len
            if step_len >= book_num:
                sys.stdout.write("\b%s>" % '='*int(float(step_len)/book_num))
                sys.stdout.flush()
                step_len = step_len%book_num
        if optimized:
            biplist.writePlist( tree, plist )
        else:
            array[-1].tail = '\n\t'
            tree.write(plist,'utf-8', True)
        sys.stdout.write('\n')
        print('Finished: %s books transfered' % str(len(books)-len(fail_list)))
        if len(fail_list):
            print('The following books are not transfered:')
            for book in fail_list:
                print(book)

def show_usage():
    print('Usage: book2pad [-d IPAD_MOUNTED_POINT] book1 [book2 book3 ...]\n')
    print('Use "-d" to indicate where ipad is mounted; '\
          'if omitted, the current\nworking directory '\
          'will be treated as where ipad is mounted.')


if __name__ == '__main__':
    try:
        if sys.argv[1] == '-h' or sys.argv[1] == '--help':
            show_usage()
        else:
            if sys.argv[1] == '-d':
                addbooks(os.path.abspath(sys.argv[2]), sys.argv[3:])
            else:
                addbooks(os.getcwd(), sys.argv[1:])
    except IndexError:
        print('Wrong arguments!\n')
        show_usage()
