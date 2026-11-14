{application, 'rabbitmq_stream', [
	{description, "RabbitMQ Stream"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['Elixir.RabbitMQ.CLI.Ctl.Commands.ActivateStreamConsumerCommand','Elixir.RabbitMQ.CLI.Ctl.Commands.AddSuperStreamCommand','Elixir.RabbitMQ.CLI.Ctl.Commands.DeleteSuperStreamCommand','Elixir.RabbitMQ.CLI.Ctl.Commands.ListStreamConnectionsCommand','Elixir.RabbitMQ.CLI.Ctl.Commands.ListStreamConsumerGroupsCommand','Elixir.RabbitMQ.CLI.Ctl.Commands.ListStreamConsumersCommand','Elixir.RabbitMQ.CLI.Ctl.Commands.ListStreamGroupConsumersCommand','Elixir.RabbitMQ.CLI.Ctl.Commands.ListStreamPublishersCommand','Elixir.RabbitMQ.CLI.Ctl.Commands.ListStreamTrackingCommand','Elixir.RabbitMQ.CLI.Ctl.Commands.ResetOffsetCommand','rabbit_stream','rabbit_stream_connection_sup','rabbit_stream_manager','rabbit_stream_metrics','rabbit_stream_metrics_gc','rabbit_stream_reader','rabbit_stream_sup','rabbit_stream_utils']},
	{registered, []},
	{applications, [kernel,stdlib,ssl,rabbit,rabbitmq_stream_common,osiris,ranch]},
	{optional_applications, []},
	{mod, {'rabbit_stream', []}},
	{env, [
	{tcp_listeners, [5552]},
	{num_tcp_acceptors, 10},
	{tcp_listen_options, [{backlog,   128},
                          {nodelay,   true}]},
	{ssl_listeners, []},
	{num_ssl_acceptors, 10},
	{ssl_listen_options, []},
	{initial_credits, 50000},
	{credits_required_for_unblocking, 12500},
	{frame_max, 1048576},
	{max_uncompressed_sub_entry_batch_size, 67108864},
	{heartbeat, 60},
	{advertised_host, undefined},
	{advertised_port, undefined}
]}
]}.