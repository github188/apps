OBJECTS = diskpw-ctl.o diskpw.o

all: diskpw-ctl
ifneq ($(STRIP),)
	$(STRIP) diskpw-ctl
endif

diskpw-ctl: $(OBJECTS)
	$(CC) -o diskpw-ctl $(OBJECTS) $(CFLAGS)

clean:
	rm -rf *.o diskpw-ctl
