{application, 'rabbitmq_web_stomp_examples', [
	{description, "Rabbit WEB-STOMP - examples"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['rabbit_web_stomp_examples_app']},
	{registered, []},
	{applications, [kernel,stdlib,rabbit_common,rabbit,rabbitmq_web_dispatch,rabbitmq_web_stomp]},
	{optional_applications, []},
	{mod, {'rabbit_web_stomp_examples_app', []}},
	{env, [
	    {listener, [{port, 15670}]}
	  ]}
]}.