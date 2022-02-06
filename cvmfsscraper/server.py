"""
Server class for cvmfs-server-metadata
"""

import json

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
        self.repositories = []

        self.repos = self.populate_repositories()

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
        if 'replicas' in repos_info:
            self.server_type = 1
            for repo_info in repos_info['replicas']:
                if self.process_repo(repo_info):
                    # use "str" to convert from unicode to string
                    self.repositories.append( Repository( self, repo_info["name"], str(repo_info["url"])) )

        if 'repositories' in repos_info:
            self.server_type = 0

            for repo_info in repos_info['repositories']:
                if self.process_repo(repo_info):
                    self.repositories.append( Repository( self, repo_info["name"], str(repo_info["url"])) )

    def process_repo(self, repo_info):
        repo_name = repo_info["name"]
        if self.forced_repositories and repo_name not in self.forced_repositories:
            return 0

        if repo_name in self.ignored_repositories:
            return 0

        if 'pass-through' in repo_info:
            return 0

        return 1


