all: watchdog libwatchdog.a libwatchdog.so

%.o : %.c
	$(CC) $(CFLAGS) -c $<

watchdog: watchdog.o libwatchdog.a
	$(CC) -o $@ $^
ifneq ($(STRIP),)
	$(STRIP) $@
endif

libwatchdog.so: libwatchdog.c
	$(CC) $(CFLAGS) -fPIC -shared -o $@ $^
ifneq ($(STRIP),)
	$(STRIP) $@
endif

libwatchdog.a: libwatchdog.o
	ar rcs $@ $^

.PHONY: clean

clean::
	rm -f *.o *.a *.so watchdog
