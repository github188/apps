LIBBUZZER += libbuzzer.a
OBJECTS := buzzer-ctl.o libbuzzer.o
ifdef only-interface
	CFLAGS += -DONLY_INTERFACE
endif
all: buzzer-ctl libbuzzer.a libbuzzer.so

buzzer-ctl:$(OBJECTS) libbuzzer.a
	gcc $(CFLAGS) -o $@ $^
ifneq ($(STRIP),)
	$(STRIP) $@
endif

libbuzzer.so: libbuzzer.c
	gcc $(CFLAGS) -fPIC -shared -o $@ $^
ifneq ($(STRIP),)
	$(STRIP) $@
endif

libbuzzer.a: libbuzzer.o
	ar -rcs $@ $^

clean:
	rm -rf *.o buzzer-ctl *.a *.so
