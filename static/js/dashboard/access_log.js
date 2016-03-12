/**
 * Created by restran on 2015/7/21.
 */
(function () {
    var app = new Vue({
        el: '#app',
        data: {
            query: null,
            beginTime: null,
            endTime: null,
            ip: '',
            status: '',
            uri: '',
            elapsedMin: null,
            elapsedMax: null,
            selectedClients: [],
            selectedEndpoints: [],
            selectedResults: [],
            clientOptions: [],
            endpointOptions: [],
            entriesReady: false,
            entries: [],
            pageInfo: {
                totalNum: 0,
                currentPage: null,
                pageSize: 200,
                lastItem: null,
                // 页面历史
                pageHistory: [],
                jumpPageId: null
            },
            cachedQuery: null,
            detailData: {
                request: {
                    headers: '',
                    body: ''
                },
                response: {
                    headers: '',
                    body: ''
                }
            }
        },
        computed: {
            totalPage: function () {
                var totalPage;
                if (this.pageInfo.totalNum == 0) {
                    totalPage = 1;
                } else {
                    totalPage = Math.ceil(this.pageInfo.totalNum / this.pageInfo.pageSize);
                }
                console.log(totalPage);
                return totalPage;
            },
            hasNextPage: function () {
                if (this.pageInfo.currentPage == null) {
                    return false;
                } else {
                    return this.pageInfo.currentPage < this.totalPage;
                }
            },
            hasPreviousPage: function () {
                if (this.pageInfo.currentPage == null) {
                    return false;
                } else {
                    return this.pageInfo.currentPage > 1;
                }
            },
            pageList: function () {
                var pageList = [];
                var i;
                var currentPage = this.pageInfo.currentPage;
                console.log(this.totalPage);
                if (this.totalPage <= 1) {

                } else if (this.totalPage < 7) {
                    for (i = 0; i < this.totalPage; i++) {
                        pageList.push(i + 1);
                    }
                } else {
                    pageList = [1, 2, '...', '...', '...', this.totalPage - 1, this.totalPage];
                    if (currentPage < 3) {
                    }
                    else if (currentPage == 3) {
                        pageList[2] = currentPage;
                    } else if (currentPage == this.totalPage - 2) {
                        pageList[4] = currentPage;
                    } else if (currentPage > this.totalPage - 2) {
                    } else {
                        pageList[3] = currentPage;
                    }
                }
                console.log(pageList);
                return pageList;
            },
            pageIndexOffset: function () {
                return (this.pageInfo.currentPage - 1) * this.pageInfo.pageSize;
            }
        },
        methods: {
            loadOptions: function () {
                var apiUrl = '/api/dashboard/get_client_options/';
                $request.get(apiUrl, null, function (data) {
                    app.clientOptions = data['data'];
                    console.log(app.clientOptions);
                    app.loadEndpoints();
                    Vue.nextTick(function () {
                        // DOM 更新了
                        $('#select-client').selectpicker('refresh');
                    });
                }, function (data, msg) {
                    toastr["error"](msg);
                })

            },
            loadEndpoints: function () {
                var apiUrl = '/api/dashboard/get_endpoint_options/';
                var clients = [];
                console.log(app.selectedClients);

                console.log(clients);
                var postData = {
                    'clients': this.selectedClients
                };

                $request.post(apiUrl, postData, function (data) {
                    app.endpointOptions = data['data'];
                    console.log(app.endpointOptions);

                    Vue.nextTick(function () {
                        // DOM 更新了
                        $('#select-endpoint').selectpicker('refresh');
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
                Pace.restart();
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
            },
            checkDateTime: function () {
                if (this.beginTime != null && this.beginTime != '' &&
                    this.endTime != null && this.endTime != '') {
                    if (this.beginTime > this.endTime) {
                        toastr['error']('开始时间不能大于结束时间');
                        return false;
                    }
                }
                return true;
            },
            showDetail: function (entry) {
                Pace.restart();
                $('#detail-modal').modal('show');
                $('#detail-data-tabs').find('a[href="#tab_request"]').click();
                var apiUrl = '/api/dashboard/access_log/get_access_detail/';
                var reqData = {
                    'headers_id': entry['request']['headers_id'],
                    'data_type': 'request'
                };

                $request.post(apiUrl, reqData, function (data) {
                    app.detailData.request.headers = data['data'];
                }, function (data, msg) {
                    toastr["error"](msg);
                    app.detailData.request.headers = '';
                });

                reqData = {
                    'body_id': entry['request']['body_id'],
                    'data_type': 'request'
                };

                $request.rawPost(apiUrl, reqData, function (data) {
                    app.detailData.request.body = data;
                }, function (data, msg) {
                    toastr["error"](msg);
                    app.detailData.request.body = '';
                });

                var resData = {
                    'headers_id': entry['response']['headers_id'],
                    'data_type': 'response'
                };

                $request.post(apiUrl, resData, function (data) {
                    app.detailData.response.headers = data['data'];
                }, function (data, msg) {
                    toastr["error"](msg);
                    app.detailData.response.headers = '';
                });

                resData = {
                    'body_id': entry['response']['body_id'],
                    'data_type': 'response'
                };

                $request.rawPost(apiUrl, resData, function (data) {
                    app.detailData.response.body = data;
                }, function (data, msg) {
                    toastr["error"](msg);
                    app.detailData.response.body = '';
                });
            }
        },
        watch: {
            beginTime: function () {
                this.checkDateTime();
            },
            endTime: function () {
                this.checkDateTime();
            }
        }
    });

    app.loadOptions();
    app.getPage(1);

    $(document).ready(function () {
        $(".date").datetimepicker({
            minView: 0,
            language: 'zh-CN',
            autoclose: true,
            todayHighlight: true,
            format: "yyyy-mm-dd hh:ii"
        });

        $('.selectpicker').selectpicker();
        var eleSelectClient = $('#select-client');
        // 默认选择所有应用
        //ele_select_agents.selectpicker('val', '-1');
        var $selectpickerClients = eleSelectClient.data('selectpicker').$newElement;

        // selectpicker 隐藏的时候，才更新数据
        $selectpickerClients.on('hide.bs.dropdown', function () {
            console.log('hide');
            //console.log(eleSelectClient.val());
            //headerSearch.selectedClients = eleSelectClient.val();
            app.loadEndpoints();
        });

        // 访问结果
        //var ele_select_results = $('#select-access-results');
        // 默认选择所有应用
        //ele_select_results.selectpicker('val', '-1');
        //var $selectpicker_results = ele_select_results.data('selectpicker').$newElement;

        // selectpicker 隐藏的时候，才更新数据
        //$selectpicker_results.on('hide.bs.dropdown', function () {
        //    console.log('hide');
        //    $scope.getData(1);
        //});

        $('#detail-data-tabs').click(function (e) {
            e.preventDefault();
            $(this).tab('show');
        });

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
