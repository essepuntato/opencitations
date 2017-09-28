/* This function transform a CSV structure into the format appropriate for
 * processing the data by column by using BillBoard.js. It uses the
 * underscore.js library. */
 function bb_convert(data, headers=[], include_header=true) {
     var array_to_zip = [];

     if (headers.length == 0) {
         Object.keys(data[0]).forEach(function(header) {
            headers.push(header);
         });
     }

     headers.forEach(function(header) {
         array_to_zip.push(_.pluck(data, header));
     });
     var final_array = _.zip.apply(_, array_to_zip);

     if (include_header) {
         final_array.unshift(headers);
     }

     return final_array;
 }

/* This function convert a string month like "YYYY-DD" into a Javascript
 * Date object */
function yyyy_mm(data, headers) {
    headers.forEach(function(header) {
        data.forEach(function(item) {
            data_string = item[header];
            item[header] = new Date(data_string + "-01T00:00:00Z");
        });
    });
    return data;
}

/* This function allows one to keep only the top n results,
 * grouping the others in a generic "other" category. It is expected
 * to have a two column CSV, where one column identifies the various
 * categories, while the other is a numeric value. */
function max_n(data, category_header, numeric_header, n=3, residual_category="other") {
    if (n < 1) {
        n = 1;
    }

    var final_data = [];
    var min = [];
    var residual = 0;
    data.forEach(function(item) {
        var cur_number = Number(item[numeric_header]);
        if (final_data.length < n || Number(min[0][numeric_header]) <= cur_number) {
            final_data.push(item);
            min = get_min(final_data, numeric_header);
            if (final_data.length > n && _.indexOf(min, item) == -1) {
                final_data = _.difference(final_data, min);
                min.forEach(function(item) { residual += Number(item[numeric_header]); });
            }
        }
    });

    if (residual) {
        residual_obj = {};
        residual_obj[numeric_header] = residual;
        residual_obj[category_header] = residual_category;
        final_data.push(residual_obj);
    }

    return final_data;
}

/* Get the objects in an array having the minimum value associate to the
 * specified header. */
function get_min(o_array, header) {
    var min_value = Math.min.apply(Math, o_array.map(function(item){
        return Number(item[header]);
    }));

    var final_array = o_array.filter(function(item) {
        return item[header] == min_value;
    });

    return final_array;
}

/* This function set all the monthly dates (JSON key: month) in all
 * the object of the data that must be visualised considering them
 * collected at the end of the month in consideration, instead of
 * at the beginning.
 */
function set_end_month(input) {
    data = input.data;
    data = MG.convert.date(data, 'month', '%Y-%m');
    data.forEach(function(el) {
        if(el.hasOwnProperty('month')){
            /* Set the last day of the next month. */
            el.month.setMonth(el.month.getMonth()+1, 0);
        }
    });
}

function set_defaults(input) {
    input.width = 600;
    input.height = 250;
    input.aggregate_rollover = true;
    input.interpolate = d3.curveLinear;
}

MG.add_hook('global.before_init', set_defaults);
MG.add_hook('global.before_init', set_end_month);
