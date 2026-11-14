#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "alloc-inl.h"
#include "aflnet.h"

int main(void) {
  unsigned char requests[] = {
    4,0,0,0,0x03,'S','E','L',
    4,0,0,0,0x03,'1','\0','x'
  };
  unsigned int count=0;
  region_t *r=extract_requests_mysql(requests,sizeof(requests),&count);
  assert(r && count==2);
  assert(r[0].start_byte==0 && r[0].end_byte==7);
  assert(r[1].start_byte==8 && r[1].end_byte==15);
  ck_free(r);

  unsigned char truncated[]={8,0,0,0,1,2};
  r=extract_requests_mysql(truncated,sizeof(truncated),&count);
  assert(r && count==1 && r[0].start_byte==0 && r[0].end_byte==5);
  ck_free(r);

  unsigned char responses[]={
    1,0,0,1,0x01,             /* result header / row data */
    5,0,0,2,0xfe,0,0,2,0,    /* EOF */
    7,0,0,3,0x00,0x00,0x00,0x02,0x00,0x00,0x00, /* OK */
    8,0,0,4,0xff,0x28,0x04,'#','4','2','0','0'
  };
  unsigned int *states=extract_response_codes_mysql(responses,sizeof(responses),&count);
  assert(states && count==5);
  assert(states[0]==0 && states[1]==21 && states[2]==22 && states[3]==30 && states[4]==40);
  ck_free(states);
  puts("MySQL classic packet framing and SQL response states passed.");
  return 0;
}
