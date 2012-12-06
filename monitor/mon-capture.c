#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include "sys-mon.h"

#define NCT_ROOT "/sys/devices/platform/nct6106.656"

const char *mod_cap_list[] = {"cpu-temp", "env-temp", "case-temp", NULL};

bool isCaptureSupported(const char *mod)
{
	const char *p = mod_cap_list[0];
	for (;p;)
	{
		if (!strcmp(p, mod))
			return true;
		p++;
	}
	return false;
}

const char *__read_file_line(const char *file)
{
	static char line[1024];
	char *p; int fd;

	line[0] = '\0';
	if ( (fd=open(file, O_RDONLY)) > 0 )
	{
		read(fd, line, sizeof(line)-1);
		p = strstr(line, "\n");
		if (p) *p = '\0';
		close(fd);
	}
	else
	{
		syslog(LOG_INFO, "%s : fail to read %s", __func__, file);
		return NULL;
	}

	return line;
}

int __atoi(const char *p)
{
	if (p)
		return atoi(p);
	return -1;
}

int __read_int_value(const char *file)
{
	return __atoi(__read_file_line(file));
}

int capture_cpu_temp()
{
	return __read_int_value(NCT_ROOT"/temp17_input");
}

int capture_env_temp()
{
	return __read_int_value(NCT_ROOT"/temp20_input");
}

int capture_case_temp()
{
	return __read_int_value(NCT_ROOT"/temp18_input");
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
