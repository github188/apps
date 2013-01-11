all:
	#$(MAKE) -C udv CFLAG=-D_UDV_DEBUG
	$(MAKE) -C common
	$(MAKE) -C udv
	$(MAKE) -C us
	$(MAKE) -C nas
	$(MAKE) -C us/md-auto-resume/mdscan
	$(MAKE) -C web-iface
	$(MAKE) -C monitor

clean:
	$(MAKE) -C udv clean
	$(MAKE) -C web-iface clean
	$(MAKE) -C us clean
	$(MAKE) -C nas clean
	$(MAKE) -C us/md-auto-resume/mdscan clean
	$(MAKE) -C common clean
	$(MAKE) -C monitor clean
