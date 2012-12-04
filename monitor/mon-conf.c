#include <string.h>
#include "sys-mon.h"


size_t mon_conf_load(struct list **conf)
{
	return 0;
}

size_t mon_conf_reload(struct list **conf)
{
	struct list *n, *nt;
	mon_conf_t *tmp;

	list_iterate_safe(n, nt, *conf)
	{
		tmp = list_struct_base(n, mon_conf_t, list);
		list_del(n);  free(tmp);
	}

	*conf = NULL;

	return mon_conf_load(conf);
}
