#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string.h>
#include <errno.h>

extern int fd_map(int out_fd, int argc, char *argv[]);

int main(int argc, char *argv[])
{
	argc--;
	argv++;

	fd_map(1, argc, argv);

	return 0;
}
