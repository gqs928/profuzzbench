/* 临时验收助手：把 Dovecot worker 的故障传递到 AFLNet 监控进程。 */
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

static pid_t read_parent_pid(pid_t pid)
{
	char path[64], line[512], state;
	int parent_pid = 0;
	FILE *file;
	char *fields;

	(void)snprintf(path, sizeof(path), "/proc/%ld/stat", (long)pid);
	file = fopen(path, "r");
	if (file == NULL)
		return 0;
	if (fgets(line, sizeof(line), file) == NULL) {
		(void)fclose(file);
		return 0;
	}
	(void)fclose(file);
	fields = strrchr(line, ')');
	if (fields == NULL || sscanf(fields + 2, "%c %d", &state, &parent_pid) != 2)
		return 0;
	return (pid_t)parent_pid;
}

int main(void)
{
	pid_t parent = getppid(), target = 0;
	FILE *trace = fopen("/tmp/dovecot-injection.trace", "a");

	if (trace != NULL)
		(void)fprintf(trace, "helper_pid=%ld initial_parent=%ld\n",
			      (long)getpid(), (long)parent);
	for (unsigned int depth = 0; parent > 1 && depth < 12; depth++) {
		char path[64], comm[64];
		FILE *file;

		(void)snprintf(path, sizeof(path), "/proc/%ld/comm", (long)parent);
		file = fopen(path, "r");
		if (file == NULL || fgets(comm, sizeof(comm), file) == NULL) {
			if (file != NULL)
				(void)fclose(file);
			break;
		}
		(void)fclose(file);
		comm[strcspn(comm, "\n")] = '\0';
		if (trace != NULL)
			(void)fprintf(trace, "ancestor depth=%u pid=%ld comm=%s\n",
				      depth, (long)parent, comm);
		if (strcmp(comm, "dovecot") == 0) {
			target = parent;
			break;
		}
		parent = read_parent_pid(parent);
	}

	errno = 0;
	int kill_result = target > 1 ? kill(target, SIGABRT) : -1;
	int kill_errno = errno;
	if (trace != NULL) {
		(void)fprintf(trace, "target_pid=%ld kill_result=%d errno=%d\n",
			      (long)target, kill_result, kill_errno);
		(void)fclose(trace);
	}
	return kill_result == 0 ? 0 : 1;
}
