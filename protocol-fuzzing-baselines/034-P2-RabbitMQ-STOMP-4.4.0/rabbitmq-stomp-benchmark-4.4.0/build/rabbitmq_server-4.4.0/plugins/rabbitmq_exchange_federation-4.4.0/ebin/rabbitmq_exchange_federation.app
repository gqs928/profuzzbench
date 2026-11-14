{application, 'rabbitmq_exchange_federation', [
	{description, "RabbitMQ Exchange Federation"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['rabbit_exchange_federation_app','rabbit_exchange_federation_sup','rabbit_federation_exchange','rabbit_federation_exchange_link','rabbit_federation_exchange_link_sup_sup','rabbit_federation_upstream_exchange']},
	{registered, []},
	{applications, [kernel,stdlib,rabbit_common,rabbit,amqp_client,rabbitmq_federation_common]},
	{optional_applications, []},
	{mod, {'rabbit_exchange_federation_app', []}},
	{env, [
	    {pgroup_name_cluster_id, false},
	    {internal_exchange_check_interval, 90000},
	    {connection_close_timeout, 5000}
	  ]},
		{broker_version_requirements, []}
]}.