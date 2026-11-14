{application, 'rabbitmq_web_dispatch', [
	{description, "RabbitMQ Web Dispatcher"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['rabbit_access_log_fmt','rabbit_cowboy_middleware','rabbit_cowboy_redirect','rabbit_cowboy_stream_h','rabbit_web_dispatch','rabbit_web_dispatch_access_control','rabbit_web_dispatch_access_log','rabbit_web_dispatch_app','rabbit_web_dispatch_listing_handler','rabbit_web_dispatch_registry','rabbit_web_dispatch_sup','rabbit_web_dispatch_util']},
	{registered, []},
	{applications, [kernel,stdlib,inets,amqp_client,rabbit_common,rabbit,cowboy]},
	{optional_applications, []},
	{mod, {'rabbit_web_dispatch_app', []}},
	{env, [
	    {access_log_dir, none}
	  ]},
		{broker_version_requirements, []}
]}.