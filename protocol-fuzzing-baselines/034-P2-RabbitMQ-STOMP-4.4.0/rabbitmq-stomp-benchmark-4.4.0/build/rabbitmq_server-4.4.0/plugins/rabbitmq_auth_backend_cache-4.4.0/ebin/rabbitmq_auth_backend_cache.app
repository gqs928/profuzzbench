{application, 'rabbitmq_auth_backend_cache', [
	{description, "RabbitMQ Authentication Backend cache"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['Elixir.RabbitMQ.CLI.Ctl.Commands.ClearAuthBackendCacheCommand','rabbit_auth_backend_cache','rabbit_auth_backend_cache_app','rabbit_auth_cache','rabbit_auth_cache_dict','rabbit_auth_cache_ets','rabbit_auth_cache_ets_segmented','rabbit_auth_cache_ets_segmented_stateless']},
	{registered, []},
	{applications, [kernel,stdlib,rabbit_common,rabbit]},
	{optional_applications, []},
	{mod, {'rabbit_auth_backend_cache_app', []}},
	{env, [
	    {cache_ttl,      15000},
	    {cache_module,   rabbit_auth_cache_ets},
	    {cache_module_args, []},
	    {cached_backend, rabbit_auth_backend_internal},
	    {cache_refusals, false}
	  ]},
		{broker_version_requirements, []}
]}.