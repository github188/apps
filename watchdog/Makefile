all: watchdog libwatchdog.a libwatchdog.so

%.o : %.c
	gcc $(CFLAGS) -c $<

watchdog: watchdog.o libwatchdog.a
	gcc -o $@ $^
ifneq ($(STRIP),)
	$(STRIP) $@
endif

libwatchdog.so: libwatchdog.c
	gcc $(CFLAGS) -fPIC -shared -o $@ $^
ifneq ($(STRIP),)
	$(STRIP) $@
endif

libwatchdog.a: libwatchdog.o
	ar rcs $@ $^

.PHONY: clean

clean::
	rm -f *.o *.a *.so watchdog
