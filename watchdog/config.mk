all:

CC := $(CROSS_COMPILE)gcc
CXX := $(CROSS_COMPILE)g++
STRIP := $(CROSS_COMPILE)strip
AR ?= $(CROSS_COMPILE)ar

RM ?= rm -f
RMDIR ?= rmdir
T ?= release

ARFLAGS = rcs

ifeq ($(T), debug)
CFLAGS += -Wall -g -O2 -DDEBUG
CXXFLAGS += -Wall -g -O2 -DDEBUG
else
CFLAGS += -Wall -Wstrict-prototypes -fomit-frame-pointer -O2 \
		-fno-common 
CXXFLAGS += -Wall -fomit-frame-pointer -O2 -fno-common
LDFLAGS += -s
endif

CFLAGS += -pipe

ifeq ($(Q),)
quiet := quiet_
MAKE = make -s
else
quiet := 
MAKE = make
endif

dot-target = $(dir $@).$(notdir $@)
depfile = $(dot-target).d
getm-objs = $(if $($(1)-objs),$($(1)-objs),$(1).o)
echo-cmd = @echo '  $($(quiet)cmd_$(1))';
cmd = @$(echo-cmd) $(cmd_$(1))

ifeq ($(findstring Win,$(OS)),Win)
gen-target = $(if 1,$(1).exe)
gen-targets = $(foreach m,$(1),$(addsuffix .exe,$(m)))
rm-suffix = $(patsubst %.exe,%,$(1))
else
gen-target = $(1)
gen-targets = $(1)
rm-suffix = $(1)
endif

define module_template
$(call gen-target,$(1)): $(addprefix $($(2)-dir)/,$(call getm-objs,$(1))) $($(1)-lds)
endef

define target_template
$(1)-dir ?= .$(1)
$(1)-objs := $(sort $(foreach m,$($(1)),$(call getm-objs,$(m))))
objs := $(obj) $$($(1)-objs)
$(1)-objs := $$(addprefix $$($(1)-dir)/,$$($(1)-objs))
endef

$(eval $(call target_template,progs))
$(foreach m,$(progs),$(eval $(call module_template,$(m),progs)))

to-progs = $(addprefix $(progs-dir)/,$(1))

objs += $(lib-objs)
progs-objs += $(call to-progs,$(lib-objs))

deps-dir ?= .deps
deps := $(addprefix $(deps-dir)/,$(patsubst %.o,%.d,$(objs)))

quiet_cmd_progs-objs = CC      $(notdir $@)
      cmd_progs-objs =  $(CC) $(CFLAGS) -c -o $@ $<
quiet_cmd_progs      = LD      $@
      cmd_progs	     = mkdir -p $(dir $@); \
                      $(CC) $(LDFLAGS) -o $@ \
                      $(addprefix $(progs-dir)/, \
                         $(call getm-objs,$(call rm-suffix,$(@F)))) \
                      $($(call rm-suffix,$(@F))-lds) $(LDLIBS) \
                      $($(call rm-suffix,$(@F))-libs)

clean_dir = (cd $(1) && $(RM) $(2) -f) >/dev/null 2>&1; \
            $(RMDIR) $(1) >/dev/null 2>&1; :

quiet_cmd_clean_progs = CLEAN   progs
      cmd_clean_progs = $(call clean_dir,$(progs-dir),*.o); \
                        $(RM) $(progs-target) -f ; :

quiet_cmd_clean_dep = CLEAN   deps
      cmd_clean_dep = $(call clean_dir,$(deps-dir),*.d)

progs-target := $(call gen-targets,$(progs))

ifeq ($(Q),)
	QUIET_CC       = @echo '  CC      $@'; $(CC) $(CFLAGS) -c -o $@ $<
	QUIET_AR       = @echo '  AR      $@'; $(AR) $(ARFLAGS) $@ $^
	QUIET_LINK     = @echo '  LINK    $@'; $(CC)
	QUIET_RM       = @echo '  CLEAN   $1'; $(RM) -f $1
else
	QUIET_CC       = $(CC) $(CFLAGS) -c -o $@ $<
	QUIET_AR       = $(AR) $(ARFLAGS) $@ $^
	QUIET_LINK     = $(CC)
	QUIET_RM       = $(RM) -f
endif

.PHONY: all

all: DEPS $(progs-target)

$(progs-target):
	$(call cmd,progs)

$(progs-objs) : $(progs-dir)/%.o : %.c
	@mkdir -p $(dir $@);
	$(call cmd,progs-objs)

DEPS: $(deps)
#$(deps)
$(deps-dir)/%.d:%.c
	@mkdir -p $(deps-dir)
	@$(CC) $(CFLAGS) -MM -MF $@.$$$$ $<; \
	sed 's,\($*\)\.o[ :]*,$(progs-dir)/\1.o $@ : Makefile ,g' < $@.$$$$ > $@; \
	rm -f $@.$$$$

clean::
	$(call cmd,clean_progs)
	$(call cmd,clean_dep)

distclean: clean

-include $(deps)
