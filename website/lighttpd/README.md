After installing the lighttpd http server on the server, follow the following steps:

1. copy the lighttpd.conf file in /etc/lighttpd;
1. copy the conf-available/10-fastcgi.conf in /etc/lightpd/conf-available;
1. enable the fastcgi by calling `lighttpd-enable-mod fastcgi`;
1. make executable (permission 755) all the directories that are accessed by the web.py application used, and readable the files they contain that are used by the same application;
1. in the web.py application directory, create the file `opencitations_log.txt` and be sure that the user 'www-data' can write it;
1. run the server by calling `/etc/init.d/lighttpd start`.

The error log is stored in `/var/log/lighttpd/error.log`. Use `/etc/init.d/lighttpd stop` for stopping the service, and `/etc/init.d/lighttpd force-reload` for reloading the service (if it is still running).