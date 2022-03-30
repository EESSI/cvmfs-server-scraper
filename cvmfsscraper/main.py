# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib.resources import Package
from time import time

from cvmfsscraper.server import Server

def scrape_server(server=None, repos=[], ignore_repos=[], type=None):
    """ Scrape a specific server """

    s = Server(server, repos, ignore_repos, type)
    return s


def scrape(stratum0=[], stratum1=[], repos=[], ignore_repos=[]):
    """
    Scrape a set of servers
    """

    server_objects = []
    processes = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        for server in stratum1:
            processes.append(executor.submit(scrape_server, server, repos, ignore_repos, 1))
        for server in stratum0:
            processes.append(executor.submit(scrape_server, server, repos, ignore_repos, 0))

    for task in as_completed(processes):
        server_objects.append(task.result())

    return server_objects
