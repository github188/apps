#ifndef __US_MON_H
#define __US_MON_H

#include "list.h"

#define MA_ADD				"add"
#define MA_REMOVE			"remove"
#define MA_CHANGE			"change"
#define MA_ONLINE			"online"
#define MA_MDSYNC			"mdsync"
#define MA_MDSYNCDONE		"mdsyncdone"
#define MA_RDKICKED			"rdkicked"

enum {
	MA_HANDLED	= 0,
	MA_NONE		= -1,
};

struct mon_node {
	struct list list;
	int (*on_event)(const char *path, const char *dev, const char *action);
};

void us_mon_enum_dev(void);
int us_mon_register_notifier(struct mon_node *node);
void us_mon_unregister_notifier(struct mon_node *node);

#endif
