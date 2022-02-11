"""
Server class for cvmfs-server-metadata
"""

import json

import urllib

from cvmfsscraper.repository import Repository
from cvmfsscraper.tools import fetch

class Server:
    def __init__(self, server, repos, ignore_repos):

        # 1. Get repos from server:
        # /cvmfs/info/v1/repositories.json

        self.name = server
        self.forced_repositories = repos
        self.ignored_repositories = ignore_repos

        self.fetch_errors = []
        self.repositories = self.populate_repositories()
        self.geoapi_status = self.check_geoapi_status()

    def __str__(self):
        content = "Server: " + self.name + "\n"
        content += "Repositories: " + str(len(self.repositories)) + "\n"
        for repo in self.repositories:
            content += "  - " + repo.name + "\n"
        return content


    def populate_repositories(self):
        content = fetch(self, self.name, "cvmfs/info/v1/repositories.json")

        if content:
            return self.process_repositories_json(content)
        else:
            return []

    def process_repositories_json(self, json_data):
        repos_info = json.loads(json_data)
        repos = []
        if 'replicas' in repos_info:
            for repo_info in repos_info['replicas']:
                self.server_type = 1
                if self.process_repo(repo_info):
                    # use "str" to convert from unicode to string
                    repos.append( Repository( self, repo_info["name"], str(repo_info["url"])) )

        if 'repositories' in repos_info:
            for repo_info in repos_info['repositories']:
                self.server_type = 0
                if self.process_repo(repo_info):
                    repos.append( Repository( self, repo_info["name"], str(repo_info["url"])) )
        
        return repos

    def process_repo(self, repo_info):
        repo_name = repo_info["name"]
        if self.forced_repositories and repo_name not in self.forced_repositories:
            return 0

        if repo_name in self.ignored_repositories:
            return 0

        if 'pass-through' in repo_info:
            return 0

        return 1

    def check_geoapi_status(self):
        """Checks the geoapi for the server with the first repo available.
        Return values:
            0 if everything is OK
            1 if the geoapi respons, but with the wrong data
            2 if the geoapi fails to respond
            9 if there is no repository to use for testing
        """
        # GEOAPI only applies to stratum1s
        if self.server_type != 1:
            return 0

        if not self.repositories:
            return 9

        url = ('http://%s/cvmfs/%s/api/v1.0/geo/cvmfs-stratum-one.cern.ch'
               '/cvmfs-s1fnal.opensciencegrid.org,cvmfs-stratum-one.cern.ch,cvmfs-stratum-one.ihep.ac.cn'
               % (self.name, self.repositories[0].name))
        try:
            request = urllib.request.Request(url)
            response = urllib.request.urlopen(request)
            output = response.read().decode('utf-8').strip()
            if output == '2,1,3':
                return 1
            else:
                return 0
        except Exception as e:
            return 2



