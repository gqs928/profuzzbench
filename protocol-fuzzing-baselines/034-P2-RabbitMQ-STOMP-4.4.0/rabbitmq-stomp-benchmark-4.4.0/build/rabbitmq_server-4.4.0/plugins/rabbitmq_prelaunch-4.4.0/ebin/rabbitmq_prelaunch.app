{application, 'rabbitmq_prelaunch', [
	{description, "RabbitMQ prelaunch setup"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['rabbit_boot_state','rabbit_boot_state_sup','rabbit_boot_state_systemd','rabbit_boot_state_xterm_titlebar','rabbit_logger_fmt_helpers','rabbit_logger_json_fmt','rabbit_logger_std_h','rabbit_logger_text_fmt','rabbit_prelaunch','rabbit_prelaunch_app','rabbit_prelaunch_conf','rabbit_prelaunch_dist','rabbit_prelaunch_early_logging','rabbit_prelaunch_erlang_compat','rabbit_prelaunch_errors','rabbit_prelaunch_file','rabbit_prelaunch_sighandler','rabbit_prelaunch_sup','rabbit_prelaunch_ulimit']},
	{registered, []},
	{applications, [kernel,stdlib,rabbit_common,cuttlefish,osiris,systemd]},
	{optional_applications, []},
	{mod, {'rabbit_prelaunch_app', []}},
	{env, []}
]}.