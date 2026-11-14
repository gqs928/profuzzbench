#ifndef AFLNET_GRAPHVIZ_STUB_H
#define AFLNET_GRAPHVIZ_STUB_H
#include <stdio.h>
typedef struct Agnode_s Agnode_t;
typedef struct Agedge_s Agedge_t;
typedef struct Agraph_s Agraph_t;
typedef struct Agdesc_s { int directed; } Agdesc_t;
#define Agdirected ((Agdesc_t){1})
#define AGNODE 0
#define AGEDGE 1
#ifndef FALSE
#define FALSE 0
#endif
#ifndef TRUE
#define TRUE 1
#endif
Agraph_t *agopen(const char *name, Agdesc_t desc, void *disc);
void *agattr(Agraph_t *g, int kind, const char *name, const char *value);
Agnode_t *agnode(Agraph_t *g, const char *name, int create);
Agedge_t *agedge(Agraph_t *g, Agnode_t *tail, Agnode_t *head, const char *name, int create);
int agset(void *obj, const char *name, const char *value);
int agwrite(Agraph_t *g, FILE *stream);
int agclose(Agraph_t *g);
#endif
