#!/bin/bash
cd /var/www/maicgregator.org/htdocs/MAICgregatorServer/data
rm -f MAICgregatorDump.txt.gz
/etc/init.d/maicgregator stop
/usr/bin/db4.6_recover
/usr/bin/db4.6_dump -f MAICgregatorDump.txt MAICgregator.db
/etc/init.d/maicgregator start
/bin/gzip MAICgregatorDump.txt
