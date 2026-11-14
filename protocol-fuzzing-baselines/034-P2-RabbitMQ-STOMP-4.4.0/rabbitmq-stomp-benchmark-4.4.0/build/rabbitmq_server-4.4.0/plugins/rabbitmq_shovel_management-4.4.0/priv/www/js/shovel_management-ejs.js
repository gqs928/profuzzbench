var COMPILED_TEMPLATES = COMPILED_TEMPLATES || {};

COMPILED_TEMPLATES["dynamic-shovel"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Dynamic Shovel: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.name) )));
        ___ViewO.push("</b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_maybe_vhost(shovel.vhost) )));
        ___ViewO.push("</h1>\n\n<div class=\"section\">\n  <h2>Overview</h2>\n  <div class=\"hider\">\n    <table class=\"facts\">\n      <tr>\n        <th>Source</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(fmt_uri_with_credentials(shovel.value['src-uri'])) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th> </th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_shovel_endpoint('src-', shovel.value) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Destination</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(fmt_uri_with_credentials(shovel.value['dest-uri'])) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th> </th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_shovel_endpoint('dest-', shovel.value) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Prefetch count</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(fallback_value(shovel, 'src-prefetch-count', 'prefetch-count')) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Reconnect delay</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_time(shovel.value['reconnect-delay'], 's') )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Add headers</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(fallback_value(shovel, 'dest-add-forward-headers', 'add-forward-headers')) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Ack mode</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.value['ack-mode']) )));
        ___ViewO.push("</td>\n      </tr>\n      <tr>\n        <th>Auto-delete</th>\n        <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(fallback_value(shovel, 'src-delete-after', 'delete-after')) )));
        ___ViewO.push("</td>\n      </tr>\n    </table>\n  </div>\n</div>\n\n\n  <div class=\"section-hidden\">\n  <h2>Delete this shovel</h2>\n  <div class=\"hider\">\n    ");
         if (!is_internal_shovel(shovel.value)) { 
        ___ViewO.push("\n      <form action=\"#/shovel-parameters\" method=\"delete\" class=\"confirm\">\n        <input type=\"hidden\" name=\"component\" value=\"shovel\"/>\n        <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.vhost) )));
        ___ViewO.push("\"/>\n        <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.name) )));
        ___ViewO.push("\"/>\n        <input type=\"submit\" value=\"Delete this shovel\"/>\n      </form>\n    ");
         } else { 
        ___ViewO.push("\n      ");
         if (shovel_has_internal_owner(shovel.value)) { 
        ___ViewO.push("\n        <span>This shovel is internal and owned by ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_resource_link(shovel_internal_owner(shovel.value)) )));
        ___ViewO.push(". Could be deleted only via CLI command with --force.</span>\n      ");
         } else { 
        ___ViewO.push("\n        <span>This shovel is internal. Could be deleted only via CLI command with '--force'.</span>\n      ");
         } 
        ___ViewO.push("\n    ");
         } 
        ___ViewO.push("\n  </div>\n  </div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["dynamic-shovels"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Dynamic Shovels</h1>\n<div class=\"section\">\n  <h2>Shovels</h2>\n  <div class=\"hider updatable\">\n");
         if (shovels.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n <thead>\n  <tr>\n");
         if (vhosts_interesting) { 
        ___ViewO.push("\n    <th>Virtual Host</th>\n");
         } 
        ___ViewO.push("\n    <th>Name</th>\n    <th colspan=\"4\">Source</th>\n    <th colspan=\"4\">Destination</th>\n    <th>Reconnect Delay</th>\n    <th>Ack mode</th>\n    <th>Auto-delete</th>\n  </tr>\n  <tr>\n");
         if (vhosts_interesting) { 
        ___ViewO.push("\n    <th colspan=\"2\"></th>\n");
         } 
        ___ViewO.push("\n");
         if (!vhosts_interesting) { 
        ___ViewO.push("\n    <th colspan=\"1\"></th>\n");
         } 
        ___ViewO.push("\n    <th>Protocol</th>\n    <th>Uri</th>\n    <th>Endpoint</th>\n    <th>Prefetch</th>\n    <th>Protocol</th>\n    <th>Uri</th>\n    <th>Endpoint</th>\n    <th>Add headers</th>\n    <th colspan=\"3\"></th>\n  </tr>\n </thead>\n <tbody>\n");
        
 for (var i = 0; i < shovels.length; i++) {
    var shovel = shovels[i];
        ___ViewO.push("\n   <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n");
         if (vhosts_interesting) { 
        ___ViewO.push("\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.vhost) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_shovel(shovel.vhost, shovel.name) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.value['src-protocol']) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_shortened_uri(fmt_uri_with_credentials(shovel.value['src-uri'])) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_shovel_endpoint('src-', shovel.value) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.value['src-prefetch-count']) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.value['dest-protocol']) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_shortened_uri(fmt_uri_with_credentials(shovel.value['dest-uri'])) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_shovel_endpoint('dest-', shovel.value) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(fallback_value(shovel, 'dest-add-forward-headers', 'add-forward-headers')) )));
        ___ViewO.push("</td>\n     <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_time(shovel.value['reconnect-delay'], 's') )));
        ___ViewO.push("</td>\n     <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.value['ack-mode']) )));
        ___ViewO.push("</td>\n     <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(fallback_value(shovel, 'src-delete-after', 'delete-after')) )));
        ___ViewO.push("</td>\n   </tr>\n");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no shovels ...</p>\n");
         } 
        ___ViewO.push("\n  </div>\n</div>\n\n<div class=\"section-hidden\">\n  <h2>Add a new shovel</h2>\n  <div class=\"hider\">\n    <form action=\"#/shovel-parameters\" method=\"put\">\n      <input type=\"hidden\" name=\"component\" value=\"shovel\"/>\n      <table class=\"form dynamic-shovels\">\n");
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
        ___ViewO.push("\n        <tr>\n          <th><label>Name:</label></th>\n          <td><input type=\"text\" name=\"name\"/><span class=\"mand\">*</span></td>\n        </tr>\n        <tr>\n          <th>Source:</th>\n          <td>\n            <select name=\"src-protocol-selector\" class=\"controls-appearance\">\n              <option value=\"amqp091-src\">AMQP 0.9.1</option>\n              <option value=\"amqp10-src\">AMQP 1.0</option>\n              <option value=\"local-src\">Local</option>\n            </select>\n            <div id=\"amqp10-src-div\" style=\"display: none;\">\n              <table class=\"subform\">\n                <tr>\n                  <td>\n                    <label class=\"wide\">\n                      URI:\n                      <span class=\"help\" id=\"shovel-uri\"></span>\n                    </label>\n                  </td>\n                  <td>\n                    <input type=\"text\" name=\"amqp10-src-uri\" value=\"amqp://localhost:5672\"/>\n                    <span class=\"mand\">*</span>\n                  </td>\n                </tr>\n                <tr>\n                  <td>\n                    <label class=\"wide\">\n                      Address:\n                      <span class=\"help\" id=\"shovel-amqp10-address\"></span>\n                    </label>\n                  </th>\n                  <td><input type=\"text\" name=\"amqp10-src-address\"/></td>\n                </tr>\n                <tr>\n                  <td>\n                    <label class=\"wide\">\n                      Prefetch count:\n                      <span class=\"help\" id=\"shovel-prefetch\"></span>\n                    </label>\n                  </td>\n                  <td><input type=\"text\" name=\"amqp10-src-prefetch-count\"/></td>\n                </tr>\n                <tr>\n                  <td>\n                    <label>\n                      Auto-delete\n                      <span class=\"help\" id=\"shovel-amqp10-auto-delete\"></span>\n                    </label>\n                  </td>\n                  <td>\n                    <select name=\"amqp10-src-delete-after-selector\" class=\"controls-appearance\">\n                      <option value=\"never\">Never</option>\n                      <option value=\"number\">After num messages</option>\n                    </select>\n                  </td>\n                  <td>\n                    <div id=\"number-div\" style=\"display: none;\">\n                      <input type=\"text\" name=\"amqp10-src-delete-after\"/>\n                    </div>\n                  </td>\n                </tr>\n              </table>\n            </div>\n            <div id=\"amqp091-src-div\">\n              <table class=\"subform\">\n                <tr>\n                  <td>\n                    <label>\n                      URI:\n                      <span class=\"help\" id=\"shovel-uri\"></span>\n                    </label>\n                  </td>\n                  <td>\n                    <select name=\"queue-or-exchange\" class=\"controls-appearance\">\n                      <option value=\"src-queue\">Queue:</option>\n                      <option value=\"src-exchange\">Exchange:</option>\n                    </select>\n                    <span class=\"help\" id=\"shovel-queue-exchange\"></span>\n                  </td>\n                </tr>\n                <tr>\n                  <td>\n                    <input type=\"text\" name=\"src-uri\" value=\"amqp://\"/>\n                    <span class=\"mand\">*</span>\n                  </td>\n                  <td>\n                    <div id=\"src-queue-div\">\n                      <input type=\"text\" name=\"amqp091-src-queue\"/>\n                    </div>\n                    <div id=\"src-exchange-div\" style=\"display: none;\">\n                      <input type=\"text\" name=\"amqp091-src-exchange\"/>\n                      Routing key: <input type=\"text\" name=\"src-exchange-key\"/>\n                    </div>\n                  </td>\n                </tr>\n                <tr>\n                  <td>\n                    <label>\n                      Prefetch count:\n                      <span class=\"help\" id=\"shovel-prefetch\"></span>\n                    </label>\n                  </td>\n                  <td><input type=\"text\" name=\"amqp091-src-prefetch-count\"/></td>\n                </tr>\n                <tr>\n                  <td>\n                    <label>\n                      Auto-delete\n                      <span class=\"help\" id=\"shovel-amqp091-auto-delete\"></span>\n                    </label>\n                  </td>\n                  <td>\n                    <select name=\"amqp091-src-delete-after\">\n                      <option value=\"never\">Never</option>\n                      <option value=\"queue-length\">After initial length transferred</option>\n                    </select>\n                  </td>\n                </tr>\n              </table>\n            </div>\n            <div id=\"local-src-div\" style=\"display: none;\">\n              <table class=\"subform\">\n                <tr>\n                  <td>\n                    <label>\n                      URI:\n                      <span class=\"help\" id=\"shovel-uri\"></span>\n                    </label>\n                  </td>\n                  <td>\n                    <select name=\"queue-or-exchange\" class=\"controls-appearance\">\n                      <option value=\"local-src-queue\">Queue:</option>\n                      <option value=\"local-src-exchange\">Exchange:</option>\n                    </select>\n                    <span class=\"help\" id=\"shovel-queue-exchange\"></span>\n                  </td>\n                </tr>\n                <tr>\n                  <td>\n                    <input type=\"text\" name=\"local-src-uri\" value=\"amqp://\"/>\n                    <span class=\"mand\">*</span>\n                  </td>\n                  <td>\n                    <div id=\"local-src-queue-div\">\n                      <input type=\"text\" name=\"local-src-queue\"/>\n                    </div>\n                    <div id=\"local-src-exchange-div\" style=\"display: none;\">\n                      <input type=\"text\" name=\"local-src-exchange\"/>\n                      Routing key: <input type=\"text\" name=\"local-src-exchange-key\"/>\n                    </div>\n                  </td>\n                </tr>\n                <tr>\n                  <td>\n                    <label>\n                      Auto-delete\n                      <span class=\"help\" id=\"shovel-local-auto-delete\"></span>\n                    </label>\n                  </td>\n                  <td>\n                    <select name=\"local-src-delete-after-selector\" class=\"controls-appearance\">\n                      <option value=\"never\">Never</option>\n                      <option value=\"queue-length\">After initial length transferred</option>\n                      <option value=\"local-number\">After num messages</option>\n                    </select>\n                  </td>\n		  <td>\n                    <div id=\"local-number-div\" style=\"display: none;\">\n                      <input type=\"text\" name=\"local-src-delete-after\"/>\n                    </div>\n                  </td>\n                </tr>\n               </table>\n            </div>\n          </td>\n        </tr>\n        <tr>\n          <th>Destination:</th>\n          <td>\n            <select name=\"dest-protocol-selector\" class=\"controls-appearance\">\n              <option value=\"amqp091-dest\">AMQP 0.9.1</option>\n              <option value=\"amqp10-dest\">AMQP 1.0</option>\n              <option value=\"local-dest\">Local</option>\n            </select>\n            <div id=\"amqp10-dest-div\" style=\"display: none;\">\n              <table class=\"subform\">\n                <tr>\n                  <td>\n                    <label>\n                    URI:\n                    <span class=\"help\" id=\"shovel-uri\"></span>\n                    </label>\n                  </td>\n                  <td>\n                    <input type=\"text\" name=\"dest-uri\" value=\"amqp://localhost:5672\"/>\n                    <span class=\"mand\">*</span>\n                  </td>\n                </tr>\n                <tr>\n                  <td>\n                    <label>\n                      Address:\n                      <span class=\"help\" id=\"shovel-amqp10-address\"></span>\n                    </label>\n                  </td>\n                  <td><input type=\"text\" name=\"amqp10-dest-address\"/></td>\n                </tr>\n                <tr>\n                  <td>\n                    <label>\n                      Add forwarding headers:\n                      <span class=\"help\" id=\"shovel-forward-headers\"></span>\n                    </label>\n                  </td>\n                  <td>\n                    <select name=\"amqp10-dest-add-forward-headers\">\n                      <option value=\"false\">No</option>\n                      <option value=\"true\">Yes</option>\n                    </select>\n                  </td>\n                </tr>\n              </table>\n            </div>\n            <div id=\"amqp091-dest-div\">\n              <table class=\"subform\">\n                <tr>\n                  <td>\n                    <label>\n                      URI\n                      <span class=\"help\" id=\"shovel-uri\"></span>\n                    </label>\n                  </td>\n                  <td>\n                    <select name=\"queue-or-exchange\" class=\"narrow controls-appearance\">\n                      <option value=\"dest-queue\">Queue:</option>\n                      <option value=\"dest-exchange\">Exchange:</option>\n                    </select>\n                    <span class=\"help\" id=\"shovel-queue-exchange\"></span>\n                  </td>\n                </tr>\n                <tr>\n                  <td><input type=\"text\" name=\"amqp091-dest-uri\" value=\"amqp://\"/><span class=\"mand\">*</span></td>\n                  <td>\n                    <div id=\"dest-queue-div\">\n                      <input type=\"text\" name=\"amqp091-dest-queue\"/>\n                    </div>\n                    <div id=\"dest-exchange-div\" style=\"display: none;\">\n                      <input type=\"text\" name=\"amqp091-dest-exchange\"/>\n                      Routing key: <input type=\"text\" name=\"amqp091-dest-exchange-key\"/>\n                    </div>\n                  </td>\n                </tr>\n                <tr>\n                  <td>\n                    <label>\n                      Add forwarding headers:\n                      <span class=\"help\" id=\"shovel-forward-headers\"></span>\n                    </label>\n                  </td>\n                  <td>\n                    <select name=\"amqp091-dest-add-forward-headers\">\n                      <option value=\"false\">No</option>\n                      <option value=\"true\">Yes</option>\n                    </select>\n                  </td>\n                </tr>\n              </table>\n            </div>\n            <div id=\"local-dest-div\" style=\"display: none;\">\n              <table class=\"subform\">\n                <tr>\n                  <td>\n                    <label>\n                      URI\n                      <span class=\"help\" id=\"shovel-uri\"></span>\n                    </label>\n                  </td>\n                  <td>\n                    <select name=\"queue-or-exchange\" class=\"narrow controls-appearance\">\n                      <option value=\"local-dest-queue\">Queue:</option>\n                      <option value=\"local-dest-exchange\">Exchange:</option>\n                    </select>\n                    <span class=\"help\" id=\"shovel-queue-exchange\"></span>\n                  </td>\n                </tr>\n                <tr>\n                  <td><input type=\"text\" name=\"local-dest-uri\" value=\"amqp://\"/><span class=\"mand\">*</span></td>\n                  <td>\n                    <div id=\"local-dest-queue-div\">\n                      <input type=\"text\" name=\"local-dest-queue\"/>\n                    </div>\n                    <div id=\"local-dest-exchange-div\" style=\"display: none;\">\n                      <input type=\"text\" name=\"local-dest-exchange\"/>\n                      Routing key: <input type=\"text\" name=\"local-dest-exchange-key\"/>\n                    </div>\n                  </td>\n                </tr>\n                <tr>\n                  <td>\n                    <label>\n                      Add forwarding headers:\n                      <span class=\"help\" id=\"shovel-forward-headers\"></span>\n                    </label>\n                  </td>\n                  <td>\n                    <select name=\"local-dest-add-forward-headers\">\n                      <option value=\"false\">No</option>\n                      <option value=\"true\">Yes</option>\n                    </select>\n                  </td>\n                </tr>\n              </table>\n            </div>\n          </td>\n        </tr>\n        <tr>\n          <th>\n            <label>\n              Reconnect delay:\n              <span class=\"help\" id=\"shovel-reconnect\"></span>\n            </label>\n          </th>\n          <td><input type=\"text\" name=\"reconnect-delay\"/> s</td>\n        </tr>\n        <tr>\n          <th>\n            <label>\n              Acknowledgement mode:\n              <span class=\"help\" id=\"shovel-ack-mode\"></span>\n            </label>\n          </th>\n          <td>\n            <select name=\"ack-mode\">\n              <option value=\"on-confirm\">On confirm</option>\n              <option value=\"on-publish\">On publish</option>\n              <option value=\"no-ack\">No ack</option>\n            </select>\n          </td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Add shovel\"/>\n    </form>\n  </div>\n</div>\n<div class=\"section-hidden\">\n  <h2>URI examples</h2>\n  <div class=\"hider\">\n    <ul>\n      <li>\n        <code>amqp://</code><br/>\n        connect to local server as default user\n      </li><br />\n      <li>\n        <code>amqp://user@/my-vhost</code><br/>\n        connect to local server with alternate user and virtual host\n        (passwords are not required for local connections)\n      </li><br />\n      <li>\n        <code>amqp://server-name</code><br/>\n        connect to server-name, without SSL and default credentials\n      </li><br />\n      <li>\n        <code>amqp://user:password@server-name/my-vhost</code><br/>\n        connect to server-name, with credentials and overridden\n        virtual host\n      </li><br />\n      <li>\n        <code>amqps://user:password@server-name?cacertfile=/path/to/cacert.pem&certfile=/path/to/cert.pem&keyfile=/path/to/key.pem&verify=verify_peer</code><br/>\n        connect to server-name, with credentials and SSL\n      </li><br />\n      <li>\n        <code>amqps://server-name?cacertfile=/path/to/cacert.pem&certfile=/path/to/cert.pem&keyfile=/path/to/key.pem&verify=verify_peer&auth_mechanism=external</code><br/>\n        connect to server-name, with SSL and EXTERNAL authentication\n      </li>\n    </ul>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["shovels"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Shovel Status</h1>\n");
        
  var extra_width = 0;
  if (vhosts_interesting) extra_width++;
  if (nodes_interesting)  extra_width++;
        ___ViewO.push("\n<div class=\"updatable\">\n");
         if (shovels.length > 0) { 
        ___ViewO.push("\n<table class=\"list\">\n <thead>\n  <tr>\n    <th>Name</th>\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n    <th>Node</th>\n");
         } 
        ___ViewO.push("\n");
         if (vhosts_interesting) { 
        ___ViewO.push("\n    <th>Virtual Host</th>\n");
         } 
        ___ViewO.push("\n    <th>State</th>\n    <th>Remaining <span class=\"help\" id=\"shovel-remaining-counter\"></span></th>\n    <th>Remaining Unacked <span class=\"help\" id=\"shovel-remaining-unacked-counter\"></span></th>\n    <th>Pending <span class=\"help\" id=\"shovel-pending-counter\"></span></th>\n    <th>Forwarded <span class=\"help\" id=\"shovel-forwarded-counter\"></span></th>\n    <th colspan=\"3\">Source</th>\n    <th colspan=\"3\">Destination</th>\n    <th>Last changed</th>\n    <th>Operations</th>\n  </tr>\n </thead>\n <tbody>\n");
        
 for (var i = 0; i < shovels.length; i++) {
    var shovel = shovels[i];
        ___ViewO.push("\n  <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n    <td>\n      ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.name) )));
        ___ViewO.push("\n      <sub>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.type) )));
        ___ViewO.push("</sub>\n    </td>\n");
         if (nodes_interesting) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(shovel.node) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (vhosts_interesting) { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.vhost, '') )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (shovel.state == 'terminated') { 
        ___ViewO.push("\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_state('red', fmt_escape_html(shovel.state)) )));
        ___ViewO.push("</td>\n    <td colspan=\"6\">\n      <pre>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.reason) )));
        ___ViewO.push("</pre>\n    </td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.timestamp) )));
        ___ViewO.push("</td>\n");
         } else { 
        ___ViewO.push("\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_object_state(shovel) )));
        ___ViewO.push("</td>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.remaining) )));
        ___ViewO.push("</td>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.remaining_unacked) )));
        ___ViewO.push("</td>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.pending) )));
        ___ViewO.push("</td>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.forwarded) )));
        ___ViewO.push("</td>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.src_protocol) )));
        ___ViewO.push("</td>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( shovel.src_uri == undefined ? fmt_string(shovel.src_uri) : fmt_string(fmt_uri_with_credentials(shovel.src_uri)) )));
        ___ViewO.push("</td>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_shovel_endpoint('src_', shovel) )));
        ___ViewO.push("</td>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.dest_protocol) )));
        ___ViewO.push("</td>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( shovel.dest_uri == undefined ? fmt_string(shovel.dest_uri) : fmt_string(fmt_uri_with_credentials(shovel.dest_uri)) )));
        ___ViewO.push("</td>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_shovel_endpoint('dest_', shovel) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.timestamp) )));
        ___ViewO.push("</td>\n");
         } 
        ___ViewO.push("\n");
         if (shovel.type == 'dynamic') { 
        ___ViewO.push("\n    <td>\n     <form action=\"#/shovel-restart-link\" method=\"delete\" class=\"confirm\">\n     <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_node(shovel.name) )));
        ___ViewO.push("\"/>\n     <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(shovel.vhost) )));
        ___ViewO.push("\"/>\n     <input type=\"submit\" value=\"Restart\"/>\n     </form>\n    </td>\n");
         } else { 
        ___ViewO.push("\n   <td/>\n  ");
         } 
        ___ViewO.push("\n  </tr>\n  ");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
         } else { 
        ___ViewO.push("\n  <p>... no shovels ...</p>\n");
         } 
        ___ViewO.push("\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};
