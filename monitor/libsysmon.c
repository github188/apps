#include <sys/socket.h>
#include <sys/un.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <json/json.h>
#include "sys-mon.h"

bool sysmon_event(const char *module,
		const char *event,
		const char *param,
		const char *msg)
{
	struct sockaddr_un servaddr;
	socklen_t addr_len;
	size_t msg_len;
	int sockfd;
	char msg_buff[1024];
	json_object *jmsg;

	if ((sockfd=socket(AF_UNIX, SOCK_DGRAM, 0)) < 0)
		return false;
	servaddr.sun_family = AF_UNIX;
	strcpy(servaddr.sun_path, SYSMON_ADDR);
	addr_len = strlen(servaddr.sun_path) + sizeof(servaddr.sun_family);

	// build message
	jmsg = json_object_new_object();
	json_object_object_add(jmsg, "module", json_object_new_string(module));
	json_object_object_add(jmsg, "event", json_object_new_string(event));
	json_object_object_add(jmsg, "param", json_object_new_string(param));
	json_object_object_add(jmsg, "msg", json_object_new_string(msg));
	strcpy(msg_buff, json_object_to_json_string(jmsg));
	msg_len = strlen(msg_buff);

	sendto(sockfd, msg_buff, msg_len, 0, (struct sockaddr*)&servaddr, addr_len);
	close(sockfd);
	return true;
}
