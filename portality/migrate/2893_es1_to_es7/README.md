# ES7 upgrade

Updating the DOAJ from ES 1.7 to 7.10 - this is the forking point with OpenSearch, since we still don't know which way Elastic and Amazon are going with them both.

## Release Procedure

**Prep:**
* Use `doaj-public-app-1` as the release server - we'll checkout the updated master there and run the migration
* Upgrade our new index machines `doaj-index-1` and `doaj-index-2` to ES7 .deb packages.
* Set up S3 buckets for backups etc
* Ensure `doaj-public-app-1` has the right nginx etc. config to be the main app server
* Ensure the new index is empty so we get the latest mappings

**Release day:**
* Place the DOAJ in read-only mode
* Initiate backup on `doaj-bg-app-1`
* Code merge with ES7 upgrade & checkout to `doaj-public-app-1`
* Give `doaj-public-app-1` access to both sets of index machines <- check DO firewall directionality ( we don't want conflicts )
* Stream records from old `doaj-new-index-1` to the new index in `doaj-index-1`^ using the migration script here
* Initiate new backup of ES7 index
* Switch the DOAJ static IP from `doaj-new-app-1` to `doaj-public-app-1` (digital ocean)
* Change config for `doaj-bg-app-1` to also use the new index.

**Cleanup:**
* Tidy up old configs from `production.cfg` file
* Discard the old index machines `doaj-new-index-1` and `doaj-new-index-2`
* Discard the old app server `doaj-new-app-1`



^This is why it was a bad choice of hostname!