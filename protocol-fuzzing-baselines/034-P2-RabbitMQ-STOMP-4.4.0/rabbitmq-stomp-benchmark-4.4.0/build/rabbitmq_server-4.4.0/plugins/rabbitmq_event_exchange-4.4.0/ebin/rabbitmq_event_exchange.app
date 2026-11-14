{application, 'rabbitmq_event_exchange', [
	{description, "Event Exchange Type"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['rabbit_event_exchange_decorator','rabbit_exchange_type_event']},
	{registered, []},
	{applications, [kernel,stdlib,rabbit_common,rabbit]},
	{optional_applications, []},
	{env, 	  [
		{protocol, amqp_0_9_1}
	  ]},
		{broker_version_requirements, []}
]}.