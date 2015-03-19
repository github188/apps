d=$(shell date "+%Y-%m-%d %H:%M:%S")

all:
	echo "Build Date: "$d > .build-date
ifndef other-hardware
	$(CC) -o pic-version pic-version.c ../pic_ctl/libpic.a
ifneq ($(STRIP),)
	$(STRIP) pic-version
endif
endif

clean:
	rm -f ./.build-date pic-version
