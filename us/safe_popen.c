/**
 * A simple popen.
 * It needn't call pclose which may block
 * Only reading support, and discard child pid
 */
#include <unistd.h>
#include "safe_popen.h"
#include <stdlib.h>

#define SHELL "/bin/sh"

int safe_system(const char *cmd)
{
	pid_t pid;

	pid = fork();
	if (pid < 0)
		return -1;
	if (pid == 0) {
		execl(SHELL, "sh", "-c", cmd, NULL);
		exit(127);
	}

	return 0;
}

int safe_popen(struct sp_child *c, const char *cmd)
{
	int pfd[2];
	pid_t pid;

	if (pipe(pfd) < 0)
		return -1;
	pid = fork();
	if (pid < 0) {
		close(pfd[0]);
		close(pfd[1]);
		return -1;
	}
	if (pid == 0) {
		/* child */
		close(pfd[0]);
		dup2(pfd[1], STDOUT_FILENO);
		close(pfd[1]);
		execl(SHELL, "sh", "-c", cmd, NULL);
		exit(127);
	}

	close(pfd[1]);
	c->pid = pid;
	c->fd = pfd[0];

	return 0;
}
