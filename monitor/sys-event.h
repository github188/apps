#include "sys-global.h"
#include "sys-action.h"
#include "list.h"

#ifndef __SYS_EVENT_H__
#define __SYS_EVENT_H__

struct _sys_event_global {
	char module[128];
	char event[128];
	char level[128];
};

/* 供配置使用 */
typedef struct _sys_event_conf sys_event_conf_t;
struct _sys_event_conf {
	struct list event_list;
	char module[128];
	char event[128];
	char level[128];
	sys_action_t *action;
	int count;
};

/* 供向action传递消息使用 */
typedef struct _sys_event sys_event_t;
struct _sys_event {
	char module[128];
	char event[128];
	char *level;
	char param[128];
	char msg[256];
};

sys_event_conf_t *sys_event_conf_alloc();

void sys_event_zero(sys_event_t *ev);

void sys_event_fill(sys_event_t *ev, const char *key, const char *value);

#endif/*__SYS_EVENT_H__*/
