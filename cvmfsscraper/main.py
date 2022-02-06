# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib.resources import Package
from time import time

from cvmfsscraper.server import Server

def scrape_server(server=None, repos=[], ignore_repos=[]):
    """ Scrape a specific server """

    s = Server(server, repos, ignore_repos)
    return s


def scrape(servers=[], repos=[], ignore_repos=[]):
    """
    Scrape a set of servers
    """

    server_objects = []
    processes = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        for server in servers:
            processes.append(executor.submit(scrape_server, server, repos, ignore_repos))

    for task in as_completed(processes):
        server_objects.append(task.result())

    return server_objects
