all:
	$(MAKE) -C common
	$(MAKE) -C udv
	$(MAKE) -C us
	$(MAKE) -C nas
	$(MAKE) -C us/md-auto-resume/mdscan
	$(MAKE) -C web-iface
	$(MAKE) -C pic_ctl
	$(MAKE) -C pmu_ctl
	$(MAKE) -C monitor
	$(MAKE) -C sys-conf
	$(MAKE) -C test-utils

clean:
	$(MAKE) -C udv clean
	$(MAKE) -C web-iface clean
	$(MAKE) -C us clean
	$(MAKE) -C nas clean
	$(MAKE) -C us/md-auto-resume/mdscan clean
	$(MAKE) -C common clean
	$(MAKE) -C monitor clean
	$(MAKE) -C pic_ctl clean
	$(MAKE) -C pmu_ctl clean
	$(MAKE) -C sys-conf clean
	$(MAKE) -C test-utils clean
	find . -name '*.pyc' -delete
