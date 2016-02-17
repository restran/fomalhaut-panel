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
            showEditDialog: function (mode, entry_index) {
                var i, item;
                // 还原一下
                $scope.config.formData = angular.copy($scope.config.formDataBak);
                if (mode == 'update') {
                    // 将entry的数据填充到form_data中
                    $scope.config.updateEntry = $scope.config.entries[entry_index];
                    $scope.config.updateEntryIndex = entry_index;
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
            updateEnableState: function (entry_index) {
                var entry = $scope.config.entries[entry_index];
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
            deleteEntry: function (entry_index) {
                var entry = $scope.config.entries[entry_index];
                $('#delete-modal-title').text(entry.name);
                $scope.config.delEntryId = entry.id;
                $scope.config.delEntryIndex = entry_index;
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
            randomKey: function (model) {
                function randomStr() {
                    var text = "";
                    var chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
                    for (var i = 0; i < 40; i++) {
                        text += chars.charAt(Math.floor(Math.random() * chars.length));
                    }

                    return text;
                }

                var shaObj = new jsSHA(randomStr(), "TEXT");
                model.data = shaObj.getHash("SHA-1", "HEX");
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


        $scope.uploadConfig = function () {
            $('#upload-modal').modal('show');
            // 是否已经有回应的数据
            $scope.has_response = false;
            $scope.response = {'success': false, 'msg': '', 'errors': []};
            $scope.processDone = false;
            $scope.processMsg = '';
            $scope.processPercentage = 0;
            $scope.processInterval = null;
            $scope.realPocessPercentage = 0;
            var progressbar = $('#upload-progress-bar');
            progressbar.addClass('hidden');
        };

        $scope.closeImportModal = function () {
            // 导入成功需要刷新页面
            if ($scope.response['success'] == true) {
                document.location.href = '/dashboard/config/';
            }
        };

        // 是否已经有回应的数据
        $scope.has_response = false;
        $scope.response = {'success': false, 'msg': '', 'errors': []};

        // 进度条
        $scope.processDone = false;
        $scope.processMsg = '';
        $scope.processPercentage = 0;
        $scope.processInterval = null;
        $scope.realPocessPercentage = 0;

        var getCookie = function (name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = $.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        };

        $scope.uploader = new plupload.Uploader({
            runtimes: 'html5,flash,silverlight,html4',
            browse_button: 'pickfiles', // you can pass in id...
            container: document.getElementById('upload-file-container'), // ... or DOM Element itself
            url: '/api/dashboard/upload/import/',
            flash_swf_url: '/static/js/plupload/Moxie.swf',
            silverlight_xap_url: '/static/js/plupload/Moxie.xap',
            multipart_params: {"csrfmiddlewaretoken": getCookie('csrftoken')},
            multi_selection: false,
            auto_start: true,
            max_file_size: '10mb',
            unique_names: true,
            // disable chunk
            chunk_size: 0,
            //chunk_size: '10mb',
            filters: {
                max_file_size: '10mb',
                mime_types: [
                    {title: "json files", extensions: "json"}
                ]
            },

            init: {
                'FilesAdded': function (up, files) {
                    var progressbar = $('#upload-progress-bar');
                    progressbar.removeClass('hidden');
                    $scope.uploader.start();

                    $scope.processDone = false;
                    $scope.processMsg = '文件上传中...';
                    $scope.processPercentage = 0;
                    $scope.realPocessPercentage = 0;
                    $scope.has_response = false;

                    if ($scope.processInterval != null) {
                        clearInterval($scope.processInterval);
                        $scope.processInterval = null;
                    }

                    // 需要手动应用一下，才会修改dom
                    $scope.$apply();
                },
                'UploadProgress': function (uploader, file) {
                    console.log('UploadProgress');
                    $scope.realPocessPercentage = Math.floor(file.percent * 10 / 100);
                    $scope.processPercentage = $scope.realPocessPercentage;
                    //var uploaded = file.loaded;
                    //var size = plupload.formatSize(uploaded).toUpperCase();
                    //
                    //console.log(size);
                    if (file.percent == 100) {
                        $scope.processMsg = '数据处理中...';
                        $scope.startProcess();
                    }
                    //setProgress(file, 'upload-progress-bar', file.percent, uploader.total.bytesPerSec);
                },
                'UploadComplete': function (uploader, files) {
                    //var progressbar = $('#upload-progress-bar');
                    //$('#upload-progress-bar').css('opacity', 0);
                    //progressbar.addClass('hidden');
                    //progressbar.find('progress-bar').attr('aria-valuenow', 0).css('width', "0%");
                },
                'FileUploaded': function (uploader, file, response) {
                    //每个文件上传成功后,处理相关的事情
                    //其中 info 是文件上传成功后，服务端返回数据
                    $scope.has_response = true;
                    try {
                        $scope.response = JSON.parse(response.response);
                    } catch (err) {
                        $scope.response['success'] = false;
                        $scope.response['msg'] = '上传失败，服务器未正确响应';
                        $scope.response['errors'] = [];
                        $scope.response['success_msgs'] = [];
                    }

                    $scope.setProcessDone();
                    // 需要手动应用一下，才会修改dom
                    $scope.$apply();
                },
                'Error': function (uploader, error) {
                    $scope.has_response = true;
                    try {
                        $scope.response = JSON.parse(error.response);
                    } catch (err) {
                        $scope.response['success'] = false;
                        $scope.response['msg'] = '上传失败，请选择 JSON 文件';
                        $scope.response['errors'] = [];
                        $scope.response['success_msgs'] = [];
                    }

                    $scope.setProcessDone();
                    // 需要手动应用一下，才会修改dom
                    $scope.$apply();
                }
            }
        });

        $scope.uploader.init();

        // 文件上传完成后，开始显示处理Excel的进度信息
        $scope.startProcess = function () {
            if ($scope.processInterval == null) {
                $scope.processInterval = setInterval(function () {
                    if ($scope.realPocessPercentage < 50) {
                        $scope.realPocessPercentage += 2;
                    } else if ($scope.realPocessPercentage < 80) {
                        $scope.realPocessPercentage += 1;
                    } else if ($scope.realPocessPercentage < 90) {
                        $scope.realPocessPercentage += 0.5;
                    } else if ($scope.realPocessPercentage < 95) {
                        $scope.realPocessPercentage += 0.1;
                    } else if ($scope.realPocessPercentage < 99) {
                        $scope.realPocessPercentage += 0.01;
                    } else {
                    }
                    $scope.processPercentage = Math.floor($scope.realPocessPercentage);

                    $scope.$apply();
                }, 250);
            }
        };

        $scope.setProcessDone = function () {
            if ($scope.processInterval != null) {
                clearInterval($scope.processInterval);
                $scope.processInterval = null;
            }
            $scope.processPercentage = 100;
            $scope.processMsg = '处理完成';
            $scope.$apply();
        };

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