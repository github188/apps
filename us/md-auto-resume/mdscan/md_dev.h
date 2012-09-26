#ifndef K_MD_DEV_H
#define K_MD_DEV_H

#include "list.h"
#include "md_super.h"

struct pdm_super_s;
struct md_dev {
	char name[MAX_DEV_NAME + 1];
	struct super_type *st;
	struct list dev_list;
	struct pdm_super_s *pdm;
	struct list pdm_dev_list;
};

#endif
