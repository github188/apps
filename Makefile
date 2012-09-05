all:
	$(MAKE) -C udv
	$(MAKE) -C web-iface

clean:
	$(MAKE) -C udv clean
	$(MAKE) -C web-iface clean

