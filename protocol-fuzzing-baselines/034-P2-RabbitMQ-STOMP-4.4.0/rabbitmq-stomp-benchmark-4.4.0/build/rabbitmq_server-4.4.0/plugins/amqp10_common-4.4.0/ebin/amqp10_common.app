{application, 'amqp10_common', [
	{description, "Modules shared by rabbitmq-amqp1.0 and rabbitmq-amqp1.0-client"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['amqp10_binary_generator','amqp10_binary_parser','amqp10_composite','amqp10_framing','amqp10_framing0','amqp10_util','serial_number']},
	{registered, []},
	{applications, [kernel,stdlib]},
	{optional_applications, []},
	{env, []},
	%% Hex.pm package informations.
	{licenses, ["MPL-2.0"]},
	{links, [
	    {"Website", "https://www.rabbitmq.com/"},
	    {"GitHub", "https://github.com/rabbitmq/rabbitmq-server/tree/main/deps/amqp10_common"}
	  ]},
	{build_tools, ["make", "rebar3"]},
	{files, [
	    	    "erlang.mk",
	    "git-revisions.txt",
	    "include",
	    "LICENSE*",
	    "Makefile",
	    "rabbitmq-components.mk",
	    "README",
	    "README.md",
	    "src"
	  ]}
]}.