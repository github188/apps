#ifndef __US_MON_H
#define __US_MON_H

#include "list.h"

enum {
	MA_ADD		= 0,
	MA_REMOVE	= 1,
	MA_CHANGE	= 2,

	MA_HANDLED	= 0,
	MA_NONE		= -1,
};

struct mon_node {
	struct list list;
	int (*on_event)(const char *path, const char *dev, int action);
};

void us_mon_enum_dev(void);
int us_mon_register_notifier(struct mon_node *node);
void us_mon_unregister_notifier(struct mon_node *node);

#endif
