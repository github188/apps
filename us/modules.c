#include "clog.h"
#include "types.h"
#include <stdlib.h>

#define DECLARE_FUNC(func)		\
	extern int func##_init(void);	\
	extern void func##_release(void)

#define MODULE(name)	{#name, name##_init, name##_release}

struct module {
	const char *name;
	int (*init)(void);
	void (*release)(void);
};

DECLARE_FUNC(us_regex);
DECLARE_FUNC(us_ev);
DECLARE_FUNC(us_mon);
DECLARE_FUNC(us_disk);
DECLARE_FUNC(us_session);
DECLARE_FUNC(us_prewarn);

static struct module us_modules[] = {
	MODULE(us_regex),
	MODULE(us_ev),
	MODULE(us_mon),
	MODULE(us_disk),
	MODULE(us_session),
#ifndef NO_DISK_PREWARN
	MODULE(us_prewarn),
#endif
};

void us_mod_init(void)
{
	int i;

	for (i = 0; i < ARRAY_SIZE(us_modules); i++) {
		struct module *mod = &us_modules[i];
		if (mod->init && (mod->init() != 0)) {
			die("%s init failed\n", mod->name);
			exit(1);
		}
	}
}

void us_mod_release(void)
{
	int i;

	for (i = ARRAY_SIZE(us_modules); i--; ) {
		struct module *mod = &us_modules[i];
		if (mod->release)
			mod->release();
	}
}

