/**
 * Created by restran on 2015/7/11.
 */
(function () {
    var app = angular.module('app', []);
    app.controller('appCtrl', ['$scope', '$http', '$timeout', '$filter', function ($scope, $http, $timeout, $filter) {

        // 由于django的csrftoken保护
        $http.defaults.xsrfCookieName = 'csrftoken';
        $http.defaults.xsrfHeaderName = 'X-CSRFToken';

        // JS获得当前时间 并格式化为:yyyy-MM-dd HH:MM:SS
        function getNowFormatDate() {
            var date = new Date();
            var seperator1 = "-";
            var seperator2 = ":";
            var month = date.getMonth() + 1;
            var strDate = date.getDate();
            if (month >= 1 && month <= 9) {
                month = "0" + month;
            }
            if (strDate >= 0 && strDate <= 9) {
                strDate = "0" + strDate;
            }
            return date.getFullYear() + seperator1 + month + seperator1 + strDate
                + " " + date.getHours() + seperator2 + date.getMinutes()
                + seperator2 + date.getSeconds();
        }

        $scope.selectedDate = getNowFormatDate().slice(0, 10);
        console.log($scope.selectedDate);

        // 访问IP统计
        $scope.ipCountList = [];

        // 获取应用的访问计数
        $scope.getAppAccessCount = function () {
            $timeout(function () {
                NProgress.start();
            });

            if ($scope.selectedAgents == null || $scope.selectedAgents.length == 0) {
                load_echarts([], [], []);
                NProgress.done();
                return;
            }

            var date, year, month;
            if ($scope.viewMode == 'month') {
                year = $scope.selectedDate.slice(0, 4);
                month = $scope.selectedDate.slice(5, 7);
            } else {
                date = $scope.selectedDate;
            }

            var agent_id_list = [];
            var agent_name_list = [];
            var name_dict = {
                '-1': '所有应用', '-100': 'Success', '-101': 'Forbidden', '-102': 'Proxy Failed',
                '-105': 'Expired Token', '-103': 'Login Validated Failed', '-104': 'Unknown'
            };
            for (var i = 0; i < $scope.selectedAgents.length; i++) {
                var index = parseInt($scope.selectedAgents[i]);
                if (index < 0) {
                    agent_id_list.push(index);
                    agent_name_list.push(name_dict[$scope.selectedAgents[i]]);
                } else {
                    agent_id_list.push($scope.accessAgentOptions[index].id);
                    agent_name_list.push($scope.accessAgentOptions[index].name);
                }
            }

            var post_url;
            var post_data;
            if ($scope.viewMode == 'month') {
                post_url = '/api/dashboard/get_total_by_month_access/';
                post_data = {'year': year, 'month': month, 'agent_id_list': agent_id_list};
            } else {
                post_url = '/api/dashboard/get_total_by_day_access/';
                post_data = {'date': date, 'agent_id_list': agent_id_list};
            }

            var get_access_count_done = false;
            var get_ip_count_done = false;
            var get_abnormal_ip_count_done = false;

            post_data['request_type'] = $scope.requestType;
            $http({
                url: post_url,
                method: 'POST',
                async: true,
                cache: false,
                data: post_data,
                headers: {'Content-Type': 'application/json; charset=utf-8'}
            }).success(function (data, status, headers, config) {
                console.log(data);
                if (data['success'] == true) {
                    var series = [];
                    for (var j = 0; j < data['data'].length; j++) {
                        var serie = {
                            name: agent_name_list[j],
                            type: 'line',
                            data: data['data'][j],
                            smooth: true,
                            itemStyle: {normal: {areaStyle: {type: 'default'}}},
                            markPoint: {
                                data: [
                                    {type: 'max', name: '最大值'},
                                    {type: 'min', name: '最小值'}
                                ]
                            }
                        };

                        series.push(serie);
                    }

                    load_echarts(agent_name_list, data['x-data'], series);
                } else {
                    toastr["error"]('获取数据失败');
                }
            }).error(function (data, status, headers, config) {
                toastr["error"]('获取数据失败');
            }).finally(function () {
                get_access_count_done = true;
                if (get_ip_count_done == true && get_abnormal_ip_count_done == true) {
                    $timeout(function () {
                        NProgress.done();
                    });
                } else {
                    $timeout(function () {
                        NProgress.inc();
                    });
                }
            });

            // 获取访问IP统计
            $http({
                url: '/api/dashboard/get_ip_count/',
                method: 'POST',
                async: true,
                cache: false,
                data: post_data,
                headers: {'Content-Type': 'application/json; charset=utf-8'}
            }).success(function (data, status, headers, config) {
                console.log(data);
                if (data['success'] == true) {
                    $scope.ipCountList = data['data'];
                    console.log(data['data']);
                } else {
                    toastr["error"]('获取IP统计数据失败');
                }
            }).error(function (data, status, headers, config) {
                toastr["error"]('获取IP统计数据失败');
            }).finally(function () {
                get_ip_count_done = true;
                if (get_access_count_done == true && get_abnormal_ip_count_done == true) {
                    $timeout(function () {
                        NProgress.done();
                    });
                } else {
                    $timeout(function () {
                        NProgress.inc();
                    });
                }
            });


            // 获取异常访问IP统计
            $http({
                url: '/api/dashboard/get_abnormal_ip_count/',
                method: 'POST',
                async: true,
                cache: false,
                data: post_data,
                headers: {'Content-Type': 'application/json; charset=utf-8'}
            }).success(function (data, status, headers, config) {
                console.log(data);
                if (data['success'] == true) {
                    $scope.abnormalIpCountList = data['data'];
                    console.log(data['data']);
                } else {
                    toastr["error"]('获取IP统计数据失败');
                }
            }).error(function (data, status, headers, config) {
                toastr["error"]('获取IP统计数据失败');
            }).finally(function () {
                get_abnormal_ip_count_done = true;
                if (get_access_count_done == true && get_ip_count_done == true) {
                    $timeout(function () {
                        NProgress.done();
                    });
                } else {
                    $timeout(function () {
                        NProgress.inc();
                    });
                }
            });
        };

        // 获取累计访问计数
        $scope.getTotalCount = function () {
            var api_url = '/api/dashboard/get_total_count/?request_type=' + $scope.requestType;
            $http.get(api_url).success(function (data, status, headers, config) {
                console.log(data);
                if (data['success'] == true) {
                    $scope.totalCount.totalCount = data['data']['total_count'];
                    $scope.totalCount.todayCount = data['data']['today_count'];
                    $scope.totalCount.yesterdayCount = data['data']['yesterday_count'];
                    $timeout(function () {
                        // 因为 data-to 第一次以后的获取有问题，因此这里直接传
                        $('#count2-total-count').countTo({to: $scope.totalCount.totalCount});
                        $('#count2-yesterday-count').countTo({to: $scope.totalCount.yesterdayCount});
                        $('#count2-today-count').countTo({to: $scope.totalCount.todayCount});
                    });

                } else {
                    toastr["error"]('获取数据失败');
                }

            }).error(function (data, status, headers, config) {
                toastr["error"]('获取数据失败');
            }).finally(function () {
            });
        };

        // 获取AccessAgentOptions
        $scope.getAccessAgentOptions = function () {
            var api_url = '/api/dashboard/get_access_agent_options/';
            $http.get(api_url).success(function (data, status, headers, config) {
                console.log(data);
                if (data['success'] == true) {
                    $scope.accessAgentOptions = data['data'];
                    console.log($scope.accessAgentOptions);

                    $timeout(function () {
                        var ele_select_agents = $('#select-access-agent');
                        ele_select_agents.selectpicker('refresh');
                        ele_select_agents.selectpicker('val', '-1');
                    });

                } else {
                    toastr["error"]('获取数据失败');
                }

            }).error(function (data, status, headers, config) {
                toastr["error"]('获取数据失败');
            }).finally(function () {
            });
        };

        // 选择的日期发生变化
        $scope.selectedDateChange = function () {
            $scope.getAppAccessCount();
        };

        $scope.viewMode = 'day';
        // 访问类型
        $scope.requestType = 'all';

        // 查看模式发生变化
        $scope.viewModeChange = function (mode) {
            $scope.viewMode = mode;
            var ele_datetime = $('#date-time');
            if (mode == 'month') {
                // 需要先清除，否则datetimepicker无法刷新
                ele_datetime.datetimepicker('remove');
                ele_datetime.datetimepicker({
                    minView: 3,// 只显示到月选择
                    language: 'zh-CN',
                    autoclose: true,
                    startView: 3,// 一开始就显示到月选择
                    format: "yyyy-mm"
                });

                $scope.selectedDate = getNowFormatDate().slice(0, 7);
            } else {
                ele_datetime.datetimepicker('remove');
                ele_datetime.datetimepicker({
                    minView: 2,// 只显示到天选择
                    language: 'zh-CN',
                    autoclose: true,
                    todayHighlight: true,
                    format: "yyyy-mm-dd"
                });

                $scope.selectedDate = getNowFormatDate().slice(0, 10);
            }

            $scope.getAppAccessCount();
        };

        // 访问类型发生变化
        $scope.requestTypeChange = function (type) {
            $scope.requestType = type;
            $scope.getTotalCount();
            $scope.getAppAccessCount();
        };

        // 路径配置
        require.config({
            paths: {
                echarts: '/static/js/echarts/dist'
            }
        });

        var load_echarts = function (legend_data, x_data, series) {
            // 使用
            require(
                [
                    'echarts',
                    'echarts/chart/line'
                ], // 按需加载
                function (ec) {
                    // 基于准备好的dom，初始化echarts图表
                    var myChart = ec.init(document.getElementById('main'), 'macarons');

                    var option = {
                        title: {
                            show: false,
                            text: '',
                            subtext: ''
                        },
                        tooltip: {
                            trigger: 'axis'
                        },
                        legend: {
                            data: legend_data
                        },
                        calculable: false,
                        grid: {
                            x: 65,
                            y: 100,
                            x2: 20,
                            y2: 60
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
                                data: x_data
                            }
                        ],
                        yAxis: [
                            {
                                splitLine: {},
                                splitArea: {
                                    show: false
                                },
                                type: 'value',
                                axisLabel: {
                                    formatter: '{value}'
                                }
                            }
                        ],
                        series: series
                    };

                    // 为echarts对象加载数据
                    myChart.setOption(option);
                }
            );
        };


        //---------------------------------------------
        $(document).ready(function () {
            $("#date-time").datetimepicker({
                minView: 2,// 只显示到月
                language: 'zh-CN',
                autoclose: true,
                todayHighlight: true,
                format: "yyyy-mm-dd"
            });

            $('[data-toggle="popover"]').popover();
            $('[data-toggle="tooltip"]').tooltip();

            $('.selectpicker').selectpicker();
            var ele_select_agents = $('#select-access-agent');
            // 默认选择所有应用
            ele_select_agents.selectpicker('val', '-1');
            var $selectpicker = ele_select_agents.data('selectpicker').$newElement;

            // selectpicker 隐藏的时候，才更新数据
            $selectpicker.on('hide.bs.dropdown', function () {
                console.log('hide');
                $scope.getAppAccessCount();
                $scope.$apply();
            });
        });

        //----------------------------------
        $scope.totalCount = {};
        $scope.accessAgentOptions = [];
        // 选择的AccessAgent
        $scope.selectedAgents = [-1];
        $scope.getAccessAgentOptions();
        $scope.getTotalCount();
        $scope.getAppAccessCount();
    }]);

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
