Automated tools run:
	* `2to3 -w . > python3_upgrade_log 2>&1`
	after upgrade, cleanup with:
		+ `find . -name "*.bak" -type f -delete`
		+ `git rm python3_upgrade_log`
