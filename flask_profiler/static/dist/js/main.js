var profile = {
  config: { dataLength: 0 },
  columnsIndex: { grouped: ["method", "name", "count", "avgElapsed", "maxElapsed", "minElapsed"], filter: ["method", "name", "elapsed", "startedAt"] },
  getData: function (a, b) {
    a = a || "grouped";
    var c,
      d = this,
      b = this.createQueryParams(a);
    return (
      $.ajax({
        type: "GET",
        async: !1,
        url: "api/measurements/" + ("grouped" === a ? a + "/" : ""),
        dataType: "json",
        data: b,
        success: function (a) {
          (c = d.dataTableClassifier(a.measurements)), (d.createdTime = moment());
        },
      }),
      c
    );
  },
  dataTableClassifier: function (a) {
    var b = this.dataTableOption;
    ajaxData = a.measurements || a;
    var c = Object.keys(ajaxData).length;
    return (c = b.length === c ? b.length + b.start + c : b.start + c), { draw: b.draw, recordsFiltered: c, recordsTotal: c, data: ajaxData };
  },
  createQueryParams: function (a, b) {
    var c,
      d = b || this.dataTableOption,
      e = d.order[0],
      f = {};
    if ("filtered" === a) {
      var g = $("#filteredTable select.method").val();
      (c = this.columnsIndex.filter), "ALL" === g && (g = ""), (f.method = g), (f.name = $("#filteredTable input.filtered-name").val()), (f.elapsed = $("#filteredTable input.elapsed").val() || 0);
    } else c = this.columnsIndex.grouped;
    return (f.sort = c[e.column] + "," + e.dir), (f.skip = d.start), (f.limit = d.length), (f.startedAt = this.dateTime.startedAt), (f.endedAt = this.dateTime.endedAt), f;
  },
};
(window.profile = profile), (window.dayFilterValue = "day"), (window.profile.dateTime = { startedAt: moment().subtract(6, "days").unix(), endedAt: moment().unix() });
var setFilteredTable = function () {
    var a = $("#filteredTable").DataTable({
      processing: !0,
      serverSide: !0,
      ajax: function (a, b, c) {
        (window.profile.dataTableOption = a), b(window.profile.getData("filtered"));
      },
      responsive: !1,
      paging: !0,
      pageLength: 100,
      dom: "Btrtip",
      stateSave: !0,
      order: [3, "desc"],
      autoWidth: !1,
      language: { processing: "Loading...", buttons: { colvis: '<span class="glyphicon glyphicon-filter"></span>' } },
      buttons: [{ extend: "colvis", columns: [":gt(1)"] }],
      columns: [
        {
          title: "method",
          data: function (a) {
            return '<span class="row--method ' + a.method.toLowerCase() + '">' + a.method + "</span>";
          },
          class: "method",
          orderable: !1,
        },
        {
          title: "name",
          data: function (a, b) {
            var c = document.createElement("div");
            return (c.innerText = a.name), "display" === b ? "<span data-json='" + JSON.stringify(a.context) + "'>" + c.innerHTML + "</span>" : c.innerHTML;
          },
          class: "name",
          orderable: !1,
        },
        {
          title: "elapsed",
          data: function (a) {
            return a.elapsed.toString().slice(0, 8);
          },
          class: "elapsed number",
        },
        {
          title: "startedAt",
          data: function (a) {
            return moment.unix(a.startedAt).format("DD/MM/YYYY h:mm:ss.MS A");
          },
          class: "startedAt",
        },
      ],
      initComplete: function () {
        $("#filteredTable>thead").append($("#filteredTable .filter-row")),
          $(".filtered-datepicker").daterangepicker(
            { timePicker: !0, timePickerSeconds: !0, startDate: moment.unix(window.profile.dateTime.startedAt).format("MM/DD/YYYY"), endDate: moment.unix(window.profile.dateTime.endedAt).format("MM/DD/YYYY") },
            function (b, c, d) {
              (profile.dateTime = { startedAt: b.unix(), endedAt: c.unix() }), a.draw();
            }
          ),
          $("#filteredTable").removeClass("loading");
      },
      drawCallback: function () {
        $("#filteredTable tbody").on("click", "tr", function () {
          $(".filteredModal .modal-body").JSONView(JSON.stringify($(this).find("[data-json]").data("json"))), $(".filteredModal").modal("show");
        }),
          $("#filteredTable").removeClass("loading"),
          $("html").animate({ scrollTop: 0 }, 300);
      },
    });
    $("#filteredTable select.method, #filteredTable input.filtered-name, #filteredTable input.elapsed")
      .off()
      .on("input", function () {
        $("#filteredTable").addClass("loading"), a.draw();
      }),
      $(".clear-filter")
        .off()
        .on("click", function () {
          var b = $(".filtered-datepicker");
          $("#filteredTable select.method").val("ALL"),
            $("#filteredTable input.filtered-name").val(""),
            $("#filteredTable input.elapsed").val(""),
            b.data("daterangepicker").setStartDate(moment().subtract(7, "days").format("MM/DD/YYYY")),
            b.data("daterangepicker").setEndDate(moment().format("MM/DD/YYYY")),
            a.draw();
        });
  },
  getCharts = function () {
    $.ajax({
      type: "GET",
      async: !0,
      url: "api/measurements/methodDistribution/",
      dataType: "json",
      data: { startedAt: window.profile.dateTime.startedAt, endedAt: window.profile.dateTime.endedAt },
      success: function (a) {
        var b = a.distribution,
          c = [];
        for (key in b) b.hasOwnProperty(key) && c.push([key, b[key]]);
        c3.generate({
          bindto: "#pieChart",
          data: { columns: c, type: "pie", colors: { GET: "#4BB74B", PUT: "#0C8DFB", DELETE: "#FB6464", POST: "#2758E4" } },
          tooltip: {
            format: {
              value: function (a, b, c) {
                return a;
              },
            },
          },
          color: { pattern: ["#9A9A9A"] },
        });
        $("#pieChart").removeClass("loading");
      },
    }),
      $.ajax({
        type: "GET",
        async: !0,
        url: "api/measurements/timeseries/",
        dataType: "json",
        data: { interval: "hours" !== window.dayFilterValue ? "daily" : "hourly", startedAt: window.profile.dateTime.startedAt, endedAt: window.profile.dateTime.endedAt },
        success: function (a) {
          var b = a.series,
            c = ["data"],
            d = [];
          for (var e in b) c.push(b[e]);
          if ("hours" === window.dayFilterValue) for (var e in Object.keys(b)) d.push(Object.keys(b)[e].substr(-2, 2));
          else d = Object.keys(b);
          c3.generate({ bindto: "#lineChart", data: { columns: [c], type: "area" }, axis: { x: { type: "category", categories: d } }, legend: { show: !1 }, color: { pattern: ["#EC5B19"] } });
          $("#lineChart").removeClass("loading");
        },
      });
  };
$(document).ready(function () {
  $('a[data-toggle="tab"]').historyTabs(),
    $("#big-users-table").on("preXhr.dt", function (a, b, c) {
      window.profile.dataTableOption = c;
      var d = profile.createQueryParams("grouped", c);
      for (key in d) d.hasOwnProperty(key) && (c[key] = d[key]);
    });
  var a = $("#big-users-table").DataTable({
    processing: !0,
    serverSide: !0,
    ajax: {
      url: "api/measurements/grouped",
      dataSrc: function (a) {
        var b = profile.dataTableClassifier(a.measurements);
        return b.data;
      },
    },
    responsive: !1,
    paging: !1,
    pageLength: 1e4,
    dom: "Btrtip",
    stateSave: !0,
    autoWidth: !1,
    order: [2, "desc"],
    language: { processing: "Loading...", buttons: { colvis: '<span class="glyphicon glyphicon-filter"></span>' } },
    buttons: [{ extend: "colvis", columns: [":gt(1)"] }],
    columns: [
      {
        title: "method",
        data: function (a) {
          return '<span class="row--method ' + a.method.toLowerCase() + '">' + a.method + "</span>";
        },
        class: "method",
        orderable: !1,
      },
      {
        title: "name",
        data: function (a) {
          var b = document.createElement("div");
          return (b.innerText = a.name), b.innerHTML;
        },
        class: "name",
        orderable: !1,
      },
      { title: "count", data: "count", class: "number" },
      {
        title: "avg elapsed",
        data: function (a) {
          return a.avgElapsed.toString().slice(0, 8);
        },
        class: "number",
      },
      {
        title: "max elapsed",
        data: function (a) {
          return a.maxElapsed.toString().slice(0, 8);
        },
        class: "number",
      },
      {
        title: "min elapsed",
        data: function (a) {
          return a.minElapsed.toString().slice(0, 8);
        },
        class: "number",
      },
    ],
    drawCallback: function () {
      $("#big-users-table tbody tr")
        .off()
        .on("click", function (a) {
          if ("A" !== $(a.target).prop("tagName")) {
            var b = $(".filtered-datepicker");
            $("#filteredTable .filter-row .filtered-name").val($(this).find("td.name").text()).trigger("input"),
              $("#filteredTable .filter-row .method").val($(this).find(".method .row--method").text()).trigger("input"),
              "object" == typeof b.data("daterangepicker") &&
                (b.data("daterangepicker").setStartDate(moment.unix(window.profile.dateTime.startedAt).format("MM/DD/YYYY")), b.data("daterangepicker").setEndDate(moment.unix(window.profile.dateTime.endedAt).format("MM/DD/YYYY"))),
              setFilteredTable(),
              $('[data-target="#tab-filtering"]').tab("show");
          }
        });
    },
    initComplete: function () {},
  });
  $(document).on("popstate", function (a) {
    console.log(a);
  }),
    $('[data-target="#tab-filtering"]').on("show.bs.tab", function () {
      setFilteredTable();
    }),
    $(".day-filter label").on("click", function (b) {
      $("#lineChart, #pieChart").addClass("loading");
      var c,
        d = $(this).find("input").val();
      window.dayFilterValue !== d,
        (window.dayFilterValue = $(this).find("input").val()),
        (c =
          "min" === window.dayFilterValue
            ? { startedAt: moment().subtract(1, "hours").unix(), endedAt: moment().unix() }
            : "hours" === window.dayFilterValue
            ? { startedAt: moment().subtract(24, "hours").unix(), endedAt: moment().unix() }
            : "days" === window.dayFilterValue
            ? { startedAt: moment().subtract(7, "days").unix(), endedAt: moment().unix() }
            : { startedAt: moment().subtract(30, "days").unix(), endedAt: moment().unix() }),
        (window.profile.dateTime = c),
        getCharts(),
        a.draw();
    }),
    getCharts(),
    (function b() {
      $(".created-time").text("Created " + moment(profile.createdTime).fromNow()), setTimeout(b, 5e3);
    })();
}),
  $(document).on("show.bs.tab", '[data-target="#tab-filtering"]', function (a) {
    setFilteredTable();
  });
