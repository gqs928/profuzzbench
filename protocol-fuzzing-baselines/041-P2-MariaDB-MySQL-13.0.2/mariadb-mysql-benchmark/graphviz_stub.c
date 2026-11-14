/* Minimal Graphviz-compatible state graph writer for AFLNet. It preserves the
 * IPSM DOT output without requiring the full Graphviz development stack. */
#include <stdlib.h>
#include <string.h>
#include "graphviz_stub.h"
typedef struct { int kind; char *color; } Agobj_t;
struct Agnode_s { Agobj_t obj; char *name; };
struct Agedge_s { Agobj_t obj; Agnode_t *tail, *head; char *name; };
struct Agraph_s { char *name, *node_color, *edge_color; Agnode_t **nodes; size_t nnodes; Agedge_t **edges; size_t nedges; };
static char *dupstr(const char *s) { size_t n=strlen(s)+1; char *p=malloc(n); if(p) memcpy(p,s,n); return p; }
Agraph_t *agopen(const char *name, Agdesc_t desc, void *disc) {
  Agraph_t *g=calloc(1,sizeof(*g)); (void)desc; (void)disc;
  if(g) { g->name=dupstr(name ? name : "g"); g->node_color=dupstr("black"); g->edge_color=dupstr("black"); }
  return g;
}
void *agattr(Agraph_t *g, int kind, const char *name, const char *value) {
  (void)name;
  if(!g || !value) return NULL;
  if(kind==AGNODE) { free(g->node_color); g->node_color=dupstr(value); }
  else if(kind==AGEDGE) { free(g->edge_color); g->edge_color=dupstr(value); }
  return NULL;
}
Agnode_t *agnode(Agraph_t *g, const char *name, int create) {
  size_t i; if(!g || !name) return NULL;
  for(i=0;i<g->nnodes;i++) if(!strcmp(g->nodes[i]->name,name)) return g->nodes[i];
  if(!create) return NULL;
  Agnode_t *n=calloc(1,sizeof(*n)); if(!n) return NULL;
  n->obj.kind=AGNODE; n->name=dupstr(name); n->obj.color=dupstr(g->node_color);
  Agnode_t **v=realloc(g->nodes,(g->nnodes+1)*sizeof(*v)); if(!v) { free(n->name); free(n->obj.color); free(n); return NULL; }
  g->nodes=v; g->nodes[g->nnodes++]=n; return n;
}
Agedge_t *agedge(Agraph_t *g, Agnode_t *tail, Agnode_t *head, const char *name, int create) {
  size_t i; if(!g || !tail || !head) return NULL;
  for(i=0;i<g->nedges;i++) if(g->edges[i]->tail==tail && g->edges[i]->head==head) return g->edges[i];
  if(!create) return NULL;
  Agedge_t *e=calloc(1,sizeof(*e)); if(!e) return NULL;
  e->obj.kind=AGEDGE; e->tail=tail; e->head=head; e->name=dupstr(name ? name : "edge"); e->obj.color=dupstr(g->edge_color);
  Agedge_t **v=realloc(g->edges,(g->nedges+1)*sizeof(*v)); if(!v) { free(e->name); free(e->obj.color); free(e); return NULL; }
  g->edges=v; g->edges[g->nedges++]=e; return e;
}
int agset(void *ptr, const char *name, const char *value) {
  Agobj_t *obj=ptr; if(!obj || !name || strcmp(name,"color") || !value) return -1;
  char *copy=dupstr(value); if(!copy) return -1; free(obj->color); obj->color=copy; return 0;
}
int agwrite(Agraph_t *g, FILE *stream) {
  size_t i; if(!g || !stream) return -1;
  if(fprintf(stream,"digraph %s {\n",g->name)<0) return -1;
  for(i=0;i<g->nnodes;i++) if(fprintf(stream,"  \"%s\" [color=\"%s\"];\n",g->nodes[i]->name,g->nodes[i]->obj.color)<0) return -1;
  for(i=0;i<g->nedges;i++) if(fprintf(stream,"  \"%s\" -> \"%s\" [color=\"%s\"];\n",g->edges[i]->tail->name,g->edges[i]->head->name,g->edges[i]->obj.color)<0) return -1;
  return fprintf(stream,"}\n")<0 ? -1 : 0;
}
int agclose(Agraph_t *g) {
  size_t i; if(!g) return 0;
  for(i=0;i<g->nnodes;i++) { free(g->nodes[i]->name); free(g->nodes[i]->obj.color); free(g->nodes[i]); }
  for(i=0;i<g->nedges;i++) { free(g->edges[i]->name); free(g->edges[i]->obj.color); free(g->edges[i]); }
  free(g->nodes); free(g->edges); free(g->name); free(g->node_color); free(g->edge_color); free(g); return 0;
}
