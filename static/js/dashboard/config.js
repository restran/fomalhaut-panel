/**
 * Created by restran on 2015/7/11.
 */
(function () {
    var app = angular.module('app', []);

    app.controller('appCtrl', ['$scope', '$http', '$timeout', '$filter', function ($scope, $http, $timeout, $filter) {

        // 由于django的csrftoken保护
        $http.defaults.xsrfCookieName = 'csrftoken';
        $http.defaults.xsrfHeaderName = 'X-CSRFToken';

        $scope.client_id = ng_params.client_id;
        $scope.endpoint_id = ng_params.endpoint_id;
        $scope.data_type = ng_params.data_type;

        var basePostUrl = '';
        if ($scope.data_type == 'client') {
            basePostUrl = '/api/dashboard/client/';
        } else if ($scope.data_type == 'client_endpoint') {
            basePostUrl = '/api/dashboard/client_endpoint/';
        } else if ($scope.data_type == 'endpoint') {
            basePostUrl = '/api/dashboard/endpoint/';
        }

        console.log(basePostUrl);

        var editDialog = $('#edit-modal');

        $scope.config = {
            entries: [],
            endpoints: [],
            endpointsDict: {},
            selectedEndpoints: [],
            aclRules: [],
            formDataBak: null,
            formData: null,
            // 需要通过index来找到entries所对应的数据
            updateEntryIndex: null,
            updateEntry: null,
            editDialogMode: null,
            delEntryId: null,
            delEntryIndex: null,
            selectEndpoint: function ($event, entry) {
                console.log(entry.selected);
                var endpointDict = {};
                for (var i = 0; i < this.endpoints.length; i++) {
                    var item = this.endpoints[i];
                    if (item.selected == true) {
                        var key = item.name + ':' + item.version;
                        if (key in endpointDict) {
                            toastr["error"]('已存在相同的API访问名称和API版本号');
                            entry.selected = false;
                            return;
                        } else {
                            endpointDict[key] = null;
                        }
                    }
                }
                if (entry.selected == true) {
                    entry.enable = true;
                }
                //$scope.config.selectedEndpoints.push()
            },
            loadData: function () {
                var api_url;
                if ($scope.data_type == 'client') {
                    api_url = '/api/dashboard/client/?get_default_form=true';
                    if ($scope.client != 'None') {
                        api_url += '&client=' + $scope.client;
                    }
                } else if ($scope.data_type == 'endpoint') {
                    api_url = '/api/dashboard/endpoint/?get_default_form=true';
                } else if ($scope.data_type == 'client_endpoint') {
                    api_url = '/api/dashboard/client_endpoint/';
                    if ($scope.client_id != 'None') {
                        api_url += '?client_id=' + $scope.client_id;
                    }
                } else {
                    // 不需要获取数据
                    return;
                }

                $http.get(api_url).success(function (data) {
                    if (data['success']) {
                        $scope.config.entries = data['data'];
                        console.log(data);
                        // 编辑对话框的表单数据
                        $scope.config.formData = data['default_form'];
                        $scope.config.formDataBak = angular.copy($scope.config.formData);

                        if ($scope.data_type == 'endpoint') {
                            $scope.config.aclRules = [];
                            $timeout(function () {
                                // 如果是从 client_endpoint 那边跳转过来, 会带上需要滚动到的 id
                                var go_to = getUrlParam('go_to', null);
                                if (go_to != null) {
                                    var ele = $('#' + go_to);
                                    // 得到pos这个div层的offset，包含两个值，top和left
                                    var scroll_offset = ele.offset();
                                    console.log(scroll_offset);
                                    var scrollTop = scroll_offset.top - 60;
                                    if (scrollTop < 0) {
                                        scrollTop = 0;
                                    }
                                    $("body,html").animate({
                                        // 让body的scrollTop等于pos的top，就实现了滚动
                                        scrollTop: scrollTop
                                    }, 1000);

                                    ele.addClass('go-to-table-row focus');
                                    //setTimeout(function () {
                                    //
                                    //}, 1000);
                                    setTimeout(function () {
                                        ele.removeClass('focus');
                                    }, 5000);
                                }
                            });
                        }
                    } else {
                        var msg = data['msg'] ? data['msg'] : '获取数据失败';
                        toastr["error"](msg);
                    }
                }).error(function (data, status) {
                    toastr['error']('获取数据失败');
                }).finally(function () {

                });

                if ($scope.data_type == 'client_endpoint') {
                    console.log('loadEndpoints');
                    $scope.config.loadEndpoints();
                }
            },
            save: function ($event) {
                var $btn = $($event.currentTarget).button('loading');
                $scope.config.saveAjaxPost(function (result) {
                    $btn.button('reset');
                    if (result['success'] != true) {
                        if (result.msg != '服务器响应失败' && result['data'] != null
                            && result['data'] != undefined) {
                            $scope.config.formData = result['data'];
                        }

                        var msg = result.msg ? result.msg : '保存失败';
                        toastr["error"](msg);
                    } else {
                        if ($scope.data_type == 'client_endpoint') {
                            $scope.config.entries = result['data'];
                        } else {
                            if ($scope.config.editDialogMode == 'create') {
                                $scope.config.entries.push(result['data']);
                            } else {
                                $scope.config.entries[$scope.config.updateEntryIndex] = result['data'];
                            }
                        }

                        toastr["success"]("保存成功");
                        //alert('保存成功');
                        editDialog.modal('hide');
                    }
                });
            },
            saveContinue: function ($event) {
                var $btn = $($event.currentTarget).button('loading');
                $scope.config.saveAjaxPost(function (result) {
                    $btn.button('reset');
                    if (result['success'] != true) {
                        if (result.msg != '服务器响应失败' && result['data'] != null
                            && result['data'] != undefined) {
                            $scope.config.formData = result['data'];
                        }

                        var msg = result.msg ? result.msg : '保存失败';
                        toastr["error"](msg);
                    } else {
                        if ($scope.config.editDialogMode == 'create') {
                            $scope.config.entries.push(result['data']);
                        }

                        $scope.config.formData = angular.copy($scope.config.formDataBak);
                        if ($scope.data_type == 'client') {
                        } else if ($scope.data_type == 'endpoint') {
                            $scope.config.aclRules = [];
                        }

                        toastr["success"]("保存成功");
                    }
                });
            },
            saveAjaxPost: function (callback) {
                var post_url = basePostUrl;

                if ($scope.config.editDialogMode == 'create') {
                    post_url += 'create/';
                } else {
                    post_url += $scope.config.updateEntry.id + '/update/';
                }

                var post_data = {};
                if ($scope.data_type == 'client_endpoint') {
                    var endpoints = [];
                    for (i = 0; i < $scope.config.endpoints.length; i++) {
                        if ($scope.config.endpoints[i].selected == true) {
                            var d = {
                                'id': $scope.config.endpoints[i].id,
                                'enable': $scope.config.endpoints[i].enable
                            };

                            endpoints.push(d);
                        }
                    }
                    // 需要添加额外的参数
                    post_data['client_id'] = $scope.client_id;
                    post_data['endpoints'] = endpoints;
                } else {
                    post_data = {'data': formDataToJson($scope.config.formData)};
                    if ($scope.data_type == 'endpoint') {

                        // 需要添加额外的参数
                        post_data['client_id'] = $scope.client_id;
                        var i;
                        var aclRules = angular.copy($scope.config.aclRules);
                        //var new_aclRules = [];
                        // 把1，0转换成true, false
                        for (i = 0; i < aclRules.length; i++) {
                            aclRules[i]['is_permit'] = aclRules[i]['is_permit'] == 'true';
                        }

                        post_data['acl_rules'] = aclRules;
                        console.log($scope.config.aclRules);
                        console.log(post_data);
                    }
                }

                $http({
                    url: post_url,
                    method: 'POST',
                    async: true,
                    cache: false,
                    data: post_data,
                    headers: {'Content-Type': 'application/json; charset=utf-8'}
                }).success(function (data, status, headers, config) {
                    console.log(data);
                    callback(data);
                }).error(function (data, status, headers, config) {
                    callback({'success': false, 'msg': '服务器响应失败'});
                }).finally(function () {
                });
            },
            showEditDialog: function (mode, entry) {
                var i, item;
                // 还原一下
                $scope.config.formData = angular.copy($scope.config.formDataBak);
                if (mode == 'update') {
                    // 将entry的数据填充到form_data中
                    $scope.config.updateEntry = entry;
                    $scope.config.updateEntryIndex = $scope.config.entries.indexOf(entry);
                    $scope.config.editDialogMode = 'update';
                    if ($scope.data_type == 'client_endpoint') {
                        for (i = 0; i < this.endpoints.length; i++) {
                            this.endpoints[i].selected = false;
                            this.endpoints[i].enable = false;
                        }

                        for (i = 0; i < this.entries.length; i++) {
                            item = this.entries[i];
                            console.log(item);
                            console.log(this.endpointsDict);
                            this.endpointsDict[item['endpoint'].id].selected = true;
                            this.endpointsDict[item['endpoint'].id].enable = item['enable'];
                        }
                    } else {
                        entryToFormData($scope.config.updateEntry, $scope.config.formData);
                        if ($scope.data_type == 'client') {

                        } else if ($scope.data_type == 'endpoint') {
                            if ($scope.config.updateEntry['acl_rules'] == undefined) {
                                $scope.config.aclRules = [];
                            } else {
                                $scope.config.aclRules = angular.copy($scope.config.updateEntry['acl_rules']);

                                // 转换一下
                                for (i = 0; i < $scope.config.aclRules.length; i++) {
                                    $scope.config.aclRules[i].is_permit =
                                        $scope.config.aclRules[i].is_permit ? 'true' : 'false';
                                }
                            }

                            console.log($scope.config.aclRules);
                        }

                        console.log($scope.config.updateEntry);
                    }
                } else {
                    // 恢复为不选择任何项
                    //$('.selectpicker').selectpicker('val', []);

                    // 有些有默认值的，选择相应项
                    $scope.config.editDialogMode = 'create';
                    if ($scope.data_type == 'client') {
                    } else if ($scope.data_type == 'endpoint') {
                        $scope.config.aclRules = [];
                    } else if ($scope.data_type == 'client_endpoint') {
                        for (i = 0; i < this.endpoints.length; i++) {
                            this.endpoints[i].selected = false;
                            this.endpoints[i].enable = false;
                        }

                        for (i = 0; i < this.entries.length; i++) {
                            item = this.entries[i];
                            this.endpointsDict[item['endpoint'].id].selected = true;
                            this.endpointsDict[item['endpoint'].id].enable = item['enable'];
                        }
                    }
                }

                editDialog.modal('show');
            },
            updateEnableState: function (entry) {
                // var entry = $scope.config.entries[entry_index];
                var post_url = basePostUrl + entry.id + '/update_enable_state/';

                var post_data = {'enable': entry.enable};
                var headers = {headers: {'Content-Type': 'application/json; charset=utf-8'}};
                $http.post(post_url, post_data, headers).success(function (data, status, headers, config) {
                    if (data['success'] != true) {
                        // 恢复
                        entry.enable = entry.enable ? false : true;
                        toastr["error"]('更新启用状态失败');
                    }
                }).error(function (data, status, headers, config) {
                    toastr["error"]('更新启用状态失败');
                    // 恢复
                    entry.enable = entry.enable ? false : true;
                }).finally(function () {

                });
            },
            deleteEntry: function (entry) {
                // var entry = $scope.config.entries[entry_index];
                $('#delete-modal-title').text(entry.name);
                $scope.config.delEntryId = entry.id;
                $scope.config.delEntryIndex = $scope.config.entries.indexOf(entry);
                $('#delete-modal').modal('show');
            },
            doDeleteEntry: function ($event) {
                var $btn = $($event.currentTarget).button('loading');
                var post_url = basePostUrl + $scope.config.delEntryId + '/delete/';
                var post_data = {};
                $http({
                    url: post_url,
                    method: 'POST',
                    async: true,
                    cache: false,
                    data: post_data,
                    headers: {'Content-Type': 'application/json; charset=utf-8'}
                }).success(function (data, status, headers, config) {
                    if (data['success'] != true) {
                        var msg = data.msg ? data.msg : '删除失败';
                        toastr["error"](msg);
                    } else {
                        // 删除 json 数组的元素
                        $scope.config.entries.splice($scope.config.delEntryIndex, 1);
                        toastr["success"]('删除成功');
                        $('#delete-modal').modal('hide');
                    }
                }).error(function (data, status, headers, config) {
                    toastr["error"]('删除失败');
                }).finally(function () {
                    $btn.button('reset');
                });
            },
            addACLRule: function () {
                var inserted = {
                    re_uri: '',
                    is_permit: 'true'
                };
                $scope.config.aclRules.push(inserted);
            },
            removeACLRule: function (index) {
                $scope.config.aclRules.splice(index, 1);
            },
            randomKey: function (model, type) {
                function randomStr() {
                    var text = "";
                    var chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
                    for (var i = 0; i < 40; i++) {
                        text += chars.charAt(Math.floor(Math.random() * chars.length));
                    }

                    return text;
                }

                // var shaObj = new jsSHA(randomStr(), "TEXT");
                // var rawKey = shaObj.getHash("SHA-1", "HEX");
                var rawKey = randomStr();
                //model.data = randomStr();
                var key = [];
                if (type == 'access_key') {
                    for (var i = 0; i < rawKey.length; i += 2) {
                        key.push(rawKey[i]);
                    }
                    model.data = key.join('');
                } else {
                    model.data = rawKey;
                }
            },
            loadEndpoints: function () {
                var api_url = '/api/dashboard/endpoint/';
                $http.get(api_url).success(function (data) {
                    console.log(data);
                    if (data['success']) {
                        $scope.config.endpoints = data['data'];
                        for (var i = 0; i < $scope.config.endpoints.length; i++) {
                            var item = $scope.config.endpoints[i];
                            $scope.config.endpointsDict[item.id] = item;
                        }

                    } else {
                        var msg = data['msg'] ? data['msg'] : '获取 Endpoint 数据失败';
                        toastr["error"](msg);
                    }
                }).error(function (data, status) {
                    toastr['error']('获取 Endpoint 数据失败');
                }).finally(function () {

                });
            }
        };

        // 载入当前页面的数据
        $scope.config.loadData();

        // 将entry的数据填充到form_data中
        function entryToFormData(entry, form_data) {
            $.each(form_data, function (name, value) {
                form_data[name].data = entry[name];
            });
        }

        // 将form_data转换成只保留数据的json，不保留错误信息
        function formDataToJson(form_data) {
            var data = {};
            $.each(form_data, function (name, value) {
                data[name] = value.data;
            });
            return data;
        }


        // 测试用例 json 数据 tab 切换
        $scope.tabChange = function ($event, tab_id) {
            $($event.currentTarget).siblings().removeClass("active");
            $($event.currentTarget).addClass("active");
            //$(tab_id).tab('show');
        };

        $scope.showTab = function ($event) {
            //e.preventDefault();
            $($event.currentTarget).tab('show');
        };

        // 同步配置数据到redis中
        $scope.transferToRedis = function ($event) {
            var $btn = $($event.currentTarget).button('loading');
            var post_url = '/api/dashboard/transfer-to-redis/';
            var post_data = {};
            $http({
                url: post_url,
                method: 'POST',
                async: true,
                cache: false,
                data: post_data,
                headers: {'Content-Type': 'application/json; charset=utf-8'}
            }).success(function (data, status, headers, config) {
                if (data['success'] != true) {
                    var msg = data.msg ? data.msg : '同步失败';
                    toastr["error"](msg);
                } else {
                    toastr["success"]('同步成功');
                }
            }).error(function (data, status, headers, config) {
                toastr["error"]('同步失败');
            }).finally(function () {
                $btn.button('reset');
            });
        };

    }]);

})();


$(document).ready(function () {
    $('[data-toggle="popover"]').popover();
    $('[data-toggle="tooltip"]').tooltip();

    $('#backend-site-tabs').find('a').click(function (e) {
        e.preventDefault();
        $(this).tab('show');
    })
});