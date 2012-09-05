#include <sys/types.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <stdint.h>
#include <unistd.h>
#include <stdio.h>

/* Return:
 * 	0:	success.
 * 	1:	child report error
 * 	<0:	failed
 */
int child_read(const char *cmd, char *buf, size_t *len)
{
	FILE *fp;
	int ret = -1;
	int r;
	int sts;

	fp = popen(cmd, "r");
	if (fp == NULL)
		return -1;
	r = fread(buf, 1, *len, fp);
	if (r < 0)
		goto out;
	*len = r;
	ret = 0;

out:
	sts = pclose(fp);
	if (ret == 0 && sts != 0)
		ret = 1;

	return ret;
}
