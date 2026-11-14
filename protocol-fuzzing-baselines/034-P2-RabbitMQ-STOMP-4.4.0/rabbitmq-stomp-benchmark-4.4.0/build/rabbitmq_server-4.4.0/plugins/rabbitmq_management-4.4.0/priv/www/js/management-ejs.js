var COMPILED_TEMPLATES = COMPILED_TEMPLATES || {};

COMPILED_TEMPLATES["404"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Not found</h1>\n\n<p>The object you clicked on was not found; it may have been deleted on the server.</p>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["add-binding"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
         if (mode == 'queue') { 
        ___ViewO.push("\n    <h3 style=\"padding-top: 20px;\">Add binding to this queue</h3>\n");
         } else { 
        ___ViewO.push("\n    <h3 style=\"padding-top: 20px;\">Add binding from this exchange</h3>\n");
         } 
        ___ViewO.push("\n    <form action=\"#/bindings\" method=\"post\">\n            <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(parent.vhost) )));
        ___ViewO.push("\"/>\n");
         if (mode == 'queue') { 
        ___ViewO.push("\n            <input type=\"hidden\" name=\"destination\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(parent.name) )));
        ___ViewO.push("\"/>\n");
         } else { 
        ___ViewO.push("\n            <input type=\"hidden\" name=\"source\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(parent.name) )));
        ___ViewO.push("\"/>\n");
         } 
        ___ViewO.push("\n            <table class=\"form\">\n");
         if (mode == 'queue') { 
        ___ViewO.push("\n              <tr>\n                <th>\n                  <label>From exchange:</label>\n                </th>\n                <td>\n                  <input type=\"hidden\" name=\"destination_type\" value=\"q\"/>\n                  <input type=\"text\" name=\"source\" value=\"\"/>\n                  <span class=\"mand\">*</span>\n                </td>\n              </tr>\n");
         } else { 
        ___ViewO.push("\n              <tr>\n                <th>\n                  <select name=\"destination_type\" class=\"narrow\">\n                    <option value=\"e\">To exchange</option>\n                    <option value=\"q\" selected=\"selected\">To queue</option>\n                  </select>:\n                </th>\n                <td>\n                  <input type=\"text\" name=\"destination\" value=\"\"/>\n                  <span class=\"mand\">*</span>\n                </td>\n              </tr>\n");
         } 
        ___ViewO.push("\n              <tr>\n                <th><label>Routing key:</label></th>\n                <td><input type=\"text\" name=\"routing_key\" value=\"\"/></td>\n              </tr>\n              <tr>\n                <th><label>Arguments:</label></th>\n                <td><div class=\"multifield\" id=\"arguments\"></div></td>\n              </tr>\n            </table>\n      <input type=\"submit\" value=\"Bind\"/>\n    </form>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["binary"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        
  if (binary == "not_available") {
        ___ViewO.push("\n<p class=\"warning\">\n  Binary statistics not available.\n</p>\n");
         } else { 
        ___ViewO.push("\n    ");
        
    var total_out = [];
    
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( format('memory-bar', {sections: BINARY_STATISTICS.sections, memory: binary, total_out: total_out}) )));
        ___ViewO.push("\n    <span class=\"clear\">&nbsp;</span>\n    <div class=\"box\">\n        ");
        ___ViewO.push((EJS.Scanner.to_text( format('memory-table', {key: BINARY_STATISTICS. key, memory: binary}) )));
        ___ViewO.push("\n    </div>\n\n<div class=\"memory-info\">\n  Last updated: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_date(new Date()) )));
        ___ViewO.push("</b>.<br/>\n  Total referenced binaries at last update: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(total_out[0]) )));
        ___ViewO.push("</b>\n  <span class=\"help\" id=\"binary-use\"></span>\n</div>\n\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["bindings"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push((EJS.Scanner.to_text( maybe_truncate(bindings) )));
        ___ViewO.push("\n");
         if (bindings.length > 0) { 
        ___ViewO.push("\n    <table class=\"list updatable\">\n      <thead>\n        <tr>\n");
         if (mode == 'exchange_source') { 
        ___ViewO.push("\n          <th>To</th>\n");
         } else { 
        ___ViewO.push("\n          <th>From</th>\n");
         } 
        ___ViewO.push("\n          <th>Routing key</th>\n          <th>Arguments</th>\n          <th></th>\n        </tr>\n      </thead>\n      <tbody>\n        ");
        
           for (var i = 0; i < bindings.length; i++) {
               var binding = bindings[i];
        
        ___ViewO.push("\n           <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n");
         if (binding.source == '') { 
        ___ViewO.push("\n             <td colspan=\"4\">\n               (Default exchange binding)\n             </td>\n");
         } else { 
        ___ViewO.push("\n");
         if (mode == 'queue' || mode == 'exchange_destination') { 
        ___ViewO.push("\n             <td>\n               <span class=\"exchange\">\n                 ");
        ___ViewO.push((EJS.Scanner.to_text( link_exchange(binding.vhost, binding.source) )));
        ___ViewO.push("\n               </span>\n             </td>\n");
         } else if (binding.destination_type == 'exchange') { 
        ___ViewO.push("\n             <td>\n               <span class=\"exchange\" title=\"Exchange\">\n                 ");
        ___ViewO.push((EJS.Scanner.to_text( link_exchange(binding.vhost, binding.destination) )));
        ___ViewO.push("\n               </span>\n             </td>\n");
         } else { 
        ___ViewO.push("\n             <td>\n               <span class=\"queue\" title=\"Queue\">\n                 ");
        ___ViewO.push((EJS.Scanner.to_text( link_queue(binding.vhost, binding.destination) )));
        ___ViewO.push("\n               </span>\n             </td>\n");
         } 
        ___ViewO.push("\n             <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(binding.routing_key) )));
        ___ViewO.push("</td>\n             <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_table_short(binding.arguments) )));
        ___ViewO.push("</td>\n             <td class=\"c\">\n               <form action=\"#/bindings\" method=\"delete\" class=\"confirm\">\n                 <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(binding.vhost) )));
        ___ViewO.push("\"/>\n                 <input type=\"hidden\" name=\"source\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_exchange_url(binding.source) )));
        ___ViewO.push("\"/>\n                 <input type=\"hidden\" name=\"destination\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(binding.destination) )));
        ___ViewO.push("\"/>\n                 <input type=\"hidden\" name=\"destination_type\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( binding.destination_type.substring(0, 1) )));
        ___ViewO.push("\"/>\n                 <input type=\"hidden\" name=\"properties_key\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(binding.properties_key) )));
        ___ViewO.push("\"/>\n                 <input type=\"submit\" value=\"Unbind\"/>\n               </form>\n             </td>\n           ");
         } 
        ___ViewO.push("\n           </tr>\n           ");
         } 
        ___ViewO.push("\n      </tbody>\n    </table>\n\n");
         } else { 
        ___ViewO.push("\n  <p>... no bindings ...</p>\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["channel"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Channel: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_escape_html(channel.name) )));
        ___ViewO.push("</b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_maybe_vhost(channel.vhost) )));
        ___ViewO.push("</h1>\n\n<div class=\"section\">\n<h2>Overview</h2>\n<div class=\"hider updatable\">\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( message_rates('msg-rates-ch', channel.message_stats) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n\n<h3>Details</h3>\n<table class=\"facts facts-l\">\n  <tr>\n    <th>Connection</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_conn(channel.connection_details.name) )));
        ___ViewO.push("</td>\n  </tr>\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n  <tr>\n    <th>Node</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(channel.node) )));
        ___ViewO.push("</td>\n  </tr>\n");
         } 
        ___ViewO.push("\n  <tr>\n    <th>Username</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(channel.user) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Mode <span class=\"help\" id=\"channel-mode\"></span></th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_channel_mode(channel) )));
        ___ViewO.push("</td>\n  </tr>\n</table>\n\n<table class=\"facts facts-l\">\n  <tr>\n    <th>State</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_object_state(channel) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Prefetch count</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( channel.prefetch_count )));
        ___ViewO.push("</td>\n  </tr>\n</table>\n\n<table class=\"facts\">\n  <tr>\n    <th>Messages unacknowledged</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( channel.messages_unacknowledged )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Messages unconfirmed</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( channel.messages_unconfirmed )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Messages uncommitted</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( channel.messages_uncommitted )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Acks uncommitted</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( channel.acks_uncommitted )));
        ___ViewO.push("</td>\n  </tr>\n</table>\n\n<table class=\"facts\">\n  <tr>\n    <th>Pending Raft commands</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( channel.pending_raft_commands )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Cached segments</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( channel.cached_segments )));
        ___ViewO.push("</td>\n  </tr>\n</table>\n\n</div>\n</div>\n\n");
         if(!disable_stats) { 
        ___ViewO.push("\n<div class=\"section\">\n  <h2 class=\"updatable\" >Consumers (");
        ___ViewO.push((EJS.Scanner.to_text((channel.consumer_details.length))));
        ___ViewO.push(") </h2>\n  <div class=\"hider updatable\">\n");
        ___ViewO.push((EJS.Scanner.to_text( format('consumers', {'mode': 'channel', 'consumers': channel.consumer_details}) )));
        ___ViewO.push("\n  </div>\n</div>\n");
         } 
        ___ViewO.push("\n\n");
         if (rates_mode == 'detailed') { 
        ___ViewO.push("\n<div class=\"section\">\n<h2>Message rates breakdown</h2>\n<div class=\"hider updatable\">\n<table class=\"two-col-layout\">\n  <tr>\n    <td>\n      ");
        ___ViewO.push((EJS.Scanner.to_text( format('msg-detail-publishes',
                 {'mode':   'channel',
                  'object': channel.publishes,
                  'label':  'Publishes'}) )));
        ___ViewO.push("\n    </td>\n    <td>\n      ");
        ___ViewO.push((EJS.Scanner.to_text( format('msg-detail-deliveries',
                 {'mode':   'channel',
                  'object': channel.deliveries}) )));
        ___ViewO.push("\n    </td>\n  </tr>\n</table>\n</div>\n</div>\n");
         } 
        ___ViewO.push("\n\n");
         if(channel.reductions || channel.garbage_collection) { 
        ___ViewO.push("\n<div class=\"section-hidden\">\n<h2>Runtime Metrics (Advanced)</h2>\n <div class=\"hider updatable\">\n ");
        ___ViewO.push((EJS.Scanner.to_text( data_reductions('reductions-rates-conn', channel) )));
        ___ViewO.push("\n <table class=\"facts\">\n    ");
         if (channel.garbage_collection.min_bin_vheap_size) { 
        ___ViewO.push("\n        <tr>\n        <th>Minimum binary virtual heap size in words (min_bin_vheap_size)</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( channel.garbage_collection.min_bin_vheap_size )));
        ___ViewO.push("</td>\n        </tr>\n    ");
         } 
        ___ViewO.push("\n\n    ");
         if (channel.garbage_collection.min_heap_size) { 
        ___ViewO.push("\n        <tr>\n        <th>Minimum heap size in words (min_heap_size)</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( channel.garbage_collection.min_heap_size )));
        ___ViewO.push("</td>\n        </tr>\n    ");
         } 
        ___ViewO.push("\n\n    ");
         if (channel.garbage_collection.fullsweep_after) { 
        ___ViewO.push("\n        <tr>\n        <th>Maximum generational collections before fullsweep (fullsweep_after)</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( channel.garbage_collection.fullsweep_after )));
        ___ViewO.push("</td>\n        </tr>\n    ");
         } 
        ___ViewO.push("\n\n    ");
         if (channel.garbage_collection.minor_gcs) { 
        ___ViewO.push("\n        <tr>\n        <th>Number of minor GCs (minor_gcs)</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( channel.garbage_collection.minor_gcs )));
        ___ViewO.push("</td>\n        </tr>\n    ");
         } 
        ___ViewO.push("\n </table>\n </div>\n</div>\n\n");
         } 
        ___ViewO.push("\n\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["channels-list"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
         if (channels.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n <thead>\n  <tr>\n");
         if (mode == 'standalone') { 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('channels', 'Overview', [true, vhosts_interesting, nodes_interesting]) )));
        ___ViewO.push("\n");
         } else { 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('channels', 'Overview', [true]) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('channels', 'Details', []) )));
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('channels', 'Transactions', []) )));
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('channels', 'Message rates', []) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n    <th class=\"plus-minus\"><span class=\"popup-options-link\" title=\"Click to change columns\" type=\"columns\" for=\"channels\">+/-</span></th>\n  </tr>\n  <tr>\n");
         if (mode == 'standalone') { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Channel',         'name') )));
        ___ViewO.push("</th>\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Node',            'node') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (vhosts_interesting) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Virtual host',    'vhost') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'user')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('User name',       'user') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'mode')) { 
        ___ViewO.push("\n    <th>Mode <span class=\"help\" id=\"channel-mode\"></span></th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'state')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('State',           'state') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'msgs-unconfirmed')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Unconfirmed',     'messages_unconfirmed') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'consumer-count')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Consumer count', 'consumer_count') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'prefetch')) { 
        ___ViewO.push("\n    <th>Prefetch <span class=\"help\" id=\"channel-prefetch\"></span></th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'msgs-unacked')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Unacked',         'messages_unacknowledged') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'msgs-uncommitted')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Uncommitted msgs', 'messages_uncommitted') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'acks-uncommitted')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Uncommitted acks', 'acks_uncommitted') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-publish')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('publish', 'message_stats.publish_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-confirm')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('confirm', 'message_stats.confirm_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-unroutable-drop')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('unroutable (drop)', 'message_stats.drop_unroutable_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-unroutable-return')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('unroutable (return)', 'message_stats.return_unroutable_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-deliver')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('deliver / get', 'message_stats.deliver_get_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-redeliver')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('redelivered', 'message_stats.redeliver_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-ack')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('ack', 'message_stats.ack_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } else { 
        ___ViewO.push("\n<!-- TODO make sortable after bug 23401 -->\n    <th>Channel</th>\n");
         if (show_column('channels', 'user')) { 
        ___ViewO.push("\n    <th>User name</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'mode')) { 
        ___ViewO.push("\n    <th>Mode <span class=\"help\" id=\"channel-mode\"></span></th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'state')) { 
        ___ViewO.push("\n    <th>State</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'msgs-unconfirmed')) { 
        ___ViewO.push("\n    <th>Unconfirmed</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'consumer-count')) { 
        ___ViewO.push("\n    <th>Consumer count</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'prefetch')) { 
        ___ViewO.push("\n    <th>Prefetch <span class=\"help\" id=\"channel-prefetch\"></span></th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'msgs-unacked')) { 
        ___ViewO.push("\n    <th>Unacked</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'msgs-uncommitted')) { 
        ___ViewO.push("\n    <th>Uncommitted msgs</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'acks-uncommitted')) { 
        ___ViewO.push("\n    <th>Uncommitted acks</th>\n");
         } 
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-publish')) { 
        ___ViewO.push("\n    <th>publish</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-confirm')) { 
        ___ViewO.push("\n    <th>confirm</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-unroutable-drop')) { 
        ___ViewO.push("\n    <th>unroutable (drop)</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-unroutable-return')) { 
        ___ViewO.push("\n    <th>unroutable (return)</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-deliver')) { 
        ___ViewO.push("\n    <th>deliver / get</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-redeliver')) { 
        ___ViewO.push("\n    <th>redelivered</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-ack')) { 
        ___ViewO.push("\n    <th>ack</th>\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n  </tr>\n </thead>\n <tbody>\n");
        
  for (var i = 0; i < channels.length; i++) {
    var channel = channels[i];
        ___ViewO.push("\n  <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n    <td>\n      ");
        ___ViewO.push((EJS.Scanner.to_text( link_channel(channel.name) )));
        ___ViewO.push("\n    </td>\n");
         if (mode == 'standalone' && nodes_interesting) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(channel.node) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (mode == 'standalone' && vhosts_interesting) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(channel.vhost) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'user')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(channel.user) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'mode')) { 
        ___ViewO.push("\n    <td class=\"c\">\n      ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_channel_mode(channel) )));
        ___ViewO.push("\n    </td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'state')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_object_state(channel) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'msgs-unconfirmed')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( channel.messages_unconfirmed )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'consumer-count')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( channel.consumer_count )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'prefetch')) { 
        ___ViewO.push("\n    <td class=\"c\">\n      ");
         if (channel.prefetch_count != 0) { 
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( channel.prefetch_count )));
        ___ViewO.push("<br/>\n      ");
         } 
        ___ViewO.push("\n    </td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'msgs-unacked')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( channel.messages_unacknowledged )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'msgs-uncommitted')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( channel.messages_uncommitted )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'acks-uncommitted')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( channel.acks_uncommitted )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-publish')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(channel.message_stats, 'publish') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-confirm')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(channel.message_stats, 'confirm') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-unroutable-drop')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(channel.message_stats, 'drop_unroutable') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-unroutable-return')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(channel.message_stats, 'return_unroutable') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-deliver')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(channel.message_stats, 'deliver_get') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-redeliver')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(channel.message_stats, 'redeliver') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('channels', 'rate-ack')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(channel.message_stats, 'ack') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n  </tr>\n  ");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no channels ...</p>\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["channels"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Channels</h1>\n<div class=\"section\">\n ");
        ___ViewO.push((EJS.Scanner.to_text( paginate_ui(channels, 'channels') )));
        ___ViewO.push("\n</div> \n<div class=\"updatable\">\n  ");
        ___ViewO.push((EJS.Scanner.to_text( format('channels-list', {'channels': channels.items, 'mode': 'standalone'}) )));
        ___ViewO.push("\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["classic-queue-arguments"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("                  <span class=\"argument-link\" field=\"arguments\" key=\"x-expires\" type=\"number\">Auto expire</span> <span class=\"help\" id=\"queue-expires\"></span> |\n                  <span class=\"argument-link\" field=\"arguments\" key=\"x-message-ttl\" type=\"number\">Message TTL</span> <span class=\"help\" id=\"queue-message-ttl\"></span> |\n                  <span class=\"argument-link\" field=\"arguments\" key=\"x-overflow\" type=\"string\">Overflow behaviour</span> <span class=\"help\" id=\"queue-overflow\"></span><br/>\n                  <span class=\"argument-link\" field=\"arguments\" key=\"x-single-active-consumer\" type=\"boolean\">Single active consumer</span> <span class=\"help\" id=\"queue-single-active-consumer\"></span> |\n                  <span class=\"argument-link\" field=\"arguments\" key=\"x-dead-letter-exchange\" type=\"string\">Dead letter exchange</span> <span class=\"help\" id=\"queue-dead-letter-exchange\"></span> |\n                  <span class=\"argument-link\" field=\"arguments\" key=\"x-dead-letter-routing-key\" type=\"string\">Dead letter routing key</span> <span class=\"help\" id=\"queue-dead-letter-routing-key\"></span><br/>\n                  <span class=\"argument-link\" field=\"arguments\" key=\"x-max-length\" type=\"number\">Max length</span> <span class=\"help\" id=\"queue-max-length\"></span> |\n                  <span class=\"argument-link\" field=\"arguments\" key=\"x-max-length-bytes\" type=\"number\">Max length bytes</span> <span class=\"help\" id=\"queue-max-length-bytes\"></span>\n                | <span class=\"argument-link\" field=\"arguments\" key=\"x-max-priority\" type=\"number\">Maximum priority</span> <span class=\"help\" id=\"queue-max-priority\"></span>\n                  | <span class=\"argument-link\" field=\"arguments\" key=\"x-queue-leader-locator\" type=\"string\">Leader locator</span><span class=\"help\" id=\"queue-leader-locator\"></span>");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["classic-queue-get-message"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<div class=\"section-hidden\">\n  <h2>Get messages</h2>\n  <div class=\"hider\">\n    <p>\n      Warning: getting messages from a queue is a destructive action.\n      <span class=\"help\" id=\"message-get-requeue\"></span>\n    </p>\n    <form action=\"#/queues/get\" method=\"post\">\n      <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.vhost) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.name) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"truncate\" value=\"50000\"/>\n      <table class=\"form\">\n        <tr>\n          <th><label>Ack Mode:</label></th>\n          <td>\n            <select name=\"ackmode\">\n                <option value=\"ack_requeue_true\" selected>Nack message requeue true</option>\n                <option value=\"ack_requeue_false\">Automatic ack</option>\n                <option value=\"reject_requeue_true\">Reject requeue true</option>\n                <option value=\"reject_requeue_false\">Reject requeue false</option>\n            </select>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Encoding:</label></th>\n          <td>\n            <select name=\"encoding\">\n              <option value=\"auto\">Auto string / base64</option>\n              <option value=\"base64\">base64</option>\n            </select>\n            <span class=\"help\" id=\"string-base64\"></span>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Messages:</label></th>\n          <td><input type=\"text\" name=\"count\" value=\"1\"/></td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Get Message(s)\" />\n    </form>\n    <div id=\"msg-wrapper\"></div>\n  </div>\n</div>");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["classic-queue-node-details"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("      <tr>\n        <th>Node</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(queue.node) )));
        ___ViewO.push("</td>\n      </tr>");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["classic-queue-operator-policy-arguments"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<tr>\n  <td>Queues [Classic]</td>\n  <td>\n    <span class=\"argument-link\" field=\"definitionop\" key=\"expires\" type=\"number\">Auto expire</span> |\n    <span class=\"argument-link\" field=\"definitionop\" key=\"max-length\" type=\"number\">Max length</span> |\n    <span class=\"argument-link\" field=\"definitionop\" key=\"max-length-bytes\" type=\"number\">Max length bytes</span> |\n    <span class=\"argument-link\" field=\"definitionop\" key=\"message-ttl\" type=\"number\">Message TTL</span> |\n    <span class=\"help\" id=\"queue-message-ttl\"></span> |\n    <span class=\"argument-link\" field=\"definitionop\" key=\"overflow\" type=\"string\">Length limit overflow behaviour</span> <span class=\"help\" id=\"queue-overflow\"></span> </br>\n  </td>\n</tr>");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["classic-queue-stats"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("    <table class=\"facts facts-l\">\n      <tr>\n        <th>State</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_object_state(queue) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         if(queue.consumers) { 
        ___ViewO.push("\n      <tr>\n        <th>Consumers</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.consumers) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         } else if(queue.hasOwnProperty('consumer_details')) { 
        ___ViewO.push("\n      <tr>\n        <th>Consumers</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.consumer_details.length) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         } 
        ___ViewO.push("\n      <tr>\n        <th>Consumer capacity <span class=\"help\" id=\"queue-consumer-capacity\"></th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_percent(queue.consumer_capacity) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         if(queue.hasOwnProperty('publishers')) { 
        ___ViewO.push("\n      <tr>\n        <th>Publishers</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.publishers) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         } 
        ___ViewO.push("\n    </table>\n\n    <table class=\"facts\">\n      <tr>\n        <td></td>\n        <th class=\"horizontal\">Total</th>\n        <th class=\"horizontal\">Ready</th>\n        <th class=\"horizontal\">Unacked</th>\n        <th class=\"horizontal\">In memory</th>\n        <th class=\"horizontal\">Persistent</th>\n      </tr>\n      <tr>\n        <th>\n          Messages\n          <span class=\"help\" id=\"queue-messages\"></span>\n        </th>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_ready) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_unacknowledged) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_ram) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_persistent) )));
        ___ViewO.push("\n        </td>\n      </tr>\n      <tr>\n        <th>\n          Message body bytes\n          <span class=\"help\" id=\"queue-message-body-bytes\"></span>\n        </th>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes_ready) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes_unacknowledged) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes_ram) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes_persistent) )));
        ___ViewO.push("\n        </td>\n      </tr>\n      <tr>\n        <th>\n          Process memory\n          <span class=\"help\" id=\"queue-process-memory\"></span>\n        </th>\n        <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.memory) )));
        ___ViewO.push("</td>\n      </tr>\n    </table>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["classic-queue-user-policy-arguments"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["cluster-name"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Cluster name: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(cluster_name.name) )));
        ___ViewO.push("</b></h1>\n\n<p>\n  The cluster name can be used by clients to identify clusters over\n  AMQP connections, and is used by the shovel and federation plugins\n  to identify which clusters a message has been routed through.\n</p>\n<p>\n  Note that the cluster name is announced to clients in the AMQP\n  server properties; i.e. before authentication has taken\n  place. Therefore it should not be considered secret.\n</p>\n<p>\n  The cluster name is generated by default from the name of the first\n  node in the cluster, but can be changed.\n</p>\n\n<div class=\"section-hidden\">\n  <h2>Change name</h2>\n  <div class=\"hider\">\n    <form action=\"#/cluster-name\" method=\"put\">\n      <table class=\"form\">\n        <tr>\n          <th><label>Name:</label></th>\n          <td><input type=\"text\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(cluster_name.name) )));
        ___ViewO.push("\"/><span class=\"mand\">*</span></td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Change name\"/>\n    </form>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["columns-options"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        
   var mode = span.attr('for');
        ___ViewO.push("\n\n<form action=\"#/column-options\" method=\"put\" class=\"auto-submit\">\n  <input type=\"hidden\" name=\"mode\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( mode )));
        ___ViewO.push("\"/>\n  <table class=\"form\" width=\"100%\">\n    <tr>\n      <td colspan=\"2\">\n        <h3>Columns for this table</h3>\n      </td>\n    </tr>\n");
         for (var group in COLUMNS[mode]) {
   var options = COLUMNS[mode][group];  
        ___ViewO.push("\n    <tr>\n      <th><label>");
        ___ViewO.push((EJS.Scanner.to_text( group )));
        ___ViewO.push(":</label></th>\n      <td>\n      ");
         for (var i = 0; i < options.length; i++) {
           if (mode === 'connections' && disable_stats &&
               (options[i][0] === 'from_client' || options[i][0] === 'to_client')) {
             continue;
           }
      
        ___ViewO.push("\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_checkbox(mode + '-' + options[i][0], options[i][1], get_pref('column-' + mode + '-' + options[i][0]) == 'true') )));
        ___ViewO.push("\n      ");
         } 
        ___ViewO.push("\n      </td>\n");
         } 
        ___ViewO.push("\n    </tr>\n  </table>\n</form>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["connection"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h2>Connection ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.name) )));
        ___ViewO.push(" ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_maybe_vhost(connection.vhost) )));
        ___ViewO.push("</h1>\n\n<div class=\"section\" id=\"connection-overview-section\">\n<h2>Overview</h2>\n<div class=\"hider updatable\">\n");
         if (!disable_stats) { 
        ___ViewO.push("\n  ");
        ___ViewO.push((EJS.Scanner.to_text( data_rates('data-rates-conn', connection, 'Data rates') )));
        ___ViewO.push("\n");
         } 
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
        ___ViewO.push("\n\n");
         if (connection.container_id) { 
        ___ViewO.push("\n<tr>\n  <th>Container ID\n    <span class=\"help\" id=\"container-id\"></span>\n  </th>\n  <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.container_id) )));
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
        ___ViewO.push("\n<tr>\n <th>SASL auth mechanism</th>\n <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.auth_mechanism) )));
        ___ViewO.push("</td>\n</tr>\n");
         } 
        ___ViewO.push("\n</table>\n\n<table class=\"facts\">\n");
         if (connection.state) { 
        ___ViewO.push("\n<tr>\n <th>State</th>\n <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_object_state(connection) )));
        ___ViewO.push("</td>\n</tr>\n");
         } 
        ___ViewO.push("\n<tr>\n <th>Heartbeat</th>\n <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_time(connection.timeout, 's') )));
        ___ViewO.push("</td>\n</tr>\n<tr>\n <th>Frame max</th>\n <td>");
        ___ViewO.push((EJS.Scanner.to_text( connection.frame_max )));
        ___ViewO.push(" bytes</td>\n</tr>\n<tr>\n <th>Channel limit</th>\n <td>");
        ___ViewO.push((EJS.Scanner.to_text( connection.channel_max )));
        ___ViewO.push(" channels</td>\n</tr>\n</table>\n\n</div>\n</div>\n\n");
         if (!disable_stats) { 
        ___ViewO.push("\n");
         if (connection.protocol === 'AMQP 1-0' ||
       connection.protocol === 'Web AMQP 1-0') { 
        ___ViewO.push("\n\n<div class=\"section\" id=\"connection-sessions-section\">\n  <h2 class=\"updatable\" >Sessions (");
        ___ViewO.push((EJS.Scanner.to_text((sessions.length))));
        ___ViewO.push(")</h2>\n  <div class=\"hider updatable\">\n    ");
        ___ViewO.push((EJS.Scanner.to_text( format('sessions-list', {'sessions': sessions}) )));
        ___ViewO.push("\n  </div>\n</div>\n\n");
         } else { 
        ___ViewO.push("\n\n<div class=\"section\" id=\"connection-channels-section\">\n  <h2 class=\"updatable\" >Channels (");
        ___ViewO.push((EJS.Scanner.to_text((channels.length))));
        ___ViewO.push(") </h2>\n  <div class=\"hider updatable\">\n    ");
        ___ViewO.push((EJS.Scanner.to_text( format('channels-list', {'channels': channels, 'mode': 'connection'}) )));
        ___ViewO.push("\n  </div>\n</div>\n\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n\n");
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
        ___ViewO.push("\n\n");
         if (properties_size(connection.client_properties) > 0) { 
        ___ViewO.push("\n<div class=\"section-hidden\" id=\"connection-client-properies-section\">\n<h2>Client properties</h2>\n<div class=\"hider updatable\">\n");
        ___ViewO.push((EJS.Scanner.to_text( fmt_table_long(connection.client_properties) )));
        ___ViewO.push("\n</div>\n</div>\n");
         } 
        ___ViewO.push("\n\n");
         if (!disable_stats && (connection.reductions || connection.garbage_collection)) { 
        ___ViewO.push("\n<div class=\"section-hidden\" id=\"connection-runtime-metrics-section\">\n<h2>Runtime Metrics (Advanced)</h2>\n <div class=\"hider updatable\">\n ");
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
        ___ViewO.push("\n\n<div class=\"section-hidden\" id=\"connection-close-section\">\n  <h2>Close this connection</h2>\n  <div class=\"hider\">\n    <form action=\"#/connections\" method=\"delete\" class=\"confirm\">\n      <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.name) )));
        ___ViewO.push("\"/>\n      <table class=\"form\">\n        <tr>\n          <th><label>Reason:</label></th>\n          <td>\n            <input type=\"text\" name=\"reason\" value=\"Closed via management plugin\" class=\"wide\"/>\n          </td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Force Close\"/>\n    </form>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["connections"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Connections</h1>\n<div class=\"section\" id=\"connections-paging-section\">\n ");
        ___ViewO.push((EJS.Scanner.to_text( paginate_ui(connections, 'connections') )));
        ___ViewO.push("\n</div>\n<div class=\"updatable\" id=\"connections-table-section\">\n");
         if (connections.items.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n <thead>\n  <tr>\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('connections', 'Overview', [vhosts_interesting, nodes_interesting, true]) )));
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('connections', 'Details', []) )));
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('connections', 'Network', []) )));
        ___ViewO.push("\n    <th class=\"plus-minus\"><span class=\"popup-options-link\" title=\"Click to change columns\" type=\"columns\" for=\"connections\">+/-</span></th>\n  </tr>\n  <tr>\n");
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
         if (show_column('connections',      'container_id')) { 
        ___ViewO.push("\n    <th>Container ID <span class=\"help\" id=\"container-id\"></span></th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'user')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('User name',      'user') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'state')  && !disable_stats) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('State',          'state') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'ssl')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('SSL / TLS',      'ssl') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'ssl_info')) { 
        ___ViewO.push("\n    <th>SSL Details</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'protocol')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Protocol',       'protocol') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'channels')  && !disable_stats) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Channels',       'channels') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'channel_max')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Channel max',    'channel_max') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'frame_max')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Frame max',      'frame_max') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'auth_mechanism')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('SASL auth mechanism', 'auth_mechanism') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'client')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Client',         'properties') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'from_client') && !disable_stats) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('From client',    'recv_oct_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'to_client') && !disable_stats) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('To client',      'send_oct_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'heartbeat')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Heartbeat',      'timeout') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections',      'connected_at')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Connected at',   'connected_at') )));
        ___ViewO.push("</th>\n");
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
        ___ViewO.push((EJS.Scanner.to_text( link_conn(connection.name) )));
        ___ViewO.push("\n      ");
         if (connection.client_properties.connection_name) { 
        ___ViewO.push("\n            <sub>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(short_conn(connection.client_properties.connection_name)) )));
        ___ViewO.push("</sub>\n      ");
         } 
        ___ViewO.push("\n    </td>\n");
         } else { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_conn(connection.name) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(connection.node) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'container_id')) { 
        ___ViewO.push("\n    <td class=\"c\">\n    ");
         if (connection.container_id) { 
        ___ViewO.push("\n      ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.container_id) )));
        ___ViewO.push("\n    ");
         } 
        ___ViewO.push("\n    </td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'user')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.user) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'state') && !disable_stats) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_object_state(connection) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'ssl')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(connection.ssl, '') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'ssl_info')) { 
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
         if (show_column('connections', 'protocol')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.protocol) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'channels')  && !disable_stats) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.channels, '') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'channel_max')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.channel_max, '') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'frame_max')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.frame_max, '') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'auth_mechanism')) { 
        ___ViewO.push("\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(connection.auth_mechanism, '') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'client')) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_client_name(connection.client_properties) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'from_client') && !disable_stats) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate_bytes(connection, 'recv_oct') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'to_client') && !disable_stats) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate_bytes(connection, 'send_oct') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'heartbeat')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_time(connection.timeout, 's') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('connections', 'connected_at')) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_timestamp_mini(connection.connected_at) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n  </tr>\n  ");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no connections ...</p>\n");
         } 
        ___ViewO.push("\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["consumers"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
         if (consumers.length > 0) { 
        ___ViewO.push("\n    <table class=\"list\" id=\"consumers\">\n      <thead>\n        <tr>\n");
         if (mode == 'queue') { 
        ___ViewO.push("\n          <th>Owner <span class=\"help\" id=\"consumer-owner\"></th>\n          <th>Consumer tag</th>\n");
         } else { 
        ___ViewO.push("\n          <th>Consumer tag</th>\n          <th>Queue</th>\n");
         } 
        ___ViewO.push("\n          <th>Ack required</th>\n          <th>Exclusive</th>\n          <th>Prefetch count</th>\n          <th>Active <span class=\"help\" id=\"consumer-active\"></span></th>\n          <th>Activity status</th>\n          <th>Consumer Timeout</th>\n          <th>Arguments</th>\n        </tr>\n      </thead>\n");
        
  for (var i = 0; i < consumers.length; i++) {
    var consumer = consumers[i];
        ___ViewO.push("\n      <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i) )));
        ___ViewO.push(">\n");
         if (mode == 'queue') { 
        ___ViewO.push("\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_consumer_owner(consumer) )));
        ___ViewO.push("</td>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(consumer.consumer_tag) )));
        ___ViewO.push("</td>\n");
         } else { 
        ___ViewO.push("\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(consumer.consumer_tag) )));
        ___ViewO.push("</td>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_queue(consumer.queue.vhost, consumer.queue.name) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(consumer.ack_required) )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(consumer.exclusive) )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( consumer.prefetch_count )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(consumer.active) )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_activity_status(consumer.activity_status) )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( consumer.consumer_timeout )));
        ___ViewO.push("</td>\n        <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_table_short(consumer.arguments) )));
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

COMPILED_TEMPLATES["deprecated-features"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Deprecated Features</h1>\n  ");
        
  var used_deprecated_features_names = [];
  for (var i = 0; i < used_deprecated_features.length; i++) {
      used_deprecated_features_names.push(used_deprecated_features[i].name);
  var needs_deprecating = false;
  if (used_deprecated_features.length > 0) {
      needs_deprecating = true;
  }
  }
  if (needs_deprecating) { 
        ___ViewO.push("\n     <p class=\"warning\">\n        Deprecated features are being used. While using deprecated features, upgrading to future minor or major versions of RabbitMQ may not be possible. <a href=\"https://www.rabbitmq.com/feature-flags.html\">[Learn more]</a>\n     </p>\n  ");
         } 
        ___ViewO.push("\n<div class=\"section\">\n  <h2>All Deprecated Features</h2>\n  <div class=\"hider\">\n");
        ___ViewO.push((EJS.Scanner.to_text( filter_ui(deprecated_features) )));
        ___ViewO.push("\n  <div class=\"updatable\">\n");
         if (deprecated_features.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n  <thead>\n    <tr>\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Name', 'name') )));
        ___ViewO.push("</th>\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Deprecation phase', 'deprecation_phase') )));
        ___ViewO.push("</th>\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Current Configuration', 'state') )));
        ___ViewO.push("</th>\n      <th>Description</th>\n    </tr>\n  </thead>\n  <tbody>\n    ");
        
       for (var i = 0; i < deprecated_features.length; i++) {
         var deprecated_feature = deprecated_features[i];
         var in_use = used_deprecated_features_names.includes(deprecated_feature.name);
         if (in_use) {
            state_color = "red";
         }
    
        ___ViewO.push("\n       <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n         <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(deprecated_feature.name) )));
        ___ViewO.push("</td>\n         <td>\n         ");
         if (in_use) { 
        ___ViewO.push("\n         <abbr class=\"status-");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(state_color) )));
        ___ViewO.push("\">In use</abbr>\n         ");
         } 
        ___ViewO.push("\n         ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_deprecation_phase(deprecated_feature.deprecation_phase, DEPRECATION_PHASES) )));
        ___ViewO.push("</td>\n         <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(deprecated_feature.state) )));
        ___ViewO.push("</td>\n         <td>\n         <p>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(deprecated_feature.desc) )));
        ___ViewO.push("</p>\n         ");
         if (deprecated_feature.doc_url) { 
        ___ViewO.push("\n         <p><a href=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(deprecated_feature.doc_url) )));
        ___ViewO.push("\">[Learn more]</a></p>\n         ");
         } 
        ___ViewO.push("\n         </td>\n       </tr>\n    ");
         } 
        ___ViewO.push("\n  </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n    <p>... no deprecated features ...</p>\n");
         } 
        ___ViewO.push("\n  <p>\n  See the <a href=\"https://www.rabbitmq.com/docs/deprecated-features\" target=\"_blank\">Deprecated features documentation</a> for more information.\n  </p>\n  </div>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["exchange"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Exchange: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_exchange(highlight_extra_whitespace(exchange.name)) )));
        ___ViewO.push("</b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_maybe_vhost(exchange.vhost) )));
        ___ViewO.push("</h1>\n\n<div class=\"section\">\n  <h2>Overview</h2>\n  <div class=\"hider updatable\">\n");
         if (!disable_stats) { 
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( message_rates('msg-rates-x', exchange.message_stats) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n    <h3>Details</h3>\n    <table class=\"facts\">\n      <tr>\n        <th>Type</th>\n        <td class=\"l\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_exchange_type(exchange.type) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Features</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_features(exchange) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Policy</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_policy(exchange.vhost, exchange.policy) )));
        ___ViewO.push("</td>\n      </tr>\n    </table>\n  </div>\n</div>\n\n");
         if (!disable_stats) { 
        ___ViewO.push("\n");
         if (rates_mode == 'detailed') { 
        ___ViewO.push("\n<div class=\"section-hidden\">\n<h2>Message rates breakdown</h2>\n<div class=\"hider updatable\">\n<table class=\"two-col-layout\">\n  <tr>\n    <td>\n      ");
        ___ViewO.push((EJS.Scanner.to_text( format('msg-detail-publishes',
                 {'mode':   'exchange-incoming',
                  'object': exchange.incoming,
                  'label':  'Incoming <span class="help" id="exchange-rates-incoming"></span>'}) )));
        ___ViewO.push("\n    </td>\n    <td>\n      ");
        ___ViewO.push((EJS.Scanner.to_text( format('msg-detail-publishes',
                 {'mode':   'exchange-outgoing',
                  'object': exchange.outgoing,
                  'label':  'Outgoing <span class="help" id="exchange-rates-outgoing"></span>'}) )));
        ___ViewO.push("\n    </td>\n  </tr>\n</table>\n</div>\n</div>\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n\n\n<div class=\"section-hidden\">\n  <h2>Bindings</h2>\n  <div class=\"hider\">\n");
         if (exchange.name == "") { 
        ___ViewO.push("\n  <h3>Default exchange</h3>\n  <p>\n    The default exchange is implicitly bound to every queue, with a\n    routing key equal to the queue name. It is not possible to\n    explicitly bind to, or unbind from the default exchange. It also\n    cannot be deleted.\n  </p>\n");
         } else { 
        ___ViewO.push("\n<div class=\"bindings-wrapper\">\n");
         if (bindings_destination.length > 0) { 
        ___ViewO.push("\n  ");
        ___ViewO.push((EJS.Scanner.to_text( format('bindings', {'mode': 'exchange_destination', 'bindings': bindings_destination}) )));
        ___ViewO.push("\n  <p class=\"arrow\">&dArr;</p>\n");
         } 
        ___ViewO.push("\n  <p><span class=\"exchange\">This exchange</span></p>\n  <p class=\"arrow\">&dArr;</p>\n  ");
        ___ViewO.push((EJS.Scanner.to_text( format('bindings', {'mode': 'exchange_source', 'bindings': bindings_source}) )));
        ___ViewO.push("\n</div>\n  ");
        ___ViewO.push((EJS.Scanner.to_text( format('add-binding', {'mode': 'exchange_source', 'parent': exchange}) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n</div>\n</div>\n\n");
         if (!exchange.internal) { 
        ___ViewO.push("\n");
        ___ViewO.push((EJS.Scanner.to_text( format('publish', {'mode': 'exchange', 'exchange': exchange}) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n\n");
         if (exchange.name != "") { 
        ___ViewO.push("\n<div class=\"section-hidden\">\n  <h2>Delete this exchange</h2>\n  <div class=\"hider\">\n    <form action=\"#/exchanges\" method=\"delete\" class=\"confirm\">\n      <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(exchange.vhost) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_exchange_url(exchange.name) )));
        ___ViewO.push("\"/>\n      <input type=\"submit\" value=\"Delete\"/>\n    </form>\n  </div>\n</div>\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["exchanges"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Exchanges</h1>\n<div class=\"section\" id=\"exchanges-paging-section\">\n   ");
        ___ViewO.push((EJS.Scanner.to_text( paginate_ui(exchanges, 'exchanges') )));
        ___ViewO.push("\n</div>\n<div class=\"updatable\" id=\"exchanges-table-section\">\n");
         if (exchanges.items.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n <thead>\n  <tr>\n");
         if (display.vhosts) { 
        ___ViewO.push("\n   <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Virtual host', 'vhost') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n   <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Name',         'name') )));
        ___ViewO.push("</th>\n");
         if (show_column('exchanges', 'type')) { 
        ___ViewO.push("\n   <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Type',         'type') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('exchanges', 'features')) { 
        ___ViewO.push("\n   <th>Features</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('exchanges', 'features_no_policy')) { 
        ___ViewO.push("\n   <th>Features</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('exchanges', 'policy')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Policy','policy') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (!disable_stats) { 
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n");
         if (show_column('exchanges', 'rate-in')) { 
        ___ViewO.push("\n   <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Message rate in',   'message_stats.publish_in_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('exchanges', 'rate-out')) { 
        ___ViewO.push("\n   <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Message rate out',  'message_stats.publish_out_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n    <th class=\"plus-minus\"><span class=\"popup-options-link\" title=\"Click to change columns\" type=\"columns\" for=\"exchanges\">+/-</span></th>\n  </tr>\n </thead>\n <tbody>\n");
        
  for (var i = 0; i < exchanges.items.length; i++) {
    var exchange = exchanges.items[i];
        ___ViewO.push("\n  <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i, exchange.arguments))));
        ___ViewO.push(">\n");
         if (display.vhosts) { 
        ___ViewO.push("\n   <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(exchange.vhost) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n   <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_exchange(exchange.vhost, exchange.name, exchange.arguments) )));
        ___ViewO.push("</td>\n   <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_exchange_type(exchange.type) )));
        ___ViewO.push("</td>\n");
         if (show_column('exchanges', 'features')) { 
        ___ViewO.push("\n   <td class=\"c\">\n     ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_features_short(exchange) )));
        ___ViewO.push("\n     ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_policy_short(exchange) )));
        ___ViewO.push("\n   </td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('exchanges', 'features_no_policy')) { 
        ___ViewO.push("\n   <td class=\"c\">\n     ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_features_short(exchange) )));
        ___ViewO.push("\n   </td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('exchanges', 'policy')) { 
        ___ViewO.push("\n   <td class=\"c\">\n     ");
        ___ViewO.push((EJS.Scanner.to_text( link_policy(exchange.vhost, exchange.policy) )));
        ___ViewO.push("\n   </td>\n");
         } 
        ___ViewO.push("\n");
         if (!disable_stats) { 
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n");
         if (show_column('exchanges', 'rate-in')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(exchange.message_stats, 'publish_in') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('exchanges', 'rate-out')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(exchange.message_stats, 'publish_out') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n  </tr>\n  ");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no exchanges ...</p>\n");
         } 
        ___ViewO.push("\n  </div>\n  </div>\n</div>\n\n");
         if (ac.canAccessVhosts()) { 
        ___ViewO.push("\n<div class=\"section-hidden\" id=\"add-new-exchange\">\n  <h2>Add a new exchange</h2>\n  <div class=\"hider\">\n    <form action=\"#/exchanges\" method=\"put\">\n      <table class=\"form\">\n");
         if (vhosts_interesting) { 
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
        ___ViewO.push("\n        <tr>\n          <th><label>Name:</label></th>\n          <td><input type=\"text\" name=\"name\"/><span class=\"mand\">*</span></td>\n        </tr>\n        <tr>\n          <th><label>Type:</label></th>\n          <td>\n            <select name=\"type\">\n              ");
         for (var i = 0; i < exchange_types.length; i++) {
                   var type = exchange_types[i];
                   if (type.internal_purpose == undefined) { 
        ___ViewO.push("\n              <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(type.name) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(type.name) )));
        ___ViewO.push("</option>\n              ");
           }
                 } 
        ___ViewO.push("\n            </select>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Durability:</label></th>\n          <td>\n            <select name=\"durable\">\n              <option value=\"true\">Durable</option>\n              <option value=\"false\">Transient</option>\n            </select>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Auto delete: <span class=\"help\" id=\"exchange-auto-delete\"></span></label></th>\n          <td>\n            <select name=\"auto_delete\">\n              <option value=\"false\">No</option>\n              <option value=\"true\">Yes</option>\n            </select>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Internal: <span class=\"help\" id=\"exchange-internal\"></span></label></th>\n          <td>\n            <select name=\"internal\">\n              <option value=\"false\">No</option>\n              <option value=\"true\">Yes</option>\n            </select>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Arguments:</label></th>\n          <td>\n            <div class=\"multifield\" id=\"arguments\"></div>\n            <table class=\"argument-links\">\n              <tr>\n                <td>Add</td>\n                <td>\n                  <span class=\"argument-link\" field=\"arguments\" key=\"alternate-exchange\" type=\"string\">Alternate exchange</span>\n                  <span class=\"help\" id=\"exchange-alternate\"></span>\n                </td>\n              </tr>\n            </table>\n          </td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Add exchange\"/>\n    </form>\n  </div>\n  ");
         } 
        ___ViewO.push("\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["feature-flags"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<!--\n    SVG icons on this page comes from:\n    https://www.svgrepo.com/collection/iconcino-interface-icons/\n-->\n<h1>Feature Flags</h1>\n  ");
        
       var nonreq_feature_flags = [];
       for (var i = 0; i < feature_flags.length; i++) {
         if (feature_flags[i].stability == 'required')
           continue;
         nonreq_feature_flags.push(feature_flags[i]);
       }
  
        ___ViewO.push("\n  <div id=\"ff-disabled-stable-warning\" class=\"warning\" style=\"display: none;\">\n      <p>\n      All stable feature flags must be enabled after completing an upgrade.\n      Without enabling all flags, upgrading to future minor or major versions\n      of RabbitMQ may not be possible.\n      <a href=\"https://www.rabbitmq.com/docs/feature-flags\">[Learn more]</a>\n      </p>\n      <button id=\"ff-enable-all-button\">Enable all stable feature flags</button>\n  </div>\n<div class=\"section\" id=\"feature-flags\">\n  <h2>Feature Flags</h2>\n  <div class=\"hider\">\n");
        ___ViewO.push((EJS.Scanner.to_text( filter_ui(nonreq_feature_flags) )));
        ___ViewO.push("\n  <div id=\"ff-table-section\" class=\"updatable\">\n");
         if (nonreq_feature_flags.length > 0) { 
        ___ViewO.push("\n<div id=\"ff-feature-flags-data\" hidden\n     data-feature-flags=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_escape_html0(JSON.stringify(nonreq_feature_flags)) )));
        ___ViewO.push("\"></div>\n\n<style>\n.specificities_icons svg {\n    width: 16px;\n    height: 16px;\n}\n\n#ff-exp-dialog {\n    width: 600px;\n}\n\n#ff-exp-dialog h3 {\n    font-size: 2em;\n    margin-top: 0;\n}\n\n#ff-exp-dialog svg {\n    width: 60px;\n    height: 60px;\n}\n\n#ff-exp-dialog.ff-exp-unsupported #ff-exp-ack-supported {\n    display: none;\n}\n\n#ff-exp-dialog.ff-exp-supported #ff-exp-ack-unsupported {\n    display: none;\n}\n\n#ff-exp-dialog button {\n    display: inline-block;\n    margin-right: 1em;\n}\n\n.ff-name {\n    font-family: monospace;\n}\n</style>\n\n<table class=\"list\">\n  <thead>\n    <tr>\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Name', 'name') )));
        ___ViewO.push("</th>\n      <th class=\"c\">Specificities</th>\n      <th class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('State', 'state') )));
        ___ViewO.push("</th>\n      <th>Description</th>\n    </tr>\n  </thead>\n  <tbody>\n    ");
        
       for (var i = 0; i < nonreq_feature_flags.length; i++) {
         var feature_flag = nonreq_feature_flags[i];
    
        ___ViewO.push("\n       <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n         <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(feature_flag.name) )));
        ___ViewO.push("</td>\n         <td class=\"specificities_icons ff-stability-");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(feature_flag.stability) )));
        ___ViewO.push(" ff-state-");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(feature_flag.state) )));
        ___ViewO.push("\">\n           ");
         if (feature_flag.callbacks.includes('enable')) { 
        ___ViewO.push("\n           <svg width=\"800px\" height=\"800px\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\" class=\"has_migration_icon\">\n               <title>This feature flags has a migration function which might take some time and consume resources.</title>\n               <path d=\"M20.9844 10H17M20.9844 10V6M20.9844 10L17.6569 6.34315C14.5327 3.21895 9.46734 3.21895 6.34315 6.34315C3.21895 9.46734 3.21895 14.5327 6.34315 17.6569C9.46734 20.781 14.5327 20.781 17.6569 17.6569C18.4407 16.873 19.0279 15.9669 19.4184 15M12 9V13L15 14.5\" stroke=\"#000000\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n           </svg>\n           ");
         } 
        ___ViewO.push("\n           ");
         if (feature_flag.stability == 'experimental') { 
        ___ViewO.push("\n           <svg width=\"800px\" height=\"800px\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\" class=\"experimental_icon\">\n               <title>This is an experimental feature flag</title>\n               <path d=\"M10 4V10L5.20285 16.8531C4.27496 18.1786 5.22327 20 6.84131 20H17.1587C18.7767 20 19.725 18.1786 18.7972 16.8531L14 10V4M10 4H14M10 4H8M14 4H16\" stroke=\"#000000\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n           </svg>\n           ");
         } 
        ___ViewO.push("\n           ");
         if (feature_flag.experiment_level == 'unsupported') { 
        ___ViewO.push("\n           <svg width=\"800px\" height=\"800px\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\">\n               <title>This experimental feature flag is not yet supported at this stage and an upgrade path is not guaranteed</title>\n               <path d=\"M12 15H12.01M12 12V9M4.98207 19H19.0179C20.5615 19 21.5233 17.3256 20.7455 15.9923L13.7276 3.96153C12.9558 2.63852 11.0442 2.63852 10.2724 3.96153L3.25452 15.9923C2.47675 17.3256 3.43849 19 4.98207 19Z\" stroke=\"#000000\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n           </svg>\n           ");
         } 
        ___ViewO.push("\n         </td>\n         <td class=\"c ff-stability-");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(feature_flag.stability) )));
        ___ViewO.push(" ff-state-");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(feature_flag.state) )));
        ___ViewO.push("\">\n           <input id=\"ff-checkbox-");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(feature_flag.name) )));
        ___ViewO.push("\" type=\"checkbox\" class=\"toggle\"\n                  data-flag-name=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(feature_flag.name) )));
        ___ViewO.push("\"\n                  ");
         if (feature_flag.state == 'enabled') { 
        ___ViewO.push("\n                  checked disabled\n                  ");
         } 
        ___ViewO.push("\n                  ");
         if (feature_flag.state == 'state_changing') { 
        ___ViewO.push("\n                  disabled\n                  ");
         } 
        ___ViewO.push("\n                  />\n           <label for=\"ff-checkbox-");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(feature_flag.name) )));
        ___ViewO.push("\" class=\"toggle\"/>\n         </td>\n         <td>\n         <p>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(feature_flag.desc) )));
        ___ViewO.push("</p>\n         ");
         if (feature_flag.doc_url) { 
        ___ViewO.push("\n         <p><a href=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(feature_flag.doc_url) )));
        ___ViewO.push("\">[Learn more]</a></p>\n         ");
         } 
        ___ViewO.push("\n         </td>\n       </tr>\n    ");
         } 
        ___ViewO.push("\n  </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n    <p>... no feature_flags ...</p>\n");
         } 
        ___ViewO.push("\n  </div>\n  </div>\n</div>\n<dialog id=\"ff-exp-dialog\">\n    <svg width=\"800px\" height=\"800px\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\">\n        <path d=\"M12 15H12.01M12 12V9M4.98207 19H19.0179C20.5615 19 21.5233 17.3256 20.7455 15.9923L13.7276 3.96153C12.9558 2.63852 11.0442 2.63852 10.2724 3.96153L3.25452 15.9923C2.47675 17.3256 3.43849 19 4.98207 19Z\" stroke=\"#000000\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n    </svg>\n    <h3>Enabling an experimental feature flag</h3>\n    <p>\n    <strong>The <code class=\"ff-name\"></code> feature flag is experimental</strong>.\n    This means the functionality behind it is still a work in progress. Here\n    are a few important things to keep in mind:\n    </p>\n    <ol>\n    <li id=\"ff-exp-ack-supported\">\n    <p>\n    Before enabling it, make sure to <strong>try it in a test environment\n    first</strong> before enabling it in production.\n    </p>\n    <p>\n    The feature flag is supported even though it is still experimental.\n    Therefore, upgrades to a later version of RabbitMQ with this feature flag\n    enabled are supported.\n    </p>\n    <p>\n    <input id=\"ff-exp-ack-supported-checkbox\" type=\"checkbox\"/>\n    <label for=\"ff-exp-ack-supported-checkbox\">I understand that this feature is experimental and should be tested first.</label>\n    </p>\n    </li>\n    <li id=\"ff-exp-ack-unsupported\">\n    <p>\n    This development of this feature is at an early stage. Support is not\n    provided and enabling it in production is not recommended.\n    </p>\n    <p>\n    Once it is enabled, upgrades to a future version of RabbitMQ is not\n    guaranteed! If there is no upgrade path, you will have to use a\n    <a href=\"https://www.rabbitmq.com/docs/blue-green-upgrade\" target=\"_blank\">blue-green migration</a>\n    to upgrade RabbitMQ.\n    </p>\n    <p>\n    <input id=\"ff-exp-ack-unsupported-checkbox1\" type=\"checkbox\"/>\n    <label for=\"ff-exp-ack-unsupported-checkbox1\">I understand that <strong>support is not provided</strong>.</label>\n    </p>\n    <p>\n    <input id=\"ff-exp-ack-unsupported-checkbox2\" type=\"checkbox\"/>\n    <label for=\"ff-exp-ack-unsupported-checkbox2\">I understand that this there is <strong>no guaranteed upgrade path</strong>.</label>\n    </p>\n    </li>\n    <li>\n    If you enable it,\n    <a href=\"https://github.com/rabbitmq/rabbitmq-server/discussions\" target=\"_blank\">please give feedback</a>,\n    this will help the RabbitMQ team polish it and make it stable as soon as\n    possible.\n    </li>\n    </ol>\n    <button id=\"ff-exp-confirm\">Enable <span class=\"ff-name\"></span></button>\n    <button id=\"ff-exp-cancel\">Cancel</button>\n</dialog>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["layout"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<div id=\"header\">\n  <ul id=\"topnav\">\n    <li id=\"interval\">\n      <label for=\"update-every\" id=\"status\"></label>\n      <select id=\"update-every\">\n        ");
         if(settings.disable_stats) { 
        ___ViewO.push("\n         <option value=\"\">Do not refresh</option>\n         <option value=\"5000\">Refresh every 5 seconds</option>\n        ");
         } else { 
        ___ViewO.push("\n         <option value=\"5000\">Refresh every 5 seconds</option>\n        ");
         } 
        ___ViewO.push("\n        <option value=\"10000\">Refresh every 10 seconds</option>\n        <option value=\"30000\">Refresh every 30 seconds</option>\n        ");
         if(!settings.disable_stats) { 
        ___ViewO.push("\n         <option value=\"\">Do not refresh</option>\n        ");
         } 
        ___ViewO.push("\n      </select>\n    </li>\n    <li id=\"vhost\">\n      <label for=\"show-vhost\">Virtual host </label>\n      <select id=\"show-vhost\">\n        <option value=\"\">All</option>\n      </select>\n    </li>\n    <li id=\"logout\">\n      <form action=\"#/logout\" method=\"put\">\n        <input type=\"submit\" value=\"Log out\"/>\n      </form>\n    </li>\n  </ul>\n  <div id=\"logo\">\n    <a href=\"#/\"><img src=\"img/rabbitmqlogo.svg\" alt=\"RabbitMQ logo\" width=\"204\" height=\"37\"/></a>\n    <span id=\"versions\"></span>\n  </div>\n  <br/>\n  <div id=\"warnings\"></div>\n  <div id=\"menu\">\n    <ul id=\"tabs\">\n    </ul>\n  </div>\n</div>\n<div id=\"rhs\"></div>\n<div id=\"main\"></div>\n<div id=\"footer\">\n  <ul>\n    <li><a rel=\"noopener noreferrer\" href=\"api/\" target=\"_blank\">HTTP API</a></li>\n    <li><a rel=\"noopener noreferrer\" href=\"https://www.rabbitmq.com/docs\" target=\"_blank\">Documentation</a></li>\n    <li><a rel=\"noopener noreferrer\" href=\"https://www.rabbitmq.com/tutorials\" target=\"_blank\">Tutorials</a></li>\n    <li><a rel=\"noopener noreferrer\" href=\"https://www.rabbitmq.com/release-information\" target=\"_blank\">New releases</a></li>\n    <li><a rel=\"noopener noreferrer\" href=\"https://www.vmware.com/products/rabbitmq.html\" target=\"_blank\">Commercial edition</a></li>\n    <li><a rel=\"noopener noreferrer\" href=\"https://www.rabbitmq.com/contact#tanzu-rabbitmq\" target=\"_blank\">Commercial support</a></li>\n    <li><a rel=\"noopener noreferrer\" href=\"https://github.com/rabbitmq/rabbitmq-server/discussions\" target=\"_blank\">Discussions</a></li>\n    <li><a rel=\"noopener noreferrer\" href=\"https://rabbitmq.com/discord/\" target=\"_blank\">Discord</a></li>\n    <li><a rel=\"noopener noreferrer\" href=\"https://www.rabbitmq.com/docs/plugins\" target=\"_blank\">Plugins</a></li>\n    <li><a rel=\"noopener noreferrer\" href=\"https://www.rabbitmq.com/github\" target=\"_blank\">GitHub</a></li>\n  </ul>\n  <button\n    class=\"theme-switcher\"\n    type=\"button\"\n    title=\"Switch between dark and light mode (currently auto mode)\"\n    aria-label=\"Switch between dark and light mode (currently auto mode)\"\n    aria-live=\"polite\"\n    aria-pressed=\"true\"\n    x-scheme=\"auto\">\n  </button>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["limits"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Limits</h1>\n\n<div class=\"section\" id=\"virtual-host-limits\">\n    <h2>Virtual host Limits</h2>\n    <div class=\"hider\">\n        <div class=\"updatable\">\n\n            ");
         if (limits.length > 0) { 
        ___ViewO.push("\n            <table class=\"list\">\n              <thead>\n                <tr>\n                  <th>Virtual Host</th>\n                  <th>Limit</th>\n                  <th>Value</th>\n                  <th class=\"administrator-only\"></th>\n                </tr>\n              </thead>\n              <tbody>\n                ");
         for (var i = 0; i < limits.length; i++) {
                  var limit = limits[i];
                  var limit_values = Object.keys(limit.value).sort().map(
                    function(k) { return {name: k, value: limit.value[k]};});
                
        ___ViewO.push("\n\n                ");
         for (var j = 0; j < limit_values.length; j++) {
                  var limit_value = limit_values[j];
                
        ___ViewO.push("\n\n                <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(j+1))));
        ___ViewO.push(">\n                    ");
         if(j == 0) { 
        ___ViewO.push("\n                    <td rowspan=\"");
        ___ViewO.push((EJS.Scanner.to_text( limit_values.length )));
        ___ViewO.push("\"> ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(limit.vhost) )));
        ___ViewO.push(" </td>\n                    ");
         } 
        ___ViewO.push("\n                    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(limit_value.name) )));
        ___ViewO.push("</td>\n                    <td>");
        ___ViewO.push((EJS.Scanner.to_text( limit_value.value )));
        ___ViewO.push("</td>\n                    <td class=\"administrator-only\">\n                        <form action=\"#/limits\" method=\"delete\" class=\"confirm\">\n                            <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(limit_value.name) )));
        ___ViewO.push("\"/>\n                            <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(limit.vhost) )));
        ___ViewO.push("\"/>\n                            <input type=\"submit\" value=\"Clear\"/>\n                        </form>\n                    </td>\n                </tr>\n                ");
         } 
        ___ViewO.push("\n                ");
         } 
        ___ViewO.push("\n              </tbody>\n            </table>\n            ");
         } 
        ___ViewO.push("\n        </div>\n    </div>\n</div>\n\n<div class=\"section administrator-only\" id=\"set-virtual-host-limits\">\n    <h2>Set / update a virtual host limit</h2>\n    <div class=\"hider\">\n        <form action=\"#/limits\" method=\"put\">\n            <table class=\"form\">\n                <tr>\n                  <th><label>Virtual host:</label></th>\n                  <td>\n                    <select name=\"vhost\">\n                        ");
         for (var i = 0; i < vhosts.length; i++) { 
        ___ViewO.push("\n                        <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("\">\n                            ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("\n                        </option>\n                        ");
         } 
        ___ViewO.push("\n                    </select>\n                  </td>\n                </tr>\n                <tr>\n                    <th><label>Limit:</label></th>\n                    <td>\n                        <select name=\"name\">\n                            <option value=\"max-connections\">max-connections</option>\n                            <option value=\"max-queues\">max-queues</option>\n                        </select>\n                    </td>\n                </tr>\n                <tr>\n                    <th><label>Value:</label></th>\n                    <td>\n                        <input type=\"text\" name=\"value\"/>\n                        <span class=\"mand\">*</span>\n                    </td>\n                </tr>\n            </table>\n            <input type=\"submit\" value=\"Set / update limit\"/>\n        </form>\n    </div>\n</div>\n\n<div class=\"section\" id=\"user-limits\">\n  <h2>User Limits</h2>\n  <div class=\"hider\">\n      <div class=\"updatable\">\n\n          ");
         if (user_limits.length > 0) { 
        ___ViewO.push("\n          <table class=\"list\">\n            <thead>\n              <tr>\n                <th>User</th>\n                <th>Limit</th>\n                <th>Value</th>\n                <th class=\"administrator-only\"></th>\n              </tr>\n            </thead>\n            <tbody>\n              ");
         for (var i = 0; i < user_limits.length; i++) {
                var user_limit = user_limits[i];
                var user_limit_values = Object.keys(user_limit.value).sort().map(
                  function(k) { return {name: k, value: user_limit.value[k]};});
              
        ___ViewO.push("\n\n              ");
         for (var j = 0; j < user_limit_values.length; j++) {
                var user_limit_value = user_limit_values[j];
              
        ___ViewO.push("\n\n              <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(j+1))));
        ___ViewO.push(">\n                  ");
         if(j == 0) { 
        ___ViewO.push("\n                  <td rowspan=\"");
        ___ViewO.push((EJS.Scanner.to_text( user_limit_values.length )));
        ___ViewO.push("\"> ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(user_limit.user) )));
        ___ViewO.push(" </td>\n                  ");
         } 
        ___ViewO.push("\n                  <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(user_limit_value.name) )));
        ___ViewO.push("</td>\n                  <td>");
        ___ViewO.push((EJS.Scanner.to_text( user_limit_value.value )));
        ___ViewO.push("</td>\n                  <td class=\"administrator-only\">\n                      <form action=\"#/user-limits\" method=\"delete\" class=\"confirm\">\n                          <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(user_limit_value.name) )));
        ___ViewO.push("\"/>\n                          <input type=\"hidden\" name=\"user\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(user_limit.user) )));
        ___ViewO.push("\"/>\n                          <input type=\"submit\" value=\"Clear\"/>\n                      </form>\n                  </td>\n              </tr>\n              ");
         } 
        ___ViewO.push("\n              ");
         } 
        ___ViewO.push("\n            </tbody>\n          </table>\n          ");
         } 
        ___ViewO.push("\n      </div>\n  </div>\n</div>\n\n");
         if(ac.isAdministratorUser()) { 
        ___ViewO.push("\n<div class=\"section administrator-only\" id=\"set-user-limits\">\n  <h2>Set / update a user limit</h2>\n  <div class=\"hider\">\n      <form action=\"#/user-limits\" method=\"put\">\n          <table class=\"form\">\n              <tr>\n                <th><label>User:</label></th>\n                <td>\n                  <select name=\"user\">\n                      ");
         for (var i = 0; i < users.length; i++) { 
        ___ViewO.push("\n                      <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(users[i].name) )));
        ___ViewO.push("\">\n                          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(users[i].name) )));
        ___ViewO.push("\n                      </option>\n                      ");
         } 
        ___ViewO.push("\n                  </select>\n                </td>\n              </tr>\n              <tr>\n                  <th><label>Limit:</label></th>\n                  <td>\n                      <select name=\"name\">\n                          <option value=\"max-connections\">max-connections</option>\n                          <option value=\"max-channels\">max-channels</option>\n                      </select>\n                  </td>\n              </tr>\n              <tr>\n                  <th><label>Value:</label></th>\n                  <td>\n                      <input type=\"text\" name=\"value\"/>\n                      <span class=\"mand\">*</span>\n                  </td>\n              </tr>\n          </table>\n          <input type=\"submit\" value=\"Set / update limit\"/>\n      </form>\n  </div>\n</div>\n");
         } 
        ___ViewO.push("\n \n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["list-exchanges"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<select name=\"exchange\">\n        ");
         for (var i = 0; i < exchanges.length; i++) { 
        ___ViewO.push("\n           <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(exchanges[i].name) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_exchange(exchanges[i].name) )));
        ___ViewO.push("</option>\n        ");
         } 
        ___ViewO.push("\n</select>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["login"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<div id=\"login\">\n  <p><img src=\"img/rabbitmqlogo.svg\" alt=\"RabbitMQ logo\" width=\"204\" height=\"37\"/></p>\n\n  <form action=\"#/login\" method=\"put\">\n    <div id=\"login-status\"></div>\n    <table class=\"form\">\n      <tr>\n        <th><label for=\"username\">Username:</label></th>\n        <td><input id=\"username\" type=\"text\" name=\"username\" autofocus autocomplete=\"username\"/><span class=\"mand\">*</span></td>\n      </tr>\n      <tr>\n        <th><label for=\"password\">Password:</label></th>\n        <td><input id=\"password\" type=\"password\" name=\"password\" autocomplete=\"current-password\"/><span class=\"mand\">*</span></td>\n      </tr>\n      <tr>\n        <th>&nbsp;</th>\n        <td><input type=\"submit\" value=\"Login\"/></td>\n      </tr>\n    </table>\n  </form>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["login_oauth"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<div id=\"login\">\n  <p><img src=\"img/rabbitmqlogo.svg\" alt=\"RabbitMQ logo\" width=\"204\" height=\"37\"/></p>\n  <!-- begin login status -->\n  <div id=\"login-status\">\n    ");
         if (Array.isArray(escaped_warnings)) { 
        ___ViewO.push("\n        ");
         for (var i = 0; i < escaped_warnings.length; i++) { 
        ___ViewO.push("\n        <p class=\"warning\">");
        ___ViewO.push((EJS.Scanner.to_text(escaped_warnings[i])));
        ___ViewO.push(" </p>\n        ");
         } 
        ___ViewO.push("\n    ");
         } 
        ___ViewO.push("\n    ");
         if (notAuthorized) { 
        ___ViewO.push("\n        <button id=\"logout\" data-oauth-action=\"logout\">Click here to logout</button>\n    ");
         } 
        ___ViewO.push("\n  </div>\n");
         if (!notAuthorized) { 
        ___ViewO.push("\n    ");
         if (strict_auth_mechanism != null && strict_auth_mechanism.type === "oauth2") { 
        ___ViewO.push("\n        <button id=\"login\" data-oauth-action=\"login\" data-resource-id=\"");
        ___ViewO.push((EJS.Scanner.to_text(fmt_string(strict_auth_mechanism.resource_id))));
        ___ViewO.push("\">Click here to log in</button>\n    ");
         } else if ((typeof resource_servers == 'object' && resource_servers.length == 1) && oauth_disable_basic_auth) { 
        ___ViewO.push("\n        <button id=\"login\" data-oauth-action=\"login\" data-resource-id=\"");
        ___ViewO.push((EJS.Scanner.to_text(fmt_string(resource_servers[0].id))));
        ___ViewO.push("\">Click here to log in</button>\n    ");
         } else if (typeof resource_servers == 'object' && resource_servers.length >= 1 && strict_auth_mechanism == null) { 
        ___ViewO.push("\n\n    <b>Login with :</b>\n    <p/>\n    ");
         const OAuth2Visible = (strict_auth_mechanism == null || strict_auth_mechanism.type === "oauth2") ||
      (preferred_auth_mechanism == null || preferred_auth_mechanism === "oauth2"); 
        ___ViewO.push("\n    ");
         const OAuth2Invisible = (preferred_auth_mechanism != null && preferred_auth_mechanism.type !== "oauth2"); 
        ___ViewO.push("\n    ");
         const OAuth2Hidden = (strict_auth_mechanism != null && strict_auth_mechanism.type !== "oauth2"); 
        ___ViewO.push("\n    ");
         const preferredResourceId = preferred_auth_mechanism != null && preferred_auth_mechanism.type === "oauth2" ? preferred_auth_mechanism.resource_id : null; 
        ___ViewO.push("\n    <!-- begin login with oauth2  -->\n    ");
         if (!OAuth2Hidden) { 
        ___ViewO.push("\n    <div class=\"section disable-pref ");
        ___ViewO.push((EJS.Scanner.to_text( OAuth2Visible ? 'section-visible' : '' )));
        ___ViewO.push("  ");
        ___ViewO.push((EJS.Scanner.to_text( OAuth2Invisible ? 'section-invisible' : '' )));
        ___ViewO.push(" \" id=\"login-with-oauth2\">\n      <h2>OAuth 2.0</h2>\n      <div class=\"hider\">\n        <div class=\"updatable\">\n          ");
         if (resource_servers.length == 1 && declared_resource_servers_count == 1) { 
        ___ViewO.push("\n          <button id=\"login\" data-oauth-action=\"login\" data-resource-id=\"");
        ___ViewO.push((EJS.Scanner.to_text(fmt_string(resource_servers[0].id))));
        ___ViewO.push("\">Click here to log in</button>\n          ");
         } else { 
        ___ViewO.push("\n          <form id=\"oauth2-resource-form\">\n            <label for=\"oauth2-resource\">Resource: </label>\n            <select id=\"oauth2-resource\">\n              ");
         for (var i = 0; i < resource_servers.length; i++) { 
        ___ViewO.push("\n               <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(resource_servers[i].id) )));
        ___ViewO.push("\" ");
        ___ViewO.push((EJS.Scanner.to_text( (preferredResourceId === resource_servers[i].id) ? 'selected="selected"' : '' )));
        ___ViewO.push(">\n                 ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(resource_servers[i].label != null ? resource_servers[i].label : resource_servers[i].id) )));
        ___ViewO.push("\n               </option>\n              ");
         } 
        ___ViewO.push("\n            </select>\n            <p/>\n            <button id=\"login\" type=\"submit\">Click here to log in</button>\n          </form>\n          ");
         } 
        ___ViewO.push("\n        </div>\n      </div>\n    </div>\n    ");
         } 
        ___ViewO.push("    \n    <!-- end login with oauth2  -->\n");
         } 
        ___ViewO.push("\n\n  <!-- begin login with basic auth   -->  \n  ");
         const basicAuthVisible = (strict_auth_mechanism != null && strict_auth_mechanism.type === "basic") ||
    (preferred_auth_mechanism != null && preferred_auth_mechanism.type === "basic"); 
        ___ViewO.push("\n  ");
         const basicAuthInvisible = (strict_auth_mechanism == null && preferred_auth_mechanism == null || (preferred_auth_mechanism != null && preferred_auth_mechanism.type !== "basic"));
        ___ViewO.push("\n  ");
         const basicAuthHidden = (strict_auth_mechanism != null && strict_auth_mechanism.type !== "basic"); 
        ___ViewO.push("\n  ");
         if (!oauth_disable_basic_auth && !basicAuthHidden) { 
        ___ViewO.push("\n  <div class=\"section disable-pref ");
        ___ViewO.push((EJS.Scanner.to_text( basicAuthInvisible ? 'section-invisible' : '')));
        ___ViewO.push("  ");
        ___ViewO.push((EJS.Scanner.to_text( basicAuthVisible ? 'section-visible' : '')));
        ___ViewO.push(" \" id=\"login-with-basic-auth\">\n    <h2>Basic Authentication</h2>\n    <div class=\"hider\">\n      <div class=\"updatable\">\n        <form action=\"#/login\"  id=\"basic-auth-form\" method=\"put\">\n        <table class=\"form\">\n          <tr>\n            <th><label>Username:</label></th>\n            <td><input type=\"text\" id=\"username\" name=\"username\" autocomplete=\"username\"/><span class=\"mand\">*</span></td>\n          </tr>\n          <tr>\n            <th><label>Password:</label></th>\n            <td><input type=\"password\" id=\"password\" name=\"password\" autocomplete=\"current-password\"/><span class=\"mand\">*</span></td>\n          </tr>\n          <tr>\n            <th>&nbsp;</th>\n            <td><input type=\"submit\" value=\"Login\"/></td>\n          </tr>\n        </table>\n        </form>\n      </div>\n    </div>\n  </div>\n  ");
         } 
        ___ViewO.push("\n  <!-- end login with basic auth  -->\n");
         } 
        ___ViewO.push("\n\n</div> <!-- login -->\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["memory-bar"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<div class=\"memory-bar\">\n");
        
  var width = 800;

  var pseudo_total = 0
  for (var section in sections) {
    pseudo_total += memory[section];
  }

  total_out[0] = pseudo_total;

  for (var section in sections) {
    if (memory[section] > 0) {
    var section_width = Math.round(width * memory[section] / pseudo_total);
        ___ViewO.push("\n  <div class=\"memory-section memory_");
        ___ViewO.push((EJS.Scanner.to_text( sections[section][0] )));
        ___ViewO.push("\"\n       style=\"width: ");
        ___ViewO.push((EJS.Scanner.to_text( section_width )));
        ___ViewO.push("px;\"\n       title=\"");
        ___ViewO.push((EJS.Scanner.to_text( sections[section][1] )));
        ___ViewO.push(" ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(memory[section]) )));
        ___ViewO.push("\">\n  </div>\n");
        
     }
   }
        ___ViewO.push("\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["memory-table"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        
  for (var i in key) {
        ___ViewO.push("\n<table class=\"facts\">\n");
        
  for (var j in key[i]) {
   var group = key[i][j];
        ___ViewO.push("\n  <tr>\n    <th><div class=\"colour-key memory_");
        ___ViewO.push((EJS.Scanner.to_text( group.colour )));
        ___ViewO.push("\"></div>");
        ___ViewO.push((EJS.Scanner.to_text( group.name )));
        ___ViewO.push("</th>\n    <td>\n      <table class=\"mini\">\n");
        
  for (var k in group.keys) {
    var name  = group.keys[k][0];
    var label = group.keys[k][1];
        ___ViewO.push("\n        <tr>\n          <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(memory[name]) )));
        ___ViewO.push("</td>\n          <td>");
        ___ViewO.push((EJS.Scanner.to_text( label )));
        ___ViewO.push("</td>\n        </tr>\n");
         } 
        ___ViewO.push("\n      </table>\n    </td>\n  </tr>\n");
         } 
        ___ViewO.push("\n</table>\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["memory"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        
  if (memory == "not_available") {
        ___ViewO.push("\n<p class=\"warning\">\n  Memory statistics not available.\n</p>\n");
         } else { 
        ___ViewO.push("\n");
        ___ViewO.push((EJS.Scanner.to_text( format('memory-bar', {sections: MEMORY_STATISTICS.sections, memory: memory, total_out: []}) )));
        ___ViewO.push("\n<span class=\"clear\">&nbsp;</span>\n<div class=\"box\">\n");
        ___ViewO.push((EJS.Scanner.to_text( format('memory-table', {key: MEMORY_STATISTICS.keys, memory: memory}) )));
        ___ViewO.push("\n</div>\n\n<div class=\"memory-info\">\n  Last updated: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_date(new Date()) )));
        ___ViewO.push("</b>.<br/>\n  Memory calculation strategy: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(memory.strategy) )));
        ___ViewO.push("</b>. <span class=\"help\" id=\"memory-calculation-strategy-breakdown\"></span><br/><br/>\n  Amount of memory used vs. allocated during last update: <span class=\"help\" id=\"memory-use\"></span><br/>\n  <table class=\"facts\">\n      <tr>\n        <th>Runtime Used</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(memory.total.erlang) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Runtime Allocated</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(memory.total.allocated) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Resident Set Size (RSS) reported by the OS</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(memory.total.rss) )));
        ___ViewO.push("</td>\n      </tr>\n    </table>\n</div>\n\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["messages"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        
   for (var i = 0; i < msgs.length; i++) {
   var msg = msgs[i];
        ___ViewO.push("\n<div class=\"box\">\n<h3>Message ");
        ___ViewO.push((EJS.Scanner.to_text( i+1 )));
        ___ViewO.push("</h3>\n<p>The server reported <b>");
        ___ViewO.push((EJS.Scanner.to_text( msg.message_count )));
        ___ViewO.push("</b> messages remaining.</p>\n<table class=\"facts\">\n  <tr>\n    <th>Exchange</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_exchange(msg.exchange) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Routing Key</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(msg.routing_key) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Redelivered</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(msg.redelivered) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Properties</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_table_short(msg.properties) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>\n      Payload\n      <sub>");
        ___ViewO.push((EJS.Scanner.to_text( msg.payload_bytes )));
        ___ViewO.push(" bytes</sub>\n      <sub>Encoding: ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(msg.payload_encoding) )));
        ___ViewO.push("</sub>\n    </th>\n    <td>\n      <pre class=\"msg-payload\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_maybe_wrap(msg.payload, msg.payload_encoding) )));
        ___ViewO.push("</pre>\n    </td>\n  </tr>\n</table>\n</div>\n");
        
  }
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["msg-detail-deliveries"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h3>Deliveries</h3>\n");
         if (object && object.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n  <tr>\n");
         if (mode == 'queue') { 
        ___ViewO.push("\n    <th>Channel</th>\n");
         } else { 
        ___ViewO.push("\n    <th>Queue</th>\n");
         } 
        ___ViewO.push("\n    <th>deliver / get</th>\n    <th>ack</th>\n  </tr>\n");
        
   for (var i = 0; i < object.length; i++) {
     var del = object[i];
        ___ViewO.push("\n     <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n");
         if (mode == 'queue') { 
        ___ViewO.push("\n       <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_channel(del.channel_details.name) )));
        ___ViewO.push("</td>\n");
         } else { 
        ___ViewO.push("\n       <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_queue(del.queue.vhost, del.queue.name) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n       <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(del.stats, 'deliver_get') )));
        ___ViewO.push("</td>\n       <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(del.stats, 'ack') )));
        ___ViewO.push("</td>\n     </tr>\n");
         } 
        ___ViewO.push("\n</table>\n");
         } else { 
        ___ViewO.push("\n<p> ... no deliveries ...</p>\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["msg-detail-publishes"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h3>");
        ___ViewO.push((EJS.Scanner.to_text( label )));
        ___ViewO.push("</h3>\n");
         if (object && object.length > 0) { 
        ___ViewO.push("\n");
        
     var col_confirm = mode != 'exchange-outgoing';
        ___ViewO.push("\n<table class=\"list\">\n  <tr>\n");
         if (mode == 'channel') { 
        ___ViewO.push("\n    <th>Exchange</th>\n");
         } else if (mode == 'exchange-incoming') { 
        ___ViewO.push("\n    <th>Channel</th>\n");
         } else if (mode == 'exchange-outgoing') { 
        ___ViewO.push("\n    <th>Queue</th>\n");
         } else { 
        ___ViewO.push("\n    <th>Exchange</th>\n");
         } 
        ___ViewO.push("\n    <th>publish</th>\n");
         if (col_confirm) { 
        ___ViewO.push("\n    <th>confirm</th>\n");
         } 
        ___ViewO.push("\n  </tr>\n");
        
     for (var i = 0; i < object.length; i++) {
       var pub = object[i];
        ___ViewO.push("\n    <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n\n");
         if (mode == 'channel') { 
        ___ViewO.push("\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_exchange(pub.exchange.vhost, pub.exchange.name) )));
        ___ViewO.push("</td>\n");
         } else if (mode == 'exchange-incoming') { 
        ___ViewO.push("\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_channel(pub.channel_details.name) )));
        ___ViewO.push("</td>\n");
         } else if (mode == 'exchange-outgoing') { 
        ___ViewO.push("\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_queue(pub.queue.vhost, pub.queue.name) )));
        ___ViewO.push("</td>\n");
         } else { 
        ___ViewO.push("\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_exchange(pub.exchange.vhost, pub.exchange.name) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n      <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(pub.stats, 'publish') )));
        ___ViewO.push("</td>\n");
         if (col_confirm) { 
        ___ViewO.push("\n      <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(pub.stats, 'confirm') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n    </tr>\n");
         } 
        ___ViewO.push("\n</table>\n");
         } else { 
        ___ViewO.push("\n<p> ... no publishes ...</p>\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["node"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Node <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node.name) )));
        ___ViewO.push("</b></h1>\n<div class=\"updatable\">\n\n");
         if (!node.running) { 
        ___ViewO.push("\n<p class=\"warning\">Node not running</p>\n");
         } else if ((node.os_pid == undefined) && (!disable_stats)) { 
        ___ViewO.push("\n<p class=\"warning\">Node statistics not available</p>\n");
         } else { 
        ___ViewO.push("\n\n");
         if(!disable_stats) { 
        ___ViewO.push("\n<div class=\"section\">\n<h2>Overview</h2>\n<div class=\"hider\">\n  <div class=\"box\">\n  <table class=\"facts facts-l\">\n");
         if (node.being_drained) { 
        ___ViewO.push("\n    <tr>\n      <th>Status</th>\n      <td><abbr class=\"status-yellow\" title=\"Maintenance mode is in effect\">The node was <a href=\"https://rabbitmq.com/upgrade.html#maintenance-mode\">put under maintenance</a></abbr></td>\n    </tr>\n");
         } 
        ___ViewO.push("\n    <tr>\n      <th>Uptime</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_uptime(node.uptime) )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Cores</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node.processors) )));
        ___ViewO.push("</td>\n    </tr>\n");
         if (rabbit_versions_interesting) { 
        ___ViewO.push("\n    <tr>\n      <th>RabbitMQ Version</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_rabbit_version(node.applications) )));
        ___ViewO.push("</td>\n    </tr>\n");
         } 
        ___ViewO.push("\n    <tr>\n      <th>\n        <a href=\"https://www.rabbitmq.com/configure.html\" target=\"_blank\">Config file</a>\n      </th>\n      <td>\n  ");
        
     for (var i = 0; i < node.config_files.length; i++) {
       var config = fmt_escape_html(node.config_files[i]);
  
        ___ViewO.push("\n        <code>");
        ___ViewO.push((EJS.Scanner.to_text( config )));
        ___ViewO.push("</code>\n  ");
         } 
        ___ViewO.push("\n      </td>\n    </tr>\n    <tr>\n      <th>Database directory</th>\n      <td>\n        <code>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node.db_dir) )));
        ___ViewO.push("</code>\n      </td>\n    </tr>\n    <tr>\n      <th>\n");
         if (node.log_files.length == 1) { 
        ___ViewO.push("\n        Log file\n");
         } else { 
        ___ViewO.push("\n        Log files\n");
         } 
        ___ViewO.push("\n      </th>\n      <td>\n      <pre style=\"margin-top: 0px; margin-bottom: 0px;\">");
        
   for (var i = 0; i < node.log_files.length; i++) {
     var config = fmt_escape_html(node.log_files[i]);
        ___ViewO.push((EJS.Scanner.to_text( config )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("</pre>\n      </td>\n    </tr>\n  </table>\n  </div>\n</div>\n</div>\n\n");
         if(!disable_stats) { 
        ___ViewO.push("\n<div class=\"section\">\n<h2>Process statistics</h2>\n<div class=\"hider\">\n  ");
        ___ViewO.push((EJS.Scanner.to_text( node_stats_prefs() )));
        ___ViewO.push("\n  <table class=\"facts\">\n    <tr>\n      <th>\n        File descriptors <span class=\"help\" id=\"file-descriptors\"></span>\n      </th>\n      <td>\n");
         if (node.fd_used != 'install_handle_from_sysinternals') { 
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( node_stat_count('fd_used', 'fd_total', node, FD_THRESHOLDS) )));
        ___ViewO.push("\n");
         } else { 
        ___ViewO.push("\n        <p class=\"c\">handle.exe missing <span class=\"help\" id=\"handle-exe\"></span><sub>");
        ___ViewO.push((EJS.Scanner.to_text( node.fd_total )));
        ___ViewO.push(" available</sub></p>\n\n");
         } 
        ___ViewO.push("\n      </td>\n    </tr>\n    <tr>\n      <th>\n        Erlang processes\n      </th>\n     <td>\n        ");
        ___ViewO.push((EJS.Scanner.to_text( node_stat_count('proc_used', 'proc_total', node, PROCESS_THRESHOLDS) )));
        ___ViewO.push("\n     </td>\n    </tr>\n    <tr>\n      <th>\n        Memory <span class=\"help\" id=\"memory-calculation-strategy\"></span>\n      </th>\n      <td>\n");
         if (node.mem_limit != 'memory_monitoring_disabled') { 
        ___ViewO.push("\n   ");
        ___ViewO.push((EJS.Scanner.to_text( node_stat('mem_used', 'Used', 'mem_limit', 'high watermark', node,
                 fmt_bytes, fmt_bytes_axis,
                 node.mem_alarm ? 'red' : 'green',
                 node.mem_alarm ? 'memory-alarm' : null) )));
        ___ViewO.push("\n");
         } else { 
        ___ViewO.push("\n   ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(node.mem_used) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n      </td>\n    </tr>\n    <tr>\n      <th>\n        Disk space\n      </th>\n      <td>\n");
         if (node.disk_free_limit != 'disk_free_monitoring_disabled') { 
        ___ViewO.push("\n   ");
        ___ViewO.push((EJS.Scanner.to_text( node_stat('disk_free', 'Free', 'disk_free_limit', 'low watermark', node,
                 fmt_bytes, fmt_bytes_axis,
                 node.disk_free_alarm ? 'red' : 'green',
                 node.disk_free_alarm ? 'disk-free-alarm' : null,
                 true) )));
        ___ViewO.push("\n");
         } else { 
        ___ViewO.push("\n         (not available)\n");
         } 
        ___ViewO.push("\n      </td>\n    </tr>\n  </table>\n</div>\n</div>\n\n<div class=\"section-hidden\">\n<h2>Persistence statistics</h2>\n<div class=\"hider\">\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('mnesia-stats-count', node,
      [['RAM only', 'mnesia_ram_tx_count'],
       ['Disk', 'mnesia_disk_tx_count']],
      fmt_rate, fmt_rate_axis, true, 'Schema data store transactions', 'mnesia-transactions') )));
        ___ViewO.push("\n\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('persister-msg-stats-count', node,
      [['QI Journal', 'queue_index_journal_write_count'],
       ['Store Read', 'msg_store_read_count'],
       ['Store Write', 'msg_store_write_count']],
      fmt_rate, fmt_rate_axis, true, 'Persistence operations (messages)', 'persister-operations-msg') )));
        ___ViewO.push("\n\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('persister-bulk-stats-count', node,
      [['QI Read', 'queue_index_read_count'],
       ['QI Write', 'queue_index_write_count']],
      fmt_rate, fmt_rate_axis, true, 'Persistence operations (bulk)', 'persister-operations-bulk') )));
        ___ViewO.push("\n</div>\n</div>\n\n<div class=\"section-hidden\">\n<h2>I/O statistics</h2>\n<div class=\"hider\">\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('persister-io-stats-count', node,
      [['Read', 'io_read_count'],
       ['Write', 'io_write_count'],
       ['Seek', 'io_seek_count'],
       ['Sync', 'io_sync_count'],
       ['File handle reopen', 'io_reopen_count']],
      fmt_rate, fmt_rate_axis, true, 'I/O operations', 'io-operations') )));
        ___ViewO.push("\n\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('persister-io-stats-bytes', node,
      [['Read', 'io_read_bytes'],
       ['Write', 'io_write_bytes']],
      fmt_rate_bytes, fmt_rate_bytes_axis, true, 'I/O data rates') )));
        ___ViewO.push("\n\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('persister-io-stats-time', node,
      [['Read', 'io_read_avg_time'],
       ['Write', 'io_write_avg_time'],
       ['Seek', 'io_seek_avg_time'],
       ['Sync', 'io_sync_avg_time']],
      fmt_ms, fmt_ms, false, 'I/O average time per operation') )));
        ___ViewO.push("\n</div>\n</div>\n\n<div class=\"section-hidden\">\n<h2>Churn statistics</h2>\n<div class=\"hider\">\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('connection-churn', node,
      [['Created', 'connection_created'],
       ['Closed', 'connection_closed']],
      fmt_rate, fmt_rate_axis, true, 'Connection operations', 'connection-operations') )));
        ___ViewO.push("\n\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('channel-churn', node,
      [['Created', 'channel_created'],
       ['Closed', 'channel_closed']],
      fmt_rate, fmt_rate_axis, true, 'Channel operations', 'channel-operations') )));
        ___ViewO.push("\n\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('queue-churn', node,
      [['Declared', 'queue_declared'],
       ['Created', 'queue_created'],
       ['Deleted', 'queue_deleted']],
      fmt_rate, fmt_rate_axis, true, 'Queue operations', 'queue-operations') )));
        ___ViewO.push("\n\n</div>\n</div>\n");
         } 
        ___ViewO.push("\n\n<div class=\"section-hidden\">\n<h2>Cluster links</h2>\n<div class=\"hider\">\n");
         if (node.cluster_links.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n  <tr>\n    <th>Remote node</th>\n    <th>Local address</th>\n    <th>Local port</th>\n    <th>Remote address</th>\n    <th>Remote port</th>\n    <th class=\"plain\">\n      ");
        ___ViewO.push((EJS.Scanner.to_text( chart_h3('cluster-link-data-rates', 'Data rates') )));
        ___ViewO.push("\n    </th>\n  </tr>\n  ");
        
   for (var i = 0; i < node.cluster_links.length; i++) {
     var link = node.cluster_links[i];
  
        ___ViewO.push("\n   <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_node(link.name) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.sock_addr) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.sock_port) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.peer_addr) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.peer_port) )));
        ___ViewO.push("</td>\n     <td class=\"plain\">\n       ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text_no_heading(
           'cluster-link-data-rates', 'cluster-link-data-rates' + link.name,
           link.stats,
           [['Recv', 'recv_bytes'],
            ['Send', 'send_bytes']],
           fmt_rate_bytes, fmt_rate_bytes_axis, true) )));
        ___ViewO.push("\n     </td>\n   </tr>\n");
         } 
        ___ViewO.push("\n</table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no cluster links ...</p>\n");
         } 
        ___ViewO.push("\n</div>\n</div>\n\n");
         } 
        ___ViewO.push("\n\n</div>\n");
         } 
        ___ViewO.push("\n\n<!--\n  The next two need to be non-updatable or we will wipe the memory details\n  as soon as we have drawn it.\n -->\n\n");
         if (node.running && (node.os_pid != undefined || disable_stats)) { 
        ___ViewO.push("\n\n<div class=\"section\">\n<h2>Memory details</h2>\n<div class=\"hider\">\n  <div id=\"memory-details\"></div>\n  <button class=\"update-manual memory-button\" for=\"memory-details\" query=\"memory\">Update</button>\n</div>\n</div>\n\n<div class=\"section-hidden\">\n<h2>Binary references</h2>\n<div class=\"hider\">\n  <p>\n    <b>Warning:</b> Calculating binary memory use can be expensive if\n    there are many small binaries in the system.\n  </p>\n  <div id=\"binary-details\"></div>\n  <button class=\"update-manual memory-button\" for=\"binary-details\" query=\"binary\">Update</button>\n</div>\n</div>\n\n");
         } 
        ___ViewO.push("\n\n");
         if(!disable_stats) { 
        ___ViewO.push("\n<div class=\"updatable\">\n");
         if (node.running && node.os_pid != undefined) { 
        ___ViewO.push("\n\n<div class=\"section-hidden\">\n<h2>Advanced</h2>\n<div class=\"hider\">\n  <div class=\"box\">\n  <h3>VM</h3>\n  <table class=\"facts\">\n    <tr>\n      <th>OS pid</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( node.os_pid )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Rates mode</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node.rates_mode) )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Net ticktime</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( node.net_ticktime )));
        ___ViewO.push("s</td>\n    </tr>\n  </table>\n\n  <table class=\"facts\">\n    <tr>\n      <th>Run queue</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( node.run_queue )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Processors</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( node.processors )));
        ___ViewO.push("</td>\n    </tr>\n  </table>\n  </div>\n\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('advanced-gc-stats-count', node,
      [['GC', 'gc_num']],
      fmt_rate, fmt_rate_axis, true, 'GC operations', 'gc-operations') )));
        ___ViewO.push("\n\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('advanced-gc-bytes-stats-count', node,
      [['GC bytes reclaimed', 'gc_bytes_reclaimed']],
      fmt_rate, fmt_rate_axis, true, 'GC bytes reclaimed', 'gc-bytes') )));
        ___ViewO.push("\n\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('advanced-context-switches-stats-count', node,
      [['Context switches', 'context_switches']],
      fmt_rate, fmt_rate_axis, true, 'Context switch operations', 'context-switches-operations') )));
        ___ViewO.push("\n\n<div class=\"box\">\n  <h3>Management GC queue length</h3>\n  <table class=\"facts\">\n    ");
         for(var k in node.metrics_gc_queue_length) {
         if(node.metrics_gc_queue_length.hasOwnProperty(k)) { 
        ___ViewO.push("\n    <tr>\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(k) )));
        ___ViewO.push("</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node.metrics_gc_queue_length[k]) )));
        ___ViewO.push("</td>\n    </tr>\n    ");
         } } 
        ___ViewO.push("\n  </table>\n</div>\n\n<div class=\"box\">\n  <h3>Quorum queue open file metrics</h3>\n  <table class=\"facts\">\n    ");
         for(var k in node.ra_open_file_metrics) { 
        ___ViewO.push("\n    <tr>\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(k) )));
        ___ViewO.push("</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node.ra_open_file_metrics[k]) )));
        ___ViewO.push("</td>\n    </tr>\n    ");
         } 
        ___ViewO.push("\n  </table>\n</div>\n\n<h3>Plugins <span class=\"help\" id=\"plugins\"></span></h3>\n<table class=\"list\">\n  <tr>\n    <th>Name</th>\n    <th>Version</th>\n    <th>Description</th>\n  </tr>\n  ");
        
     var plugins = get_plugins_list(node);
     for (var j = 0; j < plugins.length; j++) {
       var application = plugins[j];
  
        ___ViewO.push("\n         <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(j))));
        ___ViewO.push(">\n           <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(application.name) )));
        ___ViewO.push("</td>\n           <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(application.version) )));
        ___ViewO.push("</td>\n           <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(application.description) )));
        ___ViewO.push("</td>\n         </tr>\n  ");
         } 
        ___ViewO.push("\n</table>\n\n<h3>All applications</h3>\n<table class=\"list\">\n    <tr>\n      <th>Name</th>\n      <th>Version</th>\n      <th>Description</th>\n    </tr>\n    ");
        
      for (var j = 0; j < node.applications.length; j++) {
        var application = node.applications[j];
    
        ___ViewO.push("\n       <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(j))));
        ___ViewO.push(">\n         <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(application.name) )));
        ___ViewO.push("</td>\n         <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(application.version) )));
        ___ViewO.push("</td>\n         <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(application.description) )));
        ___ViewO.push("</td>\n       </tr>\n    ");
         } 
        ___ViewO.push("\n</table>\n\n<h3>Exchange types</h3>\n");
        ___ViewO.push((EJS.Scanner.to_text( format('registry', {'list': node.exchange_types, 'node': node, 'show_enabled': false} ) )));
        ___ViewO.push("\n<h3>Authentication mechanisms</h3>\n");
        ___ViewO.push((EJS.Scanner.to_text( format('registry', {'list': node.auth_mechanisms, 'node': node, 'show_enabled': true} ) )));
        ___ViewO.push("\n\n</div>\n</div>\n\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["overview"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
         if(disable_stats) { 
        ___ViewO.push("\n   <h1>Overview: Management only mode</h1>\n");
         } else { 
        ___ViewO.push("\n   <h1>Overview</h1>\n");
         } 
        ___ViewO.push("\n");
         if (user_monitor) { 
        ___ViewO.push("\n");
        ___ViewO.push((EJS.Scanner.to_text( format('partition', {'nodes': nodes}) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n\n<div class=\"updatable\">\n");
         if (overview.statistics_db_event_queue > 1000) { 
        ___ViewO.push("\n<p class=\"warning\">\n  The management statistics database currently has a queue\n  of <b>");
        ___ViewO.push((EJS.Scanner.to_text( overview.statistics_db_event_queue )));
        ___ViewO.push("</b> events to\n  process. If this number keeps increasing, so will the memory used by\n  the management plugin.\n\n  ");
         if (overview.rates_mode != 'none') { 
        ___ViewO.push("\n  You may find it useful to set the <code>rates_mode</code> config item\n  to <code>none</code>.\n  ");
         } 
        ___ViewO.push("\n</p>\n");
         } 
        ___ViewO.push("\n");
         for (i = 0; i < vhosts.length; i++)
{
    for (var vhost_status_node in vhosts[i].cluster_state) {
        if (vhosts[i].cluster_state[vhost_status_node] != 'running') {
        ___ViewO.push("\n<p class=\"warning\">\n  Virtual host <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("</b> experienced an error on node <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhost_status_node) )));
        ___ViewO.push("</b> and may be inaccessible\n</p>\n");
         }}} 
        ___ViewO.push("\n</div>\n\n<div class=\"section\" id=\"totals-section\">\n<h2>Totals</h2>\n<div  class=\"hider updatable\">\n");
         if(!disable_stats) { 
        ___ViewO.push("\n");
        ___ViewO.push((EJS.Scanner.to_text( queue_lengths('lengths-over', overview.queue_totals) )));
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n  ");
        ___ViewO.push((EJS.Scanner.to_text( message_rates('msg-rates-over', overview.message_stats) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n\n");
         if (overview.object_totals) { 
        ___ViewO.push("\n  <h3>Global counts <span class=\"help\" id=\"resource-counts\"></span></h3>\n\n  <ul id=\"global-counts\">\n    <li>\n      <a href=\"#/connections\" class=\"button\">Connections: <strong>");
        ___ViewO.push((EJS.Scanner.to_text( overview.object_totals.connections )));
        ___ViewO.push("</strong></a>\n    </li>\n");
         if(!disable_stats) { 
        ___ViewO.push("\n    <li>\n      <a href=\"#/channels\" class=\"button\">Channels: <strong>");
        ___ViewO.push((EJS.Scanner.to_text( overview.object_totals.channels )));
        ___ViewO.push("</strong></a>\n    </li>\n");
         } 
        ___ViewO.push("\n    <li>\n      <a href=\"#/exchanges\" class=\"button\">Exchanges: <strong>");
        ___ViewO.push((EJS.Scanner.to_text( overview.object_totals.exchanges )));
        ___ViewO.push("</strong></a>\n    </li>\n    <li>\n      <a href=\"#/queues\" class=\"button\">Queues: <strong>");
        ___ViewO.push((EJS.Scanner.to_text( overview.object_totals.queues )));
        ___ViewO.push("</strong></a>\n    </li>\n");
         if (overview.object_totals['consumers'] != undefined) { 
        ___ViewO.push("\n    <li>\n      <a href=\"#\" class=\"button disabled\">Consumers: <strong>");
        ___ViewO.push((EJS.Scanner.to_text( overview.object_totals.consumers )));
        ___ViewO.push("</strong></a>\n    </li>\n");
         } 
        ___ViewO.push("\n  </ul>\n");
         } 
        ___ViewO.push("\n\n</div>\n</div>\n\n");
         if (user_monitor) { 
        ___ViewO.push("\n<div class=\"section\">\n<h2>Nodes</h2>\n\n<div class=\"hider updatable\">\n\n<table class=\"list\">\n  <tr>\n    <th>Name</th>\n  ");
         if(!disable_stats) { 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'file_descriptors')) { 
        ___ViewO.push("\n    <th>File descriptors <span class=\"help\" id=\"file-descriptors\"></span></th>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'erlang_processes')) { 
        ___ViewO.push("\n    <th>Erlang processes</th>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'memory')) { 
        ___ViewO.push("\n    <th>Memory <span class=\"help\" id=\"memory-calculation-strategy\"></span></th>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'disk_space')) { 
        ___ViewO.push("\n    <th>Disk space</th>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'uptime')) { 
        ___ViewO.push("\n    <th>Uptime</th>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'cores')) { 
        ___ViewO.push("\n    <th>Cores</th>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'info')) { 
        ___ViewO.push("\n    <th>Info</th>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (user_administrator && show_column('overview', 'reset_stats')) { 
        ___ViewO.push("\n    <th>Reset stats</th>\n  ");
         } 
        ___ViewO.push("\n    <th class=\"plus-minus\"><span class=\"popup-options-link\" title=\"Click to change columns\" type=\"columns\" for=\"overview\">+/-</span></th>\n  ");
         } 
        ___ViewO.push("\n  </tr>\n");
        
   for (var i = 0; i < nodes.length; i++) {
     var node = nodes[i];
     if(!disable_stats) {
          var colspan = group_count('overview', 'Statistics', []) +
                        group_count('overview', 'General', []);
                        } else {
          var colspan = [];
          }
        ___ViewO.push("\n   <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n     <td>\n       <a href=\"#/nodes/");
        ___ViewO.push((EJS.Scanner.to_text( esc(node.name) )));
        ___ViewO.push("\" class=\"button\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(node.name) )));
        ___ViewO.push("</a>\n       ");
         if (rabbit_versions_interesting) { 
        ___ViewO.push("\n         <sub>RabbitMQ ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_rabbit_version(node.applications) )));
        ___ViewO.push("</sub>\n       ");
         } 
        ___ViewO.push("\n     </td>\n");
         if(!disable_stats) { 
        ___ViewO.push("\n");
         if (!node.running) { 
        ___ViewO.push("\n     <td colspan=\"");
        ___ViewO.push((EJS.Scanner.to_text( colspan )));
        ___ViewO.push("\">\n       <div class=\"status-red\">\n         Node not running\n       </div>\n     </td>\n");
         } else if (node.os_pid == undefined) { 
        ___ViewO.push("\n     <td colspan=\"");
        ___ViewO.push((EJS.Scanner.to_text( colspan )));
        ___ViewO.push("\">\n       <div class=\"status-yellow\">\n         <abbr title=\"The rabbitmq_management_agent plugin should be enabled on this node. If it is not, various statistics will be inaccurate.\">\n           Node statistics not available</abbr>\n       </div>\n     </td>\n");
         } else { 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'file_descriptors')) { 
        ___ViewO.push("\n     <td>\n    ");
         if (node.fd_used != 'install_handle_from_sysinternals') { 
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( node_stat_count_bar('fd_used', 'fd_total', node, FD_THRESHOLDS) )));
        ___ViewO.push("\n    ");
         } else { 
        ___ViewO.push("\n        <p class=\"c\">handle.exe missing <span class=\"help\" id=\"handle-exe\"></span><sub>");
        ___ViewO.push((EJS.Scanner.to_text( node.fd_total )));
        ___ViewO.push(" available</sub></p>\n\n    ");
         } 
        ___ViewO.push("\n     </td>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'erlang_processes')) { 
        ___ViewO.push("\n     <td>\n\n        ");
        ___ViewO.push((EJS.Scanner.to_text( node_stat_count_bar('proc_used', 'proc_total', node, PROCESS_THRESHOLDS) )));
        ___ViewO.push("\n     </td>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'memory')) { 
        ___ViewO.push("\n     <td>\n\n    ");
         if (node.mem_limit != 'memory_monitoring_disabled') { 
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( node_stat_bar('mem_used', 'mem_limit', 'high watermark', node, fmt_bytes_axis,
                          node.mem_alarm ? 'red' : 'green',
                          node.mem_alarm ? 'memory-alarm' : null) )));
        ___ViewO.push("\n    ");
         } else { 
        ___ViewO.push("\n       ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(node.mem_used) )));
        ___ViewO.push("\n    ");
         } 
        ___ViewO.push("\n     </td>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'disk_space')) { 
        ___ViewO.push("\n     <td>\n\n    ");
         if (node.disk_free_limit != 'disk_free_monitoring_disabled') { 
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( node_stat_bar('disk_free', 'disk_free_limit', 'low watermark', node, fmt_bytes_axis,
                          node.disk_free_alarm ? 'red' : 'green',
                          node.disk_free_alarm ? 'disk-free-alarm' : null, true) )));
        ___ViewO.push("\n    ");
         } else { 
        ___ViewO.push("\n         (not available)\n    ");
         } 
        ___ViewO.push("\n     </td>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'uptime')) { 
        ___ViewO.push("\n     <td><span>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_uptime(node.uptime) )));
        ___ViewO.push("</span></td>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'cores')) { 
        ___ViewO.push("\n     <td><span>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node.processors) )));
        ___ViewO.push("</span></td>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('overview', 'info')) { 
        ___ViewO.push("\n     <td>\n       ");
         if (node.being_drained) { 
        ___ViewO.push("\n         <abbr class=\"status-yellow\" title=\"Node was put under maintenance\">maintenance mode</abbr>\n       ");
         } 
        ___ViewO.push("\n         <abbr title=\"Message rates\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node.rates_mode) )));
        ___ViewO.push("</abbr>\n       ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_plugins_small(node) )));
        ___ViewO.push("\n        <abbr title=\"Memory calculation strategy\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node.mem_calculation_strategy) )));
        ___ViewO.push("</abbr>\n     </td>\n  ");
         } 
        ___ViewO.push("\n  ");
         if(user_administrator && show_column('overview', 'reset_stats')) { 
        ___ViewO.push("\n    <td>\n      <form action=\"#/reset_node\" method=\"delete\" class=\"confirm inline-form\">\n        <input type=\"hidden\" name=\"node\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node.name) )));
        ___ViewO.push("\"/>\n        <input type=\"submit\" value=\"This node\"/>\n      </form>\n      <form action=\"#/reset\" method=\"delete\" class=\"confirm inline-form-right\">\n          <input type=\"submit\" value=\"All nodes\"/>\n      </form>\n  ");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n   </tr>\n");
         } 
        ___ViewO.push("\n</table>\n\n</div>\n</div>\n\n");
         if(!disable_stats) { 
        ___ViewO.push("\n<div class=\"section-hidden\">\n<h2>Churn statistics</h2>\n<div class=\"hider updatable\">\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('connection-churn', overview.churn_rates,
      [['Created', 'connection_created'],
       ['Closed', 'connection_closed']],
      fmt_rate, fmt_rate_axis, true, 'Connection operations', 'connection-operations') )));
        ___ViewO.push("\n\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('channel-churn', overview.churn_rates,
      [['Created', 'channel_created'],
       ['Closed', 'channel_closed']],
      fmt_rate, fmt_rate_axis, true, 'Channel operations', 'channel-operations') )));
        ___ViewO.push("\n\n  ");
        ___ViewO.push((EJS.Scanner.to_text( rates_chart_or_text('queue-churn', overview.churn_rates,
      [['Declared', 'queue_declared'],
       ['Created', 'queue_created'],
       ['Deleted', 'queue_deleted']],
      fmt_rate, fmt_rate_axis, true, 'Queue operations', 'queue-operations') )));
        ___ViewO.push("\n\n</div>\n</div>\n");
         } 
        ___ViewO.push("\n\n");
         if(!disable_stats) { 
        ___ViewO.push("\n<div class=\"section-hidden\">\n<h2>Ports and contexts</h2>\n<div class=\"hider updatable\">\n<h3>Listening ports</h3>\n<table class=\"list\">\n  <tr>\n    <th>Protocol</th>\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n    <th>Node</th>\n");
         } 
        ___ViewO.push("\n    <th>Bound to</th>\n    <th>Port</th>\n    <th>TLS</th>\n  </tr>\n  ");
        
      for (var i = 0; i < overview.listeners.length; i++) {
          var listener = overview.listeners[i];
  
        ___ViewO.push("\n  <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(listener.protocol) )));
        ___ViewO.push("</td>\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(listener.node) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(listener.ip_address) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( listener.port )));
        ___ViewO.push("</td>\n    <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(listener.tls || false) )));
        ___ViewO.push("</td>\n  </tr>\n  ");
         } 
        ___ViewO.push("\n</table>\n<h3>Web contexts</h3>\n<table class=\"list\">\n  <tr>\n    <th>Context</th>\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n    <th>Node</th>\n");
         } 
        ___ViewO.push("\n    <th>Bound to</th>\n    <th>Port</th>\n    <th>SSL</th>\n    <th>Path</th>\n  </tr>\n  ");
        
    for (var i = 0; i < overview.contexts.length; i++) {
        var context = overview.contexts[i];
  
        ___ViewO.push("\n    <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(context.description) )));
        ___ViewO.push("</td>\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(context.node) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( (context.ip != undefined) ? fmt_string(context.ip) : "0.0.0.0" )));
        ___ViewO.push("</td>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( context.port )));
        ___ViewO.push("</td>\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(context.ssl || false) )));
        ___ViewO.push("</td>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(context.path) )));
        ___ViewO.push("</td>\n    </tr>\n  ");
         } 
        ___ViewO.push("\n</table>\n</div>\n</div>\n");
         } 
        ___ViewO.push("\n\n<div class=\"section-hidden administrator-only\" id=\"download-definitions-section\">\n<h2>Export definitions</h2>\n<div class=\"hider\">\n    <table class=\"two-col-layout\">\n      <tr>\n        <td>\n          <p>\n            <label for=\"download-filename\">Filename for download:</label><br/>\n            <input type=\"text\" id=\"download-filename\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_download_filename(overview.node) )));
        ___ViewO.push("\" class=\"wide\" pattern=\"[a-zA-Z0-9!#$%&'*+\\-.^_`|~]+\" title=\"Filename must only contain a-z A-Z 0-9 and the characters ! # $ % & ' * + - . ^ _ ` | ~\" />\n          </p>\n        </td>\n        <td>\n          <p>\n            <button id=\"download-definitions\">Download broker definitions</button>\n            <span class=\"help\" id=\"export-definitions\"></span>\n          </p>\n        </td>\n      </tr>\n      <tr>\n        <td>\n            ");
         if (vhosts_interesting) { 
        ___ViewO.push("\n          <label>Virtual host:</label>\n            <select name=\"vhost-download\">\n              <option value=\"all\">All</option>\n              ");
         for (var i = 0; i < vhosts.length; i++) { 
        ___ViewO.push("\n              <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("</option>\n              ");
         } 
        ___ViewO.push("\n            </select> <span class=\"help\" id=\"export-definitions-vhost\"></span>\n");
         } else { 
        ___ViewO.push("\n            <input type=\"hidden\" name=\"vhost\" value=\"all\"/>\n");
         } 
        ___ViewO.push("\n        </td>\n      </tr>\n    </table>\n</div>\n</div>\n\n<div class=\"section-hidden administrator-only\" id=\"upload-definitions-section\">\n<h2>Import definitions</h2>\n<div class=\"hider\">\n  <form  method=\"post\" enctype=\"multipart/form-data\" name=\"upload-definitions\">\n    <table class=\"two-col-layout\">\n      <tr>\n        <td>\n          <p>\n            <label>Definitions file:</label><br/>\n            <input type=\"file\" name=\"file\"");
         if (settings.definitions && settings.definitions.require_definition_json_extension) { 
        ___ViewO.push(" accept=\".json\"");
         } 
        ___ViewO.push("/>\n          </p>\n        </td>\n        <td>\n          <p>\n            <input type=\"submit\" name=\"upload-definitions\" value=\"Upload broker definitions\"/>\n            <span class=\"help\" id=\"import-definitions\"></span>\n          </p>\n        </td>\n      </tr>\n      <tr>\n        <td>\n         ");
         if (vhosts_interesting) { 
        ___ViewO.push("\n          <label>Virtual host:</label>\n            <select name=\"vhost-upload\">\n              <option value=\"all\">All</option>\n              ");
         for (var i = 0; i < vhosts.length; i++) { 
        ___ViewO.push("\n              <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("</option>\n              ");
         } 
        ___ViewO.push("\n            </select> <span class=\"help\" id=\"import-definitions-vhost\"></span>\n\n");
         } else { 
        ___ViewO.push("\n            <input type=\"hidden\" name=\"vhost\" value=\"all\"/>\n");
         } 
        ___ViewO.push("\n        </td>\n      </tr>\n    </table>\n  </form>\n</div>\n</div>\n\n");
         if (overview.rates_mode == 'none') { 
        ___ViewO.push("\n<div class=\"section-hidden\">\n<h2>Message rates disabled</h2>\n<div class=\"hider\">\n<p>\n  Message rates are currently disabled.\n</p>\n<p>\n  To re-enable message rates, edit your configuration file and\n  set <code>rates_mode</code> to <code>basic</code>\n  or <code>detailed</code> in the <code>rabbitmq_management</code>\n  application\n</p>\n</div>\n</div>\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["partition"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<div class=\"updatable\">\n");
        
   var partitions = [];
   for (var i = 0; i < nodes.length; i++) {
     var node = nodes[i];
     if (node.partitions != undefined && node.partitions.length != 0) {
       partitions.push({'node': node.name,
                        'others': node.partitions});
     }
   }
   if (partitions.length > 0) {
        ___ViewO.push("\n<p class=\"status-error\">\n  Network partition detected<br/><br/>\n  Mnesia reports that this RabbitMQ cluster has experienced a\n  network partition. There is a risk of losing data. Please read\n  <a href=\"https://www.rabbitmq.com/partitions.html\">RabbitMQ\n  documentation about network partitions and the possible solutions</a>.\n</p>\n<p>\n  The nature of the partition is as follows:\n</p>\n  <table class=\"list\">\n    <tr>\n      <th>Node</th><th>Was partitioned from</th>\n    </tr>\n\n");
        
   for (var i = 0; i < partitions.length; i++) {
     var partition = partitions[i];
        ___ViewO.push("\n    <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(partition.node) )));
        ___ViewO.push("</td>\n      <td>\n");
        
   for (var j = 0; j < partition.others.length; j++) {
     var other = partition.others[j];
        ___ViewO.push("\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(other) )));
        ___ViewO.push("<br/>\n");
         } 
        ___ViewO.push("\n      </td>\n    </tr>\n");
         } 
        ___ViewO.push("\n  </table>\n<p>\n  While running in this partitioned state, changes (such as queue or\n  exchange declaration and binding) which take place in one partition\n  will not be visible to other partition(s). Other behaviour is not\n  guaranteed.\n</p>\n<p>\n  <a target=\"_blank\"\n  href=\"https://www.rabbitmq.com/partitions.html\">More information on\n  network partitions.</a>\n</p>\n");
         } 
        ___ViewO.push("\n");
        
   var ticktime = null;
   var ticktimes_unequal = false;
   for (var i = 0; i < nodes.length; i++) {
     var node_ticktime = nodes[i].net_ticktime;
     if (node_ticktime != undefined) {

       if (ticktime != null && node_ticktime != ticktime) {
         ticktimes_unequal = true;
       }
       ticktime = nodes[i].net_ticktime;
     }
   }
   if (ticktimes_unequal) {
        ___ViewO.push("\n<p class=\"status-error\">\n  The <code>kernel</code> <code>net_ticktime</code> values are set\n  differently for different nodes in this cluster.\n</p>\n<p>\n  The values are:\n</p>\n  <table class=\"list\">\n    <tr><th>Node</th><th>net_ticktime</th></tr>\n");
        
   for (var i = 0; i < nodes.length; i++) {
        ___ViewO.push("\n      <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(nodes[i].name) )));
        ___ViewO.push("</td>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(nodes[i].net_ticktime) )));
        ___ViewO.push("</td>\n      </tr>\n");
        
   }
        ___ViewO.push("\n  </table>\n<p>\n  This is a dangerous configuration; use of substantially\n  unequal <code>net_ticktime</code> values can lead to partitions\n  being falsely detected.\n</p>\n<p>\n  <a target=\"_blank\"\n  href=\"https://www.rabbitmq.com/nettick.html\">More information on\n  <code>net_ticktime</code>.</a>\n</p>\n");
        
   }
        ___ViewO.push("\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["permissions"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<div class=\"section\" id=\"permissions\">\n  <h2>Permissions</h2>\n  <div class=\"hider\">\n    <h3>Current permissions</h3>\n    ");
         if (permissions.length > 0) { 
        ___ViewO.push("\n    <table class=\"list\">\n      <thead>\n        <tr>\n");
         if (mode == 'vhost') { 
        ___ViewO.push("\n          <th>User</th>\n");
         } else { 
        ___ViewO.push("\n          <th>Virtual host</th>\n");
         } 
        ___ViewO.push("\n          <th>Configure regexp</th>\n          <th>Write regexp</th>\n          <th>Read regexp</th>\n          <th></th>\n        </tr>\n      </thead>\n      <tbody>\n");
        
for (var i = 0; i < permissions.length; i++) {
    var permission = permissions[i];
        ___ViewO.push("\n           <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n");
         if (mode == 'vhost') { 
        ___ViewO.push("\n             <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_user(permission.user) )));
        ___ViewO.push("</td>\n");
         } else { 
        ___ViewO.push("\n             <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_vhost(permission.vhost) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n             <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(permission.configure) )));
        ___ViewO.push("</td>\n             <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(permission.write) )));
        ___ViewO.push("</td>\n             <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(permission.read) )));
        ___ViewO.push("</td>\n             <td class=\"c\">\n               <form action=\"#/permissions\" method=\"delete\" class=\"confirm\">\n                 <input type=\"hidden\" name=\"username\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(permission.user) )));
        ___ViewO.push("\"/>\n                 <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(permission.vhost) )));
        ___ViewO.push("\"/>\n                 <input type=\"submit\" value=\"Clear\"/>\n               </form>\n             </td>\n           </tr>\n           ");
         } 
        ___ViewO.push("\n      </tbody>\n    </table>\n    ");
         } else { 
        ___ViewO.push("\n      <p>... no permissions ...</p>\n    ");
         } 
        ___ViewO.push("\n\n    <h3>Set permission</h3>\n    <form action=\"#/permissions\" method=\"put\">\n      <table class=\"form\">\n        <tr>\n");
         if (mode == 'vhost') { 
        ___ViewO.push("\n          <th>User</th>\n          <td>\n            <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(parent.name) )));
        ___ViewO.push("\"/>\n            <select name=\"username\">\n              ");
         for (var i = 0; i < users.length; i++) { 
        ___ViewO.push("\n              <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(users[i].name) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(users[i].name) )));
        ___ViewO.push("</option>\n              ");
         } 
        ___ViewO.push("\n            </select>\n          </td>\n");
         } else { 
        ___ViewO.push("\n          <th><label>Virtual Host:</label></th>\n          <td>\n            <input type=\"hidden\" name=\"username\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(parent.name) )));
        ___ViewO.push("\"/>\n            <select name=\"vhost\">\n              ");
         for (var i = 0; i < vhosts.length; i++) { 
        ___ViewO.push("\n              <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("</option>\n              ");
         } 
        ___ViewO.push("\n            </select>\n          </td>\n");
         } 
        ___ViewO.push("\n        </tr>\n        <tr>\n          <th><label>Configure regexp:</label></th>\n          <td><input type=\"text\" name=\"configure\" value=\".*\"/></td>\n        </tr>\n        <tr>\n          <th><label>Write regexp:</label></th>\n          <td><input type=\"text\" name=\"write\" value=\".*\"/></td>\n        </tr>\n        <tr>\n          <th><label>Read regexp:</label></th>\n          <td><input type=\"text\" name=\"read\" value=\".*\"/></td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Set permission\"/>\n    </form>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["policies"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Policies</h1>\n<div class=\"section\" id=\"user-policies\">\n  <h2>User policies</h2>\n  <div class=\"hider\">\n");
        ___ViewO.push((EJS.Scanner.to_text( filter_ui(policies) )));
        ___ViewO.push("\n  <div class=\"updatable\">\n");
         if (policies.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n <thead>\n  <tr>\n");
         if (display.vhosts) { 
        ___ViewO.push("\n    <th>Virtual Host</th>\n");
         } 
        ___ViewO.push("\n    <th>Name</th>\n    <th>Pattern</th>\n    <th>Apply to</th>\n    <th>Definition</th>\n    <th>Priority</th>\n  </tr>\n </thead>\n <tbody>\n");
        
 for (var i = 0; i < policies.length; i++) {
    var policy = policies[i];
        ___ViewO.push("\n   <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n");
         if (display.vhosts) { 
        ___ViewO.push("\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.vhost) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (ac.isPolicyMakerUser()) { 
        ___ViewO.push("\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_policy(policy.vhost, policy.name) )));
        ___ViewO.push("</td>\n");
         } else { 
        ___ViewO.push("\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.name) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.pattern) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy['apply-to']) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_table_short(policy.definition) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.priority) )));
        ___ViewO.push("</td>\n   </tr>\n");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no policies ...</p>\n");
         } 
        ___ViewO.push("\n  </div>\n  </div>\n</div>\n\n");
         if (ac.isPolicyMakerUser() && ac.canAccessVhosts()) { 
        ___ViewO.push("\n\n<div class=\"section-hidden\">\n  <h2>Add / update a policy</h2>\n  <div class=\"hider\">\n    <form action=\"#/policies\" method=\"put\">\n      <table class=\"form\">\n");
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
        ___ViewO.push("\n        <tr>\n          <th><label>Name:</label></th>\n          <td><input type=\"text\" name=\"name\"/><span class=\"mand\">*</span></td>\n        </tr>\n        <tr>\n          <th><label>Pattern:</label></th>\n          <td><input type=\"text\" name=\"pattern\"/><span class=\"mand\">*</span></td>\n        </tr>\n        <tr>\n          <th><label>Apply to:</label></th>\n          <td>\n            <select name=\"apply-to\">\n              <option value=\"all\">Exchanges and queues</option>\n              <option value=\"exchanges\">Exchanges</option>\n              <option value=\"queues\">Queues</option>\n              ");
         for (const [typename, type_config] of Object.entries(QUEUE_TYPE)) { 
        ___ViewO.push("\n                  ");
         if (typename != "default" && type_config.policy_apply_to ) { 
        ___ViewO.push("\n              <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( type_config.policy_apply_to )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( type_config.label )));
        ___ViewO.push(" Queues</option>\n                  ");
         } 
        ___ViewO.push("\n              ");
         } 
        ___ViewO.push("\n            </select>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Priority:</label></th>\n          <td><input type=\"text\" name=\"priority\"/></td>\n        </tr>\n        <tr>\n          <th><label>Definition:</label></th>\n          <td>\n            <div class=\"multifield\" id=\"definition\"></div>\n            <table class=\"argument-links\">\n              <tr>\n                  <td>Queues [All types]</td>\n                <td>\n                  <span class=\"argument-link\" field=\"definition\" key=\"max-length\" type=\"number\">Max length</span> |\n                  <span class=\"argument-link\" field=\"definition\" key=\"max-length-bytes\" type=\"number\">Max length bytes</span> |\n                  <span class=\"argument-link\" field=\"definition\" key=\"overflow\" type=\"string\">Overflow behaviour</span> <span class=\"help\" id=\"queue-overflow\"></span> |\n                  <span class=\"argument-link\" field=\"definition\" key=\"expires\" type=\"number\">Auto expire</span> </br>\n                  <span class=\"argument-link\" field=\"definition\" key=\"dead-letter-exchange\" type=\"string\">Dead letter exchange</span> |\n                  <span class=\"argument-link\" field=\"definition\" key=\"dead-letter-routing-key\" type=\"string\">Dead letter routing key</span><br/>\n                  <span class=\"argument-link\" field=\"definition\" key=\"message-ttl\" type=\"number\">Message TTL</span><span class=\"help\" id=\"queue-message-ttl\"></span> |\n                  <span class=\"argument-link\" field=\"definition\" key=\"consumer-timeout\" type=\"number\">Consumer Timeout</span><span class=\"help\" id=\"queue-consumer-timeout\"></span> |\n                  <span class=\"argument-link\" field=\"definition\" key=\"queue-leader-locator\" type=\"string\">Leader locator</span><span class=\"help\" id=\"queue-leader-locator\"></span></br>\n                </td>\n                ");
         for (const [typename, type_config] of Object.entries(QUEUE_TYPE)) { 
        ___ViewO.push("\n                    ");
         if (typename != "default" && type_config.tmpl.user_policy_arguments) { 
        ___ViewO.push("\n                        ");
        ___ViewO.push((EJS.Scanner.to_text( format(type_config.tmpl.user_policy_arguments, {}) )));
        ___ViewO.push("\n                  ");
         } 
        ___ViewO.push("\n                ");
         } 
        ___ViewO.push("\n              <tr>\n                <td>Streams</td>\n                <td>\n                  <span class=\"argument-link\" field=\"definition\" key=\"max-age\" type=\"string\">Max age</span>\n                  <span class=\"help\" id=\"queue-max-age\"></span> |\n                  <span class=\"argument-link\" field=\"definition\" key=\"stream-filter-size-bytes\" type=\"number\">Filter size in bytes. Valid range: 16-255</span>\n                  <span class=\"help\" id=\"queue-stream-filter-size-bytes\"></span> |\n                </td>\n              </tr>\n              <tr>\n                <td>Exchanges</td>\n                <td>\n                  <span class=\"argument-link\" field=\"definition\" key=\"alternate-exchange\" type=\"string\">Alternate exchange</span>\n                  <span class=\"help\" id=\"exchange-alternate\"></span>\n                </td>\n              </tr>\n              <tr>\n                <td>Federation</td>\n                <td>\n                  <span class=\"argument-link\" field=\"definition\" key=\"federation-upstream-set\" type=\"string\">Federation upstream set</span> <span class=\"help\" id=\"policy-federation-upstream-set\"></span> |\n                  <span class=\"argument-link\" field=\"definition\" key=\"federation-upstream\" type=\"string\">Federation upstream</span>\n                  <span class=\"help\" id=\"policy-federation-upstream\"></span>\n                </td>\n              </tr>\n            </table>\n          </td>\n          <td class=\"t\"><span class=\"mand\">*</span></td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Add / update policy\"/>\n    </form>\n  </div>\n</div>\n");
         } 
        ___ViewO.push("\n\n\n<div class=\"section\" id=\"operator-policies\">\n  <h2>Operator policies</h2>\n  <div class=\"hider\">\n");
        ___ViewO.push((EJS.Scanner.to_text( filter_ui(operator_policies) )));
        ___ViewO.push("\n  <div class=\"updatable\">\n");
         if (operator_policies.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n <thead>\n  <tr>\n");
         if (display.vhosts) { 
        ___ViewO.push("\n    <th>Virtual Host</th>\n");
         } 
        ___ViewO.push("\n    <th>Name</th>\n    <th>Pattern</th>\n    <th>Apply to</th>\n    <th>Definition</th>\n    <th>Priority</th>\n");
         if (ac.isAdministratorUser() && is_op_policy_updating_enabled) { 
        ___ViewO.push("\n    <th class=\"administrator-only\">Clear</th>\n");
         } 
        ___ViewO.push("\n  </tr>\n </thead>\n <tbody>\n");
        
 for (var i = 0; i < operator_policies.length; i++) {
    var policy = operator_policies[i];
        ___ViewO.push("\n   <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n");
         if (display.vhosts) { 
        ___ViewO.push("\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.vhost) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.name) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.pattern) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy['apply-to']) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_table_short(policy.definition) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.priority) )));
        ___ViewO.push("</td>\n");
         if (ac.isAdministratorUser && is_op_policy_updating_enabled) { 
        ___ViewO.push("\n     <td class=\"administrator-only\">\n        <form action=\"#/operator_policies\" method=\"delete\" class=\"confirm\">\n            <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.name) )));
        ___ViewO.push("\"/>\n            <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.vhost) )));
        ___ViewO.push("\"/>\n            <input type=\"submit\" value=\"Clear\"/>\n        </form>\n      </td>\n");
         } 
        ___ViewO.push("\n   </tr>\n");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no policies ...</p>\n");
         } 
        ___ViewO.push("\n  </div>\n  </div>\n</div>\n\n");
         if (ac.isAdministratorUser() && ac.canAccessVhosts() > 0 && is_op_policy_updating_enabled) { 
        ___ViewO.push("\n\n<div class=\"section-hidden\">\n  <h2>Add / update an operator policy</h2>\n  <div class=\"hider\">\n    <form action=\"#/operator_policies\" method=\"put\">\n      <table class=\"form\">\n");
         if (display.vhosts) { 
        ___ViewO.push("\n        <tr>\n          <th><label>Virtual host:</label></th>\n          <td>\n            <select name=\"vhost\">\n              ");
         for (var i = 0; i < vhosts.length; i++) { 
        ___ViewO.push("\n              <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("</option>\n              ");
         } 
        ___ViewO.push("\n            </select>\n          </td>\n        </tr>\n");
         } else { 
        ___ViewO.push("\n        <tr><td><input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[0].name) )));
        ___ViewO.push("\"/></td></tr>\n");
         } 
        ___ViewO.push("\n        <tr>\n          <th><label>Name:</label></th>\n          <td><input type=\"text\" name=\"name\"/><span class=\"mand\">*</span></td>\n        </tr>\n        <tr>\n          <th><label>Pattern:</label></th>\n          <td><input type=\"text\" name=\"pattern\"/><span class=\"mand\">*</span></td>\n        </tr>\n        <tr>\n          <th><label>Apply to:</label></th>\n          <td>\n            <select name=\"apply-to\">\n              <option value=\"queues\">Queues</option>\n              ");
         for (const [typename, type_config] of Object.entries(QUEUE_TYPE)) { 
        ___ViewO.push("\n                  ");
         if (typename != "default"  && type_config.policy_apply_to  ) { 
        ___ViewO.push("\n                      <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( type_config.policy_apply_to )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( type_config.label )));
        ___ViewO.push(" Queues</option>\n                  ");
         } 
        ___ViewO.push("\n              ");
         } 
        ___ViewO.push("\n            </select>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Priority:</label></th>\n          <td><input type=\"text\" name=\"priority\"/></td>\n        </tr>\n        <tr>\n          <th><label>Definition:</label></th>\n          <td>\n            <div class=\"multifield\" id=\"definitionop\"></div>\n            <table class=\"argument-links\">\n                ");
         for (const [typename, type_config] of Object.entries(QUEUE_TYPE)) { 
        ___ViewO.push("\n                    ");
         if (typename != "default" && type_config.tmpl.operator_policy_arguments) { 
        ___ViewO.push("\n                        ");
        ___ViewO.push((EJS.Scanner.to_text( format(type_config.tmpl.operator_policy_arguments, {}) )));
        ___ViewO.push("\n                    ");
         } 
        ___ViewO.push("\n                ");
         } 
        ___ViewO.push("\n            </table>\n          </td>\n          <td class=\"t\"><span class=\"mand\">*</span></td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Add / update operator policy\"/>\n    </form>\n  </div>\n</div>\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["policy"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Policy: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.name) )));
        ___ViewO.push("</b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_maybe_vhost(policy.vhost) )));
        ___ViewO.push("</h1>\n\n<div class=\"section\">\n  <h2>Overview</h2>\n  <div class=\"hider\">\n    <table class=\"facts\">\n      <tr>\n        <th>Pattern</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.pattern) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Apply to</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy['apply-to']) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Definition</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_table_short(policy.definition) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Priority</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.priority) )));
        ___ViewO.push("</td>\n      </tr>\n    </table>\n  </div>\n</div>\n\n<div class=\"section-hidden\">\n  <h2>Delete this policy</h2>\n  <div class=\"hider\">\n    <form action=\"#/policies\" method=\"delete\" class=\"confirm\">\n      <input type=\"hidden\" name=\"component\" value=\"policy\"/>\n      <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.vhost) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(policy.name) )));
        ___ViewO.push("\"/>\n      <input type=\"submit\" value=\"Delete this policy\"/>\n    </form>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["popup"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<div class=\"form-popup-");
        ___ViewO.push((EJS.Scanner.to_text( type )));
        ___ViewO.push("\">\n  ");
        ___ViewO.push((EJS.Scanner.to_text( text )));
        ___ViewO.push("\n  <br/>\n  <br/>\n  <span id=\"close\">Close</span>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["publish"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<div class=\"section-hidden\">\n  <h2>Publish message</h2>\n  <div class=\"hider\">\n    <form action=\"#/exchanges/publish\" method=\"post\">\n");
         if (mode == 'queue') { 
        ___ViewO.push("\n      <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.vhost) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"name\" value=\"amq.default\"/>\n");
         } else { 
        ___ViewO.push("\n      <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(exchange.vhost) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_exchange_url(exchange.name) )));
        ___ViewO.push("\"/>\n");
         } 
        ___ViewO.push("\n      <input type=\"hidden\" name=\"properties\" value=\"\"/>\n      <table class=\"form\">\n");
         if (mode == 'queue') { 
        ___ViewO.push("\n        <tr>\n          <td colspan=\"2\"><input type=\"hidden\" name=\"routing_key\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.name) )));
        ___ViewO.push("\"/> Message will be published to the default exchange with routing key <strong>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.name) )));
        ___ViewO.push("</strong>, routing it to this queue.</td>\n        </tr>\n");
         } else { 
        ___ViewO.push("\n        <tr>\n          <th><label>Routing key:</label></th>\n          <td><input type=\"text\" name=\"routing_key\" value=\"\"/></td>\n        </tr>\n");
         } 
        ___ViewO.push("\n        ");
         if (mode == 'queue' && is_classic(queue)) { 
        ___ViewO.push("\n        <tr>\n          <th><label>Delivery mode:</label></th>\n          <td>\n            <select name=\"delivery_mode\">\n              <option value=\"1\">1 - Non-persistent</option>\n              <option value=\"2\">2 - Persistent</option>\n            </select>\n          </td>\n        </tr>\n        ");
         } else { 
        ___ViewO.push("\n          <input type=\"hidden\" name=\"delivery_mode\" value=\"2\">\n        ");
         } 
        ___ViewO.push("\n        <tr>\n          <th>\n            <label>\n              Headers:\n              <span class=\"help\" id=\"message-publish-headers\"></span>\n            </label>\n          </th>\n          <td>\n            <div class=\"multifield\" id=\"headers\"></div>\n          </td>\n        </tr>\n        <tr>\n          <th>\n            <label>\n              Properties:\n              <span class=\"help\" id=\"message-publish-properties\"></span>\n            </label>\n          </th>\n          <td>\n            <div class=\"multifield string-only\" id=\"props\"></div>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Payload:</label></th>\n          <td><textarea name=\"payload\"></textarea></td>\n        </tr>\n        <tr>\n          <th><label>Payload encoding:</label></th>\n          <td>\n            <select name=\"payload_encoding\">\n              <option value=\"string\" selected>String (default)</option>\n              <option value=\"base64\">Base64</option>\n            </select>\n          </td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Publish message\" />\n    </form>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["queue"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Queue <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(highlight_extra_whitespace(queue.name)) )));
        ___ViewO.push("</b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_maybe_vhost(queue.vhost) )));
        ___ViewO.push("</h1>\n\n<div class=\"section\">\n  <h2>Overview</h2>\n");
         if(!disable_stats) { 
        ___ViewO.push("\n  <div class=\"hider updatable\">\n    ");
        ___ViewO.push((EJS.Scanner.to_text( queue_lengths('lengths-q', queue) )));
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( message_rates('msg-rates-q', queue.message_stats) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n\n    <h3>Details</h3>\n    <table class=\"facts facts-l\" id=\"details-queue-table\">\n      <tr>\n        <th>Features</th>\n        <td id=\"details-queue-features\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_features(queue) )));
        ___ViewO.push("</td>\n      </tr>\n");
         if(!disable_stats) { 
        ___ViewO.push("\n      <tr>\n        <th>Policy</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_policy(queue.vhost, queue.policy) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Operator policy</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.operator_policy, '') )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         if (queue.owner_pid_details != undefined) { 
        ___ViewO.push("\n        <tr>\n          <th>Exclusive owner</th>\n          <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_conn(queue.owner_pid_details.name) )));
        ___ViewO.push("</td>\n        </tr>\n      ");
         } 
        ___ViewO.push("\n      <tr>\n        <th>Effective policy definition</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_table_short(queue.effective_policy_definition) )));
        ___ViewO.push("</td>\n      </tr>\n");
         } 
        ___ViewO.push("\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n   ");
        ___ViewO.push((EJS.Scanner.to_text( format(QUEUE_TYPE(queue).tmpl.node_details, {queue: queue}) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n    </table>\n\n    ");
         if(!disable_stats) { 
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( format(QUEUE_TYPE(queue).tmpl.stats, {queue: queue}) )));
        ___ViewO.push("\n    ");
         } 
        ___ViewO.push("\n  </div>\n</div>\n\n");
         if (rates_mode == 'detailed') { 
        ___ViewO.push("\n<div class=\"section-hidden\">\n<h2>Message rates breakdown</h2>\n<div class=\"hider updatable\">\n<table class=\"two-col-layout\">\n  <tr>\n    <td>\n      ");
        ___ViewO.push((EJS.Scanner.to_text( format('msg-detail-publishes',
                 {'mode':   'queue',
                  'object': queue.incoming,
                  'label':  'Incoming'}) )));
        ___ViewO.push("\n\n    </td>\n    <td>\n      ");
        ___ViewO.push((EJS.Scanner.to_text( format('msg-detail-deliveries',
                 {'mode':   'queue',
                  'object': queue.deliveries}) )));
        ___ViewO.push("\n    </td>\n  </tr>\n</table>\n</div>\n</div>\n\n");
         } 
        ___ViewO.push("\n\n");
         if(!disable_stats) { 
        ___ViewO.push("\n");
        ___ViewO.push((EJS.Scanner.to_text( maybe_format_extra_queue_content(queue, extra_content) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n\n");
         if(!disable_stats) { 
        ___ViewO.push("\n<div class=\"section-hidden\" id=\"queue-consumers-section\">\n  <h2 class=\"updatable\">Consumers (");
        ___ViewO.push((EJS.Scanner.to_text((queue.consumer_details.length))));
        ___ViewO.push(") </h2>\n  <div class=\"hider updatable\">\n");
        ___ViewO.push((EJS.Scanner.to_text( format('consumers', {'mode': 'queue', 'consumers': queue.consumer_details}) )));
        ___ViewO.push("\n  </div>\n</div>\n");
         } 
        ___ViewO.push("\n\n<div class=\"section-hidden\">\n  <h2 class=\"updatable\">Bindings (");
        ___ViewO.push((EJS.Scanner.to_text((bindings.length))));
        ___ViewO.push(") </h2>\n  <div class=\"hider\">\n    <div class=\"bindings-wrapper\">\n      ");
        ___ViewO.push((EJS.Scanner.to_text( format('bindings', {'mode': 'queue', 'bindings': bindings}) )));
        ___ViewO.push("\n      <p class=\"arrow\">&dArr;</p>\n      <p><span class=\"queue\">This queue</span></p>\n\n      ");
        ___ViewO.push((EJS.Scanner.to_text( format('add-binding', {'mode': 'queue', 'parent': queue}) )));
        ___ViewO.push("\n    </div>\n  </div>\n</div>\n\n");
        ___ViewO.push((EJS.Scanner.to_text( format('publish', {'mode': 'queue', 'queue': queue}) )));
        ___ViewO.push("\n\n");
         if (QUEUE_TYPE(queue).actions.get_message) { 
        ___ViewO.push("\n  ");
        ___ViewO.push((EJS.Scanner.to_text( format((QUEUE_TYPE(queue).tmpl && QUEUE_TYPE(queue).tmpl.get_message) || "classic-queue-get-message", {queue: queue}) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n\n");
         if (is_user_policymaker) { 
        ___ViewO.push("\n<div class=\"section-hidden\">\n  <h2>Move messages</h2>\n  <div class=\"hider\">\n  ");
         if (NAVIGATION['Admin'][0]['Shovel Management'] == undefined) { 
        ___ViewO.push("\n    <p>To move messages, the shovel plugin must be enabled, try:</p>\n    <pre>$ rabbitmq-plugins enable rabbitmq_shovel rabbitmq_shovel_management</pre>\n  ");
         } else { 
        ___ViewO.push("\n    <p>\n      The shovel plugin can be used to move messages from this queue\n      to another one. The form below will create a temporary shovel to\n      move messages to another queue on the same virtual host, with\n      default settings.\n    </p>\n    <p>\n      For more options <a href=\"#/dynamic-shovels\">see the shovel\n      interface</a>.\n    </p>\n    <form action=\"#/shovel-parameters-move-messages\" method=\"put\">\n      <input type=\"hidden\" name=\"component\" value=\"shovel\"/>\n      <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.vhost) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"name\" value=\"Move from ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.name) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"src-uri\" value=\"amqp:///");
        ___ViewO.push((EJS.Scanner.to_text( esc(queue.vhost) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"src-queue\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.name) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"src-protocol\" value=\"amqp091\"/>\n      <input type=\"hidden\" name=\"src-prefetch-count\" value=\"1000\"/>\n      <input type=\"hidden\" name=\"src-delete-after\" value=\"queue-length\"/>\n      <input type=\"hidden\" name=\"dest-protocol\" value=\"amqp091\"/>\n      <input type=\"hidden\" name=\"dest-uri\" value=\"amqp:///");
        ___ViewO.push((EJS.Scanner.to_text( esc(queue.vhost) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"dest-add-forward-headers\" value=\"false\"/>\n      <input type=\"hidden\" name=\"ack-mode\" value=\"on-confirm\"/>\n      ");
         if (is_stream(queue)) { 
        ___ViewO.push("\n        <input type=\"hidden\" name=\"src-consumer-args-stream-offset\" value=\"first\"/>\n      ");
         } 
        ___ViewO.push("\n      <input type=\"hidden\" name=\"redirect\" value=\"#/queues\"/>\n\n      <table class=\"form\">\n        <tr>\n          <th>Destination queue:</th>\n          <td><input type=\"text\" name=\"dest-queue\"/></td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Move messages\"/>\n    </form>\n  ");
         } 
        ___ViewO.push("\n  </div>\n</div>\n");
         } 
        ___ViewO.push("\n\n");
         if (!is_internal(queue)) { 
        ___ViewO.push("\n<div class=\"section-hidden\" id=\"delete\">\n  <h2>Delete</h2>\n  <div class=\"hider\">\n    <form action=\"#/queues\" method=\"delete\" class=\"confirm-queue inline-form\">\n      <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.vhost) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.name) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"mode\" value=\"delete\"/>\n      <input type=\"submit\" value=\"Delete Queue\" />\n    </form>\n  </div>\n</div>\n");
         } 
        ___ViewO.push("\n\n");
         if (QUEUE_TYPE(queue).actions.purge) { 
        ___ViewO.push("\n<div class=\"section-hidden\">\n  <h2>Purge</h2>\n  <div class=\"hider\">\n    <form action=\"#/queues\" method=\"delete\" class=\"confirm-purge-queue inline-form\">\n      <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.vhost) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.name) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"mode\" value=\"purge\"/>\n      <input type=\"submit\" value=\"Purge Messages\" />\n    </form>\n  </div>\n</div>\n");
         } 
        ___ViewO.push("\n\n");
         if(queue.reductions || queue.garbage_collection) { 
        ___ViewO.push("\n<div class=\"section-hidden\">\n<h2>Runtime Metrics (Advanced)</h2>\n <div class=\"hider updatable\">\n ");
        ___ViewO.push((EJS.Scanner.to_text( data_reductions('reductions-rates-queue', queue) )));
        ___ViewO.push("\n <table class=\"facts\">\n    ");
         if (queue.garbage_collection.min_bin_vheap_size) { 
        ___ViewO.push("\n        <tr>\n        <th>Minimum binary virtual heap size in words (min_bin_vheap_size)</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( queue.garbage_collection.min_bin_vheap_size )));
        ___ViewO.push("</td>\n        </tr>\n    ");
         } 
        ___ViewO.push("\n\n    ");
         if (queue.garbage_collection.min_heap_size) { 
        ___ViewO.push("\n        <tr>\n        <th>Minimum heap size in words (min_heap_size)</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( queue.garbage_collection.min_heap_size )));
        ___ViewO.push("</td>\n        </tr>\n    ");
         } 
        ___ViewO.push("\n\n    ");
         if (queue.garbage_collection.fullsweep_after) { 
        ___ViewO.push("\n        <tr>\n        <th>Maximum generational collections before fullsweep (fullsweep_after)</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( queue.garbage_collection.fullsweep_after )));
        ___ViewO.push("</td>\n        </tr>\n    ");
         } 
        ___ViewO.push("\n\n    ");
         if (queue.garbage_collection.minor_gcs) { 
        ___ViewO.push("\n        <tr>\n        <th>Number of minor GCs (minor_gcs)</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( queue.garbage_collection.minor_gcs )));
        ___ViewO.push("</td>\n        </tr>\n    ");
         } 
        ___ViewO.push("\n </table>\n </div>\n</div>\n\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["queues"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("\n<h1>Queues</h1>\n<div class=\"section\" id=\"queues-paging-section\">\n  ");
        ___ViewO.push((EJS.Scanner.to_text( paginate_ui(queues, 'queues') )));
        ___ViewO.push("\n</div>\n<div class=\"updatable\" id=\"queues-table-section\">\n");
         if (queues.items.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n <thead>\n  <tr>\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('queues', 'Overview', [display.vhosts, display.nodes, true]) )));
        ___ViewO.push("\n");
         if(disable_stats && enable_queue_totals) { 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('queues', 'Messages', []) )));
        ___ViewO.push("\n");
         } else { 
        ___ViewO.push("\n");
         if(!disable_stats) { 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('queues', 'Messages', []) )));
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('queues', 'Message bytes', []) )));
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('queues', 'Message rates', []) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n    <th class=\"plus-minus\"><span class=\"popup-options-link\" title=\"Click to change columns\" type=\"columns\" for=\"queues\">+/-</span></th>\n  </tr>\n  <tr>\n");
         if (display.vhosts) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Virtual host', 'vhost') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Name',         'name') )));
        ___ViewO.push("</th>\n");
         if (display.nodes) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Node',         'node') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'type')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Type', 'type') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'features')) { 
        ___ViewO.push("\n    <th>Features</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'features_no_policy')) { 
        ___ViewO.push("\n    <th>Features</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'policy')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Policy','policy') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'consumers')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Consumers',    'consumers') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'consumer_capacity')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Consumer capacity', 'consumer_capacity') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'state')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('State',        'state') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if(disable_stats && enable_queue_totals) { 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-ready')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Ready',        'messages_ready') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-unacked')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Unacked',      'messages_unacknowledged') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-total')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Total',        'messages') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         if(!disable_stats) { 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-ready')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Ready',        'messages_ready') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-unacked')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Unacked',      'messages_unacknowledged') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-delayed')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Delayed',      'messages_delayed') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-ram')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('In Memory',    'messages_ram') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-persistent')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Persistent',   'messages_persistent') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-total')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Total',        'messages') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msg-bytes-ready')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Ready',        'message_bytes_ready') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msg-bytes-unacked')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Unacked',      'message_bytes_unacknowledged') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msg-bytes-ram')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('In Memory',    'message_bytes_ram') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msg-bytes-persistent')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Persistent',   'message_bytes_persistent') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msg-bytes-total')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Total',        'message_bytes') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n  ");
         if (show_column('queues', 'rate-incoming')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('incoming', 'message_stats.publish_details.rate') )));
        ___ViewO.push("</th>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('queues', 'rate-deliver')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('deliver / get', 'message_stats.deliver_get_details.rate') )));
        ___ViewO.push("</th>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('queues', 'rate-redeliver')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('redelivered', 'message_stats.redeliver_details.rate') )));
        ___ViewO.push("</th>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('queues', 'rate-ack')) { 
        ___ViewO.push("\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('ack', 'message_stats.ack_details.rate') )));
        ___ViewO.push("</th>\n  ");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n  </tr>\n </thead>\n <tbody>\n");
        
  for (var i = 0; i < queues.items.length; i++) {
    var queue = queues.items[i];
        ___ViewO.push("\n  <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i, queue.arguments) )));
        ___ViewO.push(">\n");
         if (display.vhosts) { 
        ___ViewO.push("\n   <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.vhost) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n   <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_queue(queue.vhost, queue.name, queue.arguments) )));
        ___ViewO.push("</td>\n");
         if (display.nodes) { 
        ___ViewO.push("\n   <td>\n     ");
         if (queue.node) { 
        ___ViewO.push("\n      ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(queue.node) )));
        ___ViewO.push("\n     ");
         } else { 
        ___ViewO.push("\n      ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(queue.leader) )));
        ___ViewO.push("\n     ");
         } 
        ___ViewO.push("\n     ");
         if (queue.hasOwnProperty('members')) { 
        ___ViewO.push("\n      ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_members(queue) )));
        ___ViewO.push("\n     ");
         } 
        ___ViewO.push("\n   </td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'type')) { 
        ___ViewO.push("\n   <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.type, '') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'features')) { 
        ___ViewO.push("\n   <td class=\"c\">\n     ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_features_short(queue) )));
        ___ViewO.push("\n     ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_policy_short(queue) )));
        ___ViewO.push("\n     ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_op_policy_short(queue) )));
        ___ViewO.push("\n   </td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'features_no_policy')) { 
        ___ViewO.push("\n   <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_features_short(queue) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'policy')) { 
        ___ViewO.push("\n   <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( link_policy(queue.vhost, queue.policy) )));
        ___ViewO.push("\n                 ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.operator_policy) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'consumers')) { 
        ___ViewO.push("\n   <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.consumers) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'consumer_capacity')) { 
        ___ViewO.push("\n   <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_percent(queue.consumer_capacity) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'state')) { 
        ___ViewO.push("\n   <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_object_state(queue) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if(!disable_stats || (disable_stats && enable_queue_totals)) { 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-ready')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_ready) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-unacked')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_unacknowledged) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         if(!disable_stats) { 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-delayed')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_delayed) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-ram')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_ram) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-persistent')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_persistent) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         if(!disable_stats || (disable_stats && enable_queue_totals)) { 
        ___ViewO.push("\n");
         if (show_column('queues', 'msgs-total')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         if(!disable_stats) { 
        ___ViewO.push("\n");
         if (show_column('queues', 'msg-bytes-ready')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes_ready) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msg-bytes-unacked')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes_unacknowledged) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msg-bytes-ram')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes_ram) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msg-bytes-persistent')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes_persistent) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('queues', 'msg-bytes-total')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n  ");
         if (show_column('queues', 'rate-incoming')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(queue.message_stats, 'publish') )));
        ___ViewO.push("</td>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('queues', 'rate-deliver')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(queue.message_stats, 'deliver_get') )));
        ___ViewO.push("</td>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('queues', 'rate-redeliver')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(queue.message_stats, 'redeliver') )));
        ___ViewO.push("</td>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('queues', 'rate-ack')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(queue.message_stats, 'ack') )));
        ___ViewO.push("</td>\n  ");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n  </tr>\n  ");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no queues ...</p>\n");
         } 
        ___ViewO.push("\n  </div>\n  </div>\n</div>\n\n");
         if (ac.canAccessVhosts()) { 
        ___ViewO.push("\n<div class=\"section-hidden\" id=\"add-new-queue\">\n  <h2>Add a new queue</h2>\n  <div class=\"hider\">\n    <form action=\"#/queues\" method=\"put\">\n      <table class=\"form\">\n        <tr>\n          <th><label>Type:</label></th>\n          <td>\n            <select name=\"queuetype\">\n                <option value=\"default\">Default for virtual host</option>\n                ");
         for (const [typename, type_config] of Object.entries(QUEUE_TYPE)) { 
        ___ViewO.push("\n                  ");
         if (typename != "default" && type_config.tmpl.arguments) { 
        ___ViewO.push("\n                  ");
         if (queue_type == typename) { 
        ___ViewO.push("\n                      <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( typename)));
        ___ViewO.push("\" selected>");
        ___ViewO.push((EJS.Scanner.to_text( type_config["label"])));
        ___ViewO.push("</option>\n                  ");
         } else { 
        ___ViewO.push("\n                      <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( typename)));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( type_config["label"])));
        ___ViewO.push("</option>\n                  ");
         } 
        ___ViewO.push("\n                  ");
         } 
        ___ViewO.push("\n                ");
         } 
        ___ViewO.push("\n            </select>\n          </td>\n        </tr>\n");
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
        ___ViewO.push("\n        <tr>\n          <th><label>Name:</label></th>\n          <td><input type=\"text\" name=\"name\"/><span class=\"mand\">*</span></td>\n        </tr>\n");
         if (queue_type == "classic" || queue_type == "default") { 
        ___ViewO.push("\n        <tr>\n          <th><label>Durability:</label></th>\n          <td>\n            <select name=\"durable\">\n              <option value=\"true\">Durable</option>\n              <option value=\"false\">Transient</option>\n            </select>\n          </td>\n        </tr>\n");
         } 
        ___ViewO.push("\n");
        
  if (ac.canListNodes()) {
   var nodes = display.data.nodes
        ___ViewO.push("\n        <tr>\n          <th><label>Node:</label></th>\n          <td>\n            <select name=\"node\">\n              ");
         for (var i = 0; i < nodes.length; i++) { 
        ___ViewO.push("\n              <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(nodes[i].name) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(nodes[i].name) )));
        ___ViewO.push("</option>\n              ");
         } 
        ___ViewO.push("\n            </select>\n          </td>\n        </tr>\n");
         } 
        ___ViewO.push("\n");
         if (queue_type == "classic") { 
        ___ViewO.push("\n        <tr>\n          <th><label>Auto delete: <span class=\"help\" id=\"queue-auto-delete\"></span></label></th>\n          <td>\n            <select name=\"auto_delete\">\n              <option value=\"false\">No</option>\n              <option value=\"true\">Yes</option>\n            </select>\n          </td>\n        </tr>\n        ");
         } 
        ___ViewO.push("\n        <tr>\n          <th><label>Arguments:</label></th>\n          <td>\n            <div class=\"multifield\" id=\"arguments\"></div>\n            <table class=\"argument-links\">\n              <tr>\n                <td>Add</td>\n                <td>\n                        ");
        ___ViewO.push((EJS.Scanner.to_text( format(QUEUE_TYPE[queue_type].tmpl['arguments'], {}) )));
        ___ViewO.push("\n                </td>\n              </tr>\n            </table>\n          </td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Add queue\"/>\n    </form>\n  </div>\n  ");
         } 
        ___ViewO.push("\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["quorum-queue-arguments"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<span class=\"argument-link\" field=\"arguments\" key=\"x-expires\" type=\"number\">Auto expire</span> <span class=\"help\" id=\"queue-expires\"></span> |\n<span class=\"argument-link\" field=\"arguments\" key=\"x-message-ttl\" type=\"number\">Message TTL</span> <span class=\"help\" id=\"queue-message-ttl\"></span> |\n<span class=\"argument-link\" field=\"arguments\" key=\"x-overflow\" type=\"string\">Overflow behaviour</span> <span class=\"help\" id=\"quorum-queue-overflow\"></span><br/>\n<span class=\"argument-link\" field=\"arguments\" key=\"x-single-active-consumer\" type=\"boolean\">Single active consumer</span> <span class=\"help\" id=\"queue-single-active-consumer\"></span> |\n<span class=\"argument-link\" field=\"arguments\" key=\"x-dead-letter-exchange\" type=\"string\">Dead letter exchange</span> <span class=\"help\" id=\"queue-dead-letter-exchange\"></span> |\n<span class=\"argument-link\" field=\"arguments\" key=\"x-dead-letter-routing-key\" type=\"string\">Dead letter routing key</span> <span class=\"help\" id=\"queue-dead-letter-routing-key\"></span><br/>\n<span class=\"argument-link\" field=\"arguments\" key=\"x-max-length\" type=\"number\">Max length</span> <span class=\"help\" id=\"queue-max-length\"></span> |\n<span class=\"argument-link\" field=\"arguments\" key=\"x-max-length-bytes\" type=\"number\">Max length bytes</span> <span class=\"help\" id=\"queue-max-length-bytes\"></span>\n| <span class=\"argument-link\" field=\"arguments\" key=\"x-delivery-limit\" type=\"number\">Delivery limit</span><span class=\"help\" id=\"delivery-limit\"></span>\n| <span class=\"argument-link\" field=\"arguments\" key=\"x-quorum-initial-group-size\" type=\"number\">Initial cluster size</span><span class=\"help\" id=\"queue-initial-cluster-size\"></span><br/>\n| <span class=\"argument-link\" field=\"arguments\" key=\"x-quorum-target-group-size\" type=\"number\">Target cluster size</span> <span class=\"help\" id=\"quorum-queue-target-group-size\"></span>\n  | <span class=\"argument-link\" field=\"arguments\" key=\"x-dead-letter-strategy\" type=\"string\">Dead letter strategy</span><span class=\"help\" id=\"queue-dead-letter-strategy\"></span>\n| <span class=\"argument-link\" field=\"arguments\" key=\"x-queue-leader-locator\" type=\"string\">Leader locator</span><span class=\"help\" id=\"queue-leader-locator\"></span>\n| <span class=\"argument-link\" field=\"arguments\" key=\"x-consumer-disconnected-timeout\" type=\"number\">Consumer disconnected timeout</span><span class=\"help\" id=\"queue-consumer-disconnected-timeout\"></span><br/>\n| <span class=\"argument-link\" field=\"arguments\" key=\"x-delayed-retry-type\" type=\"string\">Delayed retry type</span><span class=\"help\" id=\"queue-delayed-retry-type\"></span>\n| <span class=\"argument-link\" field=\"arguments\" key=\"x-delayed-retry-min\" type=\"number\">Delayed retry min</span><span class=\"help\" id=\"queue-delayed-retry-min\"></span>\n| <span class=\"argument-link\" field=\"arguments\" key=\"x-delayed-retry-max\" type=\"number\">Delayed retry max</span><span class=\"help\" id=\"queue-delayed-retry-max\"></span>\n| <span class=\"argument-link\" field=\"arguments\" key=\"x-member-placement-tag\" type=\"string\">Member placement tag</span><span class=\"help\" id=\"queue-member-placement-tag\"></span>");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["quorum-queue-node-details"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("      <tr>\n        <th>Leader</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(queue.leader) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n          <th>Online</th>\n          <td>\n              ");
         for (var i in queue.online) { 
        ___ViewO.push("\n                  ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(queue.online[i]) )));
        ___ViewO.push("\n                  <br/>\n              ");
         } 
        ___ViewO.push("\n          </td>\n      </tr>\n      <th>Members</th>\n      <td>\n          ");
         for (var i in queue.members) {  
        ___ViewO.push("\n              ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(queue.members[i]) )));
        ___ViewO.push("\n              <br/>\n          ");
         } 
        ___ViewO.push("\n      </td>\n      </tr>");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["quorum-queue-operator-policy-arguments"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<tr>\n  <td>Queues [Quorum]</td>\n  <td>\n    <span class=\"argument-link\" field=\"definitionop\" key=\"delivery-limit\" type=\"number\">Delivery limit</span>\n    <span class=\"help\" id=\"delivery-limit\"></span> |\n    <span class=\"argument-link\" field=\"definitionop\" key=\"expires\" type=\"number\">Auto expire</span> |\n    <span class=\"argument-link\" field=\"definitionop\" key=\"max-in-memory-bytes\" type=\"number\">Max in-memory bytes</span> |\n    <span class=\"argument-link\" field=\"definitionop\" key=\"max-in-memory-length\" type=\"number\">Max in-memory length</span> <br>\n    <span class=\"argument-link\" field=\"definitionop\" key=\"max-length\" type=\"number\">Max length</span> |\n    <span class=\"argument-link\" field=\"definitionop\" key=\"max-length-bytes\" type=\"number\">Max length bytes</span> |\n    <span class=\"argument-link\" field=\"definitionop\" key=\"message-ttl\" type=\"number\">Message TTL</span>\n    <span class=\"help\" id=\"queue-message-ttl\"></span> |\n    <span class=\"argument-link\" field=\"definitionop\" key=\"target-group-size\" type=\"number\">Target group size</span> |\n    <span class=\"argument-link\" field=\"definitionop\" key=\"overflow\" type=\"string\">Length limit overflow behaviour</span> <span class=\"help\" id=\"queue-overflow\"></span> |</br>\n    <span class=\"argument-link\" field=\"definitionop\" key=\"member-placement-tag\" type=\"string\">Member placement tag</span>\n    <span class=\"help\" id=\"queue-member-placement-tag\"></span>\n  </td>\n</tr>");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["quorum-queue-stats"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("   <table class=\"facts facts-l\" id=\"details-queue-stats-table\">\n      <tbody>\n      <tr>\n        <th>State</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_object_state(queue) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         if(queue.consumers) { 
        ___ViewO.push("\n      <tr>\n        <th>Consumers</th>\n        <td id=\"consumers\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.consumers) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         } else if(queue.hasOwnProperty('consumer_details')) { 
        ___ViewO.push("\n      <tr>\n        <th>Consumers</th>\n        <td id=\"consumers\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.consumer_details.length) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         } 
        ___ViewO.push("\n      ");
         if(queue.hasOwnProperty('publishers')) { 
        ___ViewO.push("\n      <tr>\n        <th>Publishers</th>\n        <td id=\"publishers\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.publishers) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         } 
        ___ViewO.push("\n      <tr>\n        <th>Open files</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_table_short(queue.open_files) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         if (queue.hasOwnProperty('messages_by_priority')) { 
        ___ViewO.push("\n      <tr>\n        <th>Messages by priority</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_table_short(queue.messages_by_priority) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         } 
        ___ViewO.push("\n      ");
         if (queue.next_delayed_at) { 
        ___ViewO.push("\n      <tr>\n        <th>Next delayed retry</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_date(new Date(queue.next_delayed_at)) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         } 
        ___ViewO.push("\n      ");
         if (queue.last_delayed_at) { 
        ___ViewO.push("\n      <tr>\n        <th>Last delayed retry</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_date(new Date(queue.last_delayed_at)) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         } 
        ___ViewO.push("\n      ");
         if (queue.hasOwnProperty('delivery_limit')) { 
        ___ViewO.push("\n      <tr>\n        <th>Delivery limit <span class=\"help\" id=\"queue-delivery-limit\"></th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.delivery_limit) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         } 
        ___ViewO.push("\n    </tbody>\n    </table>\n\n    <table class=\"facts\">\n      <tr>\n        <td></td>\n        <th class=\"horizontal\">Total</th>\n        <th class=\"horizontal\">Ready</th>\n        <th class=\"horizontal\">Unacked</th>\n        <th class=\"horizontal\">Returned</th>\n        <th class=\"horizontal\">Delayed</th>\n        <th class=\"horizontal\">Dead-lettered\n        <span class=\"help\" id=\"queue-dead-lettered\"></span>\n        </th>\n      </tr>\n      <tr>\n        <th>\n          Messages\n          <span class=\"help\" id=\"queue-messages\"></span>\n        </th>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_ready) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_unacknowledged) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_ready_returned) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_delayed) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages_dlx) )));
        ___ViewO.push("\n        </td>\n      </tr>\n      <tr>\n        <th>\n          Message body bytes\n          <span class=\"help\" id=\"queue-message-body-bytes\"></span>\n        </th>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes_ready) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes_unacknowledged) )));
        ___ViewO.push("\n        </td>\n        <td class=\"r\">\n        </td>\n        <td class=\"r\">\n        </td>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.message_bytes_dlx) )));
        ___ViewO.push("\n        </td>\n      </tr>\n      <tr>\n        <th>\n          Process memory\n          <span class=\"help\" id=\"queue-process-memory\"></span>\n        </th>\n        <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.memory) )));
        ___ViewO.push("</td>\n      </tr>\n    </table>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["quorum-queue-user-policy-arguments"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<tr>\n  <td>Queues [Quorum]</td>\n  <td>\n    <span class=\"argument-link\" field=\"definition\" key=\"delivery-limit\" type=\"number\">Delivery limit</span>\n    <span class=\"help\" id=\"delivery-limit\"></span> |\n    <span class=\"argument-link\" field=\"definition\" key=\"dead-letter-strategy\" type=\"string\">Dead letter strategy</span>\n    <span class=\"help\" id=\"queue-dead-letter-strategy\"></span> |\n    <span class=\"argument-link\" field=\"definition\" key=\"consumer-disconnected-timeout\" type=\"number\">Consumer disconnected timeout</span>\n    <span class=\"help\" id=\"queue-consumer-disconnected-timeout\"></span> |<br/>\n    <span class=\"argument-link\" field=\"definition\" key=\"delayed-retry-type\" type=\"string\">Delayed retry type</span>\n    <span class=\"help\" id=\"queue-delayed-retry-type\"></span> |\n    <span class=\"argument-link\" field=\"definition\" key=\"delayed-retry-min\" type=\"number\">Delayed retry min</span>\n    <span class=\"help\" id=\"queue-delayed-retry-min\"></span> |\n    <span class=\"argument-link\" field=\"definition\" key=\"delayed-retry-max\" type=\"number\">Delayed retry max</span>\n    <span class=\"help\" id=\"queue-delayed-retry-max\"></span> |\n    <span class=\"argument-link\" field=\"definition\" key=\"member-placement-tag\" type=\"string\">Member placement tag</span>\n    <span class=\"help\" id=\"queue-member-placement-tag\"></span> |\n  </td>\n</tr>");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["rate-options"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        
   var id = span.attr('for');
   var mode = get_pref('rate-mode-' + id);
   var size = get_pref('chart-size-' + id);
   var range_pref = get_pref('chart-range');
        ___ViewO.push("\n\n<form action=\"#/rate-options\" method=\"put\" class=\"auto-submit\">\n  <input type=\"hidden\" name=\"id\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( id )));
        ___ViewO.push("\"/>\n  <table class=\"form\" width=\"100%\">\n    <tr>\n      <td colspan=\"2\">\n        <h3>This time series</h3>\n      </td>\n    </tr>\n    <tr>\n      <th><label>Display:</label></th>\n      <td>\n        ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_radio('mode', 'Chart',         'chart', mode) )));
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_radio('mode', 'Current value',  'curr', mode) )));
        ___ViewO.push("\n        ");
         if (id != 'node-stats') { 
        ___ViewO.push("\n             ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_radio('mode', 'Moving average',  'avg', mode) )));
        ___ViewO.push("\n        ");
         } 
        ___ViewO.push("\n      </td>\n    </tr>\n    <tr>\n      <th><label>Chart size:</label></th>\n      <td>\n        ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_radio('size', 'Small',   'small', size) )));
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_radio('size', 'Medium', 'medium', size) )));
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_radio('size', 'Large',   'large', size) )));
        ___ViewO.push("\n      </td>\n    </tr>\n    <tr>\n      <td colspan=\"2\">\n        <h3>All time series</h3>\n      </td>\n    </tr>\n    <tr>\n      <th><label>Chart range:</label></th>\n      <td>\n");
        
   var range_type = get_chart_range_type(id);
   for (var i = 0; i < CHART_RANGES[range_type].length; ++i) {
      var data = CHART_RANGES[range_type][i];
      var range = data[0];
      var desc = data[1];
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_radio('range', desc, range, range_pref) )));
        ___ViewO.push("\n");
        
   }
        ___ViewO.push("\n      </td>\n    </tr>\n  </table>\n</form>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["registry"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
         if (node.running) { 
        ___ViewO.push("\n<table class=\"list\">\n    <tr>\n      <th>Name</th>\n      <th>Description</th>\n");
         if (show_enabled) { 
        ___ViewO.push("\n      <th>Enabled</th>\n");
         } 
        ___ViewO.push("\n    </tr>\n    ");
        
      for (var i = 0; i < list.length; i++) {
        var item = list[i];
    
        ___ViewO.push("\n       <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n         <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(item.name) )));
        ___ViewO.push("</td>\n         <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(item.description) )));
        ___ViewO.push("</td>\n");
         if (show_enabled) { 
        ___ViewO.push("\n         <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(item.enabled) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n       </tr>\n    ");
         } 
        ___ViewO.push("\n</table>\n");
         } else {
        ___ViewO.push("\n<p>...node not running...</p>\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["sessions-list"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        
function getAddressClass(address) {
  return address === '/management' ? 'grey-background' : '';
}

function getCreditClass(credit) {
  return credit === 0 || credit === '0' ? 'yellow-background' : '';
}

function fmt_amqp_filter(filters) {
    if (!filters || filters.length === 0) {
        return '';
    }

    var entries = [];
    for (var i = 0; i < filters.length; i++) {
        var filter = filters[i];
        var formatted_value = fmt_filter_value(filter.value);
        var entry = '<abbr title="(descriptor: ' + fmt_escape_html(filter.descriptor) + ') ' +
                    fmt_escape_html(formatted_value) + '">' +
                    fmt_escape_html(filter.name) + '</abbr>';
        entries.push(entry);
    }
    return entries.join(' ');
}

function fmt_filter_value(value) {
    if (typeof value === 'string') {
        return value;
    } else if (Array.isArray(value)) {
        if (value.length === 0) return '[]';

        if (value[0] && value[0].key !== undefined) {
            // array of key-value pairs
            var props = value.map(function(kv) {
                return kv.key + '=' + fmt_filter_value(kv.value);
            }).join(', ');
            return '{' + props + '}';
        } else {
            // regular array
            return '[' + value.map(fmt_filter_value).join(', ') + ']';
        }
    } else if (typeof value === 'object' && value !== null) {
        return JSON.stringify(value);
    } else {
        return String(value);
    }
}
        ___ViewO.push("\n\n");
         if (sessions.length > 0) { 
        ___ViewO.push("\n<table class=\"list\" id=\"sessions\">\n <thead>\n  <tr>\n   <th>Channel number</th>\n   <th>handle-max</th>\n   <th>next-incoming-id</th>\n   <th>incoming-window</th>\n   <th>next-outgoing-id</th>\n   <th>remote-incoming-window</th>\n   <th>remote-outgoing-window</th>\n   <th>Outgoing unsettled deliveries <span class=\"help\" id=\"outgoing-unsettled-deliveries\"></span></th>\n  </tr>\n </thead>\n\n <tbody>\n");
        
 for (var i = 0; i < sessions.length; i++) {
  var session = sessions[i];
        ___ViewO.push("\n  <tr class=\"session\">\n   <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(session.channel_number) )));
        ___ViewO.push("</td>\n   <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(session.handle_max) )));
        ___ViewO.push("</td>\n   <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(session.next_incoming_id) )));
        ___ViewO.push("</td>\n   <td class=\"c ");
        ___ViewO.push((EJS.Scanner.to_text( getCreditClass(session.incoming_window) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(session.incoming_window) )));
        ___ViewO.push("</td>\n   <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(session.next_outgoing_id) )));
        ___ViewO.push("</td>\n   <td class=\"c ");
        ___ViewO.push((EJS.Scanner.to_text( getCreditClass(session.remote_incoming_window) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(session.remote_incoming_window) )));
        ___ViewO.push("</td>\n   <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(session.remote_outgoing_window) )));
        ___ViewO.push("</td>\n   <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(session.outgoing_unsettled_deliveries) )));
        ___ViewO.push("</td>\n  </tr>\n");
         if (session.incoming_links.length > 0) { 
        ___ViewO.push("\n  <tr>\n  <td colspan=\"8\" >\n   <p>Incoming Links (");
        ___ViewO.push((EJS.Scanner.to_text((session.incoming_links.length))));
        ___ViewO.push(") <span class=\"help\" id=\"incoming-links\"></span></p>\n   <table class=\"list\" id=\"incoming-links\">\n    <thead>\n     <tr>\n      <th>Link handle</th>\n      <th>Link name</th>\n      <th>Target address <span class=\"help\" id=\"target-address\"></span></th>\n      <th>snd-settle-mode <span class=\"help\" id=\"snd-settle-mode\"></span></th>\n      <th>max-message-size (bytes)</th>\n      <th>delivery-count</th>\n      <th>link-credit</th>\n      <th>Unconfirmed messages <span class=\"help\" id=\"amqp-unconfirmed-messages\"></span></th>\n     </tr>\n    </thead>\n    <tbody>\n");
        
 for (var j = 0; j < session.incoming_links.length; j++) {
  var in_link = session.incoming_links[j];
        ___ViewO.push("\n     <tr class=\"link\">\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(in_link.handle) )));
        ___ViewO.push("</td>\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(in_link.link_name) )));
        ___ViewO.push("</td>\n      <td class=\"c ");
        ___ViewO.push((EJS.Scanner.to_text( getAddressClass(in_link.target_address) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(in_link.target_address) )));
        ___ViewO.push("</td>\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(in_link.snd_settle_mode) )));
        ___ViewO.push("</td>\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(in_link.max_message_size) )));
        ___ViewO.push("</td>\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(in_link.delivery_count) )));
        ___ViewO.push("</td>\n      <td class=\"c ");
        ___ViewO.push((EJS.Scanner.to_text( getCreditClass(in_link.credit) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(in_link.credit) )));
        ___ViewO.push("</td>\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(in_link.unconfirmed_messages) )));
        ___ViewO.push("</td>\n     </tr>\n");
         } 
        ___ViewO.push("\n    </tbody>\n   </table>\n  </td>\n  </tr>\n");
         } 
        ___ViewO.push("\n");
         if (session.outgoing_links.length > 0) { 
        ___ViewO.push("\n  <tr>\n  <td colspan=\"8\" >\n   <p>Outgoing Links (");
        ___ViewO.push((EJS.Scanner.to_text((session.outgoing_links.length))));
        ___ViewO.push(") <span class=\"help\" id=\"outgoing-links\"></span></p>\n   <table class=\"list\" id=\"outgoing-links\">\n    <thead>\n     <tr>\n      <th>Link handle</th>\n      <th>Link name</th>\n      <th>Source address <span class=\"help\" id=\"source-address\"></span></th>\n      <th>Source queue <span class=\"help\" id=\"amqp-source-queue\"></span></th>\n      <th>Sender settles <span class=\"help\" id=\"sender-settles\"></span></th>\n      <th>max-message-size (bytes)</th>\n      <th>delivery-count</th>\n      <th>link-credit</th>\n      <th>Consumer timeout <span class=\"help\" id=\"amqp-consumer-timeout\"></span></th>\n      <th>Filters <span class=\"help\" id=\"amqp-filter\"></span></th>\n     </tr>\n    </thead>\n    <tbody>\n");
        
 for (var k = 0; k < session.outgoing_links.length; k++) {
  var out_link = session.outgoing_links[k];
        ___ViewO.push("\n     <tr class=\"link\">\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(out_link.handle) )));
        ___ViewO.push("</td>\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(out_link.link_name) )));
        ___ViewO.push("</td>\n      <td class=\"c ");
        ___ViewO.push((EJS.Scanner.to_text( getAddressClass(out_link.source_address) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(out_link.source_address) )));
        ___ViewO.push("</td>\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(out_link.queue_name) )));
        ___ViewO.push("</td>\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(out_link.send_settled) )));
        ___ViewO.push("</td>\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(out_link.max_message_size) )));
        ___ViewO.push("</td>\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(out_link.delivery_count) )));
        ___ViewO.push("</td>\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(out_link.credit) )));
        ___ViewO.push("</td>\n      <td class=\"c ");
        ___ViewO.push((EJS.Scanner.to_text( out_link.consumer_timeout ? 'yellow-background' : '' )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(out_link.consumer_timeout) )));
        ___ViewO.push("</td>\n      <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_amqp_filter(out_link.filter) )));
        ___ViewO.push("</td>\n     </tr>\n");
         } 
        ___ViewO.push("\n    </tbody>\n   </table>\n  </td>\n  </tr>\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n <p>No sessions</p>\n");
         } 
        ___ViewO.push("\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["status"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<span class=\"status-");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(status) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( text )));
        ___ViewO.push("</span>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["stream-queue-arguments"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<span class=\"argument-link\" field=\"arguments\" key=\"x-max-length-bytes\" type=\"number\">Max length bytes</span> <span class=\"help\" id=\"queue-max-length-bytes\"></span>\n| <span class=\"argument-link\" field=\"arguments\" key=\"x-max-age\" type=\"string\">Max time retention</span><span class=\"help\" id=\"queue-max-age\"></span>\n| <span class=\"argument-link\" field=\"arguments\" key=\"x-stream-max-segment-size-bytes\" type=\"number\">Max segment size in bytes</span><span class=\"help\" id=\"queue-stream-max-segment-size-bytes\"></span></br>\n <span class=\"argument-link\" field=\"arguments\" key=\"x-stream-filter-size-bytes\" type=\"number\">Filter size (per chunk) in bytes</span><span class=\"help\" id=\"queue-stream-filter-size-bytes\"></span>\n| <span class=\"argument-link\" field=\"arguments\" key=\"x-stream-initial-offset\" type=\"number\">Initial offset</span><span class=\"help\" id=\"queue-stream-initial-offset\"></span></br>\n <span class=\"argument-link\" field=\"arguments\" key=\"x-initial-cluster-size\" type=\"number\">Initial cluster size</span><span class=\"help\" id=\"queue-initial-cluster-size\"></span>\n| <span class=\"argument-link\" field=\"arguments\" key=\"x-queue-leader-locator\" type=\"string\">Leader locator</span><span class=\"help\" id=\"queue-leader-locator\"></span>");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["stream-queue-node-details"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("      <tr>\n        <th>Leader</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(queue.leader) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n          <th>Online</th>\n          <td>\n              ");
         for (var i in queue.online) { 
        ___ViewO.push("\n                  ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(queue.online[i]) )));
        ___ViewO.push("\n                  <br/>\n              ");
         } 
        ___ViewO.push("\n          </td>\n      </tr>\n      <th>Members</th>\n      <td>\n          ");
         for (var i in queue.members) {  
        ___ViewO.push("\n              ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(queue.members[i]) )));
        ___ViewO.push("\n              <br/>\n          ");
         } 
        ___ViewO.push("\n      </td>\n      </tr>");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["stream-queue-operator-policy-arguments"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<tr>\n  <td>Queues [Streams]</td>\n  <td>\n    <span class=\"argument-link\" field=\"definitionop\" key=\"max-length-bytes\" type=\"number\">Max length bytes</span>\n  </td>\n</tr>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["stream-queue-stats"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<table class=\"facts facts-l\">\n      <tr>\n        <th>State</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_object_state(queue) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         if(queue.consumers) { 
        ___ViewO.push("\n      <tr>\n        <th>Consumers</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.consumers) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         } else if(queue.hasOwnProperty('consumer_details')) { 
        ___ViewO.push("\n      <tr>\n        <th>Consumers</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.consumer_details.length) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         } 
        ___ViewO.push("\n      ");
         if(queue.hasOwnProperty('publishers')) { 
        ___ViewO.push("\n      <tr>\n        <th>Publishers</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.publishers) )));
        ___ViewO.push("</td>\n      </tr>\n      ");
         } 
        ___ViewO.push("\n      <tr>\n        <th>Readers</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_table_short(queue.readers) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Segments</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(queue.segments) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Oldest message</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_timestamp_mini(queue.first_timestamp) )));
        ___ViewO.push("</td>\n      </tr>\n    </table>\n\n    <table class=\"facts\">\n      <tr>\n        <td></td>\n        <th class=\"horizontal\">Total</th>\n      </tr>\n      <tr>\n        <th>\n          Messages\n          <span class=\"help\" id=\"queue-messages-stream\"></span>\n        </th>\n        <td class=\"r\">\n          ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(queue.messages) )));
        ___ViewO.push("\n        </td>\n      </tr>\n      <tr>\n      </tr>\n      <tr>\n        <th>\n          Process memory\n          <span class=\"help\" id=\"queue-process-memory\"></span>\n        </th>\n        <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(queue.memory) )));
        ___ViewO.push("</td>\n      </tr>\n    </table>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["stream-queue-user-policy-arguments"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["topic-permissions"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<div class=\"section\" id=\"topic-permissions\">\n  <h2>Topic permissions</h2>\n  <div class=\"hider\">\n    <h3>Current topic permissions</h3>\n    ");
         if (topic_permissions.length > 0) { 
        ___ViewO.push("\n    <table class=\"list\">\n      <thead>\n        <tr>\n");
         if (mode == 'vhost') { 
        ___ViewO.push("\n          <th>User</th>\n");
         } else { 
        ___ViewO.push("\n          <th>Virtual host</th>\n");
         } 
        ___ViewO.push("\n          <th>Exchange</th>\n          <th>Write regexp</th>\n          <th>Read regexp</th>\n          <th></th>\n        </tr>\n      </thead>\n      <tbody>\n");
        
for (var i = 0; i < topic_permissions.length; i++) {
    var permission = topic_permissions[i];
        ___ViewO.push("\n           <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n");
         if (mode == 'vhost') { 
        ___ViewO.push("\n             <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_user(permission.user) )));
        ___ViewO.push("</td>\n");
         } else { 
        ___ViewO.push("\n             <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_vhost(permission.vhost) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n             <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_exchange(permission.exchange) )));
        ___ViewO.push("</td>\n             <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(permission.write) )));
        ___ViewO.push("</td>\n             <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(permission.read) )));
        ___ViewO.push("</td>\n             <td class=\"c\">\n               <form action=\"#/topic-permissions\" method=\"delete\" class=\"confirm\">\n                 <input type=\"hidden\" name=\"username\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(permission.user) )));
        ___ViewO.push("\"/>\n                 <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(permission.vhost) )));
        ___ViewO.push("\"/>\n                 <input type=\"hidden\" name=\"exchange\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_exchange_url(permission.exchange) )));
        ___ViewO.push("\"/>\n                 <input type=\"submit\" value=\"Clear\"/>\n               </form>\n             </td>\n           </tr>\n           ");
         } 
        ___ViewO.push("\n      </tbody>\n    </table>\n    ");
         } else { 
        ___ViewO.push("\n      <p>... no topic permissions ...</p>\n    ");
         } 
        ___ViewO.push("\n\n<h3>Set topic permission</h3>\n    <form action=\"#/topic-permissions\" method=\"put\">\n      <table class=\"form\">\n        <tr>\n");
         if (mode == 'vhost') { 
        ___ViewO.push("\n          <th>User</th>\n          <td>\n            <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(parent.name) )));
        ___ViewO.push("\"/>\n            <select name=\"username\">\n              ");
         for (var i = 0; i < users.length; i++) { 
        ___ViewO.push("\n              <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(users[i].name) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(users[i].name) )));
        ___ViewO.push("</option>\n              ");
         } 
        ___ViewO.push("\n            </select>\n          </td>\n");
         } else { 
        ___ViewO.push("\n          <th><label>Virtual Host:</label></th>\n          <td>\n            <input type=\"hidden\" name=\"username\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(parent.name) )));
        ___ViewO.push("\"/>\n            <select name=\"vhost\" class=\"list-exchanges\">\n              ");
         for (var i = 0; i < vhosts.length; i++) { 
        ___ViewO.push("\n              <option value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhosts[i].name) )));
        ___ViewO.push("</option>\n              ");
         } 
        ___ViewO.push("\n            </select>\n          </td>\n");
         } 
        ___ViewO.push("\n        </tr>\n        <tr>\n          <th><label>Exchange:</label></th>\n          <td>\n          <div id='list-exchanges'>\n            ");
        ___ViewO.push((EJS.Scanner.to_text( format('list-exchanges', {'exchanges': exchanges}) )));
        ___ViewO.push("\n          </div>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Write regexp:</label></th>\n          <td><input type=\"text\" name=\"write\" value=\".*\"/></td>\n        </tr>\n        <tr>\n          <th><label>Read regexp:</label></th>\n          <td><input type=\"text\" name=\"read\" value=\".*\"/></td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Set topic permission\"/>\n    </form>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["user"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>User: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(user.name) )));
        ___ViewO.push("</b></h1>\n\n");
         if (permissions.length == 0) { 
        ___ViewO.push("\n<p class=\"warning\">\n  This user does not have permission to access any virtual hosts.<br/>\n  Use \"Set Permission\" below to grant permission to access virtual hosts.\n</p>\n");
         } 
        ___ViewO.push("\n\n<div class=\"section\">\n  <h2>Overview</h2>\n  <div class=\"hider\">\n<table class=\"facts\">\n  <tr>\n    <th>Tags</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(user.tags) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n    <th>Can log in with password</th>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(user.has_password) )));
        ___ViewO.push("</td>\n  </tr>\n</table>\n  </div>\n</div>\n\n");
        ___ViewO.push((EJS.Scanner.to_text( format('permissions', {'mode': 'user', 'permissions': permissions, 'vhosts': vhosts, 'parent': user}) )));
        ___ViewO.push("\n\n");
        ___ViewO.push((EJS.Scanner.to_text( format('topic-permissions', {'mode': 'user', 'topic_permissions': topic_permissions, 'vhosts': vhosts, 'parent': user, 'exchanges': exchanges}) )));
        ___ViewO.push("\n\n<div class=\"section-hidden\">\n  <h2>Update this user</h2>\n  <div class=\"hider\">\n    <form action=\"#/users-modify\" method=\"put\">\n      <input type=\"hidden\" name=\"username\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(user.name) )));
        ___ViewO.push("\"/>\n      <table class=\"form\">\n        <tr>\n          <th>\n            <label>\n              <select name=\"has-password\" class=\"narrow controls-appearance\">\n                ");
         if (user.has_password) { 
        ___ViewO.push("\n                <option value=\"password\" selected=\"selected\">Password:</option>\n                <option value=\"no-password\">No password</option>\n                ");
         } else { 
        ___ViewO.push("\n                <option value=\"password\">Password:</option>\n                <option value=\"no-password\" selected=\"selected\">No password</option>\n                ");
         } 
        ___ViewO.push("\n              </select>\n            </label>\n          </th>\n          <td>\n            ");
         if (user.has_password) { 
        ___ViewO.push("\n            <div id=\"password-div\">\n            ");
         } else { 
        ___ViewO.push("\n            <div id=\"password-div\" style=\"display: none;\">\n            ");
         } 
        ___ViewO.push("\n              <input type=\"password\" name=\"password\" />\n              <span class=\"mand\">*</span><br/>\n              <input type=\"password\" name=\"password_confirm\" />\n              <span class=\"mand\">*</span>\n              (confirm)\n            </div>\n            ");
         if (user.has_password) { 
        ___ViewO.push("\n            <div id=\"no-password-div\" style=\"display: none;\">\n            ");
         } else { 
        ___ViewO.push("\n            <div id=\"no-password-div\">\n            ");
         } 
        ___ViewO.push("\n              User cannot log in using password.\n            </div>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Tags:</label></th>\n          <td>\n            <input type=\"text\" name=\"tags\" id=\"tags\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(user.tags) )));
        ___ViewO.push("\" />\n            <span class=\"help\" id=\"user-tags\"/>\n            <sub>\n              [<span class=\"tag-link\" tag=\"administrator\">Admin</span>]\n              [<span class=\"tag-link\" tag=\"monitoring\">Monitoring</span>]\n              [<span class=\"tag-link\" tag=\"policymaker\">Policymaker</span>]\n              [<span class=\"tag-link\" tag=\"management\">Management</span>]\n              [<span class=\"tag-link\" tag=\"impersonator\">Impersonator</span>]\n              [<span class=\"tag-link\" tag=\"\">None</span>]\n            </sub>\n          </td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Update user\"/>\n    </form>\n  </div>\n</div>\n\n<div class=\"section-hidden\">\n  <h2>Delete this user</h2>\n  <div class=\"hider\">\n    <form action=\"#/users\" method=\"delete\" class=\"confirm\">\n      <input type=\"hidden\" name=\"username\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(user.name) )));
        ___ViewO.push("\"/>\n      <input type=\"submit\" value=\"Delete\"/>\n    </form>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["users"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Users</h1>\n<div class=\"section\">\n    ");
        ___ViewO.push((EJS.Scanner.to_text( paginate_ui(users, 'users') )));
        ___ViewO.push("\n</div>\n<div class=\"updatable\">\n    ");
         if (users.items.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n  <thead>\n    <tr>\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Name', 'name') )));
        ___ViewO.push("</th>\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Tags', 'tags') )));
        ___ViewO.push("</th>\n      <th>Can access virtual hosts</th>\n      <th>Has password</th>\n    </tr>\n  </thead>\n  <tbody>\n    ");
        
       for (var i = 0; i < users.items.length; i++) {
         var user = users.items[i];
    
        ___ViewO.push("\n       <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n         <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_user(user.name) )));
        ___ViewO.push("</td>\n         <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(user.tags) )));
        ___ViewO.push("</td>\n         <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_permissions(user, permissions, 'user', 'vhost',
                           '<p class="warning">No access</p>') )));
        ___ViewO.push("</td>\n         <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(user.has_password) )));
        ___ViewO.push("</td>\n       </tr>\n    ");
         } 
        ___ViewO.push("\n  </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n    <p>... no users ...</p>\n");
         } 
        ___ViewO.push("\n    <p><span class=\"help\" id=\"internal-users-only\"></span></p>\n  </div>\n  </div>\n</div>\n\n<div class=\"section-hidden\">\n  <h2>Add a user</h2>\n  <div class=\"hider\">\n    <form action=\"#/users-add\" method=\"put\">\n      <table class=\"form\">\n        <tr>\n          <th><label>Username:</label></th>\n          <td>\n            <input type=\"text\" name=\"username\"/>\n            <span class=\"mand\">*</span>\n          </td>\n        </tr>\n        <tr>\n          <th>\n            <label>\n              <select name=\"has-password\" class=\"narrow controls-appearance\">\n                <option value=\"password\">Password:</option>\n                <option value=\"no-password\">No password</option>\n              </select>\n            </label>\n          </th>\n          <td>\n            <div id=\"password-div\">\n              <input type=\"password\" name=\"password\" />\n              <span class=\"mand\">*</span><br/>\n              <input type=\"password\" name=\"password_confirm\" />\n              <span class=\"mand\">*</span>\n              (confirm)\n            </div>\n            <div id=\"no-password-div\" style=\"display: none;\">\n              User cannot log in using password.\n            </div>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Tags:</label></th>\n          <td>\n            <input type=\"text\" name=\"tags\" id=\"tags\" />\n            <span class=\"help\" id=\"user-tags\"/>\n            <table class=\"argument-links\">\n              <tr>\n                <td>Set</td>\n                <td>\n                  <span class=\"tag-link\" tag=\"administrator\">Admin</span> |\n                  <span class=\"tag-link\" tag=\"monitoring\">Monitoring</span> |\n                  <span class=\"tag-link\" tag=\"policymaker\">Policymaker</span><br />\n                  <span class=\"tag-link\" tag=\"management\">Management</span> |\n                  <span class=\"tag-link\" tag=\"impersonator\">Impersonator</span> |\n                  <span class=\"tag-link\" tag=\"\">None</span>\n                </td>\n              </tr>\n            </table>\n          </td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Add user\"/>\n    </form>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["vhost"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Virtual Host: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhost.name) )));
        ___ViewO.push("</b></h1>\n\n");
         if (permissions.length == 0) { 
        ___ViewO.push("\n<p class=\"warning\">\n  No users have permission to access this virtual host.<br/>\n  Use \"Set Permission\" below to grant users permission to access this virtual host.\n</p>\n");
         } 
        ___ViewO.push("\n\n");
         if (!disable_stats) { 
        ___ViewO.push("\n<div class=\"section\" id=\"overview\">\n  <h2>Overview</h2>\n  <div class=\"hider updatable\">\n    ");
        ___ViewO.push((EJS.Scanner.to_text( queue_lengths('lengths-vhost', vhost) )));
        ___ViewO.push("\n");
         if (rates_mode != 'none' && vhost.message_stats) { 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( message_rates('msg-rates-vhost', vhost.message_stats) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( data_rates('data-rates-vhost', vhost, 'Data rates') )));
        ___ViewO.push("\n    <h3>Details</h3>\n    <table class=\"facts\">\n      <tr>\n        <th>Tracing enabled:</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(vhost.tracing) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Default queue type:</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( vhost.default_queue_type == "undefined" ? "&lt;not set&gt;" : fmt_string(vhost.default_queue_type) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Deletion protection:</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( vhost.protected_from_deletion ? "enabled" :"disabled" )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>State:</th>\n        <td>\n        <table class=\"mini\">\n        ");
         for (var node in vhost.cluster_state) { 
        ___ViewO.push("\n            <tr>\n            <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_escape_html(node) )));
        ___ViewO.push(" :</th>\n            <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhost.cluster_state[node]) )));
        ___ViewO.push("\n            ");
         if (vhost.cluster_state[node] == "stopped"){ 
        ___ViewO.push("\n                <form action=\"#/restart_vhost\" method=\"post\">\n                    <input type=\"hidden\" name=\"node\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node) )));
        ___ViewO.push("\"/>\n                    <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhost.name) )));
        ___ViewO.push("\"/>\n                    <input type=\"submit\" value=\"Restart\"/>\n                </form>\n            ");
         } 
        ___ViewO.push("\n            </td>\n            </tr>\n        ");
         } 
        ___ViewO.push("\n\n        </table>\n        </td>\n      </tr>\n    </table>\n</div>\n</div>\n");
         } 
        ___ViewO.push("\n\n");
        ___ViewO.push((EJS.Scanner.to_text( format('permissions', {'mode': 'vhost', 'permissions': permissions, 'users': users, 'parent': vhost}) )));
        ___ViewO.push("\n\n");
        ___ViewO.push((EJS.Scanner.to_text( format('topic-permissions', {'mode': 'vhost', 'topic_permissions': topic_permissions, 'users':users, 'parent': vhost, 'exchanges': exchanges}) )));
        ___ViewO.push("\n\n<div class=\"section-hidden\" id=\"delete-vhost\">\n<h2>Delete this vhost</h2>\n<div class=\"hider\">\n<form action=\"#/vhosts\" method=\"delete\" class=\"confirm\">\n<input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhost.name) )));
        ___ViewO.push("\"/>\n<input type=\"submit\" value=\"Delete this virtual host\"/>\n</form>\n</div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["vhosts"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Virtual Hosts</h1>\n\n<div class=\"section\" id=\"vhosts\">\n  <h2>All virtual hosts</h2>\n  <div class=\"hider\">\n");
        ___ViewO.push((EJS.Scanner.to_text( filter_ui(vhosts) )));
        ___ViewO.push("\n  <div class=\"updatable\">\n");
         if (vhosts.length > 0) { 
        ___ViewO.push("\n<table class=\"list\" >\n  <thead>\n  <tr>\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('vhosts', 'Overview', [true, true, true]) )));
        ___ViewO.push("\n    ");
         if (!disable_stats) { 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('vhosts', 'Messages', []) )));
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('vhosts', 'Network', []) )));
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n    ");
        ___ViewO.push((EJS.Scanner.to_text( group_heading('vhosts', 'Message rates', []) )));
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n    ");
         } 
        ___ViewO.push("\n    <th class=\"plus-minus\"><span class=\"popup-options-link\" title=\"Click to change columns\" type=\"columns\" for=\"vhosts\">+/-</span></th>\n  </tr>\n    <tr>\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Name', 'name') )));
        ___ViewO.push("</th>\n      <th>Users <span class=\"help\" id=\"internal-users-only\"></span></th>\n      <th>State</th>\n");
         if (show_column('vhosts',           'default-queue-type')) { 
        ___ViewO.push("\n      <th>Default queue type</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts',           'cluster-state')) { 
        ___ViewO.push("\n      <th>Cluster state</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts',           'description')) { 
        ___ViewO.push("\n      <th>Description</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts',           'tags')) { 
        ___ViewO.push("\n      <th>Tags</th>\n");
         } 
        ___ViewO.push("\n");
         if (!disable_stats) { 
        ___ViewO.push("\n");
         if (show_column('vhosts',           'msgs-ready')) { 
        ___ViewO.push("\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Ready',        'messages_ready') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts',           'msgs-unacked')) { 
        ___ViewO.push("\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Unacked',      'messages_unacknowledged') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts',           'msgs-total')) { 
        ___ViewO.push("\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('Total',        'messages') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts',           'from_client')) { 
        ___ViewO.push("\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('From client',  'recv_oct_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts',           'to_client')) { 
        ___ViewO.push("\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('To client',    'send_oct_details.rate') )));
        ___ViewO.push("</th>\n");
         } 
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n  ");
         if (show_column('vhosts',         'rate-publish')) { 
        ___ViewO.push("\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('publish',     'message_stats.publish_details.rate') )));
        ___ViewO.push("</th>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('vhosts',         'rate-deliver')) { 
        ___ViewO.push("\n      <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort('deliver / get','message_stats.deliver_get_details.rate') )));
        ___ViewO.push("</th>\n  ");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n    </tr>\n  </thead>\n  <tbody>\n    ");
        
       for (var i = 0; i < vhosts.length; i++) {
         var vhost = vhosts[i];
    
        ___ViewO.push("\n       <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n         <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_vhost(vhost.name) )));
        ___ViewO.push("</td>\n         <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_permissions(vhost, permissions, 'vhost', 'user',
                           '<p class="warning">No users</p>') )));
        ___ViewO.push("</td>\n         <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_vhost_state(vhost) )));
        ___ViewO.push("</td>\n");
         if (show_column('vhosts', 'default-queue-type')) { 
        ___ViewO.push("\n   <td>\n     ");
        ___ViewO.push((EJS.Scanner.to_text( vhost.default_queue_type == "undefined" ? "&lt;not set&gt;" : fmt_string(vhost.default_queue_type) )));
        ___ViewO.push("\n   </td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts', 'cluster-state')) { 
        ___ViewO.push("\n         <td>\n             <table>\n             <tbody>\n            ");
        
            for (var node in vhost.cluster_state) {
                var state = vhost.cluster_state[node];
            
        ___ViewO.push("\n            <tr>\n            <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node) )));
        ___ViewO.push("</td>\n            <td>\n            ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(state) )));
        ___ViewO.push("\n            ");
         if (state == "stopped"){ 
        ___ViewO.push("\n                <form action=\"#/restart_vhost\" method=\"post\" class=\"confirm\">\n                    <input type=\"hidden\" name=\"node\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node) )));
        ___ViewO.push("\"/>\n                    <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhost.name) )));
        ___ViewO.push("\"/>\n                    <input type=\"submit\" value=\"Restart\"/>\n                </form>\n            ");
         } 
        ___ViewO.push("\n            </td>\n            </tr>\n            ");
        
            }
            
        ___ViewO.push("\n             </tbody>\n             </table>\n         </td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts', 'description')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhost.description) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts', 'tags')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(vhost.tags) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (!disable_stats) { 
        ___ViewO.push("\n");
         if (show_column('vhosts', 'msgs-ready')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(vhost.messages_ready) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts', 'msgs-unacked')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(vhost.messages_unacknowledged) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts', 'msgs-total')) { 
        ___ViewO.push("\n   <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_num_thousands(vhost.messages) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts', 'from_client')) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate_bytes(vhost, 'recv_oct') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (show_column('vhosts', 'to_client')) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate_bytes(vhost, 'send_oct') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (rates_mode != 'none') { 
        ___ViewO.push("\n  ");
         if (show_column('vhosts', 'rate-publish')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(vhost.message_stats, 'publish') )));
        ___ViewO.push("</td>\n  ");
         } 
        ___ViewO.push("\n  ");
         if (show_column('vhosts', 'rate-deliver')) { 
        ___ViewO.push("\n    <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(vhost.message_stats, 'deliver_get') )));
        ___ViewO.push("</td>\n  ");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n");
         } 
        ___ViewO.push("\n       </tr>\n    ");
         } 
        ___ViewO.push("\n  </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no vhosts ...</p>\n");
         } 
        ___ViewO.push("\n  </div>\n  </div>\n</div>\n\n<div class=\"section-hidden\">\n  <h2>Add a new virtual host</h2>\n  <div class=\"hider\">\n    <form action=\"#/vhosts\" method=\"put\">\n      <table class=\"form\">\n        <tr>\n          <th><label>Name:</label></th>\n          <td><input type=\"text\" name=\"name\"/><span class=\"mand\">*</span></td>\n        </tr>\n        <tr>\n          <th><label>Description:</label></th>\n          <td><input type=\"text\" name=\"description\"/></td>\n        </tr>\n        <tr>\n          <th><label>Tags:</label></th>\n          <td><input type=\"text\" name=\"tags\"/></td>\n        </tr>\n        <tr>\n          <th><label>Default Queue Type:</label></th>\n          <td>\n            <!-- <select name=\"queuetype\" onchange=\"select_queue_type(queuetype)\"> -->\n            <select name=\"default_queue_type\">\n                <option value=\"classic\">Classic</option>\n                <option value=\"quorum\">Quorum</option>\n                <option value=\"stream\">Stream</option>\n            </select>\n          </td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Add virtual host\"/>\n    </form>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};
