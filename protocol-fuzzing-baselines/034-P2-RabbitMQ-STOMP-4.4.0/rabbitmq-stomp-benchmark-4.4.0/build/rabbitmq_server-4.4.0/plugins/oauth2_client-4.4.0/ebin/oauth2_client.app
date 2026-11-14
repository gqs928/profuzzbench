{application, 'oauth2_client', [
	{description, "OAuth2 client from the RabbitMQ Project"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['jwt_helper','oauth2_client']},
	{registered, []},
	{applications, [kernel,stdlib,ssl,inets,crypto,public_key,rabbit_common]},
	{optional_applications, []},
	{env, []}
]}.