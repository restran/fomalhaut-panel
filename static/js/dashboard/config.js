/**
 * Created by restran on 2016/3/11.
 */
(function () {
    var app = new Vue({
        el: '#config-app',
        data: {
            clientId: globalParams.client_id,
            endpointId: globalParams.endpoint_id,
            dataType: globalParams.data_type,
            basePostUrl: '',
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
            deleteModalTitle: ''
            // editDialog: $('#edit-modal')
        },
        methods: {
            init: function () {
                if (this.dataType == 'client') {
                    this.basePostUrl = '/api/dashboard/client/';
                } else if (this.dataType == 'client_endpoint') {
                    this.basePostUrl = '/api/dashboard/client_endpoint/';
                } else if (this.dataType == 'endpoint') {
                    this.basePostUrl = '/api/dashboard/endpoint/';
                }
                console.log(this.basePostUrl);
            },
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
            // 把 base64 字符串转换成 url 安全
            toUrlSafeBase64: function (b64Str) {
                return b64Str.replace(/[+\/]/g, function (m0) {
                    return m0 == '+' ? '-' : '_';
                }).replace(/=/g, '');
            },
            loadData: function () {
                var api_url;
                if (this.dataType == 'client') {
                    api_url = '/api/dashboard/client/?get_default_form=true';
                    if (this.client != 'None') {
                        api_url += '&client=' + this.client;
                    }
                } else if (this.dataType == 'endpoint') {
                    api_url = '/api/dashboard/endpoint/?get_default_form=true';
                } else if (this.dataType == 'client_endpoint') {
                    api_url = '/api/dashboard/client_endpoint/';
                    if (this.clientId != 'None') {
                        api_url += '?client_id=' + this.clientId;
                    }
                } else {
                    // 不需要获取数据
                    return;
                }

                var that = this;
                $request.get(api_url, null, function (data) {
                    if (data['success']) {
                        that.entries = data['data'];
                        console.log(data);
                        // 编辑对话框的表单数据
                        // that.formData = data['default_form'];
                        that.formDataBak = JSON.parse(JSON.stringify(data['default_form']));

                        if (that.dataType == 'endpoint') {
                            that.aclRules = [];
                            Vue.nextTick(function () {
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
                }, function (data, msg) {
                    toastr['error'](msg);
                });


                if (this.dataType == 'client_endpoint') {
                    console.log('loadEndpoints');
                    this.loadEndpoints();
                }
            },
            save: function ($event) {
                var $btn = $($event.currentTarget).button('loading');
                var that = this;
                this.saveAjaxPost(function (result) {
                    $btn.button('reset');
                    if (result['success'] != true) {
                        if (result.msg != '服务器响应失败' && result['data'] != null
                            && result['data'] != undefined) {
                            that.formData = result['data'];
                        }

                        var msg = result.msg ? result.msg : '保存失败';
                        toastr["error"](msg);
                    } else {
                        if (that.dataType == 'client_endpoint') {
                            that.entries = result['data'];
                        } else {
                            if (that.editDialogMode == 'create') {
                                that.entries.push(result['data']);
                            } else {
                                that.entries[that.updateEntryIndex] = result['data'];
                            }
                        }

                        toastr["success"]("保存成功");
                        //alert('保存成功');
                        $('#edit-modal').modal('hide');
                    }
                });
            },
            saveContinue: function ($event) {
                var $btn = $($event.currentTarget).button('loading');
                var that = this;
                this.saveAjaxPost(function (result) {
                    $btn.button('reset');
                    if (result['success'] != true) {
                        if (result.msg != '服务器响应失败' && result['data'] != null
                            && result['data'] != undefined) {
                            that.formData = result['data'];
                        }

                        var msg = result.msg ? result.msg : '保存失败';
                        toastr["error"](msg);
                    } else {
                        if (that.editDialogMode == 'create') {
                            that.entries.push(result['data']);
                        }

                        that.formData = JSON.parse(JSON.stringify(that.formDataBak));
                        if (that.dataType == 'client') {
                        } else if (that.dataType == 'endpoint') {
                            that.aclRules = [];
                        }

                        toastr["success"]("保存成功");
                    }
                });
            },
            saveAjaxPost: function (callback) {
                var postUrl = this.basePostUrl;

                if (this.editDialogMode == 'create') {
                    postUrl += 'create/';
                } else {
                    postUrl += this.updateEntry.id + '/update/';
                }

                var postData = {};
                if (this.dataType == 'client_endpoint') {
                    var endpoints = [];
                    for (i = 0; i < this.endpoints.length; i++) {
                        if (this.endpoints[i].selected == true) {
                            var d = {
                                'id': this.endpoints[i].id,
                                'enable': this.endpoints[i].enable
                            };

                            endpoints.push(d);
                        }
                    }
                    // 需要添加额外的参数
                    postData['client_id'] = this.clientId;
                    postData['endpoints'] = endpoints;
                } else {
                    postData = {'data': this.formDataToJson(this.formData)};
                    if (this.dataType == 'endpoint') {

                        // 需要添加额外的参数
                        postData['client_id'] = this.clientId;
                        var i;
                        var aclRules = JSON.parse(JSON.stringify(this.aclRules));
                        //var new_aclRules = [];
                        // 把1，0转换成true, false
                        for (i = 0; i < aclRules.length; i++) {
                            aclRules[i]['is_permit'] = aclRules[i]['is_permit'] == 'true';
                        }

                        postData['acl_rules'] = aclRules;
                        console.log(this.aclRules);
                        console.log(postData);
                    }
                }

                $request.post(postUrl, postData, function (data) {
                    console.log(data);
                    callback(data);
                }, function (data, msg) {
                    callback({'success': false, 'msg': '服务器响应失败'});
                });
            },
            showEditDialog: function (mode, entry) {
                var i, item;
                // 还原一下
                this.formData = JSON.parse(JSON.stringify(this.formDataBak));
                if (mode == 'update') {
                    // 将entry的数据填充到form_data中
                    this.updateEntry = entry;
                    this.updateEntryIndex = this.entries.indexOf(entry);
                    this.editDialogMode = 'update';
                    if (this.dataType == 'client_endpoint') {
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
                        this.entryToFormData(this.updateEntry, this.formData);
                        if (this.dataType == 'client') {

                        } else if (this.dataType == 'endpoint') {
                            if (this.updateEntry['acl_rules'] == undefined) {
                                this.aclRules = [];
                            } else {
                                this.aclRules = JSON.parse(JSON.stringify(this.updateEntry['acl_rules']));

                                // 转换一下
                                for (i = 0; i < this.aclRules.length; i++) {
                                    this.aclRules[i].is_permit =
                                        this.aclRules[i].is_permit ? 'true' : 'false';
                                }
                            }

                            console.log(this.aclRules);
                        }

                        console.log(this.updateEntry);
                    }
                } else {
                    // 恢复为不选择任何项
                    //$('.selectpicker').selectpicker('val', []);

                    // 有些有默认值的，选择相应项
                    this.editDialogMode = 'create';
                    if (this.dataType == 'client') {
                    } else if (this.dataType == 'endpoint') {
                        this.aclRules = [];
                    } else if (this.dataType == 'client_endpoint') {
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

                $('#edit-modal').modal('show');
            },
            updateEnableState: function (entry) {
                var postUrl = this.basePostUrl + entry.id + '/update_enable_state/';
                var postData = {'enable': entry.enable};
                $request.post(postUrl, postData, function (data) {
                    if (data['success'] != true) {
                        // 恢复
                        entry.enable = entry.enable ? false : true;
                        toastr["error"]('更新启用状态失败');
                    }
                }, function (data, msg) {
                    toastr["error"]('更新启用状态失败');
                    // 恢复
                    entry.enable = entry.enable ? false : true;
                });
            },
            deleteEntry: function (entry) {
                // var entry = $scope.config.entries[entry_index];
                this.deleteModalTitle = entry.name;
                // $('#delete-modal-title').text(entry.name);
                this.delEntryId = entry.id;
                this.delEntryIndex = this.entries.indexOf(entry);
                $('#delete-modal').modal('show');
            },
            doDeleteEntry: function ($event) {
                var $btn = $($event.currentTarget).button('loading');
                var postUrl = this.basePostUrl + this.delEntryId + '/delete/';
                var postData = {};
                $request.post(postUrl, postData, function (data) {
                    if (data['success'] != true) {
                        var msg = data.msg ? data.msg : '删除失败';
                        toastr["error"](msg);
                    } else {
                        // 删除 json 数组的元素
                        this.entries.splice(this.delEntryIndex, 1);
                        toastr["success"]('删除成功');
                        $('#delete-modal').modal('hide');
                    }
                    $btn.button('reset');
                }, function (data, msg) {
                    toastr["error"]('删除失败');
                    $btn.button('reset');
                });
            },
            addACLRule: function () {
                var inserted = {
                    re_uri: '',
                    is_permit: 'true'
                };
                this.aclRules.push(inserted);
            },
            removeACLRule: function (index) {
                this.aclRules.splice(index, 1);
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

                var shaObj;
                // var rawKey = shaObj.getHash("SHA-1", "HEX");
                // var rawKey = randomStr();
                //model.data = randomStr();
                // var key = [];
                if (type == 'access_key') {
                    // for (var i = 0; i < rawKey.length; i += 2) {
                    //     key.push(rawKey[i]);
                    // }
                    shaObj = new jsSHA("SHA-1", "TEXT");
                    shaObj.update(randomStr());
                    console.log(shaObj.getHash("B64"));
                    model.data = this.toUrlSafeBase64(shaObj.getHash("B64"));
                } else {
                    shaObj = new jsSHA("SHA-256", "TEXT");
                    shaObj.update(randomStr());
                    model.data = this.toUrlSafeBase64(shaObj.getHash("B64"));
                }
            },
            loadEndpoints: function () {
                var apiUrl = '/api/dashboard/endpoint/';
                var that = this;
                $request.get(apiUrl, null, function (data) {
                    console.log(data);
                    if (data['success']) {
                        that.endpoints = data['data'];
                        for (var i = 0; i < that.endpoints.length; i++) {
                            var item = that.endpoints[i];
                            that.endpointsDict[item.id] = item;
                        }

                    } else {
                        var msg = data['msg'] ? data['msg'] : '获取 Endpoint 数据失败';
                        toastr["error"](msg);
                    }
                }, function (data, msg) {
                    toastr['error']('获取 Endpoint 数据失败');
                });
            },
            // 将entry的数据填充到form_data中
            entryToFormData: function (entry, formData) {
                for (var name in formData) {
                    if (formData.hasOwnProperty(name)) {
                        formData[name].data = entry[name];
                    }
                }

                // $.each(form_data, function (name, value) {
                //     form_data[name].data = entry[name];
                // });
            },
            // 将form_data转换成只保留数据的json，不保留错误信息
            formDataToJson: function (formData) {
                var data = {};
                for (var name in formData) {
                    if (formData.hasOwnProperty(name)) {
                        data[name] = formData[name].data;
                    }
                }

                // $.each(form_data, function (name, value) {
                //     data[name] = value.data;
                // });
                return data;
            },
            // 测试用例 json 数据 tab 切换
            tabChange: function ($event, tab_id) {
                $($event.currentTarget).siblings().removeClass("active");
                $($event.currentTarget).addClass("active");
                //$(tab_id).tab('show');
            },
            showTab: function ($event) {
                $event.preventDefault();
                $($event.currentTarget).tab('show');
            },
            // 同步配置数据到redis中
            transferToRedis: function ($event) {
                var $btn = $($event.currentTarget).button('loading');
                var postUrl = '/api/dashboard/transfer-to-redis/';
                var postData = {};
                $request.post(postUrl, postData, function (data) {
                    if (data['success'] != true) {
                        var msg = data.msg ? data.msg : '同步失败';
                        toastr["error"](msg);
                    } else {
                        toastr["success"]('同步成功');
                    }
                    $btn.button('reset');
                }, function (data, msg) {
                    toastr["error"]('同步失败');
                    $btn.button('reset');
                });
            }
        },
        computed: {},
        watch: {}
    });

    app.init();
    app.loadData();
})();


$(document).ready(function () {
    $('[data-toggle="popover"]').popover();
    $('[data-toggle="tooltip"]').tooltip();

    $('#backend-site-tabs').find('a').click(function (e) {
        e.preventDefault();
        $(this).tab('show');
    })
});