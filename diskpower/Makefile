all: diskpower-ctl

%.o : %.c %.h
	gcc $(CFLAGS) -c $<

diskpower-ctl: diskpower-ctl.o diskpower.o
	gcc -o $@ $^
ifneq ($(STRIP),)
	$(STRIP) $@
endif

.PHONY: clean

clean::
	rm -f *.o *.a *.so diskpower-ctl
