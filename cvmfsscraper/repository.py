import datetime
import json

from cvmfsscraper.tools import fetch

class Repository:
    def __init__(self, server, name, url):
        self.server = server
        self.name = name
        self.path = url

        self.last_gc = None
        self.last_snapshot = None

        self._repo_status_loaded = 0
        self._cvmfspublished_loaded = 0

        # 1. Get data per repo:
        #  a. {url}/.cvmfspublished : Overall data
        #  b. {url}/.cvmfs_status.json

        self.fetch_errors = []

        content = fetch(self, self.server.name, self.path + "/.cvmfspublished")
        self.parse_cvmfspublished(content)

        content = fetch(self, self.server.name, self.path + "/.cvmfs_status.json")
        self.parse_status_json(content)

    def parse_status_json(self, json_data):
        if not json_data:
            return

        try:
            repo_status = json.loads(json_data)
            self._repo_status_loaded = 1
        except Exception as e:
            print(e)

        timeformat = "%a %b %d %H:%M:%S %Z %Y"

        if "last_snapshot" in repo_status:
            self.last_snapshot = datetime.datetime.strptime(repo_status["last_snapshot"], timeformat).timestamp()

        if "last_gc" in repo_status:
            self.last_gc = datetime.datetime.strptime(repo_status["last_gc"], timeformat).timestamp()

    def parse_cvmfspublished(self, content):
        """Parses a repositories .cvmfspublished
        https://cvmfs.readthedocs.io/en/stable/cpt-details.html#internal-manifest-structure
        """

        if not content:
            return

        self._cvmfspublished_loaded = 1

        signature_inc = False
        self.signature = bytes()
        for line in content.splitlines():
            if signature_inc:
                self.signature = self.signature + line
            else: 
                if chr(line[0]) == "-":
                    signature_inc = True
                else:
                    line = line.decode("iso-8859-1")
                    (key, value) = (line[0], line[1:])
                    self.process_cvmfspublished_key_value(key, value)
        
        return

    def process_cvmfspublished_key_value(self, key, value):
        if key == "C":
            self.root_cryptographic_hash = value
        elif key == "B":
            self.root_size = value
        elif key == "A":
            self.alternative_name = value
        elif key == "R":
            self.root_path_hash = value
        elif key == "X":
            self.signing_certificate_cryptographic_hash = value
        elif key == "G":
            self.is_garbage_collectable = value
        elif key == "H":
            self.tag_history_cryptographic_hash = value
        elif key == "T":
            self.revision_timestamp = value
        elif key == "D":
            self.root_catalogue_ttl = value
        elif key == "S":
            self.revision = value
        elif key == "N":
            self.full_name = value
        elif key == "M":
            self.metadata_cryptographic_hash = value
        elif key == "Y":
            self.reflog_checksum_cryptographic_hash = value
        elif key == "L":
            self.micro_cataloges = value
        else:
            pass
