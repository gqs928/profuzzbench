{application, 'rabbitmq_auth_backend_http', [
	{description, "RabbitMQ HTTP Authentication Backend"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['rabbit_auth_backend_http','rabbit_auth_backend_http_app']},
	{registered, []},
	{applications, [kernel,stdlib,ssl,inets,crypto,public_key,rabbit_common,rabbit,amqp_client]},
	{optional_applications, []},
	{mod, {'rabbit_auth_backend_http_app', []}},
	{env, [
	    {http_method,   	 get},
	    {request_timeout,    15000},
	    {connection_timeout, 15000},
	    {user_path,     "http://localhost:8000/auth/user"},
	    {vhost_path,    "http://localhost:8000/auth/vhost"},
	    {resource_path, "http://localhost:8000/auth/resource"},
	    {topic_path,    "http://localhost:8000/auth/topic"},
	    {authorization_failure_disclosure, false}
	  ]},
		{broker_version_requirements, []}
]}.