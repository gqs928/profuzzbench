var COMPILED_TEMPLATES = COMPILED_TEMPLATES || {};

COMPILED_TEMPLATES["ets_tables"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Top ETS Tables: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(top.node) )));
        ___ViewO.push("</b></h1>\n\n<p>\n  Node:\n  <select id=\"top-node-ets\">\n  ");
         for (var i = 0; i < nodes.length; i++) { 
        ___ViewO.push("\n     <option name=\"#/top/");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(nodes[i].name) )));
        ___ViewO.push("\"");
         if (nodes[i].name == top.node) { 
        ___ViewO.push("selected=\"selected\"");
         } 
        ___ViewO.push(">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(nodes[i].name) )));
        ___ViewO.push("</option>\n  ");
         } 
        ___ViewO.push("\n  </select>\n\n  Rows:\n  <select id=\"row-count-ets\">\n  ");
        
    var row_counts = [20, 50, 100, 150];
    for (var i = 0; i < row_counts.length; i++) {
  
        ___ViewO.push("\n    <option name=\"");
        ___ViewO.push((EJS.Scanner.to_text( row_counts[i] )));
        ___ViewO.push("\"\n        ");
         if (row_counts[i] == top.row_count) { 
        ___ViewO.push("selected=\"selected\"");
         } 
        ___ViewO.push(">\n    ");
        ___ViewO.push((EJS.Scanner.to_text( row_counts[i] )));
        ___ViewO.push("</option>\n  ");
         } 
        ___ViewO.push("\n  </select>\n</p>\n\n<table class=\"list updatable\">\n <thead>\n  <tr>\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort_desc_by_default('Name', 'name') )));
        ___ViewO.push("</th>\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort_desc_by_default('Owner Name', 'owner_name') )));
        ___ViewO.push("</th>\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort_desc_by_default('Memory', 'memory') )));
        ___ViewO.push("</th>\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort_desc_by_default('Size', 'size') )));
        ___ViewO.push("</th>\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort_desc_by_default('Type', 'type') )));
        ___ViewO.push("</th>\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort_desc_by_default('Named', 'named_table') )));
        ___ViewO.push("</th>\n    <th>Protection</th>\n    <th>Compressed</th>\n  </tr>\n </thead>\n <tbody>\n");
        
 for (var i = 0; i < top.ets_tables.length; i++) {
    var table = top.ets_tables[i];
        ___ViewO.push("\n  <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(table.name) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(table.owner_name) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(table.memory * 1.0) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( table.size )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(table.type) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(table.named_table) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(table.protection) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(table.compressed) )));
        ___ViewO.push("</td>\n  </tr>\n");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["process"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Process: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(process.pid) )));
        ___ViewO.push("</b></h1>\n\n<div class=\"updatable\">\n  <table class=\"facts\">\n    <tr>\n      <th>Description</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_process_name(process) )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Type</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_remove_rabbit_prefix(process.name.type) )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Memory</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(process.memory) )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Reductions / sec</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_reduction_delta(process.reduction_delta) )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Total reductions</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( process.reductions )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Erlang mailbox</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( process.message_queue_len )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>gen_server2 buffer <span class=\"help\" id=\"gen-server2-buffer\"></span></th>\n      <td><pre>");
        ___ViewO.push((EJS.Scanner.to_text( process.buffer_len )));
        ___ViewO.push("</pre></td>\n    </tr>\n    <tr>\n      <th>Status</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(process.status) )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Trap exit</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_boolean(process.trap_exit) )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Links</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_pids(process.links) )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Monitors</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_pids(process.monitors) )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Monitored by</th>\n      <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_pids(process.monitored_by) )));
        ___ViewO.push("</td>\n    </tr>\n    <tr>\n      <th>Current stacktrace</th>\n      <td><pre>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(process.current_stacktrace) )));
        ___ViewO.push("</pre></td>\n    </tr>\n  </table>\n</div>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};

COMPILED_TEMPLATES["processes"] = function(_CONTEXT, _VIEW) {
  try {
    with(_VIEW) {
      with(_CONTEXT) {
        var ___ViewO = [];
        ___ViewO.push("<h1>Top Processes: <b>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(top.node) )));
        ___ViewO.push("</b></h1>\n\n<p>\n  Node:\n  <select id=\"top-node\">\n  ");
         for (var i = 0; i < nodes.length; i++) { 
        ___ViewO.push("\n     <option name=\"#/top/");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(nodes[i].name) )));
        ___ViewO.push("\"");
         if (nodes[i].name == top.node) { 
        ___ViewO.push("selected=\"selected\"");
         } 
        ___ViewO.push(">");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(nodes[i].name) )));
        ___ViewO.push("</option>\n  ");
         } 
        ___ViewO.push("\n  </select>\n\n  Rows:\n  <select id=\"row-count\">\n  ");
        
    var row_counts = [20, 50, 100, 150];
    for (var i = 0; i < row_counts.length; i++) {
  
        ___ViewO.push("\n    <option name=\"");
        ___ViewO.push((EJS.Scanner.to_text( row_counts[i] )));
        ___ViewO.push("\"\n        ");
         if (row_counts[i] == top.row_count) { 
        ___ViewO.push("selected=\"selected\"");
         } 
        ___ViewO.push(">\n    ");
        ___ViewO.push((EJS.Scanner.to_text( row_counts[i] )));
        ___ViewO.push("</option>\n  ");
         } 
        ___ViewO.push("\n  </select>\n</p>\n\n<table class=\"list updatable\">\n <thead>\n  <tr>\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort_desc_by_default('Process', 'pid') )));
        ___ViewO.push("</th>\n    <th>Description</th>\n    <th>Type</th>\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort_desc_by_default('Memory', 'memory') )));
        ___ViewO.push("</th>\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort_desc_by_default('Reductions / sec', 'reduction_delta') )));
        ___ViewO.push("</th>\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort_desc_by_default('Erlang mailbox', 'message_queue_len') )));
        ___ViewO.push("</th>\n    <th>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_sort_desc_by_default('gen_server2 buffer', 'buffer_len') )));
        ___ViewO.push("<span class=\"help\" id=\"gen-server2-buffer\"></span></th>\n    <th>Status</th>\n  </tr>\n </thead>\n <tbody>\n");
        
 for (var i = 0; i < top.processes.length; i++) {
    var process = top.processes[i];
        ___ViewO.push("\n  <tr");
        ___ViewO.push((EJS.Scanner.to_text( alt_rows(i))));
        ___ViewO.push(">\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( link_pid(process.pid) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_process_name(process) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_remove_rabbit_prefix(process.name.type) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_bytes(process.memory * 1.0) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_reduction_delta(process.reduction_delta) )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( process.message_queue_len )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( process.buffer_len )));
        ___ViewO.push("</td>\n    <td>");
        ___ViewO.push((EJS.Scanner.to_text( fmt_string(process.status) )));
        ___ViewO.push("</td>\n  </tr>\n");
         } 
        ___ViewO.push("\n </tbody>\n</table>\n");
        return ___ViewO.join('');
      }
    }
  } catch(e) { e.lineNumber = null; throw e; }
};
