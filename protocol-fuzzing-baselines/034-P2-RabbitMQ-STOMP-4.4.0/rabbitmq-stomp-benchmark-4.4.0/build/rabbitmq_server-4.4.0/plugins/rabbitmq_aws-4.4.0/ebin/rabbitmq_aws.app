{application, 'rabbitmq_aws', [
	{description, "AWS API library used by rabbitmq_peer_discovery_aws"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['rabbitmq_aws','rabbitmq_aws_app','rabbitmq_aws_config','rabbitmq_aws_json','rabbitmq_aws_sign','rabbitmq_aws_sup','rabbitmq_aws_urilib','rabbitmq_aws_xml']},
	{registered, [rabbitmq_aws_sup,rabbitmq_aws_sup]},
	{applications, [kernel,stdlib,crypto,inets,ssl,xmerl,public_key]},
	{optional_applications, []},
	{mod, {'rabbitmq_aws_app', []}},
	{env, []}
]}.