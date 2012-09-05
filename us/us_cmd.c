#include <string.h>

#include "us_disk.h"
#include "clog.h"
#include "types.h"

#define MAX_CMD	(128)
#define MAX_ARGS (8)

struct cmd_tbl {
	char *name;
	int (*cmd) (struct cmd_tbl *, int fd, int argc, char *argv[]);
};

static int do_disk(struct cmd_tbl *tbl, int fd, int argc, char *argv[]);

static struct cmd_tbl all_cmds[MAX_CMD] = {
	{ "disk", do_disk },
};
static int cur_cmds = 1;


static int do_disk(struct cmd_tbl *tbl, int fd, int argc, char *argv[])
{
	if (argc < 2 || strcmp(argv[1], "--list") == 0) {
		if (argc > 2)
			us_disk_dump(fd, argv[2], 0);
		else
			us_disk_dump(fd, NULL, 0);
	} else if (strcmp(argv[1], "--get-detail") == 0) {
		us_disk_dump(fd, argv[2], 1);
	} else if (strcmp(argv[1], "name") == 0) {
		if (argc <= 2)
			return -1;
		us_disk_slot_to_name(fd, argv[2]);
	} else if (strcmp(argv[1], "slot") == 0) {
		if (argc <= 2)
			return -1;
		us_disk_name_to_slot(fd, argv[2]);
	} else if (strcmp(argv[1], "update") == 0) {
		char *slot = NULL;
		char *op = NULL;

		if (argc > 2)
			slot = argv[2];
		if (argc > 3)
			op = argv[3];
		us_disk_update_slot(slot, op);
	}

	return 0;
}

static struct cmd_tbl *find_cmd(const char *name)
{
	int i;

	for (i = 0; i < cur_cmds; i++)
		if (strcmp(name, all_cmds[i].name) == 0)
			return &all_cmds[i];
	return NULL;
}

int us_install_cmd(struct cmd_tbl *tbl)
{
	int i;

	if (cur_cmds == MAX_CMD)
		return -1;
	if (tbl->name == NULL)
		return -1;
	for (i = 0; i < cur_cmds; i++) {
		if (strcmp(tbl->name, all_cmds[i].name) == 0)
			return -1;
	}
	all_cmds[cur_cmds++] = *tbl;

	return 0;
}

static int make_argv(char *s, char *argv[], int argvsz)
{
	int argc = 0;

	while (argc < argvsz - 1) {
		while (*s == ' ' || *s == '\t')
			s++;
		if (*s == 0)
			break;
		argv[argc++] = s;

		while (*s && (*s != ' ') && (*s != '\t'))
			s++;
		if (*s == '\0')
			break;

		*s++ = '\0';
	}
	argv[argc] = NULL;

	return argc;
}

int us_do_cmd(int fd, char *buf)
{
	int argc;
	char *argv[MAX_ARGS + 1];
	struct cmd_tbl *cmd;


	argc = make_argv(buf, argv, ARRAY_SIZE(argv));
	if (argc == 0)
		return -1;
	cmd = find_cmd(argv[0]);
	if (cmd == NULL) {
		clog(LOG_WARNING, "%s: %s not defined\n",
		     __func__, argv[0]);
		return -1;
	}
	cmd->cmd(cmd, fd, argc, argv);

	return 0;
}
