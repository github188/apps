all:
	#$(MAKE) -C udv CFLAG=-D_UDV_DEBUG
	$(MAKE) -C udv
	$(MAKE) -C us
	$(MAKE) -C nas
	$(MAKE) -C us/md-auto-resume/mdscan
	$(MAKE) -C common
	$(MAKE) -C web-iface

clean:
	$(MAKE) -C udv clean
	$(MAKE) -C web-iface clean
	$(MAKE) -C us clean
	$(MAKE) -C nas clean
	$(MAKE) -C us/md-auto-resume/mdscan clean
	$(MAKE) -C common clean
