#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string.h>
#include <errno.h>
#include <stdio.h>

static int sock_connect(int sock, const char *host, int port)
{

	struct sockaddr_in addr;
	int ret;

	memset(&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	addr.sin_port = htons(port);
	ret = inet_pton(AF_INET, host, &addr.sin_addr);
	if (ret < 0)
		return -1;

	return connect(sock, (struct sockaddr *)&addr, sizeof(addr));
}


int fd_map(int out_fd, int argc, char *argv[])
{
	int sock;
	char cmd[4096];
	char *p = cmd;
	int i;

	if (argc <= 0)
		return -1;

	sock = socket(AF_INET, SOCK_STREAM, 0);
	if (sock < 0)
		return -1;
	if (sock_connect(sock, "127.0.0.1", 9000) < 0) {
		close(sock);
		return -1;
	}
	for (i = 0; i < argc; i++) {
		p += sprintf(p, "%s ", argv[i]);
	}
	sprintf(p, "\n");

	write(sock, cmd, strlen(cmd));
	for (;;) {
		int ret;
		char buf[4096];

		ret = read(sock, buf, sizeof(buf));
		if (ret < 0 &&
		    (errno == EAGAIN || errno == EWOULDBLOCK))
			continue;
		if (ret <= 0)
			break;
		write(out_fd, buf, ret);
	}

	return 0;
}
