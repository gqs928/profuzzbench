#ifndef NFS_TEST_AFLNET_H
#define NFS_TEST_AFLNET_H

typedef struct {
	int start_byte;
	int end_byte;
	char modifiable;
	unsigned int *state_sequence;
	unsigned int state_count;
} region_t;

region_t *extract_requests_nfs(unsigned char *buf, unsigned int buf_size,
			       unsigned int *region_count_ref);
unsigned int *extract_response_codes_nfs(unsigned char *buf,
					 unsigned int buf_size,
					 unsigned int *state_count_ref);

#endif
