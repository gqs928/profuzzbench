var COMPILED_TEMPLATES = COMPILED_TEMPLATES || {};

COMPILED_TEMPLATES["traces"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Traces: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(node.name) )));
        ___ViewO.push("</b></h1>\n<p>\n  Node:\n  <select id=\"traces-node\">\n  ");
         for (var i = 0; i < nodes.length; i++) { 
        ___ViewO.push("\n     <option name=\"#/traces/");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(nodes[i].name) )));
        ___ViewO.push("\"");
         if (nodes[i].name == node.name) { 
        ___ViewO.push("selected=\"selected\"");
         } 
        ___ViewO.push(">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(nodes[i].name) )));
        ___ViewO.push("</option>\n  ");
         } 
        ___ViewO.push("\n  </select>\n</p>\n\n<div class=\"section\">\n  <h2>All traces</h2>\n  <div class=\"hider updatable\">\n    <table class=\"two-col-layout\">\n      <tr>\n        <td>\n          <h3>Currently running traces</h3>\n          ");
         if (traces.length > 0) { 
        ___ViewO.push("\n          <table class=\"list\">\n            <thead>\n              <tr>\n                ");
         if (vhosts_interesting) { 
        ___ViewO.push("\n                  <th>Virtual host</th>\n                ");
         } 
        ___ViewO.push("\n                <th>Name</th>\n                <th>Pattern</th>\n                <th>Format</th>\n                <th>Payload limit</th>\n                <th>Rate</th>\n                <th>Queued</th>\n                <th>Tracer connection username</th>\n                <th></th>\n              </tr>\n            </thead>\n            <tbody>\n              ");
        
                 for (var i = 0; i < traces.length; i++) {
                     var trace = traces[i];
              
        ___ViewO.push("\n              <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n                ");
         if (vhosts_interesting) { 
        ___ViewO.push("\n                  <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(trace.vhost) )));
        ___ViewO.push("</td>\n                ");
         } 
        ___ViewO.push("\n                <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(trace.name) )));
        ___ViewO.push("</td>\n                <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(trace.pattern) )));
        ___ViewO.push("</td>\n                <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(trace.format) )));
        ___ViewO.push("</td>\n                <td class=\"c\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(trace.max_payload_bytes, 'Unlimited') )));
        ___ViewO.push("</td>\n                ");
         if (trace.queue) { 
        ___ViewO.push("\n                <td class=\"r\">\n                  ");
        ___ViewO.push((EJS.Scanner.to_text( fmt_detail_rate(trace.queue.message_stats, 'deliver_no_ack') )));
        ___ViewO.push("\n                </td>\n                <td class=\"r\">\n                  ");
        ___ViewO.push((EJS.Scanner.to_text( trace.queue.messages )));
        ___ViewO.push("\n                  <sub>");
        ___ViewO.push((EJS.Scanner.to_text( link_trace_queue(trace) )));
        ___ViewO.push("</sub>\n                </td>\n                ");
         } else { 
        ___ViewO.push("\n                <td colspan=\"2\">\n                  <div class=\"status-red\"><acronym title=\"The trace failed to start - check the server logs for details.\">FAILED</acronym></div>\n                </td>\n                ");
         } 
        ___ViewO.push("\n                <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(trace.tracer_connection_username) )));
        ___ViewO.push("</td>\n                <td>\n                  <form action=\"#/traces/node/");
        ___ViewO.push((EJS.Scanner.to_text( esc(node.name) )));
        ___ViewO.push("\" method=\"delete\">\n                    <input type=\"hidden\" name=\"vhost\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(trace.vhost) )));
        ___ViewO.push("\"/>\n                    <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(trace.name) )));
        ___ViewO.push("\"/>\n                    <input type=\"submit\" value=\"Stop\"/>\n                  </form>\n                </td>\n              </tr>\n              ");
         } 
        ___ViewO.push("\n            </tbody>\n          </table>\n          ");
         } else { 
        ___ViewO.push("\n          <p>... no traces running ...</p>\n          ");
         } 
        ___ViewO.push("\n        </td>\n        <td>\n          <h3>Trace log files</h3>\n          ");
         if (files.length > 0) { 
        ___ViewO.push("\n            <table class=\"list\">\n              <thead>\n                <tr>\n                  <th>Name</th>\n                  <th>Size</th>\n                  <th></th>\n                </tr>\n              </thead>\n              <tbody>\n              ");
        
                for (var i = 0; i < files.length; i++) {
                  var file = files[i];
              
        ___ViewO.push("\n                <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n                  <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_trace(node.name, file.name) )));
        ___ViewO.push("</td>\n                  <td class=\"r\">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(file.size) )));
        ___ViewO.push("</td>\n                  <td>\n                    <form action=\"#/trace-files/node/");
        ___ViewO.push((EJS.Scanner.to_text( esc(node.name) )));
        ___ViewO.push("\" method=\"delete\" class=\"inline-form\">\n                      <input type=\"hidden\" name=\"name\" value=\"");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(file.name) )));
        ___ViewO.push("\"/>\n                      <input type=\"submit\" value=\"Delete\" />\n                    </form>\n                  </td>\n                </tr>\n              ");
         } 
        ___ViewO.push("\n              </tbody>\n            </table>\n          ");
         } else { 
        ___ViewO.push("\n            <p>... no files ...</p>\n          ");
         } 
        ___ViewO.push("\n        </td>\n      </tr>\n    </table>\n  </div>\n</div>\n\n<div class=\"section\">\n  <h2>Add a new trace</h2>\n  <div class=\"hider\">\n    <form action=\"#/traces/node/");
        ___ViewO.push((EJS.Scanner.to_text( esc(node.name) )));
        ___ViewO.push("\" method=\"put\">\n      <table class=\"form\">\n");
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
        ___ViewO.push("\n        <tr>\n          <th><label>Name:</label></th>\n          <td><input type=\"text\" name=\"name\"/><span class=\"mand\">*</span></td>\n        </tr>\n        <tr>\n          <th><label>Format:</label></th>\n          <td>\n            <select name=\"format\">\n              <option value=\"text\">Text</option>\n              <option value=\"json\">JSON</option>\n            </select>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Tracer connection username:</label></th>\n          <td><input type=\"text\" name=\"tracer_connection_username\"/></td>\n          <td><label>Tracer connection password:</label></td>\n          <td>\n            <div id=\"password-div\">\n              <input type=\"password\" name=\"tracer_connection_password\"/>\n            </div>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Max payload bytes: <span class=\"help\" id=\"tracing-max-payload\"></span></label></th>\n          <td>\n            <input type=\"text\" name=\"max_payload_bytes\" value=\"\"/>\n          </td>\n        </tr>\n        <tr>\n          <th><label>Pattern:</label></th>\n          <td>\n            <input type=\"text\" name=\"pattern\" value=\"#\"/>\n            <sub>Examples: #, publish.#, deliver.# #.amq.direct, #.myqueue</sub>\n          </td>\n        </tr>\n      </table>\n      <input type=\"submit\" value=\"Add trace\"/>\n    </form>\n  </div>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};
