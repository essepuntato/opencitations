
var search = (function () {

		var search_conf_json = {};
		var table_conf ={
				data: null,
				category: "",
				filters : {"limit":null, "arr_entries":[], "fields":[], "data":null},
				view: {"page": 0, "page_limit": null, "fields_filter_index":{}}
		}

		/* an sync GET request for the search configuration file */
		function _request_search_conf(callback) {
		    var xreq_obj = new XMLHttpRequest();
		    xreq_obj.overrideMimeType("application/json");
				// with false it becomes an synchronous request
		    xreq_obj.open('GET', 'static/js/search-conf.json', false);
		    xreq_obj.onreadystatechange = function () {
		          if (xreq_obj.readyState == 4 && xreq_obj.status == "200") {
		            callback(xreq_obj.responseText);
		          }
		    };
		    xreq_obj.send(null);
		 }

		 function _get_search_conf() {
				var json_data = _request_search_conf(function(response) {
					 search_conf_json = JSON.parse(response);
				});
		 }

		/* get the rule which matches my query_text*/
		function _get_rule(query_text) {
			for (i = 0; i < search_conf_json["rules"].length; i++) {
				var re = new RegExp(search_conf_json["rules"][i]["regex"]);
				if (query_text.match(re)) {
					//console.log("Match with rule number"+String(i));
					return search_conf_json["rules"][i];
				}
			}
			return -1;
		}

		/*build a string with all the prefixes in a turtle format*/
		function _build_turtle_prefixes(){
			var turtle_prefixes = "";
			for (var i = 0; i < search_conf_json.prefixes.length; i++) {
				var pref_elem = search_conf_json.prefixes[i];
				turtle_prefixes = turtle_prefixes+" "+"PREFIX "+pref_elem["prefix"]+":<"+pref_elem["iri"]+"> ";
			}
			return turtle_prefixes;
		}

		/*build a string representing the sparql query in a turtle format*/
		function _build_turtle_query(arr_query){
			var turtle_prefixes = "";
			for (var i = 0; i < arr_query.length; i++) {
				turtle_prefixes = turtle_prefixes +" "+ arr_query[i];
			}
			return turtle_prefixes;
		}

		/*THE MAIN FUNCTION CALL
		call the sparql endpoint and do the query 'qtext'*/
		function do_sparql_query(qtext){
			var header_container = document.getElementById("search_header");

			if (qtext != "") {

				//initialize and get the search_config_json
				_get_search_conf();
				//search_conf_json = search_conf;

				//get the rule of my input qtext
				var rule =  _get_rule(qtext);
				//console.log(rule);

				//build the sparql query in turtle format
				var sparql_query = _build_turtle_prefixes() + _build_turtle_query(rule.query);
				var global_r = new RegExp("<VAR>", "g");
				sparql_query = sparql_query.replace(global_r, "'"+qtext+"'");

				//use this url to contact the sparql_endpoint triple store
				var query_contact_tp = String(search_conf_json.sparql_endpoint)+"?query="+ encodeURIComponent(sparql_query) +"&format=json";

				//put a loader div
				header_container.appendChild(htmldom.loader(true));

				//call the sparql end point and retrieve results in json format
				$.ajax({
			        dataType: "json",
			        url: query_contact_tp,
							type: 'GET',
	    				success: function( res_data ) {
									htmldom.loader(false);
									htmldom.remove_footer();
									console.log(JSON.parse(JSON.stringify(res_data)));
									_init_data(rule,res_data);
									_apply_limit_filter();
									_build_tab_filters(rule);
									_build_tab_header(rule);
									_update_page();
	    				}
			   });

			 }else {
	 				header_container.innerHTML = htmldom.searching_main_entry();
			 }
		}


		/*init all the local data*/
		function _init_data(rule, json_data){

			table_conf.category = rule.category;

			var index_category_conf = util.index_in_arrjsons(search_conf_json.categories,["name"],[rule.category]);
			var category_conf_obj = search_conf_json.categories[index_category_conf];

			//Adapt the resulting data
			// init uri values
			json_data.results.bindings = _init_uris(json_data.results.bindings);
			// group by the rows
			var group_by = category_conf_obj.group_by;
			if (group_by != undefined) {
				if ((group_by.keys != []) && (group_by.concats != [])) {
					json_data.results.bindings = util.group_by(json_data.results.bindings, group_by.keys, group_by.concats);
				}
			}
			//console.log("After linking and grouping :");
			//console.log(JSON.parse(JSON.stringify(json_data)));

			//init the data
			table_conf.data = JSON.parse(JSON.stringify(json_data));
			// keep only the fields I want
			var fields = category_conf_obj.fields;
			// the header first
			var new_header = [];
			for (var i = 0; i < table_conf.data.head.vars.length; i++) {
				//if the field not in my fields I will remove it
				if(util.index_in_arrjsons(fields,["value"],[table_conf.data.head.vars[i]]) != -1){
					new_header.push(table_conf.data.head.vars[i]);
				}
			}
			table_conf.data.head.vars = new_header;
			// now the results
			for (var i = 0; i < table_conf.data.results.bindings.length; i++) {
				for (var key in table_conf.data.results.bindings[i]) {
						if(util.index_in_arrjsons(fields,["value"],[key]) == -1){
							delete table_conf.data.results.bindings[i][key];
						}
				}
			}

			//set all the other table_conf fields
			//init all the filtered fields
			//-- filtered data
			table_conf.filters.data = table_conf.data;
			//-- maximum number of results
			table_conf.filters.limit = 100;
			if (search_conf_json.filters.limit_res.init != undefined) {
				table_conf.filters.limit = search_conf_json.filters.limit_res.init;
			}

			//-- the filtered checked fields
			table_conf.filters.arr_entries = [];
			//init all the view fields
			table_conf.view.page = 0;
			table_conf.view.page_limit = 10;
			if (search_conf_json.filters.page_limit != undefined) {
				if (search_conf_json.filters.page_limit.length != 0) {
					table_conf.view.page_limit = search_conf_json.filters.page_limit[0];
				}
			}

			for (var i = 0; i < fields.length; i++) {
				if (fields[i].filter != undefined) {
							var my_obj = {"value": fields[i].value, "config": fields[i].filter,"dropdown_active": false};
							if (fields[i].title != undefined) {my_obj["title"] = fields[i].title;}
							table_conf.filters.fields.push(my_obj);
							table_conf.view.fields_filter_index[fields[i].value] = {"i_from": 0,"i_to": fields[i].filter.min};
				}
			}
		}

		/*map the fields with their corresponding links*/
		function _init_uris(data){
			var new_data = data;
			for (var i = 0; i < new_data.length; i++) {
				var obj_elem = new_data[i];
				for (var key_field in obj_elem) {
					if (obj_elem.hasOwnProperty(key_field)) {
						new_data[i] = _get_uri(new_data[i], key_field);
					}
				}
			}
			return new_data;

			function _get_uri(elem_obj, field){
				var new_elem_obj = elem_obj;

				//lets look for the uri
				var index_category = util.index_in_arrjsons(search_conf_json.categories,["name"],[table_conf.category]);
				var index_field = util.index_in_arrjsons(search_conf_json.categories[index_category].fields, ["value"], [field]);
				var uri = null;
				if (index_field != -1){
					var field_obj = search_conf_json.categories[index_category].fields[index_field];
					var link_obj = field_obj.link;

					if (link_obj != undefined) {
						if ((link_obj.field != null) && (link_obj.field != "")) {
							// I have field to link to

							if (elem_obj.hasOwnProperty(link_obj.field)) {
								uri = elem_obj[link_obj.field].value;
								if (link_obj.hasOwnProperty("prefix")) {
									uri = String(link_obj.prefix) + uri;
								}
								new_elem_obj[field]["uri"] = uri;
							}
						}
					}
				}
				return new_elem_obj;
			}
		}

		function _build_tab_header(rule){

			//array of my fields
			var myfields = search_conf_json.categories[util.index_in_arrjsons(search_conf_json.categories,["name"],[rule.category])].fields;

			//get the possible fields to use as sort options
			var arr_options = [];
			for (var i = 0; i < table_conf.data.head.vars.length; i++) {
				var index = util.index_in_arrjsons(myfields,["value"],[table_conf.data.head.vars[i]]);
				if (index != -1) {
					if(myfields[index].hasOwnProperty("sort")){
						if(myfields[index].sort == true){
							var str_html = myfields[index].value;
							if(myfields[index].title != undefined){str_html = myfields[index].title; }
							arr_options.push({"value": myfields[index].value, "type": myfields[index].type, "order": "asc", "text":str_html+" &#8593;" });
							arr_options.push({"value": myfields[index].value, "type": myfields[index].type, "order": "desc", "text":str_html+" &#8595;"});
						}
					}

				}
			}
			var html_container = document.getElementById("sort_results");
			if (html_container != null) {
				html_container.innerHTML = htmldom.sort_box(arr_options);
			}

			//get the possible fields to use as page limit options
			arr_options = [];
			if(search_conf_json.filters.hasOwnProperty("page_limit")){
				arr_options = search_conf_json.filters.page_limit;
			}

			html_container = document.getElementById("rows_per_page");
			if (html_container != null) {
				html_container.innerHTML = htmldom.page_limit(arr_options);
			}
		}

		function _build_tab_filters(){

			_build_limit_res(table_conf.data.results.bindings);
			var container = document.getElementById("filter_btns");
			if (container != null) {
				container.innerHTML = htmldom.filter_btns();

				_update_data_checkboxes();
				_update_filter_checkboxes();
			}
		}

		function _build_limit_res(data){
			//init limit results filter
			var max_val = data.length;
			var init_val = max_val;
			if(max_val > 20){
				init_val = Math.floor(max_val/2);
			}
			table_conf.filters.limit = init_val;
			var min_val = 0;

			var container = document.getElementById("limit_results");
			if (container != null) {
				container.innerHTML = htmldom.limit_filter(init_val, max_val, min_val, max_val);
			}
		}

		function _update_data_checkboxes(){

			table_conf.filters.arr_entries = [];

			// create the list of values I can filter
			var myfields = table_conf.filters.fields;
			for (var i = 0; i < myfields.length; i++) {

							var filter_field = myfields[i].value;

							//the data base
							var list_data = table_conf.filters.data["results"]["bindings"];

							//insert a check list for distinct values in the rows
							var j_to = list_data.length;
							var arr_check_values = [];
							for (var j = 0; j < j_to; j++) {
								var res_obj = list_data[j];

								if(res_obj.hasOwnProperty(filter_field)){
										var elem = res_obj[filter_field];
										var arr = [];
										if(elem.hasOwnProperty("concat-list")){arr = elem["concat-list"];}
										else {arr.push(elem);}

										for (var k = 0; k < arr.length; k++) {
											var new_val = arr[k].value;
											var index_in_arr = util.index_in_arrjsons(arr_check_values,["value"],[new_val]);
											if (index_in_arr == -1){
												arr_check_values.push({"field": filter_field,"value":new_val,"sum":1,"checked":false});
											}else{
												arr_check_values[index_in_arr]["sum"] = arr_check_values[index_in_arr]["sum"] + 1;
											}
										}
								}
							}

							//insert them all
							for (var j = 0; j < arr_check_values.length; j++) {
								table_conf.filters.arr_entries.push(arr_check_values[j]);
							}
			}
		}

		function _update_filter_checkboxes(){

			// create dynamic table
			var table = document.createElement("table");
			table.className = "table filter-values-tab";

			// build cells of fields to filter
			var myfields = table_conf.filters.fields;
			for (var i = 0; i < myfields.length; i++) {
						//insert the header
						var tr = table.insertRow(-1);
						var href_string = "javascript:search.select_filter_field('"+String(myfields[i].value)+"');";
						tr.innerHTML = htmldom.field_filter_header(myfields[i], href_string, false).outerHTML;

						var arr_check_values = util.get_sub_arr(table_conf.filters.arr_entries,"field",myfields[i].value);
						//in case i don't have checkbox values i remove header
						if (arr_check_values.length == 0) {
							table.deleteRow(table.rows.length -1);
						}else {
							if (myfields[i].dropdown_active == true)
							{
									arr_check_values = util.sort_json_by_key(arr_check_values, myfields[i].config.order, myfields[i].config.sort, myfields[i].config.type_sort);
									var j_from = table_conf.view.fields_filter_index[myfields[i].value].i_from;
									var j_to = table_conf.view.fields_filter_index[myfields[i].value].i_to;
									if (j_to > arr_check_values.length) { j_to = arr_check_values.length;}

									for (var j = j_from; j < j_to; j++) {
										//insert a checkbox entry
										tr = table.insertRow(-1);
										tr.innerHTML = htmldom.checkbox_value(myfields[i],arr_check_values[j]).outerHTML;
									}
									tr = table.insertRow(-1);
									tr.innerHTML = htmldom.nav_btns_filter(j_from,j_to,arr_check_values.length,myfields[i]).outerHTML;
							}else {
								//dropdown is closed
								var tr = table.rows[table.rows.length -1];
								tr.innerHTML = htmldom.field_filter_header(myfields[i], href_string, true).outerHTML;
							}
						}
				}
				//insert in html container
				var tab_res_container = document.getElementById("filter_values_list");
				tab_res_container.innerHTML = "";
				tab_res_container.appendChild(table);

				__update_checkboxes();

				//click and check the enabled checkboxes
				function __update_checkboxes() {

					var myfields = table_conf.filters.fields;
					for (var i = 0; i < myfields.length; i++) {
						if (myfields[i].dropdown_active == true){
							var arr_check_values = util.get_sub_arr(table_conf.filters.arr_entries,"field",myfields[i].value);
							var j_to = arr_check_values.length;
							for (var j = 0; j < j_to; j++) {
								var dom_id = arr_check_values[j].field+"-"+arr_check_values[j].value;
								if (arr_check_values[j].checked == true) {
									document.getElementById(dom_id).click();
								}
							}
						}
					}
				}
		}

		function _update_page(){
			var tab_res_container = document.getElementById("search_results");
			if (tab_res_container != null) {
				var new_arr_tab = __build_page();
				tab_res_container.innerHTML = "";
				tab_res_container.appendChild(new_arr_tab[0]);
				tab_res_container.appendChild(new_arr_tab[1]);
			}

			function __build_page(){
				// create new tables
				var new_tab_res = document.createElement("table");
				var new_footer_tab = document.createElement("table");

				new_tab_res.id = "tab_res";
				new_tab_res.className = "table results-tab";

				//create table header
				var col = table_conf.filters.data["head"]["vars"];
				var tr = new_tab_res.insertRow(-1);
				var index_category = util.index_in_arrjsons(search_conf_json.categories,["name"],[table_conf.category]);
				var category_fields = search_conf_json.categories[index_category].fields;

				tr.innerHTML = htmldom.table_res_header(col, category_fields).outerHTML;

				//create tr of all the other results
				var results = table_conf.filters.data["results"]["bindings"];
				if (results.length > 0) {
					var i_from = table_conf.view.page * table_conf.view.page_limit;
					var i_to = i_from + table_conf.view.page_limit;
					if (i_to > results.length){i_to = results.length;}

					for (var i = i_from; i < i_to; i++) {
							tr = new_tab_res.insertRow(-1);
							tr.innerHTML = htmldom.table_res_list(col,category_fields,results[i]).outerHTML;
					}

					//i will build the nav index for the pages
					new_footer_tab = htmldom.table_footer(false, __init_prev_next_btn());
				}else {
					//i have no results
					new_footer_tab = htmldom.table_footer(true, "No results were found");
				}

				return [new_tab_res,new_footer_tab];

				function __init_prev_next_btn(){
					var num_results = table_conf.filters.data["results"]["bindings"].length;
					var tot_pages = Math.floor(num_results/table_conf.view.page_limit);
					if(num_results % table_conf.view.page_limit > 0){tot_pages = tot_pages + 1;}
					var arr_values = __init_page_nav(tot_pages);
					return htmldom.table_index_and_btns(arr_values, table_conf.view.page, tot_pages, table_conf.filters.data.results.bindings.length, table_conf.view.page_limit);
				}
				function __init_page_nav(tot_pages){

					var c_pages = 5;

					//get the number of previous c_pages before me
					var current_page = table_conf.view.page + 1;
					var all_arr_values = __prev_values(c_pages,current_page - 1);
					var min_index = all_arr_values[all_arr_values.length - 1];

					//get the number of next c_pages before me
					var remaining_values = (c_pages - all_arr_values.length) + c_pages;
					var index = current_page + 1;
					var res_obj = __next_values(remaining_values,index,tot_pages);
					all_arr_values = all_arr_values.concat(res_obj.arr);
					remaining_values = res_obj["remaining_values"];

					//get other pages numbers previous to me if I have not still reached a c_pages*2 num
					res_obj = __prev_values(remaining_values,min_index - 1);
					all_arr_values = all_arr_values.concat(res_obj);

					//push my page also
					all_arr_values.push(current_page);

					return all_arr_values.sort(util.sort_int);

					//returns an array of the indexes before me
					function __next_values(rm,i,tot_pages){
						var arr_values = [];
						var remaining_values = rm;
						var index = i;
						while ((remaining_values > 0) && (index <= tot_pages)) {
							arr_values.push(index);
							index = index + 1;
							remaining_values = remaining_values - 1;
						}
						return {"arr": arr_values, "remaining_values": remaining_values};
					}

					//returns an array of the indexes before me
					function __prev_values(rm,i){
						var arr_values = [];
						var remaining_values = rm;
						var index = i;
						while ((remaining_values > 0) && (index > 0)) {
							arr_values.push(index);
							index = index - 1;
							remaining_values = remaining_values - 1;
						}
						return arr_values;
					}
				}
			}
		}

		/*Get only the n limit number of results from all the data*/
		function _apply_limit_filter(){
			var new_data = JSON.parse(JSON.stringify(table_conf.data));
			var arr_new_results = [];

			var i_to = table_conf.filters.limit;
			if (i_to > table_conf.data.results.bindings.length) {
				i_to = table_conf.data.results.bindings.length;
			}

			for (var i = 0; i < i_to; i++) {
				var data_obj = table_conf.data.results.bindings[i];
				arr_new_results.push(data_obj);
			}
			new_data.results.bindings = arr_new_results;
			table_conf.filters.data = new_data;
		}

		//functions to call from the html interface
		function next_page(){
			table_conf.view.page = table_conf.view.page + 1;
			_update_page();
		}
		function prev_page(){
			table_conf.view.page = table_conf.view.page - 1;
			_update_page();
		}
		function update_page_limit(new_page_limit){
			table_conf.view.page_limit = parseInt(new_page_limit);
			table_conf.view.page = 0;
			_update_page();
		}
		function update_res_limit(new_res_limit){
			table_conf.filters.limit = parseInt(new_res_limit);
			table_conf.view.page = 0;
			//reset the sort box
			document.getElementById("sort_box_input").value = "";
			_apply_limit_filter();
			_update_data_checkboxes();
			_update_filter_checkboxes();
			_update_page();
		}
		function show_or_exclude(flag){
			var new_data = JSON.parse(JSON.stringify(table_conf.filters.data));
			var arr_new_results = [];

			var list_data = table_conf.filters.data.results.bindings;
			for (var i = 0; i < list_data.length; i++) {
				var data_obj = list_data[i];
				if(__check_if_respects_filters(data_obj) == flag){
					arr_new_results.push(data_obj);
				}
			}
			new_data.results.bindings = arr_new_results;
			table_conf.filters.data = new_data;
			table_conf.view.page = 0;
			//reset the sort box
			document.getElementById("sort_box_input").value = "";

			_build_limit_res(table_conf.filters.data.results.bindings);
			_update_data_checkboxes();
			_update_filter_checkboxes();
			_update_filter_btns();
			_update_page();

			function __check_if_respects_filters(data_obj){
				//retrieve the entries checked
				var arr_entries = util.get_sub_arr(table_conf.filters.arr_entries,"checked",true);
				var my_fields = [];
				var all_fields = [];

				for (var j = 0; j < arr_entries.length; j++) {
					if (data_obj.hasOwnProperty(arr_entries[j].field)) {

						var arr = [];
						if (data_obj[arr_entries[j].field].hasOwnProperty("concat-list")){
							arr = data_obj[arr_entries[j].field]["concat-list"];
						}
						else {arr.push(data_obj[arr_entries[j].field]);}

						//check if at least 1 in the list respects all the filter
						for (var k = 0; k < arr.length; k++) {
							var elem = arr[k];
							if (elem.value == arr_entries[j].value){
								if (my_fields.indexOf(arr_entries[j].field) == -1){
									my_fields.push(arr_entries[j].field);
									break;
								}
							}
						}
					}
					if (all_fields.indexOf(arr_entries[j].field) == -1){
						all_fields.push(arr_entries[j].field);
					}

				}
				//check if all fields are in the array of the fields filters I respect
				var filters_flag = true;
				for (var j = 0; j < all_fields.length; j++) {
					if(my_fields.indexOf(all_fields[j]) == -1){
						filters_flag = false;
					}
				}
				return filters_flag;
			}
		}
		function show_all() {
			//reset the sort box
			document.getElementById("sort_box_input").value = "";

			//table_conf.filters.data = table_conf.data;
			_update_filter_btns();
			_build_limit_res(table_conf.data.results.bindings);
			_apply_limit_filter();
			_update_data_checkboxes();
			_update_filter_checkboxes();
			_update_page();
		}
		function select_page(page_num) {
			table_conf.view.page = page_num;
			_update_page();
		}
		function checkbox_changed(c_box){
			var index = util.index_in_arrjsons(table_conf.filters.arr_entries,["field","value"],[c_box.getAttribute("field"),c_box.value]);
			if (index != -1) {
				table_conf.filters.arr_entries[index].checked = c_box.checked;
			}

			_update_filter_btns();
		}
		function _update_filter_btns(){
			var checked_filters_arr = util.get_sub_arr(table_conf.filters.arr_entries,"checked",true);
			if(checked_filters_arr.length == 0){
				document.getElementById("show-only").disabled = true;
				document.getElementById("exclude").disabled = true;
			}else {
				document.getElementById("show-only").disabled = false;
				document.getElementById("exclude").disabled = false;
			}
		}
		function sort_results(option){
			//sort according to the field, its type and the order
			var field = option.getAttribute("value");
			var order = option.getAttribute("order");
			var val_type = option.getAttribute("type");

			var field_val = ".value";
			var index_category = util.index_in_arrjsons(search_conf_json.categories,["name"],[table_conf.category]);
			if (search_conf_json.categories[index_category]["group_by"].concats.indexOf(field) != -1) {
				field_val = ".concat-list";
			}

			table_conf.filters.data.results.bindings = util.sort_json_by_key(
						table_conf.filters.data.results.bindings,
						order,
						field+field_val,
						val_type
			);
			table_conf.view.page = 0;
			_update_page();
		}
		function select_filter_field(field_value){
			var field_index = util.index_in_arrjsons(table_conf.filters.fields,["value"],[field_value]);
			if(field_index != -1){
				table_conf.filters.fields[field_index].dropdown_active = !table_conf.filters.fields[field_index].dropdown_active;
			}
			_update_filter_checkboxes();
		}
		function next_filter_page(myfield){
			myfield = JSON.parse(myfield);
			table_conf.view.fields_filter_index[myfield.value].i_from += myfield.config.min;
			table_conf.view.fields_filter_index[myfield.value].i_to += myfield.config.min;
			_update_filter_checkboxes();
		}
		function prev_filter_page(myfield){
			myfield = JSON.parse(myfield);
			table_conf.view.fields_filter_index[myfield.value].i_from -= myfield.config.min;
			table_conf.view.fields_filter_index[myfield.value].i_to -= myfield.config.min;
			_update_filter_checkboxes();
		}
		return {
				next_page: next_page,
				prev_page: prev_page,
				update_page_limit: update_page_limit,
				update_res_limit: update_res_limit,
				show_or_exclude: show_or_exclude,
				checkbox_changed: checkbox_changed,
				show_all: show_all,
				sort_results: sort_results,
				select_page: select_page,
				select_filter_field: select_filter_field,
				next_filter_page: next_filter_page,
				prev_filter_page: prev_filter_page,
				do_sparql_query: do_sparql_query
		 }
})();


var util = (function () {

	/*group by the 'arr_objs' with distinct 'keys' and by concatinating
	the fields in 'arr_fields_concat'*/
	function group_by(arr_objs, keys, arr_fields_concat){
		var new_arr = [];
		for (var i = 0; i < arr_objs.length; i++) {
			var values = collect_values(arr_objs[i], keys);
			var index = index_in_arrjsons(new_arr, keys, values);
			if (index == -1) {
				for (var j = 0; j < arr_fields_concat.length; j++) {
					var elem = arr_objs[i];
					if (arr_objs[i].hasOwnProperty(arr_fields_concat[j])) {
						elem[arr_fields_concat[j]] = {"concat-list": [elem[arr_fields_concat[j]]]};
					}
					new_arr.push(elem);
				}
			}else {
				for (var j = 0; j < arr_fields_concat.length; j++) {
					if (arr_objs[i].hasOwnProperty(arr_fields_concat[j])) {
						var elem = arr_objs[i][arr_fields_concat[j]];

						var index_concat_list = index_in_arrjsons(new_arr[index][arr_fields_concat[j]]["concat-list"], ["value"], [elem.value]);
						if(index_concat_list == -1){
							new_arr[index][arr_fields_concat[j]]["concat-list"].push(elem);
						}
					}
				}
			}
		}
		return new_arr;
	}

	/*collect the values of all the 'keys' in obj*/
	function collect_values(obj,keys){
		var new_arr = [];
		for (var k in obj) {
			if ((obj.hasOwnProperty(k)) && (keys.indexOf(k) != -1)) {
				new_arr.push(obj[k].value);
			}
		}
		return new_arr;
	}

	/* returns a specific column 'field' from an array of objects*/
	function get_sub_arr(arr_objs, field, value){
		var arr = [];
		for (var i = 0; i < arr_objs.length; i++) {
			if(arr_objs[i].hasOwnProperty(field)){
				if (arr_objs[i][field] == value) {
					arr.push(arr_objs[i]);
				}
			}
		}
		return arr;
	}

	/*get index of obj from 'arr_objs' where
	obj['key'] (or an array of multi keys) equals val
	(or an array of multi values), it returns -1 in
	case there is no object*/
	function index_in_arrjsons(arr_objs, keys, vals){

		for (var i = 0; i < arr_objs.length; i++) {
			var elem_obj = arr_objs[i];
			var flag = true;

			for (var j = 0; j < keys.length; j++) {
				if (elem_obj.hasOwnProperty(keys[j])) {
					if (elem_obj[keys[j]].hasOwnProperty("value")) {
						flag = flag && (elem_obj[keys[j]].value == vals[j]);
					}else{
						flag = flag && (elem_obj[keys[j]] == vals[j]);
					}
				}else {
					flag = false;
				}
			}

			if (flag) {
				return i;
			}
		}
		return -1;
	}

	/*sort 'array' of objects with respect to the field "key"
	with data type equal to 'val_type' in the order 'order'*/
	function sort_json_by_key(array, order, key, val_type) {
					var array_key = key.split('.');
					return array.sort(function(a, b) {

						var a_val = _init_val(a, array_key, val_type);
						var b_val = _init_val(b, array_key, val_type);

						if (val_type == "text"){
							var x = a_val.toLowerCase();
							var y = b_val.toLowerCase();
						}else{
								if (val_type == "date") {
										 var x = new Date(a_val);
										 var y = new Date(b_val);
								}else{
											if (val_type == "int") {
														var x = parseFloat(a_val);
														var y = parseFloat(b_val);
											}
											else{
														var x = parseInt(a_val);
														var y = parseInt(b_val);
											}
								}
						}

						if (order == 'desc') {
							return ((x > y) ? -1 : ((x < y) ? 1 : 0));
						}else{
							return ((x < y) ? -1 : ((x > y) ? 1 : 0));
						}
					});

					function _init_val(arr,array_key,val_type) {
						var val= null;
						if (arr.hasOwnProperty(array_key[0])) {
							val= arr[array_key[0]];
							if(array_key.length > 1){
								val = arr[array_key[0]][array_key[1]];
							}
						}else{
							switch (val_type) {
								case "text": val= ""; break;
								case "int": val= -1; break;
								default:
							}
						}
						if ( (val == "None") && (val_type = "int")){
							val = -1;
						}

						if (array_key[1] == "concat-list") {
							var str_concat = "";
							for (var i = 0; i < val.length; i++) {
								str_concat = str_concat + " " +val[i].value;
							}
							val = str_concat;
						}

						return val;
					}

		}

	/*sort int function*/
	function sort_int(a,b) {
		return a - b;
	}

	return {
		group_by: group_by,
		collect_values: collect_values,
		get_sub_arr: get_sub_arr,
		sort_json_by_key: sort_json_by_key,
		sort_int: sort_int,
		index_in_arrjsons: index_in_arrjsons
	 }
})();


var htmldom = (function () {

	function table_res_header(cols,fields){

		var tr = document.createElement("tr");
		for (var i = 0; i < fields.length; i++) {
			f_obj = fields[i];
			var index = cols.indexOf(f_obj["value"]);
			if (index != -1) {
				var th = document.createElement("th");
				if (f_obj["column_width"] != undefined) {
					th.width = f_obj["column_width"];
				}
				th.innerHTML = f_obj["value"];
				if (f_obj["title"] != undefined) {
					th.innerHTML = f_obj["title"];
				}
				tr.appendChild(th);
			}
		}
		return tr;
	}

	function table_res_list(cols,fields,results_obj){
		tr = document.createElement("tr");

		for (var i = 0; i < fields.length; i++) {
				f_obj = fields[i];
				var index = cols.indexOf(f_obj["value"]);
				if (index != -1) {

					var tabCell = tr.insertCell(-1);
					if (results_obj.hasOwnProperty(f_obj["value"])) {
						var str_html = "";

						//check if field is concatenated through group_by
						if (results_obj[f_obj["value"]].hasOwnProperty("concat-list")) {
							var arr = results_obj[f_obj["value"]]["concat-list"];
							var str_sep = ", ";
							for (var k = 0; k < arr.length; k++) {
								if (k == arr.length -1) {str_sep = " ";}
								if(arr[k].hasOwnProperty("uri")){
									str_html = str_html + "<a class='res-val-link' href='"+String(arr[k].uri)+"'>"+arr[k].value+"</a>";
								}else {
									str_html = str_html + String(arr[k].value);
								}
								str_html = String(str_html) + String(str_sep);
							}
						}
						else {
							if(results_obj[f_obj["value"]].hasOwnProperty("uri")){
								str_html = "<a class='res-val-link' href='"+String(results_obj[f_obj["value"]].uri)+"'>"+results_obj[f_obj["value"]].value+"</a>";
							}else {
								str_html = results_obj[f_obj["value"]].value;
							}
						}
					}else{
						str_html = "";
					}
					tabCell.innerHTML = str_html;
				}
		}
		return tr;
	}

	function table_footer(no_results_flag, my_tr){
		var new_footer_tab = document.createElement("table");
		if (! no_results_flag){
			new_footer_tab.id = "tab_next_prev";
			new_footer_tab.className = "table tab-footer";
			tr = new_footer_tab.insertRow(-1);
			tr.innerHTML = my_tr.innerHTML;
		}else{
			new_footer_tab.id = "footer_tab";
			new_footer_tab.className = "table tab-footer noresults";
			tr = new_footer_tab.insertRow(-1);
			tr.innerHTML = my_tr;
		}
		return new_footer_tab;
	}

	function table_index_and_btns(arr_values, mypage, tot_pages, tot_res, pages_lim){

		var str_html = pages_nav(arr_values, mypage + 1, tot_pages);
		var new_btn = document.createElement("a");
		//Prev button
		if(mypage > 0){
			new_btn = htmldom.pages_prev_btn("javascript:search.prev_page()");
			str_html = "<spanfooter>"+String(new_btn.outerHTML)+"</spanfooter>" + "<spanfooter>"+str_html+"</spanfooter>";
		}
		//Next prev
		var remaining_results = tot_res - ((mypage + 1) * pages_lim);
		if(remaining_results > 0) {
			new_btn = htmldom.pages_next_btn("javascript:search.next_page()");
			str_html = "<spanfooter>"+str_html+"</spanfooter>" + "<spanfooter>"+String(new_btn.outerHTML)+"</spanfooter>";
		}
		var new_tr = document.createElement("tr");
		new_tr.innerHTML = str_html;
		return new_tr;
	}

	function checkbox_value(myfield, check_value){
		var tr = document.createElement("tr");
		var tabCell = document.createElement("td");
		tabCell.innerHTML = "<div class='checkbox'><label><input type='checkbox' field="+
												myfield.value+" value='"+String(check_value.value)+
												"' onchange='search.checkbox_changed(this);'"+
												//"checked='"+check_value.checked+"' "+
												"id='"+String(myfield.value)+"-"+String(check_value.value)+"' "+
												">"+
												check_value.value+" ("+check_value.sum+
												")</label></div></div>";
		tr.appendChild(tabCell);
		return tr;
	}

	function field_filter_header(myfield, href_string, is_closed){
		var tr = document.createElement("tr");
		var tabCell = document.createElement("th");
		//tabCell.className = "dynamic_field";

		var title_val = myfield.value;
		if (myfield.title != undefined) {
			title_val = generate_text(myfield.title,12);
		}

		var href_string = "javascript:search.select_filter_field('"+String(myfield.value)+"');";
		if (!is_closed) {
			tabCell.innerHTML = "Select <a href="+href_string+">"+ title_val +"<arrow>&#8744;</arrow>"+"</a>";
		}else {
			tabCell.innerHTML = "Select <a href="+href_string+">"+ title_val +"<arrow>&#8743;</arrow>"+"</a>";
		}
		tr.appendChild(tabCell);
		return tr;
	}

	function nav_btns_filter(i_from, i_to, tot, myfield) {
		var new_tr = document.createElement("tr");
		new_tr.id = "next_prev";
		var tabCell = new_tr.insertCell(-1);

		var str_html = "";
		if (tot - i_to > 0) {
			var str_href = "javascript:search.next_filter_page('"+JSON.stringify(myfield)+"')";
			str_html= "<ar><a class='arrow-nav right' href="+str_href+">&#8680;</a></ar>" + str_html;
		}
		if ((i_from+1)/myfield.config.min >= 1) {
			var str_href = "javascript:search.prev_filter_page('"+JSON.stringify(myfield)+"')";
			str_html= "<ar><a class='arrow-nav left' href="+str_href+">&#8678;</a></ar>" + str_html;
		}

		tabCell.innerHTML = str_html;
		return new_tr;
	}

	function page_limit(arr_options){
		var options_html = "";
		for (var i = 0; i < arr_options.length; i++) {
			var str_option = "<option>"+String(arr_options[i])+"</option>";
			options_html= options_html + str_option;
		}

		var str_html =
		"<div class='rows-per-page'> Number of rows per page: "+"<select class='form-control input' onchange='search.update_page_limit(this.options[selectedIndex].text)'' id='sel1'> </div>"+
			options_html+"</select>";

		return str_html;
	}

	function sort_box(arr_options){
		var options_html = "<option disabled selected value></option>";
		for (var i = 0; i < arr_options.length; i++) {
			var str_option = "<option value="+arr_options[i].value+" type="+arr_options[i].type+" order="+arr_options[i].order+">"+arr_options[i].text+"</option>";
			options_html= options_html + str_option;
		}
		var str_html =
			"<div class='sort-results'>Sort: <select class='form-control input' onchange='search.sort_results(this.options[selectedIndex])' id='sort_box_input'></div>"+
			options_html+"</select>";

		return str_html;
	}

	function searching_main_entry(){
		var str_html = "<div class='search-entry'>"+
											"Search inside the <a href='/'><span class='oc-purple'>Open</span><span class='oc-blue'>Citations</span></a> corpus"+
											"<form class='input-group search-box' action='search' method='get'>"+
											"<input type='text' class='form-control oc-purple' placeholder='Search...' name='text'>"+
												"<div class='input-group-btn'>"+
												"<button class='btn btn-default oc-purple' type='submit'><i class='glyphicon glyphicon-search'></i></button>"+
												"</div>"+
											"</form>"+
										 "</div>";

		return str_html;
	}

	function filter_btns(){
		str_html =
			"<div class='btn-group filters-btns' active='false' role='group'>"+
			"<button type='button' class='btn btn-primary' id='all' onclick='search.show_all();'>All</button>"+
			"<button type='button' class='btn btn-primary' id='show-only' onclick='search.show_or_exclude("+true+");' disabled>Show only</button>"+
			"<button type='button' class='btn btn-primary' id='exclude' onclick='search.show_or_exclude("+false+");' disabled>Exclude</button>"+
			"</div>";
		return str_html;
	}

	function limit_filter(init_val, tot_res, slider_min, slider_max){
		str_html =
		"<div class='limit-results'>"+
		"Limit to <myrange class='limit-results-value' id='lbl_range' for='final_text'> "+String(init_val)+"</myrange>/"+String(tot_res)+" results"+
		"</div>"+
		"<div class='slider-container'>"+
		"<input type='range' min="+String(slider_min)+" max="+String(slider_max)+" value="+String(init_val)+" class='slider' oninput='lbl_range.innerHTML=this.value; search.update_res_limit(this.value);' id='myRange'>"+
		"</div>";
		return str_html;
	}

	function pages_nav(arr_values, mypage, tot_pages){
		var str_html = "";
		var str_start = "<ul class='nav pages-nav'>";
		if (arr_values[0] > 1) { str_start = str_start + "...";}

		var str_end = "</ul>";
		if (arr_values[arr_values.length - 1] < tot_pages) { str_end = "..."+ str_end;}
		for (var i = arr_values.length - 1; i >= 0; i--) {
			var elem_a = "<li><a class='pages-nav' href='javascript:search.select_page("+String(arr_values[i]-1)+");'>"+ String(arr_values[i])+" " +"</a></li>";
			if (arr_values[i] == mypage) {
				elem_a = "<li class='active'><a class='pages-nav' href='javascript:search.select_page("+String(arr_values[i]-1)+");'>"+ String(arr_values[i])+" " +"</a></li>";
			}
			str_html = elem_a +" "+ str_html;
		}
		str_html = str_start + str_html + str_end;
		return str_html;
	}

	function pages_prev_btn(href){
		var new_btn = document.createElement("a");
		new_btn.className = "tab-nav-btn prev";
		new_btn.innerHTML = "&laquo; Previous";
		new_btn.href = String(href);
		return new_btn;
	}

	function pages_next_btn(href){
		var new_btn = document.createElement("a");
		new_btn.className = "tab-nav-btn next";
		new_btn.innerHTML = "Next &raquo;";
		new_btn.href = String(href);
		return new_btn;
	}

	function loader(build_bool){
		if (build_bool) {
			var str_html = "<div id='search_loader' class='searchloader'> Searching in the corpus ...</div>";
			parser = new DOMParser()
  		return parser.parseFromString(str_html, "text/xml").firstChild;
		}else {
			var element = document.getElementById("search_loader");
			element.parentNode.removeChild(element);
		}
	}

	function generate_text(text,numchar) {
		var new_text = text;
		if(text.length > numchar){
			new_text = text.substring(0, numchar-3)+"...";
		}
		return new_text;
	}

	function remove_footer(){
		var footer = document.getElementById("footer");
		footer.parentNode.removeChild(footer);
	}

	return {
		generate_text: generate_text,
		table_res_header: table_res_header,
		table_res_list: table_res_list,
		table_footer: table_footer,
		table_index_and_btns: table_index_and_btns,
		checkbox_value: checkbox_value,
		field_filter_header: field_filter_header,
		nav_btns_filter: nav_btns_filter,
		page_limit: page_limit,
		sort_box: sort_box,
		searching_main_entry: searching_main_entry,
		filter_btns: filter_btns,
		limit_filter: limit_filter,
		pages_nav: pages_nav,
		pages_prev_btn: pages_prev_btn,
		pages_next_btn: pages_next_btn,
		loader: loader,
		remove_footer: remove_footer
	}
})();
