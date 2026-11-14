var COMPILED_TEMPLATES = COMPILED_TEMPLATES || {};

COMPILED_TEMPLATES["federation-upstream"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Federation Upstream: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.name) )));
        ___ViewO.push("</b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_maybe_vhost(upstream.vhost) )));
        ___ViewO.push("</h1>\n\n<div class=\"section\">\n  <h2>Overview</h2>\n  <div class=\"hider\">\n    <table class=\"facts\">\n       <tr>\n          <th>\n          <h3>General parameters</h3>\n         </th>\n      <tr>\n        <th>URI</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(fmt_uri_with_credentials(upstream.value.uri)) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Prefetch Count</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.value['prefetch-count']) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Reconnect Delay</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_time(upstream.value['reconnect-delay'], 's') )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Ack Mode</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.value['ack-mode']) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Trust User-ID</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(upstream.value['trust-user-id']) )));
        ___ViewO.push("</td>\n      </tr>\n\n       <tr>\n          <th>\n          <h3>Federated exchange parameters</h3>\n         </th>\n        </tr>\n      <tr>\n        <th>Exchange</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.value['exchange']) )));
        ___ViewO.push("</td>\n      </tr>\n\n\n      <tr>\n        <th>Max Hops</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.value['max-hops']) )));
        ___ViewO.push("</td>\n      </tr>\n\n      <tr>\n        <th>Expires</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_time(upstream.value.expires, 'ms') )));
        ___ViewO.push("</td>\n      </tr>\n\n      <tr>\n        <th>Message TTL</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_time(upstream.value['message-ttl'], 'ms') )));
        ___ViewO.push("</td>\n      </tr>\n\n      <tr>\n        <th>Queue Type</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.value['queue-type']) )));
        ___ViewO.push("</td>\n      </tr>\n\n       <tr>\n          <th>\n          <h3>Federated queue parameters</h3>\n         </th>\n        </tr>\n\n      <tr>\n        <th>Queue</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.value['queue']) )));
        ___ViewO.push("</td>\n      </tr>\n\n      <tr>\n        <th>Consumer tag</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.value['consumer-tag']) )));
        ___ViewO.push("</td>\n      </tr>\n\n\n\n    </table>\n  </div>\n</div>\n\n<div class=\"section-hidden\">\n  <h2>Delete this upstream</h2>\n  <div class=\"hider\">\n    <form action=\"#/fed-parameters\" method=\"delete\" class=\"confirm\">\n      <input type=\"hidden\" name=\"component\" value=\"federation-upstream\"/>\n      <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.vhost) )));
        ___ViewO.push("\"/>\n      <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.name) )));
        ___ViewO.push("\"/>\n      <input type=\"submit\" value=\"Delete this upstream\"/>\n    </form>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["federation-upstreams"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Federation Upstreams</h1>\n<div class=\"section\">\n  <h2>Upstreams</h2>\n  <div class=\"hider updatable\">\n");
         if (upstreams.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n <thead>\n  <tr>\n");
         if (vhosts_interesting) { 
        ___ViewO.push("\n    <th>Virtual Host</th>\n");
         } 
        ___ViewO.push("\n    <th>Name</th>\n    <th>URI</th>\n    <th>Prefetch Count</th>\n    <th>Reconnect Delay</th>\n    <th>Ack mode</th>\n    <th>Trust User-ID</th>\n    <th>Exchange</th>\n    <th>Max Hops</th>\n    <th>Expiry</th>\n    <th>Message TTL</th>\n    <th>Queue Type</th>\n    <th>Queue</th>\n    <th>Consumer tag</th>\n  </tr>\n </thead>\n <tbody>\n");
        
 for (var i = 0; i < upstreams.length; i++) {
    var upstream = upstreams[i];
        ___ViewO.push("\n   <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n");
         if (vhosts_interesting) { 
        ___ViewO.push("\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.vhost) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_fed_conn(upstream.vhost, upstream.name) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_shortened_uri(fmt_uri_with_credentials(upstream.value.uri)) )));
        ___ViewO.push("</td>\n     <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( upstream.value['prefetch-count'] )));
        ___ViewO.push("</td>\n     <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_time(upstream.value['reconnect-delay'], 's') )));
        ___ViewO.push("</td>\n     <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.value['ack-mode']) )));
        ___ViewO.push("</td>\n     <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(upstream.value['trust-user-id']) )));
        ___ViewO.push("</td>\n     <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.value['exchange']) )));
        ___ViewO.push("</td>\n     <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( upstream.value['max-hops'] )));
        ___ViewO.push("</td>\n     <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_time(upstream.value.expires, 'ms') )));
        ___ViewO.push("</td>\n     <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_time(upstream.value['message-ttl'], 'ms') )));
        ___ViewO.push("</td>\n     <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.value['queue-type']) )));
        ___ViewO.push("</td>\n     <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.value['queue']) )));
        ___ViewO.push("</td>\n     <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(upstream.value['consumer-tag']) )));
        ___ViewO.push("</td>\n   </tr>\n");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no upstreams ...</p>\n");
         } 
        ___ViewO.push("\n  </div>\n</div>\n\n<div class=\"section-hidden\">\n  <h2>Add a new upstream</h2>\n  <div class=\"hider\">\n    <form action=\"#/fed-parameters\" method=\"put\">\n      <input type=\"hidden\" name=\"component\" value=\"federation-upstream\"/>\n      <table class=\"form\">\n       <tr>\n          <th>\n          <h3>  General parameters </h3>\n         </th>\n        </tr>\n");
         if (vhosts_interesting) { 
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
        ___ViewO.push("\n        <tr>\n          <th><label>Name:</label></th>\n          <td><input type=\"text\" name=\"name\"/><span class=\"mand\">*</span></td>\n        </tr>\n\n\n        <tr>\n          <th>\n            <label>\n              URI:\n              <span class=\"help\" id=\"federation-uri\"></span>\n            </label>\n          </th>\n          <td><input type=\"text\" name=\"uri\"/><span class=\"mand\">*</span></td>\n        </tr>\n        <tr>\n          <th>\n            <label>\n              Prefetch count:\n              <span class=\"help\" id=\"federation-prefetch\"></span>\n            </label>\n          </th>\n          <td><input type=\"text\" name=\"prefetch-count\"/></td>\n        </tr>\n        <tr>\n          <th>\n            <label>\n              Reconnect delay:\n              <span class=\"help\" id=\"federation-reconnect\"></span>\n            </label>\n          </th>\n          <td><input type=\"text\" name=\"reconnect-delay\"/> s</td>\n        </tr>\n        <tr>\n          <th>\n            <label>\n              Acknowledgement Mode:\n              <span class=\"help\" id=\"federation-ack-mode\"></span>\n            </label>\n          </th>\n          <td>\n            <select name=\"ack-mode\">\n              <option value=\"on-confirm\">On confirm</option>\n              <option value=\"on-publish\">On publish</option>\n              <option value=\"no-ack\">No ack</option>\n            </select>\n          </td>\n        </tr>\n        <tr>\n          <th>\n            <label>\n              Trust User-ID:\n              <span class=\"help\" id=\"federation-trust-user-id\"></span>\n            </label>\n          </th>\n\n          <td>\n            <select name=\"trust-user-id\">\n              <option value=\"false\">No</option>\n              <option value=\"true\">Yes</option>\n            </select>\n          </td>\n\n        <tr>\n          <th>\n          <h3>Federated exchanges parameters </h3>\n         </th>\n        </tr>\n\n\n         <tr>\n          <th>\n            <label>\n              Exchange:\n              <span class=\"help\" id=\"exchange\"></span>\n            </label>\n          </th>\n          <td><input type=\"text\" name=\"exchange\"/></td>\n        </tr>\n\n       <tr>\n          <th>\n            <label>\n              Max hops:\n              <span class=\"help\" id=\"federation-max-hops\"></span>\n            </label>\n          </th>\n          <td><input type=\"text\" name=\"max-hops\"/></td>\n        </tr>\n\n        <tr>\n          <th>\n            <label>\n              Expires:\n              <span class=\"help\" id=\"federation-expires\"></span>\n            </label>\n          </th>\n          <td><input type=\"text\" name=\"expires\"/> ms</td>\n        </tr>\n\n        <tr>\n          <th>\n            <label>\n              Message TTL:\n              <span class=\"help\" id=\"federation-ttl\"></span>\n            </label>\n          </th>\n          <td><input type=\"text\" name=\"message-ttl\"/> ms</td>\n        </tr>\n\n\n        <tr>\n          <th>\n            <label>\n              Queue Type:\n              <span class=\"help\" id=\"queue-type\"></span>\n            </label>\n          </th>\n          <td><input type=\"text\" name=\"queue-type\"/></td>\n        </tr>\n        </tr>\n\n       <tr>\n          <th>\n          <h3>Federated queues parameter </h3>\n         </th>\n        </tr>\n\n         <tr>\n          <th>\n            <label>\n              Queue:\n              <span class=\"help\" id=\"queue\"></span>\n            </label>\n          </th>\n          <td><input type=\"text\" name=\"queue\"/></td>\n        </tr>\n        <tr>\n          <th>\n            <label>\n              Consumer tag:\n              <span class=\"help\" id=\"consumer-tag\"></span>\n            </label>\n          </th>\n          <td><input type=\"text\" name=\"consumer-tag\"/></td>\n        </tr>\n        </tr>\n\n\n\n      </table>\n      <input type=\"submit\" value=\"Add upstream\"/>\n    </form>\n  </div>\n</div>\n<div class=\"section-hidden\">\n  <h2>URI examples</h2>\n  <div class=\"hider\">\n    <ul>\n      <li>\n        <code>amqp://server-name</code><br/>\n        connect to server-name, without SSL and default credentials\n      </li>\n      <li>\n        <code>amqp://user:password@server-name/my-vhost</code><br/>\n        connect to server-name, with credentials and overridden\n        virtual host\n      </li>\n      <li>\n        <code>amqps://user:password@server-name?cacertfile=/path/to/cacert.pem&certfile=/path/to/cert.pem&keyfile=/path/to/key.pem&verify=verify_peer</code><br/>\n        connect to server-name, with credentials and SSL\n      </li>\n      <li>\n        <code>amqps://server-name?cacertfile=/path/to/cacert.pem&certfile=/path/to/cert.pem&keyfile=/path/to/key.pem&verify=verify_peer&fail_if_no_peer_cert=true&auth_mechanism=external</code><br/>\n        connect to server-name, with SSL and EXTERNAL authentication\n      </li>\n    </ul>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["federation"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Federation Status</h1>\n<div class=\"section\">\n  <h2>Running Links</h2>\n  <div class=\"hider updatable\">\n");
         if (links.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n <thead>\n  <tr>\n    <th>Upstream</th>\n    <th>URI</th>\n");
         if (vhosts_interesting) { 
        ___ViewO.push("\n    <th>Virtual Host</th>\n");
         } 
        ___ViewO.push("\n    <th>Exchange / Queue</th>\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n    <th>Node</th>\n");
         } 
        ___ViewO.push("\n    <th>State</th>\n    <th>Inbound message rate</th>\n    <th>Last changed</th>\n    <th>ID</th>\n    <th>Consumer tag</th>\n    <th>Operations</th>\n  </tr>\n </thead>\n <tbody>\n");
        
 for (var i = 0; i < links.length; i++) {
    var link = links[i];
        ___ViewO.push("\n   <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n    <td>\n      ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.upstream) )));
        ___ViewO.push("\n      ");
         if (link.type == 'exchange' &&
             link.exchange != link.upstream_exchange) { 
        ___ViewO.push("\n        <sub>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.upstream_exchange) )));
        ___ViewO.push("</sub>\n      ");
         } else if (link.type == 'queue' &&
                    link.queue != link.upstream_queue) { 
        ___ViewO.push("\n        <sub>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.upstream_queue) )));
        ___ViewO.push("</sub>\n      ");
         } 
        ___ViewO.push("\n    </td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(fmt_uri_with_credentials(link.uri)) )));
        ___ViewO.push("</td>\n");
         if (vhosts_interesting) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.vhost) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n    <td>\n      ");
         if (link.type == 'exchange') { 
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( link_exchange(link.vhost, link.exchange) )));
        ___ViewO.push("\n      ");
         } else { 
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( link_queue(link.vhost, link.queue) )));
        ___ViewO.push("\n      ");
         } 
        ___ViewO.push("\n    <sub>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.type) )));
        ___ViewO.push("</sub>\n    </td>\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(link.node) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (link.error) { 
        ___ViewO.push("\n    <td>\n      ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_state('red', fmt_escape_html(link.status)) )));
        ___ViewO.push("\n    </td>\n    <td></td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.timestamp) )));
        ___ViewO.push("</td>\n  </tr>\n  <tr>\n");
         if (vhosts_interesting) { 
        ___ViewO.push("\n    <td colspan=\"7\">\n");
         } else { 
        ___ViewO.push("\n    <td colspan=\"6\">\n");
         } 
        ___ViewO.push("\n      Error detail:\n      <pre>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_escape_html(link.error) )));
        ___ViewO.push("</pre>\n    </td>\n  </tr>\n");
         } else { 
        ___ViewO.push("\n    <td>\n      ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_state(link.status == 'starting' ? 'yellow' : 'green', fmt_escape_html(link.status)) )));
        ___ViewO.push("\n    </td>\n    <td class=\"r\">\n      ");
         if (link.local_channel) { 
        ___ViewO.push("\n        ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(link.local_channel.message_stats, 'confirm') )));
        ___ViewO.push("\n      ");
         } 
        ___ViewO.push("\n    </td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.timestamp) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.id) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.consumer_tag) )));
        ___ViewO.push("</td>\n    <td>\n        <form action=\"#/federation-restart-link\" method=\"delete\" class=\"confirm\">\n        <input type=\"hidden\" name=\"id\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.id) )));
        ___ViewO.push("\"/>\n        <input type=\"hidden\" name=\"node\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(link.node) )));
        ___ViewO.push("\"/>\n        <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(link.vhost) )));
        ___ViewO.push("\"/>\n        <input type=\"submit\" value=\"Restart\"/>\n        </form>\n    </td>\n  </tr>\n");
         } 
        ___ViewO.push("\n  ");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no links ...</p>\n");
         } 
        ___ViewO.push("\n</div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};
