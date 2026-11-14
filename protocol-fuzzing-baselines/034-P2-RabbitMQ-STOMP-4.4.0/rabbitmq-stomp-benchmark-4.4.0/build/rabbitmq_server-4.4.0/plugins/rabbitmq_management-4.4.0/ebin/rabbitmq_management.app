{application, 'rabbitmq_management', [
	{description, "RabbitMQ Management Console"},
	{vsn, "4.4.0"},
	{id, "24d5157"},
	{modules, ['rabbit_mgmt_app','rabbit_mgmt_basic_credentials_token','rabbit_mgmt_cors','rabbit_mgmt_csp','rabbit_mgmt_db','rabbit_mgmt_db_cache','rabbit_mgmt_db_cache_sup','rabbit_mgmt_dispatcher','rabbit_mgmt_extension','rabbit_mgmt_features','rabbit_mgmt_headers','rabbit_mgmt_hsts','rabbit_mgmt_load_definitions','rabbit_mgmt_login','rabbit_mgmt_nodes','rabbit_mgmt_oauth_bootstrap','rabbit_mgmt_oauth_token_proxy','rabbit_mgmt_reset_handler','rabbit_mgmt_schema','rabbit_mgmt_stats','rabbit_mgmt_sup','rabbit_mgmt_sup_sup','rabbit_mgmt_util','rabbit_mgmt_wm_aliveness_test','rabbit_mgmt_wm_auth','rabbit_mgmt_wm_auth_attempts','rabbit_mgmt_wm_binding','rabbit_mgmt_wm_bindings','rabbit_mgmt_wm_channel','rabbit_mgmt_wm_channels','rabbit_mgmt_wm_channels_vhost','rabbit_mgmt_wm_cluster_name','rabbit_mgmt_wm_connection','rabbit_mgmt_wm_connection_channels','rabbit_mgmt_wm_connection_sessions','rabbit_mgmt_wm_connection_user_name','rabbit_mgmt_wm_connections','rabbit_mgmt_wm_connections_vhost','rabbit_mgmt_wm_consumers','rabbit_mgmt_wm_definitions','rabbit_mgmt_wm_deprecated_features','rabbit_mgmt_wm_environment','rabbit_mgmt_wm_exchange','rabbit_mgmt_wm_exchange_publish','rabbit_mgmt_wm_exchanges','rabbit_mgmt_wm_extensions','rabbit_mgmt_wm_feature_flag_enable','rabbit_mgmt_wm_feature_flags','rabbit_mgmt_wm_global_parameter','rabbit_mgmt_wm_global_parameters','rabbit_mgmt_wm_hash_password','rabbit_mgmt_wm_health_check_alarms','rabbit_mgmt_wm_health_check_below_node_connection_limit','rabbit_mgmt_wm_health_check_certificate_expiration','rabbit_mgmt_wm_health_check_is_in_service','rabbit_mgmt_wm_health_check_local_alarms','rabbit_mgmt_wm_health_check_metadata_store_initialized','rabbit_mgmt_wm_health_check_metadata_store_initialized_with_data','rabbit_mgmt_wm_health_check_node_is_quorum_critical','rabbit_mgmt_wm_health_check_port_listener','rabbit_mgmt_wm_health_check_protocol_listener','rabbit_mgmt_wm_health_check_quorum_queues_without_elected_leaders','rabbit_mgmt_wm_health_check_quorum_queues_without_elected_leaders_across_all_vhosts','rabbit_mgmt_wm_health_check_reached_target_cluster_size','rabbit_mgmt_wm_health_check_ready_to_serve_clients','rabbit_mgmt_wm_health_check_virtual_hosts','rabbit_mgmt_wm_healthchecks','rabbit_mgmt_wm_init','rabbit_mgmt_wm_limit','rabbit_mgmt_wm_limits','rabbit_mgmt_wm_login','rabbit_mgmt_wm_node','rabbit_mgmt_wm_node_memory','rabbit_mgmt_wm_node_memory_ets','rabbit_mgmt_wm_nodes','rabbit_mgmt_wm_operator_policies','rabbit_mgmt_wm_operator_policy','rabbit_mgmt_wm_overview','rabbit_mgmt_wm_parameter','rabbit_mgmt_wm_parameters','rabbit_mgmt_wm_permission','rabbit_mgmt_wm_permissions','rabbit_mgmt_wm_permissions_user','rabbit_mgmt_wm_permissions_vhost','rabbit_mgmt_wm_policies','rabbit_mgmt_wm_policy','rabbit_mgmt_wm_queue','rabbit_mgmt_wm_queue_actions','rabbit_mgmt_wm_queue_get','rabbit_mgmt_wm_queue_purge','rabbit_mgmt_wm_queues','rabbit_mgmt_wm_quorum_queue_replicas_add_member','rabbit_mgmt_wm_quorum_queue_replicas_delete_member','rabbit_mgmt_wm_quorum_queue_replicas_grow','rabbit_mgmt_wm_quorum_queue_replicas_shrink','rabbit_mgmt_wm_quorum_queue_status','rabbit_mgmt_wm_rebalance_queues','rabbit_mgmt_wm_redirect','rabbit_mgmt_wm_reset','rabbit_mgmt_wm_static','rabbit_mgmt_wm_topic_permission','rabbit_mgmt_wm_topic_permissions','rabbit_mgmt_wm_topic_permissions_user','rabbit_mgmt_wm_topic_permissions_vhost','rabbit_mgmt_wm_user','rabbit_mgmt_wm_user_limit','rabbit_mgmt_wm_user_limits','rabbit_mgmt_wm_user_queues','rabbit_mgmt_wm_users','rabbit_mgmt_wm_users_bulk_delete','rabbit_mgmt_wm_version','rabbit_mgmt_wm_vhost','rabbit_mgmt_wm_vhost_deletion_protection','rabbit_mgmt_wm_vhost_restart','rabbit_mgmt_wm_vhosts','rabbit_mgmt_wm_whoami']},
	{registered, []},
	{applications, [kernel,stdlib,ranch,ssl,crypto,public_key,inets,rabbit_common,rabbit,amqp_client,cowboy,cowlib,rabbitmq_web_dispatch,rabbitmq_management_agent,oauth2_client]},
	{optional_applications, []},
	{mod, {'rabbit_mgmt_app', []}},
	{env, [
	    {http_log_dir,      none},
	    {load_definitions,  none},
	    {management_db_cache_multiplier, 5},
	    {process_stats_gc_timeout, 300000},
	    {stats_event_max_backlog, 250},

	    {cors_allow_origins, []},
	    {cors_max_age, 1800},
	    {content_security_policy, "script-src 'self'; object-src 'self'; base-uri 'none'"},
	    {max_http_body_size, 10000000},
	    {delegate_count, 5},
	    {require_auth_for_api_reference, false}
	  ]},
		{broker_version_requirements, []}
]}.