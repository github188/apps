all: diskpower-ctl

%.o : %.c %.h
	$(CC) $(CFLAGS) -c $<

diskpower-ctl: diskpower-ctl.o diskpower.o
	$(CC) -o $@ $^
ifneq ($(STRIP),)
	$(STRIP) $@
endif

.PHONY: clean

clean::
	rm -f *.o *.a *.so diskpower-ctl
