#include <assert.h>
#include <string.h>
#include "alloc-inl.h"
#include "aflnet.h"
region_t *extract_requests_netconf(unsigned char *,unsigned int,unsigned int *);
unsigned int *extract_response_codes_netconf(unsigned char *,unsigned int,unsigned int *);
int main(void){
 unsigned char req[]="<hello xmlns=\"urn:ietf:params:xml:ns:netconf:base:1.0\"/>]]>]]><rpc message-id=\"1\"/>]]>]]>";
 unsigned char chunk[]="\n#6\n<rpc/>\n##\n";
 unsigned char rsp[]="<hello/>]]>]]><rpc-reply><rpc-error/></rpc-reply>]]>]]>";
 unsigned int n=0,ns=0;region_t*r=extract_requests_netconf(req,sizeof(req)-1,&n);assert(n==2);assert(r[0].start_byte==0);assert(req[r[0].end_byte]=='>');ck_free(r);
 r=extract_requests_netconf(chunk,sizeof(chunk)-1,&n);assert(n==1&&r[0].end_byte==(int)sizeof(chunk)-2);ck_free(r);
 unsigned int*s=extract_response_codes_netconf(rsp,sizeof(rsp)-1,&ns);assert(ns==3&&s[0]==0&&s[1]==0x100&&s[2]==0x301);ck_free(s);
 return 0;
}
