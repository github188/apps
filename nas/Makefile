all:
	gcc -o tr-simple tr-simple.c
ifneq ($(STRIP),)
	$(STRIP) tr-simple
endif

clean:
	rm -fr tr-simple a.out
