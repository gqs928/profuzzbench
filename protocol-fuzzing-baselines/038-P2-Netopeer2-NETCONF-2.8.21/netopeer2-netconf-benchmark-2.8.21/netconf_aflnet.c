/* NETCONF delimiter and chunked framing parser for AFLNet state feedback. */
#include <ctype.h>
#include <string.h>
#include "alloc-inl.h"
#include "aflnet.h"

static void add_region(region_t **r, unsigned int *n, unsigned int s, unsigned int e) {
  *r=(region_t *)ck_realloc(*r,(*n+1)*sizeof(region_t));
  (*r)[*n].start_byte=(int)s; (*r)[*n].end_byte=(int)e;
  (*r)[*n].modifiable=1; (*r)[*n].state_sequence=NULL; (*r)[*n].state_count=0; (*n)++;
}

/* Return the exclusive end of one framed message, or 0 for incomplete input. */
static unsigned int frame_end(const unsigned char *b,unsigned int n,unsigned int s) {
  static const unsigned char end10[]={']',']','>',']',']','>'};
  unsigned int i;
  if (s>=n) return 0;
  /* RFC 6242 chunk framing: one or more LF-#length-LF chunks, then LF-##-LF. */
  if (n-s>=2 && b[s]=='\n' && b[s+1]=='#') {
    unsigned int p=s;
    for (;;) {
      unsigned int line=p+2, len=0, digits=0;
      if (line<n && b[line]=='#') {
        unsigned int q=line+1;
        while(q<n && b[q]!='\n') q++;
        return q<n ? q+1 : 0;
      }
      while(line<n && isdigit((unsigned char)b[line])) {
        if (len>(0xffffffffu-(unsigned int)(b[line]-'0'))/10u) return 0;
        len=len*10u+(unsigned int)(b[line]-'0'); line++; digits++;
      }
      if (!digits || line>=n || b[line]!='\n') return 0;
      p=line+1;
      if (len>n-p) return 0;
      p+=len;
      if (p+2>n || b[p]!='\n' || b[p+1]!='#') return 0;
    }
  }
  for(i=s;i+sizeof(end10)<=n;i++) if(!memcmp(b+i,end10,sizeof(end10))) return i+sizeof(end10);
  return 0;
}

region_t *extract_requests_netconf(unsigned char *buf,unsigned int size,unsigned int *count_ref) {
  region_t *r=NULL; unsigned int n=0,p=0;
  if(!buf||!size){*count_ref=0;return NULL;}
  while(p<size){unsigned int e=frame_end(buf,size,p); if(!e){add_region(&r,&n,p,size-1);break;} add_region(&r,&n,p,e-1);p=e;}
  *count_ref=n;return r;
}

static int contains(const unsigned char *b,unsigned int n,const char *s) {
  unsigned int m=(unsigned int)strlen(s),i;
  if(m>n)return 0;
  for(i=0;i+m<=n;i++)if(!memcmp(b+i,s,m))return 1;
  return 0;
}
static unsigned int classify(const unsigned char *b,unsigned int n) {
  if(contains(b,n,"<hello")||contains(b,n,":hello"))return 0x100;
  if(contains(b,n,"<notification")||contains(b,n,":notification"))return 0x400;
  if(contains(b,n,"<rpc-reply")||contains(b,n,":rpc-reply"))
    return (contains(b,n,"<rpc-error")||contains(b,n,":rpc-error"))?0x301:0x300;
  return 0x1fff;
}
unsigned int *extract_response_codes_netconf(unsigned char *buf,unsigned int size,unsigned int *count_ref) {
  unsigned int *states=NULL,n=0,p=0;
  states=(unsigned int *)ck_realloc(states,sizeof(unsigned int));states[n++]=0;
  while(buf&&p<size){unsigned int e=frame_end(buf,size,p);states=(unsigned int *)ck_realloc(states,(n+1)*sizeof(unsigned int));
    if(!e){states[n++]=0x1fff;break;} states[n++]=classify(buf+p,e-p);p=e;}
  *count_ref=n;return states;
}
