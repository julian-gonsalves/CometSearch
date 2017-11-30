# -*- coding: utf-8 -*-

import sys
from urllib import urlopen
from BeautifulSoup import BeautifulSoup
from Queue import Queue, Empty
from threading import Thread

visited = set()
queue = Queue()

def get_parser(host, root, charset):

    def parse():
        try:
            while True:
                url = queue.get_nowait()
                try:
                    content = urlopen(url).read().decode(charset)
                except UnicodeDecodeError:
                    continue
                for link in BeautifulSoup(content).findAll('a'):
                    try:
                        href = link['href']
                    except KeyError:
                        continue
                    if not href.startswith('http://'):
                        href = 'http://%s%s' % (host, href)
                    if not href.startswith('http://%s%s' % (host, root)):
                        continue
                    if href not in visited:
                        visited.add(href)
                        queue.put(href)
                        print href
        except Empty:
            pass

    return parse

if __name__ == '__main__':
    host, root, charset = sys.argv[1:]
    parser = get_parser(host, root, charset)
    queue.put('http://%s%s' % (host, root))
    workers = []
    for i in range(5):
        worker = Thread(target=parser)
        worker.start()
        workers.append(worker)
    for worker in workers:
        worker.join()