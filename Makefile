all:
	#$(MAKE) -C udv CFLAG=-D_UDV_DEBUG
	$(MAKE) -C udv
	$(MAKE) -C web-iface
	$(MAKE) -C us
	$(MAKE) -C us/md-auto-resume/mdscan

clean:
	$(MAKE) -C udv clean
	$(MAKE) -C web-iface clean
	$(MAKE) -C us clean
	$(MAKE) -C us/md-auto-resume/mdscan clean

