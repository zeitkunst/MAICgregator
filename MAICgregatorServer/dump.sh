#!/bin/bash
cd /var/www/maicgregator.org/htdocs/MAICgregatorServer/data
/etc/init.d/lighttpd stop
/usr/bin/db4.6_dump -f MAICgregatorDump.txt MAICgregator.db
/etc/init.d/lighttpd start
/bin/gzip MAICgregatorDump.txt
