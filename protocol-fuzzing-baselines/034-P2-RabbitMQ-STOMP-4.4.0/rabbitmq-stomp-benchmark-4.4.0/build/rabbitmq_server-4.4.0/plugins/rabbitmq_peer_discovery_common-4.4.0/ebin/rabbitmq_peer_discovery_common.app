{application, 'rabbitmq_peer_discovery_common', [
	{description, "Modules shared by various peer discovery backends"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['rabbit_peer_discovery_cleanup','rabbit_peer_discovery_common_app','rabbit_peer_discovery_common_sup','rabbit_peer_discovery_config','rabbit_peer_discovery_httpc','rabbit_peer_discovery_util']},
	{registered, []},
	{applications, [kernel,stdlib,inets,rabbit_common,rabbit]},
	{optional_applications, []},
	{mod, {'rabbit_peer_discovery_common_app', []}},
	{env, []}
]}.