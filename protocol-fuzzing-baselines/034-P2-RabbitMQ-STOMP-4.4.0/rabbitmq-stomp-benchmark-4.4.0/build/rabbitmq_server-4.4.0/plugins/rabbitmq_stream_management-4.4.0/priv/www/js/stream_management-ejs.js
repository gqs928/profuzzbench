var COMPILED_TEMPLATES = COMPILED_TEMPLATES || {};

COMPILED_TEMPLATES["streamConnection"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h2>Connection ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.name) )));
        ___ViewO.push(" ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_maybe_vhost(connection.vhost) )));
        ___ViewO.push("</h1>\n\n");
         if (!disable_stats) { 
        ___ViewO.push("\n<div class=\"section\">\n<h2>Overview</h2>\n<div class=\"hider updatable\">\n  ");
        ___ViewO.push((EJS.Scanner.to_text( data_rates('data-rates-conn', connection, 'Data rates') )));
        ___ViewO.push("\n\n<h3>Details</h3>\n<table class=\"facts facts-l\">\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n<tr>\n  <th>Node</th>\n  <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(connection.node) )));
        ___ViewO.push("</td>\n</tr>\n");
         } 
        ___ViewO.push("\n\n");
         if (connection.client_properties.connection_name) { 
        ___ViewO.push("\n<tr>\n  <th>Client-provided connection name</th>\n  <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.client_properties.connection_name) )));
        ___ViewO.push("</td>\n</tr>\n");
         } 
        ___ViewO.push("\n\n<tr>\n <th>Username</th>\n <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.user) )));
        ___ViewO.push("</td>\n</tr>\n<tr>\n <th>Protocol</th>\n <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.protocol) )));
        ___ViewO.push("</td>\n</tr>\n<tr>\n  <th>Connected at</th>\n  <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_timestamp(connection.connected_at) )));
        ___ViewO.push("</td>\n</tr>\n\n");
         if (connection.ssl) { 
        ___ViewO.push("\n<tr>\n <th>SSL</th>\n <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(connection.ssl) )));
        ___ViewO.push("</td>\n</tr>\n");
         } 
        ___ViewO.push("\n\n");
         if (connection.auth_mechanism) { 
        ___ViewO.push("\n<tr>\n <th>Authentication</th>\n <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.auth_mechanism) )));
        ___ViewO.push("</td>\n</tr>\n");
         } 
        ___ViewO.push("\n</table>\n\n");
         if (connection.state) { 
        ___ViewO.push("\n<table class=\"facts\">\n<tr>\n <th>State</th>\n <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_object_state(connection) )));
        ___ViewO.push("</td>\n</tr>\n<tr>\n <th>Heartbeat</th>\n <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_time(connection.timeout, 's') )));
        ___ViewO.push("</td>\n</tr>\n<tr>\n <th>Frame max</th>\n <td>");
        ___ViewO.push((EJS.Scanner.to_text( connection.frame_max )));
        ___ViewO.push(" bytes</td>\n</tr>\n</table>\n\n");
         } 
        ___ViewO.push("\n\n</div>\n</div>\n\n");
         if (connection.ssl) { 
        ___ViewO.push("\n<div class=\"section\">\n<h2>SSL</h2>\n<div class=\"hider\">\n\n<table class=\"facts\">\n  <tr>\n    <th>Protocol Version</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.ssl_protocol) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Key Exchange Algorithm</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.ssl_key_exchange) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Cipher Algorithm</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.ssl_cipher) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Hash Algorithm</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.ssl_hash) )));
        ___ViewO.push("</td>\n  </tr>\n</table>\n\n");
         if (connection.peer_cert_issuer != '') { 
        ___ViewO.push("\n<table class=\"facts\">\n  <tr>\n    <th>Peer Certificate Serial Number</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.peer_cert_serial_number) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Peer Certificate Issuer</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.peer_cert_issuer) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Peer Certificate Subject</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.peer_cert_subject) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Peer Certificate Validity</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.peer_cert_validity) )));
        ___ViewO.push("</td>\n  </tr>\n</table>\n");
         } 
        ___ViewO.push("\n</div>\n</div>\n");
         } 
        ___ViewO.push("\n\n<div class=\"section\">\n  <h2 class=\"updatable\">Publishers (");
        ___ViewO.push((EJS.Scanner.to_text((publishers.length))));
        ___ViewO.push(") </h2>\n  <div class=\"hider updatable\">\n    ");
        ___ViewO.push((EJS.Scanner.to_text( format('streamPublishersList', {'publishers': publishers, 'mode' : 'connection'}) )));
        ___ViewO.push("\n  </div>\n</div>\n\n<div class=\"section\">\n  <h2 class=\"updatable\" >Consumers (");
        ___ViewO.push((EJS.Scanner.to_text((consumers.length))));
        ___ViewO.push(")</h2>\n  <div class=\"hider updatable\">\n    ");
        ___ViewO.push((EJS.Scanner.to_text( format('streamConsumersList', {'consumers': consumers}) )));
        ___ViewO.push("\n  </div>\n</div>\n\n");
         if (properties_size(connection.client_properties) > 0) { 
        ___ViewO.push("\n<div class=\"section-hidden\">\n<h2>Client properties</h2>\n<div class=\"hider updatable\">\n");
        ___ViewO.push((EJS.Scanner.to_text( fmt_table_long(connection.client_properties) )));
        ___ViewO.push("\n</div>\n</div>\n");
         } 
        ___ViewO.push("\n\n");
         if(connection.reductions || connection.garbage_collection) { 
        ___ViewO.push("\n<div class=\"section-hidden\">\n<h2>Runtime Metrics (Advanced)</h2>\n <div class=\"hider updatable\">\n ");
        ___ViewO.push((EJS.Scanner.to_text( data_reductions('reductions-rates-conn', connection) )));
        ___ViewO.push("\n <table class=\"facts\">\n    ");
         if (connection.garbage_collection.min_bin_vheap_size) { 
        ___ViewO.push("\n        <tr>\n        <th>Minimum binary virtual heap size in words (min_bin_vheap_size)</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( connection.garbage_collection.min_bin_vheap_size )));
        ___ViewO.push("</td>\n        </tr>\n    ");
         } 
        ___ViewO.push("\n\n    ");
         if (connection.garbage_collection.min_heap_size) { 
        ___ViewO.push("\n        <tr>\n        <th>Minimum heap size in words (min_heap_size)</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( connection.garbage_collection.min_heap_size )));
        ___ViewO.push("</td>\n        </tr>\n    ");
         } 
        ___ViewO.push("\n\n    ");
         if (connection.garbage_collection.fullsweep_after) { 
        ___ViewO.push("\n        <tr>\n        <th>Maximum generational collections before fullsweep (fullsweep_after)</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( connection.garbage_collection.fullsweep_after )));
        ___ViewO.push("</td>\n        </tr>\n    ");
         } 
        ___ViewO.push("\n\n    ");
         if (connection.garbage_collection.minor_gcs) { 
        ___ViewO.push("\n        <tr>\n        <th>Number of minor GCs (minor_gcs)</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( connection.garbage_collection.minor_gcs )));
        ___ViewO.push("</td>\n        </tr>\n    ");
         } 
        ___ViewO.push("\n </table>\n </div>\n</div>\n\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n\n<div class=\"section-hidden\">\n  <h2>Close this connection</h2>\n  <div class=\"hider\">\n    <form action=\"#/connections\" method=\"delete\" class=\"confirm\">\n      <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.name) )));
        ___ViewO.push("\"/>\n      <table class=\"form\">\n        <tr>\n          <th><label>Reason:</label></th>\n          <td>\n            <input type=\"text\" name=\"reason\" value=\"Closed via management plugin\" class=\"wide\"/>\n          </td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Force Close\"/>\n    </form>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["streamConnections"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<div class=\"section\">\n ");
        ___ViewO.push((EJS.Scanner.to_text( paginate_ui(connections, 'streamConnections', 'stream connections') )));
        ___ViewO.push("\n</div>\n<div class=\"updatable\">\n");
         if (connections.items.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n <thead>\n  <tr>\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('streamConnections', 'Overview', [vhosts_interesting, nodes_interesting, true]) )));
        ___ViewO.push("\n    ");
         if (!disable_stats) { 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('streamConnections', 'Details', []) )));
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('streamConnections', 'Network', []) )));
        ___ViewO.push("\n    ");
         } 
        ___ViewO.push("\n    <th class=\"plus-minus\"><span class=\"popup-options-link\" title=\"Click to change columns\" type=\"columns\" for=\"streamConnections\">+/-</span></th>\n  </tr>\n  <tr>\n");
         if (vhosts_interesting) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Virtual host', 'vhost') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if(disable_stats) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Name',           'name') )));
        ___ViewO.push("</th>\n");
         } else { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Name',           'client_properties.connection_name') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Node',           'node') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections',      'user')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('User name',      'user') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (!disable_stats) { 
        ___ViewO.push("\n");
         if (show_column('streamConnections',      'state')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('State',          'state') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections',      'ssl')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('SSL / TLS',      'ssl') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections',      'ssl_info')) { 
        ___ViewO.push("\n    <th>SSL Details</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections',      'protocol')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Protocol',       'protocol') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections',      'frame_max')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Frame max',      'frame_max') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections',      'auth_mechanism')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Auth mechanism', 'auth_mechanism') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections',      'client')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Client',         'properties') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections',      'from_client')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('From client',    'recv_oct_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections',      'to_client')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('To client',      'send_oct_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections',      'heartbeat')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Heartbeat',      'timeout') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections',      'connected_at')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Connected at',   'connected_at') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n  </tr>\n </thead>\n <tbody>\n");
        
 for (var i = 0; i < connections.items.length; i++) {
    var connection = connections.items[i];
        ___ViewO.push("\n  <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n");
         if (vhosts_interesting) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.vhost) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if(connection.client_properties) { 
        ___ViewO.push("\n    <td>\n      ");
        ___ViewO.push((EJS.Scanner.to_text( link_stream_conn(connection.vhost, connection.name) )));
        ___ViewO.push("\n      <sub>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(short_conn(connection.client_properties.connection_name)) )));
        ___ViewO.push("</sub>\n    </td>\n");
         } else { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_stream_conn(connection.vhost, connection.name) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(connection.node) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections', 'user')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.user) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (!disable_stats) { 
        ___ViewO.push("\n");
         if (show_column('streamConnections', 'state')) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_object_state(connection) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections', 'ssl')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(connection.ssl, '') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections', 'ssl_info')) { 
        ___ViewO.push("\n    <td>\n    ");
         if (connection.ssl) { 
        ___ViewO.push("\n      ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.ssl_protocol) )));
        ___ViewO.push("\n      <sub>\n        ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.ssl_key_exchange) )));
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.ssl_cipher) )));
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.ssl_hash) )));
        ___ViewO.push("\n      </sub>\n    ");
         } 
        ___ViewO.push("\n    </td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections', 'protocol')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.protocol) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections', 'frame_max')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.frame_max, '') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections', 'auth_mechanism')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.auth_mechanism, '') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections', 'client')) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_client_name(connection.client_properties) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections', 'from_client')) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate_bytes(connection, 'recv_oct') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections', 'to_client')) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate_bytes(connection, 'send_oct') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections', 'heartbeat')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_time(connection.timeout, 's') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('streamConnections', 'connected_at')) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_timestamp_mini(connection.connected_at) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n  ");
         } 
        ___ViewO.push("\n  </tr>\n  ");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no connections ...</p>\n");
         } 
        ___ViewO.push("\n</div>");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["streamConsumersList"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
         if (consumers.length > 0) { 
        ___ViewO.push("\n    <table class=\"list\">\n      <thead>\n        <tr>\n          <th>Subscription ID</th>\n          <th>Stream</th>\n          <th>Messages Consumed</th>\n          <th>Offset</th>\n          <th>Offset Lag</th>\n          <th>Credits</th>\n          <th>Active</span></th>\n          <th>Activity status</th>\n          <th>Properties</th>\n        </tr>\n      </thead>\n");
        
  for (var i = 0; i < consumers.length; i++) {
    var consumer = consumers[i];
        ___ViewO.push("\n      <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i) )));
        ___ViewO.push(">\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( consumer.subscription_id )));
        ___ViewO.push("</td>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_queue(consumer.queue.vhost, consumer.queue.name) )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( consumer.consumed )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( consumer.offset )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( consumer.offset_lag )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( consumer.credits )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(consumer.active, "&#9679;") )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_activity_status(consumer.activity_status, "up") )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_table_short(consumer.properties) )));
        ___ViewO.push("</td>\n      </tr>\n");
         } 
        ___ViewO.push("\n    </table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no consumers ...</p>\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["streamPublishersList"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
         if (publishers.length > 0) { 
        ___ViewO.push("\n    <table class=\"list\">\n      <thead>\n        <tr>\n");
         if (mode == 'queue') { 
        ___ViewO.push("\n          <th>Connection</th>\n          <th>ID</th>\n          <th>Reference</th>\n");
         } else { 
        ___ViewO.push("\n          <th>ID</th>\n          <th>Reference</th>\n          <th>Queue</th>\n");
         } 
        ___ViewO.push("\n          <th>Messages Published</th>\n          <th>Messages Confirmed</th>\n          <th>Messages Errored</th>\n        </tr>\n      </thead>\n");
        
  for (var i = 0; i < publishers.length; i++) {
    var publisher = publishers[i];
        ___ViewO.push("\n      <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i) )));
        ___ViewO.push(">\n");
         if (mode == 'queue') { 
        ___ViewO.push("\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_stream_conn(publisher.queue.vhost, publisher.connection_details.name) )));
        ___ViewO.push("</td>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( publisher.publisher_id )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(publisher.reference) )));
        ___ViewO.push("</td>\n");
         } else { 
        ___ViewO.push("\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( publisher.publisher_id )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(publisher.reference) )));
        ___ViewO.push("</td>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_queue(publisher.queue.vhost, publisher.queue.name) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( publisher.published )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( publisher.confirmed )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( publisher.errored )));
        ___ViewO.push("</td>\n      </tr>\n");
         } 
        ___ViewO.push("\n    </table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no publishers ...</p>\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["superStreams"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h2> Super Streams </h2>\n\n");
         if (ac.canAccessVhosts()) { 
        ___ViewO.push("\n<div class=\"section\">\n  <h2>Add a new super stream</h2>\n  <div class=\"hider\">\n    <form action=\"#/stream/super-streams\" method=\"put\">\n      <table class=\"form\">\n");
         if (display.vhosts) { 
        ___ViewO.push("\n        <tr>\n          <th><label>Virtual host:</label></th>\n          <td>\n            <select name=\"vhost\">\n              ");
         for (var i = 0; i < vhosts.length; i++) { 
        ___ViewO.push("\n              <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("\" ");
        ___ViewO.push((EJS.Scanner.to_text( (vhosts[i].name === current_vhost) ? 'selected="selected"' : '' )));
        ___ViewO.push(">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("</option>\n              ");
         } 
        ___ViewO.push("\n            </select>\n          </td>\n        </tr>\n");
         } else { 
        ___ViewO.push("\n        <tr><td><input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[0].name) )));
        ___ViewO.push("\"/></td></tr>\n");
         } 
        ___ViewO.push("\n        <tr>\n          <th><label>Name:</label></th>\n          <td><input type=\"text\" name=\"name\"/><span class=\"mand\">*</span></td>\n        </tr>\n        <tr>\n          <th>\n            <label>\n              <select name=\"has-partitions\" class=\"narrow controls-appearance\">\n                <option value=\"partitions\" selected=\"selected\">Partitions:</option>\n                <option value=\"binding-keys\">Binding keys:</option>\n              </select>\n            </label>\n          </th>\n          <td>\n            <div id=\"partitions-div\">\n              <input type=\"partitions\" name=\"partitions\" />\n              <span class=\"mand\">*</span><br/>\n            </div>\n            <div id=\"binding-keys-div\" style=\"display: none;\">\n              <input type=\"binding-keys\" name=\"binding-keys\" />\n              <span class=\"mand\">*</span><br/>\n            </div>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Arguments:</label></th>\n          <td>\n            <div class=\"multifield\" id=\"arguments\"></div>\n            <table class=\"argument-links\">\n              <tr>\n                <td>Add</td>\n                <td>\n                  <span class=\"argument-link\" field=\"arguments\" key=\"max-length-bytes\" type=\"number\">Max length bytes</span> <span class=\"help\" id=\"queue-max-length-bytes\"></span>\n                  | <span class=\"argument-link\" field=\"arguments\" key=\"max-age\" type=\"string\">Max time retention</span><span class=\"help\" id=\"queue-max-age\"></span>\n                  | <span class=\"argument-link\" field=\"arguments\" key=\"stream-max-segment-size-bytes\" type=\"number\">Max segment size in bytes</span><span class=\"help\" id=\"queue-stream-max-segment-size-bytes\"></span></br>\n                  | <span class=\"argument-link\" field=\"arguments\" key=\"stream-initial-offset\" type=\"string\">Initial offset</span><span class=\"help\" id=\"queue-stream-initial-offset\"></span>\n                  | <span class=\"argument-link\" field=\"arguments\" key=\"initial-cluster-size\" type=\"number\">Initial cluster size</span><span class=\"help\" id=\"queue-initial-cluster-size\"></span>\n                  | <span class=\"argument-link\" field=\"arguments\" key=\"queue-leader-locator\" type=\"string\">Leader locator</span><span class=\"help\" id=\"queue-leader-locator\"></span>\n                </td>\n              </tr>\n            </table>\n          </td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Add super stream\"/>\n    </form>\n  </div>\n</div>\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};
