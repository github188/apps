/*
 * mkdir-p.c  -- create directory recursively
 *
 * Copyright (C) 2012-2013 yanyg (yygcode@gmail.com, cppgp@qq.com)
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; see the file COPYING, if not see
 * <http://www.gnu.org/licenses/>.
 */

#include <limits.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "config-os.h"

#include "jw-unistd.h"
#include "debug.h"

/* create directory recursively */
int mkdir_p(const char *path)
{
	int n;
	char buf[PATH_MAX], *p = buf;

	assert(path);

	if ((n = strlen(path)) >= PATH_MAX) {
		DBGP("over length: %d, %d", n, PATH_MAX);
		return -1;
	}

	DBGP("len=%d; path='%s'\n", n, path);

	strcpy(buf, path);
	while ((p = strchr(p+1, '/'))) {
		struct stat sb;
		*p = '\0';
		if (stat(buf, &sb) && mkdir(buf, ACCESSPERMS)) {
			DBGE("stat/create '%s' failed", buf);
			return -1;
		}
		*p = '/';
	}

	return n;
}

/* eof */
