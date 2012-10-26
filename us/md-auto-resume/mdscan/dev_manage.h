#ifndef K_DEV_MANAGE_H
#define K_DEV_MANAGE_H

#include "list.h"
#include "md_dev.h"

extern const char *dev_patterns[];
extern struct list *load_md_devs(struct list *dlist);
extern void free_md_devs(struct list *dlist);

#endif

