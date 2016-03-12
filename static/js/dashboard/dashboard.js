/**
 * Created by restran on 2015/7/11.
 */
(function () {
    var app = new Vue({
        el: '#dashboard-app',
        data: {
            disableTimeFrame: false,
            sum7d: '',
            totalCount: 0,
            beginTime: '',
            endTime: '',
            selectedTimeFrame: '24h',
            selectedClients: ['-1'],
            selectedEndpoints: [],
            selectedClientEndpoints: [],
            selectedResults: [],
            clientOptions: [],
            endpointOptions: [],
            clientEndpointOptions: [],
            clientOptionDict: {},
            endpointOptionDict: {},
            clientEndpointOptionDict: {},
            resultOptionDict: {
                '200': '200 成功',
                '400': '400 请求数据不完整',
                '401': '401 登录验证失败',
                '403': '403 HMAC 鉴权失败',
                '500': '500 服务端错误',
                '503': '504 Endpoint 服务不可用',
                '510': '510 Client 配置有误'
            }
        },
        computed: {},
        methods: {
            loadOptions: function () {
                var apiUrl = '/api/dashboard/get_options/';
                $request.get(apiUrl, null, function (data) {
                    app.clientOptions = data['data']['clients'];
                    app.endpointOptions = data['data']['endpoints'];
                    app.clientEndpointOptions = data['data']['client_endpoints'];
                    var i, item;
                    for (i = 0; i < app.clientOptions.length; i++) {
                        item = app.clientOptions[i];
                        app.clientOptionDict[item.id] = item.name;
                    }
                    app.clientOptionDict['-1'] = '所有应用';
                    for (i = 0; i < app.endpointOptions.length; i++) {
                        item = app.endpointOptions[i];
                        app.endpointOptionDict[item.id] = item['unique_name'];
                    }
                    for (i = 0; i < app.clientEndpointOptions.length; i++) {
                        item = app.clientEndpointOptions[i];
                        console.log(item);
                        console.log(item.client_id + '/' + item.endpoint_id);
                        app.clientEndpointOptionDict[item.client_id + '/' + item.endpoint_id] = item.name;
                    }

                    Vue.nextTick(function () {
                        // DOM 更新了
                        var ele = $('#select-client');
                        ele.selectpicker('refresh');
                        //ele.selectpicker('val', '-1');
                        $('#select-endpoint').selectpicker('refresh');
                        $('#select-client-endpoint').selectpicker('refresh');
                    });
                }, function (data, msg) {
                    toastr["error"](msg);
                })
            },
            search: function () {
                if (this.checkDateTime() == false) {
                    return;
                }
                Pace.restart();
                console.log('search');
                var client_endpoint_list = [];
                var i, item;
                for (i = 0; i < this.selectedClientEndpoints.length; i++) {
                    item = this.clientEndpointOptions[this.selectedClientEndpoints[i]];
                    client_endpoint_list.push([item.client_id, item.endpoint_id]);
                }
                var postData = {
                    'by_search': true,
                    'begin_time': this.beginTime,
                    'end_time': null,
                    'client_list': this.selectedClients,
                    'endpoint_list': this.selectedEndpoints,
                    'client_endpoint_list': client_endpoint_list,
                    'result_code_list': this.selectedResults
                };
                if (this.disableTimeFrame == false) {
                    postData['time_frame'] = this.selectedTimeFrame;
                }
                if (this.endTime != null && this.endTime != '') {
                    postData['end_time'] = this.endTime;
                }

                var nameMap = {
                    'total': '全部应用',
                    'client': {},
                    'endpoint': {},
                    'client_endpoint': {},
                    'result_code': {}
                };

                var clientMap = {};
                for (i = 0; i < postData['client_list'].length; i++) {
                    item = postData['client_list'][i];
                    clientMap[item] = this.clientOptionDict[item];
                }
                nameMap['client'] = clientMap;

                var endpointMap = {};
                for (i = 0; i < postData['endpoint_list'].length; i++) {
                    item = postData['endpoint_list'][i];
                    endpointMap[item] = this.endpointOptionDict[item];
                }
                nameMap['endpoint'] = endpointMap;

                var clientEndpointMap = {};
                for (i = 0; i < postData['client_endpoint_list'].length; i++) {
                    item = postData['client_endpoint_list'][i];
                    var k = item[0] + '/' + item[1];
                    clientEndpointMap[k] = this.clientEndpointOptionDict[k];
                }
                nameMap['client_endpoint'] = clientEndpointMap;

                var resultMap = {};
                for (i = 0; i < postData['result_code_list'].length; i++) {
                    item = postData['result_code_list'][i];
                    resultMap[item] = this.resultOptionDict[item];
                }
                nameMap['result_code'] = resultMap;

                postData['name_map'] = nameMap;

                var apiUrl = '/api/dashboard/query_access_count/';
                console.log(postData);
                $request.post(apiUrl, postData, function (data) {
                    console.log(data);
                    var x_data = data['data']['x_data'];
                    var y_data = data['data']['y_data'];
                    app.renderChart(x_data, y_data);
                }, function (data, msg) {
                    toastr["error"](msg);
                });
            },
            switchTimeFrame: function () {
                this.search();
            },
            renderChart: function (x_data, y_data) {
                var legend = [];
                var series = [];
                console.log(y_data.length);
                for (var i = 0; i < y_data.length; i++) {
                    var item = y_data[i];
                    legend.push(item[0]);
                    var entry = {
                        name: item[0],
                        type: 'line',
                        areaStyle: {normal: {opacity: 0.25}},
                        markPoint: {
                            data: [
                                {type: 'max', name: '最大值'}
                                //{type: 'min', name: '最小值'}
                            ]
                        },
                        data: item[1]
                    };

                    series.push(entry);
                }
                option.legend.data = legend;
                console.log(legend);
                console.log(x_data);
                console.log(series);
                option.xAxis[0].data = x_data;
                option.series = series;
                console.log(option);
                chart.clear();
                chart.setOption(option);
            },
            loadRecentTotal: function () {
                var postData = {
                    'by_search': false,
                    'begin_time': this.beginTime,
                    'end_time': null,
                    'time_frame': '7d'
                };

                postData['name_map'] = {
                    'total': '全部应用'
                };

                var apiUrl = '/api/dashboard/query_access_count/';
                console.log(postData);
                $request.post(apiUrl, postData, function (data) {
                    console.log(data);
                    var x_data = data['data']['x_data'];
                    var y_data = data['data']['y_data'];
                    var legend = [];
                    var series = [];
                    for (var i = 0; i < y_data.length; i++) {
                        var item = y_data[i];
                        legend.push(item[0]);
                        var entry = {
                            name: item[0],
                            type: 'line',
                            areaStyle: {normal: {opacity: 0.25}},
                            markPoint: {
                                data: [
                                    //{type: 'max', name: '最大值'},
                                    //{type: 'min', name: '最小值'}
                                ]
                            },
                            data: item[1]
                        };
                        var sum = 0;
                        for (i = 0; i < item[1].length; i++) {
                            sum += item[1][i];
                        }
                        app.sum7d = sum;
                        series.push(entry);
                    }
                    optionTotal.xAxis[0].data = x_data;
                    optionTotal.series = series;
                    chartTotal.clear();
                    chartTotal.setOption(optionTotal);
                }, function (data, msg) {
                    toastr["error"](msg);
                });
            },
            checkDateTime: function () {
                if (this.beginTime != '' && this.endTime != '') {
                    if (this.beginTime > this.endTime) {
                        toastr['error']('开始时间不能大于结束时间');
                        return false;
                    }
                }

                return true;
            },
            getTotalCount: function () {
                var apiUrl = '/api/dashboard/get_total_count/';
                $request.get(apiUrl, null, function (data) {

                    app.totalCount = data['data']['total_count'];
                    Vue.nextTick(function () {
                        // DOM 更新了
                        $('#count2-total-count').countTo({to: app.totalCount});
                    });
                    console.log(app.totalCount);
                }, function (data, msg) {
                    toastr["error"](msg);
                });
            }
        },
        watch: {
            selectedTimeFrame: function () {
                console.log('selectedTimeFrame change');
                this.switchTimeFrame();
            },
            beginTime: function () {
                this.checkDateTime();
                this.disableTimeFrame = (this.beginTime != '');
                Vue.nextTick(function () {
                    // DOM 更新了
                    $('#select-time-frame').selectpicker('refresh');
                });
            },
            endTime: function () {
                this.checkDateTime();
            }
        }
    });

    var ratioApp = new Vue({
        el: '#ratio-app',
        data: {
            disableTimeFrame: false,
            beginTime: '',
            endTime: '',
            selectedTimeFrame: '24h'
        },
        computed: {},
        methods: {
            search: function () {
                if (this.checkDateTime() == false) {
                    return;
                }
                Pace.restart();
                console.log('search');

                var postData = {
                    'begin_time': this.beginTime,
                    'end_time': this.endTime
                };

                if (this.disableTimeFrame == false) {
                    postData['time_frame'] = this.selectedTimeFrame;
                }

                this.getCountRatio(postData);
            },
            switchTimeFrame: function () {
                this.search();
            },
            checkDateTime: function () {
                this.disableTimeFrame = (this.beginTime != '');
                Vue.nextTick(function () {
                    // DOM 更新了
                    $('#select-time-frame').selectpicker('refresh');
                });

                if (this.beginTime != '' && this.endTime != '') {
                    if (this.beginTime > this.endTime) {
                        toastr['error']('开始时间不能大于结束时间');
                        return false;
                    }
                }

                return true;
            },
            getCountRatio: function (postData) {
                var apiUrl = '/api/dashboard/get_client_ratio/';
                $request.post(apiUrl, postData, function (data) {
                    var legend = data['data']['legend'];
                    var y_data = data['data']['y_data'];
                    var optionClient = {
                        title: {
                            text: '应用访问占比',
                            subtext: '',
                            x: 'center'
                        },
                        tooltip: {
                            trigger: 'item',
                            formatter: "{a} <br/>{b}: {c} ({d}%)"
                        },
                        legend: {
                            orient: 'vertical',
                            x: 'left',
                            data: legend
                        },
                        series: [
                            {
                                name: '应用访问占比',
                                type: 'pie',
                                radius: ['40%', '55%'],
                                data: y_data
                            }
                        ]
                    };
                    chartClientRatio.clear();
                    chartClientRatio.setOption(optionClient);
                }, function (data, msg) {
                    toastr["error"](msg);
                });

                apiUrl = '/api/dashboard/get_endpoint_ratio/';
                $request.post(apiUrl, postData, function (data) {
                    var legend = data['data']['legend'];
                    var y_data = data['data']['y_data'];
                    var optionEndpoint = {
                        title: {
                            text: 'API 端点访问占比',
                            subtext: '',
                            x: 'center'
                        },
                        tooltip: {
                            trigger: 'item',
                            formatter: "{a} <br/>{b}: {c} ({d}%)"
                        },
                        legend: {
                            orient: 'vertical',
                            x: 'left',
                            data: legend
                        },
                        series: [
                            {
                                name: 'API 端点访问占比',
                                type: 'pie',
                                radius: ['40%', '55%'],
                                data: y_data
                            }
                        ]
                    };
                    chartEndpointRatio.clear();
                    chartEndpointRatio.setOption(optionEndpoint);
                }, function (data, msg) {
                    toastr["error"](msg);
                });
            }
        },
        watch: {
            selectedTimeFrame: function () {
                console.log('selectedTimeFrame change');
                this.switchTimeFrame();
            },
            beginTime: function () {
                this.checkDateTime();
            },
            endTime: function () {
                this.checkDateTime();
            }
        }
    });

    // 第二个参数可以指定前面引入的主题
    var chart = echarts.init(document.getElementById('echarts-main'), 'macarons');
    var chartTotal = echarts.init(document.getElementById('echarts-total'), 'macarons');
    var chartClientRatio = echarts.init(document.getElementById('echarts-client-ratio'), 'macarons');
    var chartEndpointRatio = echarts.init(document.getElementById('echarts-endpoint-ratio'), 'macarons');

    var option = {
        title: {
            text: '',
            show: false
        },
        tooltip: {
            trigger: 'axis'
        },
        legend: {
            data: []
        },
        toolbox: {
            feature: {
                saveAsImage: {}
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: [
            {
                splitLine: {
                    show: false
                },
                splitArea: {
                    show: false
                },
                type: 'category',
                boundaryGap: false,
                data: []
            }
        ],
        yAxis: [
            {
                splitLine: {
                    show: true
                },
                splitArea: {
                    show: false
                },
                type: 'value'
            }
        ],
        series: []
    };
    var optionTotal = {
        title: {
            text: '',
            show: false
        },
        tooltip: {
            trigger: 'axis'
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '0%',
            top: '10%',
            containLabel: true
        },
        xAxis: [
            {
                splitLine: {
                    show: false
                },
                splitArea: {
                    show: false
                },
                type: 'category',
                boundaryGap: false,
                data: []
            }
        ],
        yAxis: [
            {
                splitLine: {
                    show: false
                },
                splitArea: {
                    show: false
                },
                splitNumber: 3,
                axisTick: {
                    show: true
                },
                axisLabel: {},
                type: 'value'
            }
        ],
        series: []
    };
    //chart.setOption(option);
    app.loadOptions();
    app.switchTimeFrame();
    app.getTotalCount();
    app.loadRecentTotal();

    ratioApp.switchTimeFrame();

    $(document).ready(function () {
        $(".date-hour").datetimepicker({
            minView: 0, // 显示到分
            language: 'zh-CN',
            autoclose: true,
            todayHighlight: true,
            format: "yyyy-mm-dd hh:ii"
        });

        $(".date-day").datetimepicker({
            minView: 2,
            language: 'zh-CN',
            autoclose: true,
            todayHighlight: true,
            format: "yyyy-mm-dd"
        });

        $('.selectpicker').selectpicker();

        $('[data-toggle="tooltip"]').tooltip();
        $('[data-toggle="popover"]').popover();

        $(window).on('resize', function () {
            console.log('resize');
            chart.resize();
            chartTotal.resize();
            chartClientRatio.resize();
            chartEndpointRatio.resize();
        });
    });
})();


(function ($) {
    $.fn.selectpicker.defaults = {
        noneSelectedText: '没有选中任何项',
        noneResultsText: '没有找到匹配项',
        countSelectedText: '选中{1}中的{0}项',
        maxOptionsText: ['超出限制 (最多选择{n}项)', '组选择超出限制(最多选择{n}组)'],
        multipleSeparator: ', '
    };
}(jQuery));
