{application, 'rabbitmq_peer_discovery_k8s', [
	{description, "Kubernetes-based RabbitMQ peer discovery backend"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['rabbit_peer_discovery_k8s','rabbitmq_peer_discovery_k8s']},
	{registered, []},
	{applications, [kernel,stdlib,rabbit_common,rabbitmq_peer_discovery_common,rabbit]},
	{optional_applications, []},
	{env, []}
]}.