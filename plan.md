# Plan of attack

## Usage

> server.status()

Returns: OK, DEGRADED, WARNING, FAILED

OK: All good
DEGRADED: GEO API failing or some (or all) repos haven't GCed in X hour
WARNING: X% of repos haven't updated in X hours
CRITICAL: X% of repos haven't updated in X+Y hours
FAILED: Offline or all repos have failed to update


> repo.status()

Returns: OK, DEGRADED, WARNING, FAILED

OK: All good
DEGRADED: low % of stratum1s are in non-OK states
WARNING: up to half of stratum1s are in non-OK states
CRITICAL: all but X (one?) stratum1s are in FAILED state
FAILED: all stratum1 are in FAILED states


## Sources:

### 

### Fetch repos:

http://aws-eu-west1.stratum1.cvmfs.eessi-infra.org/cvmfs/info/v1/repositories.json 

````
{
  "schema"       : 1,
  "repositories" : [
  ],
  "replicas" : [
    {
      "name"  : "ci.eessi-hpc.org",
      "url"   : "/cvmfs/ci.eessi-hpc.org"
    },
    {
      "name"  : "pilot.eessi-hpc.org",
      "url"   : "/cvmfs/pilot.eessi-hpc.org"
    }
  ]
}
````

For each repo:

#### Overall data:

http://aws-eu-west1.stratum1.cvmfs.eessi-infra.org/cvmfs/pilot.eessi-hpc.org/.cvmfspublished

See https://cvmfs.readthedocs.io/en/stable/cpt-details.html#internal-manifest-structure for the implementation.

````
Cd878504f599bd734d5d12d2a1f81e5a55ac4c526
B59392
Rd41d8cd98f00b204e9800998ecf8427e
D240
S356
Gyes
Ano
Npilot.eessi-hpc.org
Xd15a3f7ff8c3674c47b2aefd2b1093cf954ead17
Hc15153165a6f0f5a9cf3d45600d5ff9fb24fcf87
T1644000097
M85e4f386da0d5d77c7f66cf2f58e10951f24b653
Y4d0710e854c3b0aedc3560d9c1cdfec33fbd30e6
--
0878b68923635e1cf6032a6abe8a42de1494996f
JXiXO:;
       5S(_Jjy8R#R'SHQA0H qlS;8TQu[t3
TFO_%"[F8IO83v  ~6r#)4:22Lrg0XR+ve{NYqt&WÑZDvEGb|g0jX95IMɃ(
LH 2R<$LKYj?%

````

C: Cryptographic hash of the repository’s current root catalog
B: Size of the root file catalog in bytes
A: “yes” if the catalog should be fetched under its alternative name (outside servers /data directory)
R: MD5 hash of the repository’s root path (usually always d41d8cd98f00b204e9800998ecf8427e)
X: Cryptographic hash of the signing certificate
G: “yes” if the repository is garbage-collectable
H: Cryptographic hash of the repository’s named tag history database
T: Unix timestamp of this particular revision
D: Time To Live (TTL) of the root catalog
S: Revision number of this published revision
N: The full name of the manifested repository
M: Cryptographic hash of the repository JSON metadata
Y: Cryptographic hash of the reflog checksum
L: currently unused (reserved for micro catalogs)

#### Last snapshot and last garbage collection:

http://aws-eu-west1.stratum1.cvmfs.eessi-infra.org/cvmfs/pilot.eessi-hpc.org/.cvmfs_status.json

````
{
  "last_snapshot": "Sat Feb  5 00:00:03 UTC 2022",
  "last_gc": "Sun Jan 30 00:00:32 UTC 2022"
}
````


