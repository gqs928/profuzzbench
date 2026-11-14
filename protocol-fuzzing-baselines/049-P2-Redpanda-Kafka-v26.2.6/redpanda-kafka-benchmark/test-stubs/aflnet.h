#ifndef KAFKA_BENCHMARK_AFLNET_STUB_H
#define KAFKA_BENCHMARK_AFLNET_STUB_H

typedef struct {
  int start_byte;
  int end_byte;
  unsigned char modifiable;
  unsigned int *state_sequence;
  unsigned int state_count;
} region_t;

region_t *extract_requests_kafka(unsigned char *buf, unsigned int buf_size,
                                 unsigned int *region_count_ref);
unsigned int *extract_response_codes_kafka(unsigned char *buf,
                                           unsigned int buf_size,
                                           unsigned int *state_count_ref);

#endif
