/**
 * Created by restran on 2015/7/21.
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

        $scope.pageId = null;

        $scope.refreshLog = function ($event) {
            console.log('refreshLog');
            var obj = $($event.currentTarget).find('span');
            if (obj.hasClass('rotate')) {
                return;
            } else {
                obj.addClass('rotate');
            }

            var post_url = '/api/dashboard/access_log/refresh/';

            $http({
                url: post_url,
                method: 'POST',
                async: true,
                cache: false,
                data: {},
                headers: {'Content-Type': 'application/json; charset=utf-8'}
            }).success(function (data) {
                if (data['success']) {
                    $scope.getData($scope.pageId);
                } else {
                    toastr["error"]('刷新日志失败');
                }
            }).error(function (data, status, headers, config) {
                toastr["error"]('刷新日志失败');
            }).finally(function () {
                obj.removeClass('rotate')
            });
        };

        $scope.getData = function (page_id) {
            if (page_id == null || page_id < 0) {
                return;
            }

            $scope.pageId = page_id;

            NProgress.start();
            var post_url = '/api/dashboard/access_log/';
            var agent_id_list = [];
            var i, index;
            for (i = 0; i < $scope.selectedAgents.length; i++) {
                index = parseInt($scope.selectedAgents[i]);
                if (index == -1) {
                    agent_id_list.push(-1);
                } else {
                    agent_id_list.push($scope.accessAgentOptions[index].id);
                }
            }

            var result_code_list = [];
            for (i = 0; i < $scope.selectedResults.length; i++) {
                var code = $scope.selectedResults[i];
                if (code == '-1') {
                    result_code_list.push('-1');
                } else {
                    result_code_list.push(code);
                }
            }

            var post_data = {
                'date': $scope.selectedDate, 'agent_id_list': agent_id_list,
                'page_id': page_id, 'result_code_list': result_code_list
            };

            $http({
                url: post_url,
                method: 'POST',
                async: true,
                cache: false,
                data: post_data,
                headers: {'Content-Type': 'application/json; charset=utf-8'}
            }).success(function (data) {
                if (data['success']) {
                    $scope.entries = data['data'];
                    $scope.page_info = data['page_info'];

                    $timeout(function () {
                        $('[data-toggle="tooltip"]').tooltip();
                    });
                } else {
                    toastr["error"]('获取数据失败');
                }
            }).error(function (data, status, headers, config) {
                toastr["error"]('获取数据失败');
            }).finally(function () {
                NProgress.done();
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
            $scope.getData(1);
        };

        // 访问日志，分页的页码跳转
        $scope.jumpPage = {
            jumpPageId: null,
            doJumpPage: function () {
                console.log($scope.jumpPage.jumpPageId);
                var jumpPageId = parseInt($scope.jumpPage.jumpPageId);
                if (isNaN(jumpPageId)) {
                    toastr['error']('请输入整数页码');
                    return;
                }
                console.log($scope.page_info['total_page']);

                if (jumpPageId < 1 || jumpPageId > $scope.page_info['total_page']) {
                    toastr['error']('请输入正确的页码范围');
                    return;
                }

                $scope.getData(jumpPageId);
            }
        };

        $scope.selectedDate = getNowFormatDate().slice(0, 10);
        $scope.accessAgentOptions = [];
        // 选择的AccessAgent
        $scope.selectedAgents = [-1];
        // 选择的访问结果
        $scope.selectedResults = [-1];

        // 获取第一页
        $scope.getData(1);
        $scope.getAccessAgentOptions();

        $(document).ready(function () {
            $("#date-time").datetimepicker({
                minView: 2,// 只显示到月
                language: 'zh-CN',
                autoclose: true,
                todayHighlight: true,
                format: "yyyy-mm-dd"
            });

            $('.selectpicker').selectpicker();
            var ele_select_agents = $('#select-access-agent');
            // 默认选择所有应用
            ele_select_agents.selectpicker('val', '-1');
            var $selectpicker_agents = ele_select_agents.data('selectpicker').$newElement;

            // selectpicker 隐藏的时候，才更新数据
            $selectpicker_agents.on('hide.bs.dropdown', function () {
                console.log('hide');
                $scope.getData(1);
            });

            // 访问结果
            var ele_select_results = $('#select-access-results');
            // 默认选择所有应用
            ele_select_results.selectpicker('val', '-1');
            var $selectpicker_results = ele_select_results.data('selectpicker').$newElement;

            // selectpicker 隐藏的时候，才更新数据
            $selectpicker_results.on('hide.bs.dropdown', function () {
                console.log('hide');
                $scope.getData(1);
            });

            $('[data-toggle="tooltip"]').tooltip();
            $('[data-toggle="popover"]').popover();
        });
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
