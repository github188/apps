OF ?= obj_Makefile
CM ?= cus_Makefile
all:
include $(OF)

CC := $(CROSS_COMPILE)gcc
CXX := $(CROSS_COMPILE)g++
STRIP := $(CROSS_COMPILE)strip
RM ?= rm -f
RMDIR ?= rmdir
TARGET ?= release

ifeq ($(TARGET), debug)
CFLAGS += -Wall -g -O3
CXXFLAGS += -Wall -g -O3
else
CFLAGS += -Wall -Wstrict-prototypes -fomit-frame-pointer -O3 -fno-common
CXXFLAGS += -Wall -fomit-frame-pointer -O2 -fno-common
LDFLAGS += -s 
endif
CFLAGS += -pipe

SOURCES := $(wildcard *.c *.cpp *.cc)
OBJS := $(patsubst %.c,%.o,$(patsubst %.cpp,%.o,$(patsubst %.cc,%o,$(SOURCES))))

DEP_DIR = .deps/
DEPS := $(addprefix $(DEP_DIR),$(patsubst %.o,%.d,$(OBJS))) 
#MISSING_DEPS := $(filter-out $(wildcard $(DEPS)),$(DEPS))


.PHONY: all clean deps

all: $(progs)

$(progs):
	@echo "  LD      $@"
	@$(CC) $(LDFLAGS) $^ -o $@ $($@-libs)
ifneq ($(TARGET), debug)
	@$(STRIP) -s $@
endif

define PROG_template
$(1): $(if $($(1)-obj),$$($(1)-obj),$(1).o)
endef

$(foreach prog,$(progs),$(eval $(call PROG_template,$(prog))))

deps: $(DEPS)
$(DEPS):$(DEP_DIR)%.d:%.c
	@mkdir -p $(DEP_DIR)
#	$(CC) -MM -MF $@ $<
	@$(CC) -MM -MF $@.$$$$ $<; \
	sed 's,\($*\)\.o[ :]*,\1.o $@ : ,g' < $@.$$$$ > $@; \
	rm -f $@.$$$$

clean::
	$(RM) *.o mdscan mdinfo
cleanall: clean
	@(cd $(DEP_DIR) && $(RM) *.d)
	@$(RMDIR) $(DEP_DIR)
	$(RM) $(progs) *.a

%o:%c
	@echo "  CC      $@"
	@$(CC) $(CFLAGS) -c $< -o $@
%o:%cpp
	@echo "  CXX     $@"
	@$(CXX) $(CXXFLAGS) -c $< -o $@
%o:%cxx
	@echo "  CXX     $@"
	@$(CXX) $(CXXFLAGS) -c $< -o $@

-include $(DEPS)
-include $(CM)

#ifneq ($(MISSING_DEPS),)
#$(MISSING_DEPS) :
#	echo $@
#	$(RM) $(patsubst $(DEP_DIR)%.d,%.o,$@)
#endif 	
