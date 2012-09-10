all:
	$(MAKE) -C udv CFLAG=-D_UDV_DEBUG
	$(MAKE) -C web-iface

clean:
	$(MAKE) -C udv clean
	$(MAKE) -C web-iface clean

