#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include "sys-interval-check.h"

#define NCT_ROOT "/sys/devices/platform/nct6106.656"

const char *mod_cap_list[] = {"cpu-temp", "env-temp", "case-temp", "case-fan1", "case-fan2", "cpu-fan", "power", NULL};

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
	int tmp = -1;

	if (p)
		tmp = atoi(p);
	return tmp;
}

// retcode: -1 表示文件不存在
int __read_int_value(const char *file)
{
	return __atoi(__read_file_line(file));
}

int capture_cpu_temp(char *msg)
{
	int val = __read_int_value(NCT_ROOT"/temp17_input");
	if (val>0)
		return (int)(val/1000);
	return val;
}

int capture_env_temp(char *msg)
{
	int val = __read_int_value(NCT_ROOT"/temp20_input");
	if (val > 0)
		return (int)(val/1000);
	return val;
}

int capture_case_temp(char *msg)
{
	int val = __read_int_value(NCT_ROOT"/temp18_input");
	if (val > 0)
		return (int)(val/1000);
	return val;
}

int capture_case_fan1(char *msg)
{
	syslog(LOG_INFO, "capture case fan1");
	return __read_int_value(NCT_ROOT"/fan1_input");
}

int capture_case_fan2(char *msg)
{
	return __read_int_value(NCT_ROOT"/fan3_input");
}

int capture_cpu_fan(char *msg)
{
	return __read_int_value(NCT_ROOT"/fan2_input");
}

int capture_power(char *msg)
{
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
	else if (!strcmp(mod, "case-fan1"))
		return capture_case_fan1;
	else if (!strcmp(mod, "case-fan2"))
		return capture_case_fan2;
	else if (!strcmp(mod, "cpu-fan"))
		return capture_cpu_fan;
	else if (!strcmp(mod, "power"))
		return capture_power;
	return NULL;
}

void sys_capture_init()
{
	list_init(&_g_capture);
}

void sys_capture_release()
{
	struct list *n, *nt;
	sys_capture_t *c;

	list_iterate_safe(n, nt, &_g_capture)
	{
		c = list_struct_base(n, sys_capture_t, list);
		list_del(&c->list);
		syslog(LOG_INFO, "release capture '%s' !", c->name);
		free(c);
	}
}

sys_capture_t *sys_capture_alloc()
{
	sys_capture_t *tmp;

	tmp = (sys_capture_t*)malloc(sizeof(sys_capture_t));
	if (tmp)
	{
		tmp->name[0] = '\0';
		tmp->check_intval = VAL_INVALID;
		tmp->min_thr = tmp->max_thr = VAL_INVALID;
		tmp->_last_update = time(NULL);
		tmp->_capture = NULL;
		tmp->_error = false;
		tmp->_preset = false;
	}

	return tmp;
}

void sys_capture_set_handler(sys_capture_t *cap)
{
	if (isCaptureSupported(cap->name))
		cap->_capture = capture_get(cap->name);
}

void sys_capture_add(sys_capture_t *cap)
{
	if (cap)
		list_add(&_g_capture, &cap->list);
}
