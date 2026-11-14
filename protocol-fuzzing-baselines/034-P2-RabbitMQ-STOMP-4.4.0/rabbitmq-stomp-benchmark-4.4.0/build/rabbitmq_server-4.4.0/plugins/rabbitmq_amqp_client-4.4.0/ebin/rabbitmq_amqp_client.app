{application, 'rabbitmq_amqp_client', [
	{description, "AMQP 1.0 client for RabbitMQ"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['rabbitmq_amqp_address','rabbitmq_amqp_client']},
	{registered, []},
	{applications, [kernel,stdlib,amqp10_client]},
	{optional_applications, []},
	{env, []}
]}.