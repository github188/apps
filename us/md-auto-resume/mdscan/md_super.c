/**
 * Md super operation support.
 */

#include <string.h>
#include "md_super.h"
#include "util.h"

extern struct super_ops super1;

struct super_ops *md_super_ops[] = {
	&super1, NULL,
};


struct super_type * md_load_super(int fd, const char *name)
{
	struct super_ops **ops = md_super_ops;
	int ret;
	struct super_type *st;

	st = xmalloc(sizeof(*st));
	memset(st, 0, sizeof(*st));

	while (*ops) {
		ret = (*ops)->load_super(st, fd, name);
		if (ret == 0) {
			st->s_op = *ops;
			return st;
		}
		ops++;
	}

	xfree(st);

	return NULL;
}

void md_free_super(struct super_type *st)
{
	st->s_op->free_super(st);
	xfree(st);
}
