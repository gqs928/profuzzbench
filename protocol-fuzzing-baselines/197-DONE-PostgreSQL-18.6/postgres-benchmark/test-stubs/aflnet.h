#ifndef POSTGRES_BENCHMARK_AFLNET_STUB_H
#define POSTGRES_BENCHMARK_AFLNET_STUB_H

typedef struct {
  int start_byte;
  int end_byte;
  unsigned char modifiable;
  unsigned int *state_sequence;
  unsigned int state_count;
} region_t;

/* PostgreSQL 协议适配器的请求切分与响应状态入口。 */
region_t *extract_requests_postgres(unsigned char *buf, unsigned int buf_size,
                                    unsigned int *region_count_ref);
unsigned int *extract_response_codes_postgres(unsigned char *buf,
                                              unsigned int buf_size,
                                              unsigned int *state_count_ref);

#endif
