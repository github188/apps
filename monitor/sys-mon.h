#include "sys-global.h"

#ifndef __SYS_MON_H__
#define __SYS_MON_H__

extern int global_print_on;
#define likely(x)       __builtin_expect((x),1)
#define unlikely(x)     __builtin_expect((x),0)

bool sysmon_event(const char *module, const char *event, const char *param, const char *msg);

#endif/*__SYS_MON_H__*/
