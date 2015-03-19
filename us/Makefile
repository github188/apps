CROSS_COMPILE =

CFLAGS += -Dclog_level=CL_NONE -DNDEBUG -Wstrict-aliasing=0
LDFLAGS =
LDLIBS =
uslibs = -lev -ludev -latasmart -lxml2  -L../common -llog -lsqlite3 -ljson
ifndef isolated-storage
uslibs += ../monitor/libsysmon.a
endif
progs = us_d us_cmd

us_modules = us_regex.o us_ev.o us_mon.o us_disk.o us_cmd.o us_cl.o modules.o
ifndef no-disk-prewarn
us_modules += us_prewarn.o
else
CFLAGS += -DNO_DISK_PREWARN 
endif
us_utils = disk_utils.o safe_popen.o os_utils.o

us_cmd-objs = us_map.o fd_map.o
us_d-objs = $(us_modules) $(us_utils) main.o
mon_test-objs = $(us_modules) $(us_utils) us_mon_test.o

us_d-libs = $(uslibs)
mon_test-libs = $(uslibs)

-include config.mk
