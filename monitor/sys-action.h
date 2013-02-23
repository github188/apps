#include "sys-global.h"
#include "list.h"

#ifndef __SYS_ACTION_H__
#define __SYS_ACTION_H__

typedef void (*sys_alarm_handler)(void *event);

typedef struct _sys_alarm sys_alarm_t;
struct _sys_alarm {
	struct list alarm_list;
	char name[128];
	sys_alarm_handler handler;
};

typedef struct _sys_action sys_action_t;
struct _sys_action {
	struct list list;
	struct list alarm_list;
	char name[128];
};

extern struct list _gaction_list;

/* action */

void sys_action_init();

void sys_action_release();

bool sys_action_add(const char *name);

sys_action_t *sys_action_get(const char *name);

/* action - alarm */

sys_alarm_t *sys_alarm_alloc();

bool sys_action_alarm_add(const char *name, sys_alarm_t *alarm);

sys_alarm_t *sys_action_alarm_get(const char *action, const char *alarm);

void sys_alarm_set_handler(sys_alarm_t *alarm, const char *handler_name);

void do_sys_action(sys_action_t *action, void *event);

void dump_action_alarm();


/* alarm */

void sys_alarm_default(void *event);

void sys_alarm_buzzer(void *event);

void sys_alarm_sysled(void *event);

void sys_alarm_diskled(void *event);


#endif/*__SYS_ACTION_H__*/
