var x_timeseries_default = {
    axis: {
        x: {
            type: "timeseries",
            tick: {
                format: "%B %Y",
                fit: false,
                rotate: 90
            }
        },
        y: {
            label: {
                text: "Time series",
                position: "outer-middle"
            }
        },
        y2: {
            label: {
                text: "Histogram",
                position: "outer-middle"
            }
        }
    }
}

function createGraph(jQuery) {
    d3.csv(conf.figshare, function(d) {
        var obj = {
            data: {
                rows: bb_convert(yyyy_mm(d, ["month"])),
                x: "month",
                type: "bar"
            },
            bindto: "#figshare"
        };
        obj = $.extend(true, {}, obj, x_timeseries_default);
        bb.generate(obj);
    });

    d3.csv(conf.access, function(d) {
        var all_headers = subSameDate(d, "page", "accesses");
        var total_visits = _.map(all_headers, function(k, v) { return {page: v, accesses: k}});
        all_headers = _.map(max_n(total_visits, "page", "accesses"),
                                function(v) {return v["page"]});
        all_headers.sort();
        var converted_data = create_matrix_of_categories(d, "month", "page", "accesses");
        var data_with_residual = calculate_residual(converted_data, all_headers, ["month"])
        all_headers.push("month");
        bb_data = bb_convert(yyyy_mm(data_with_residual, ["month"]), all_headers);
        y_objects = _.difference(all_headers, ["month", "total"]);
        y_types = _.object(y_objects, _.range(y_objects.length).map(function () { return 'bar' }))

        var obj = {
            data: {
                rows: bb_data,
                x: "month",
                types: y_types
            },
            bindto: "#website"
        };
        obj = $.extend(true, {}, obj, x_timeseries_default);
        bb.generate(obj);
    });

    d3.csv(conf.twitter, function(d) {
        var obj = {
            data: {
                rows: bb_convert(yyyy_mm(d, ["month"]),
                                ["month", "tweet impressions", "profile visits",
                                "mentions", "new followers", "tweets"]),
                x: "month",
                axes: {
                    "tweets": "y2",
                    "mentions": "y2",
                    "new followers": "y2"
                },
                types: {
                  "mentions": "bar",
                  "new followers": "bar",
                  "tweets": "bar"
                }
            },
            bindto: "#twitter"
        };
        obj = $.extend(true, {}, obj, x_timeseries_default);
        obj.axis.y2.show = true;
        bb.generate(obj);
    });

    d3.csv(conf.wordpress, function(d) {
        cur_data = bb_convert(yyyy_mm(d, ["month"]),
                              ["month", "blog post", "blog views", "blog visitors"]);

        var obj = {
            data: {
                rows: cur_data,
                x: "month",
                axes: {
                    "blog post": "y2"
                },
                types: {
                  "blog post": "bar"
                }
            },
            bindto: "#wordpress"
        };
        obj = $.extend(true, {}, obj, x_timeseries_default);
        obj.axis.y2.show = true;

        max_tick_blog_post = _.max(_.rest(bb_transpose(cur_data)[1]));
        obj.axis.y2.tick = { values: _.range(0, max_tick_blog_post + 1) };
        bb.generate(obj);
    });

    d3.csv(conf.country, function(d) {
        bb.generate({
            data: {
                columns: bb_convert(max_n(d, "country", "accesses"), ["country", "accesses"], false),
                type: "pie"
            },
            bindto: "#access_country"
        });
    });

    d3.csv(conf.occ, function(d) {
        var transpose_data = bb_transpose(bb_convert(d));
        var obj = {
            data: {
                columns: _.rest(transpose_data),
                type: "bar"
            },
            axis: {
                x: {
                    type: "category",
                    categories: _.rest(transpose_data[0])
                }
            },
            bindto: "#occstat"
        };
        bb.generate(obj);
    });
}
