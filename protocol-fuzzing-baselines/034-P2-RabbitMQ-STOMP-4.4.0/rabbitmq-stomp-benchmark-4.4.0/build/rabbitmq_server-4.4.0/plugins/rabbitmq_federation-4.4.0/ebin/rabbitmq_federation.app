{application, 'rabbitmq_federation', [
	{description, "Deprecated no-op RabbitMQ Federation"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['rabbitmq_federation_noop']},
	{registered, []},
	{applications, [kernel,stdlib,rabbit,rabbitmq_queue_federation,rabbitmq_exchange_federation]},
	{optional_applications, []},
	{env, []}
]}.