{application, 'rabbitmq_prometheus', [
	{description, "Prometheus metrics for RabbitMQ"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['prometheus_process_collector','prometheus_rabbitmq_alarm_metrics_collector','prometheus_rabbitmq_core_metrics_collector','prometheus_rabbitmq_dynamic_collector','prometheus_rabbitmq_global_metrics_collector','prometheus_rabbitmq_message_size_metrics_collector','prometheus_rabbitmq_raft_metrics_collector','rabbit_prometheus_app','rabbit_prometheus_dispatcher','rabbit_prometheus_handler']},
	{registered, []},
	{applications, [kernel,stdlib,cowboy,rabbit,rabbitmq_management_agent,prometheus,rabbitmq_web_dispatch]},
	{optional_applications, []},
	{mod, {'rabbit_prometheus_app', []}},
	{env, [
	{ssl_config, []},
	{return_per_object_metrics, false}
]}
]}.