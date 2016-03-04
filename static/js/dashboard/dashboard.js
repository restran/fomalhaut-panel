/**
 * Created by restran on 2015/7/11.
 */
(function () {
    var app = new Vue({
        el: '#dashboard-app',
        data: {
            baseTime: null,
            selectedClients: [],
            selectedEndpoints: [],
            selectedResults: [],
            clientOptions: [],
            endpointOptions: [],
            clientEndpointOptions: [],
            entriesReady: false,
            entries: [],
            cachedQuery: null
        },
        computed: {},
        methods: {
            loadOptions: function () {
                var apiUrl = '/api/dashboard/get_options/';
                $request.get(apiUrl, null, function (data) {
                    app.clientOptions = data['data']['clients'];
                    app.endpointOptions = data['data']['endpoints'];
                    app.clientEndpointOptions = data['data']['client_endpoints'];

                    Vue.nextTick(function () {
                        // DOM 更新了
                        $('#select-client').selectpicker('refresh');
                        $('#select-endpoint').selectpicker('refresh');
                        $('#select-client-endpoint').selectpicker('refresh');
                    });
                }, function (data, msg) {
                    toastr["error"](msg);
                })
            },
            search: function () {
                console.log('search');
                this.getPage(1, true);
            },
            getPage: function (pageId, isSearch) {
                pageId = parseInt(pageId);
                if (isNaN(pageId)) {
                    toastr['error']('请输入整数页码');
                    return;
                }

                if (pageId < 1 || pageId > this.totalPage) {
                    console.log('error pageId ' + pageId);
                    toastr['error']('请输入正确的页码范围');
                    return;
                }

                var pageInfo = this.pageInfo;
                var skip, lastItem;
                var i;

                if (!isSearch && pageId == pageInfo.currentPage) {
                    return;
                }

                if (pageId == 1) {
                    pageInfo.currentPage = 1;
                    pageInfo.lastItem = null;
                    pageInfo.pageHistory = [];
                    pageInfo.totalNum = 0;
                } else {
                    // 记录页面历史
                    pageInfo.pageHistory.push({
                        pageId: pageInfo.currentPage,
                        lastItem: pageInfo.lastItem
                    });

                    if (pageInfo.pageHistory.length > 20) {
                        // 删掉最后一个元素
                        pageInfo.pageHistory.pop();
                    }
                }

                var minOffset = null;
                var page = null;
                for (i = 0; i < pageInfo.pageHistory.length; i++) {
                    var item = pageInfo.pageHistory[i];
                    var offset = pageId - item.pageId;
                    if (minOffset == null || (offset > 0 && offset < minOffset)) {
                        page = item;
                        minOffset = offset;
                    }
                }
                console.log(page);
                if (page != null) {
                    skip = pageInfo.pageSize * (pageId - page.pageId - 1);
                    lastItem = page.lastItem;
                } else {
                    skip = pageInfo.pageSize * (pageId - 1);
                    lastItem = null;
                }

                pageInfo.currentPage = pageId;
                var postData;
                if (pageId != 1) {
                    postData = $.extend(true, {}, this.cachedQuery);
                } else {
                    var statusList = this.status.replace('，', ',').split(',');
                    var ipList = this.ip.replace('，', ',').split(',');
                    var newIpList = [];
                    for (i = 0; i < ipList.length; i++) {
                        var ip = ipList[i].trim();
                        if (ip != '') {
                            newIpList.push(ip);
                        }
                    }
                    ipList = newIpList;

                    var newStatusList = [];
                    for (i = 0; i < statusList.length; i++) {
                        var status = statusList[i].trim();
                        if (status != '' && !isNaN(status)) {
                            newStatusList.push(parseInt(status))
                        }
                    }
                    statusList = newStatusList;
                    console.log(statusList);
                    console.log(ipList);
                    postData = {
                        'begin_time': this.beginTime,
                        'end_time': this.endTime,
                        'uri': this.uri,
                        'elapsed_min': parseInt(this.elapsedMin),
                        'elapsed_max': parseInt(this.elapsedMax),
                        'selected_clients': this.selectedClients,
                        'selected_endpoints': this.selectedEndpoints,
                        'selected_results': this.selectedResults
                    };
                    if (statusList.length == 1) {
                        postData['status'] = statusList[0];
                    } else {
                        postData['status_list'] = statusList;
                    }

                    if (ipList.length == 1) {
                        postData['ip'] = ipList[0];
                    } else {
                        postData['ip_list'] = ipList;
                    }

                    this.cachedQuery = $.extend(true, {}, postData);
                }
                postData['limit'] = pageInfo.pageSize;
                postData['skip'] = skip;
                postData['last_item'] = lastItem;

                postData['require_total_num'] = pageId == 1;

                this.getAccessLog(postData, pageId);
            },
            getAccessLog: function (postData) {
                this.entriesReady = false;
                var apiUrl = '/api/dashboard/access_log/query/';
                console.log(postData);
                $request.post(apiUrl, postData, function (data) {
                    console.log(data);
                    app.entries = data['data']['entries'];
                    var totalNum = data['data']['total_num'];
                    if (totalNum != null) {
                        app.pageInfo.totalNum = totalNum;
                        console.log(totalNum);
                    }

                    var lastItem;
                    if (app.entries.length == 0) {
                        lastItem = null;
                    } else {
                        lastItem = {
                            'id': app.entries[app.entries.length - 1]['id'],
                            'timestamp': app.entries[app.entries.length - 1]['timestamp']
                        }
                    }

                    app.pageInfo.lastItem = lastItem;
                    console.log(lastItem);

                    //if (totalNum != null) {
                    //    app.firstPageFirstItem = lastItem;
                    //}
                    Vue.nextTick(function () {
                        app.entriesReady = true;
                    });
                }, function (data, msg) {
                    toastr["error"](msg);
                    Vue.nextTick(function () {
                        app.entriesReady = true;
                    });
                })
            }
        },
        watch: {}
    });


    // 第二个参数可以指定前面引入的主题
    var chart = echarts.init(document.getElementById('echarts-main'), 'macarons');

    var option = {
        title: {
            text: '',
            show: false
        },
        tooltip: {
            trigger: 'axis'
        },
        legend: {
            data: ['邮件营销', '联盟广告', '视频广告', '直接访问', '搜索引擎']
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
                data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
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
        series: [
            {
                name: '邮件营销',
                type: 'line',
                areaStyle: {normal: {opacity: 0.25}},
                markPoint: {
                    data: [
                        {type: 'max', name: '最大值'},
                        {type: 'min', name: '最小值'}
                    ]
                },
                data: [120, 132, 101, 134, 90, 230, 210]
            },
            {
                name: '联盟广告',
                type: 'line',
                areaStyle: {normal: {opacity: 0.25}},
                markPoint: {
                    data: [
                        {type: 'max', name: '最大值'},
                        {type: 'min', name: '最小值'}
                    ]
                },
                data: [220, 182, 191, 234, 290, 330, 310]
            },
            {
                name: '视频广告',
                type: 'line',
                areaStyle: {normal: {opacity: 0.25}},
                markPoint: {
                    data: [
                        {type: 'max', name: '最大值'},
                        {type: 'min', name: '最小值'}
                    ]
                },
                data: [150, 232, 201, 154, 190, 330, 410]
            },
            {
                name: '直接访问',
                type: 'line',
                areaStyle: {normal: {opacity: 0.25}},
                markPoint: {
                    data: [
                        {type: 'max', name: '最大值'},
                        {type: 'min', name: '最小值'}
                    ]
                },
                data: [320, 332, 301, 334, 390, 330, 320]
            },
            {
                name: '搜索引擎',
                type: 'line',
                //label: {
                //    normal: {
                //        show: true,
                //        position: 'top'
                //    }
                //},
                areaStyle: {normal: {opacity: 0.25}},
                markPoint: {
                    data: [
                        {type: 'max', name: '最大值'},
                        {type: 'min', name: '最小值'}
                    ]
                },
                data: [820, 932, 901, 934, 1290, 1330, 1320]
            }
        ]
    };
    chart.setOption(option);

    app.loadOptions();


    $(document).ready(function () {
        $(".date").datetimepicker({
            minView: 0,
            language: 'zh-CN',
            autoclose: true,
            todayHighlight: true,
            format: "yyyy-mm-dd hh:ii"
        });

        $('.selectpicker').selectpicker();

        $('[data-toggle="tooltip"]').tooltip();
        $('[data-toggle="popover"]').popover();
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
