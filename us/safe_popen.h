#ifndef __SAFE_POPEN_H
#define __SAFE_POPEN_H

struct sp_child {
	pid_t pid;
	int fd;
};

int safe_popen(struct sp_child *c, const char *cmd);
int safe_system(const char *cmd);

#endif
