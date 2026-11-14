{application, 'rabbitmq_auth_mechanism_ssl', [
	{description, "RabbitMQ SSL authentication (SASL EXTERNAL)"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['rabbit_auth_mechanism_ssl','rabbit_auth_mechanism_ssl_app']},
	{registered, []},
	{applications, [kernel,stdlib,public_key,rabbit_common,rabbit]},
	{optional_applications, []},
	{mod, {'rabbit_auth_mechanism_ssl_app', []}},
	{env, [
	    {name_from, distinguished_name}
	  ]},
		{broker_version_requirements, []}
]}.