#include "sys-mon.h"

const char *mod_cap_list[] = {"cpu-temp", "env-temp", "case-temp", NULL};

bool isCaptureSupported(const char *mod)
{
	const char *p = mod_cap_list[0];
	for (;p;)
		if (!strcmp(p, mod))
			return true;
	return false;
}

int capture_cpu_temp()
{
	return 0;
}

int capture_env_temp()
{
	return 0;
}

int capture_case_temp()
{
	return 0;
}

capture_func capture_get(const char *mod)
{
	if (!isCaptureSupported(mod))
		return NULL;

	if (!strcmp(mod, "cpu-temp"))
		return capture_cpu_temp;
	else if (!strcmp(mod, "env-temp"))
		return capture_env_temp;
	else if (!strcmp(mod, "case-temp"))
		return capture_case_temp;
	return NULL;
}
