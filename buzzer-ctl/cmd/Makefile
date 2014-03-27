LDFLAGS += libbuzzer.a
OBJECTS := buzzer-ctl.o libbuzzer.o

all: buzzer-ctl libbuzzer.a

buzzer-ctl:$(OBJECTS) libbuzzer.a
	gcc -o buzzer-ctl $(OBJECTS) $(LDFLAGS)
ifneq ($(STRIP),)
	$(STRIP) buzzer-ctl
endif

libbuzzer.a:libbuzzer.o
	ar -rcs libbuzzer.a libbuzzer.o

clean:
	rm -rf *.o buzzer-ctl *.a
