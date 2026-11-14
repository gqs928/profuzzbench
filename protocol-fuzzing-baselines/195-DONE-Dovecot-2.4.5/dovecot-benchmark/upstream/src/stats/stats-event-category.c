/* Copyright (c) Dovecot authors, see top-level COPYING file */

#include "lib.h"
#include "array.h"
#include "stats-event-category.h"

static pool_t categories_pool;
static ARRAY(struct event_category *) registered_categories;

void stats_event_category_register(const char *name,
				   struct event_category *parent)
{
	struct event_category *category =
		p_new(categories_pool, struct event_category, 1);
	category->parent = parent;
	category->name = p_strdup(categories_pool, name);
	array_push_back(&registered_categories, &category);

	/* Create a temporary event to register the category. A bit slower
	   than necessary, but this code won't be called often. */
	struct event *event = event_create(NULL);
	struct event_category *categories[] = { category, NULL };
	event_add_categories(event, categories);
	event_unref(&event);
}

void stats_event_categories_init(void)
{
	categories_pool = pool_alloconly_create("categories", 1024);
	p_array_init(&registered_categories, categories_pool, 16);
}

void stats_event_categories_deinit(void)
{
	struct event_category *category;

	/* The categories stay registered in lib-event, but the structs
	   allocated from the pool must not be referenced anymore. */
	array_foreach_elem(&registered_categories, category)
		event_category_unregister(category);
	pool_unref(&categories_pool);
}
