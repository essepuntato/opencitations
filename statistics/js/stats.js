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
                text: "Count",
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
        Object.assign(obj, x_timeseries_default);
        bb.generate(obj);
    });

    d3.csv(conf.access, function(d) {
        var obj = {
            data: {
                rows: bb_convert(yyyy_mm(d, ["month"]), ["month", "accesses"]),
                x: "month"
            },
            bindto: "#website"
        };
        Object.assign(obj, x_timeseries_default);
        bb.generate(obj);
    });

    d3.csv(conf.twitter, function(d) {
        console.log(d);
        var obj = {
            data: {
                rows: bb_convert(yyyy_mm(d, ["month"]), ["month", "tweet impressions", "profile visits"]),
                x: "month"
            },
            bindto: "#twitter"
        };
        Object.assign(obj, x_timeseries_default);
        bb.generate(obj);
    });

    d3.csv(conf.page, function(d) {
        bb.generate({
            data: {
                columns: bb_convert(max_n(d, "page", "accesses"), ["page", "accesses"], false),
                type: "pie"
            },
            bindto: "#access_page"
        });
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

}
