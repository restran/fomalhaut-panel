/**
 * Created by restran on 2015/6/27.
 */

(function () {
    var app = new Vue({
        el: '#app',
        data: {
            formData: {
                email: '',
                name: ''
            },
            formDataBak: {
                email: '',
                name: ''
            },
            delEntryIndex: null,
            delEntry: null,
            entries: [],
            createSuccess: false
        },
        computed: {},
        methods: {
            getData: function () {
                var apiUrl = '/api/accounts/';
                var that = this;
                $request.get(apiUrl, null, function (data) {
                    if (data['success']) {
                        that.entries = data['data'];
                    }
                });
            },
            deleteEntry: function (entry) {
                this.delEntry = entry;
                this.delEntryIndex = this.entries.indexOf(entry);
                $('#delete-modal').modal('show');
            },
            doDeleteEntry: function () {
                var btn = $('#btn-delete').button('loading');
                var postUrl = '/api/accounts/delete/';
                var postData = {'user_id': this.delEntry.id};
                var that = this;
                $request.post(postUrl, postData, function (data) {
                    if (data['success'] == true) {
                        toastr["success"]('删除成功');
                        // 删除 json 数组的元素
                        that.entries.splice(that.delEntryIndex, 1);
                        $('#delete-modal').modal('hide');
                    } else {
                        var msg = data['msg'] ? data['msg'] : '删除失败';
                        toastr["error"](msg);
                    }
                    btn.button('reset');
                }, function (data, msg) {
                    toastr["error"](msg);
                    btn.button('reset');
                });
            },
            showEditDialog: function (mode, entry) {
                this.formData = JSON.parse(JSON.stringify(this.formDataBak));
                // 还原一下
                if (mode == 'update') {
                    this.editDialogMode = 'update';
                    // 将entry的数据填充到form_data中
                    this.updateEntry = entry;
                    this.updateEntryIndex = this.entries.indexOf(entry);
                    this.formData = JSON.parse(JSON.stringify(this.updateEntry));
                } else {
                    // 有些有默认值的，选择相应项
                    this.editDialogMode = 'create';
                }
                this.$validate(true);
                this.$resetValidation();
                console.log('$resetValidation');
                $('#edit-modal').modal('show');
            },
            // 编辑对话框保存按钮
            save: function ($event) {
                this.$validate(true);
                if (this.$validation.invalid) {
                    return;
                }

                var $btn = $($event.currentTarget).button('loading');
                var postUrl = '/api/accounts/';

                if (this.editDialogMode == 'create') {
                    postUrl += 'create/';
                } else {
                    postUrl += 'update/' + this.updateEntry.id + '/';
                }
                var postData = {
                    'email': this.formData.email,
                    'name': this.formData.name
                };

                var that = this;
                $request.post(postUrl, postData, function (data) {
                    $btn.button('reset');
                    if (data['success'] == true) {
                        if (that.editDialogMode == 'create') {
                            that.entries.push(data['item']);
                        } else {
                            var entry = that.entries[that.updateEntryIndex];
                            for (var name in that.formData) {
                                if (that.formData.hasOwnProperty(name)) {
                                    entry[name] = that.formData[name];
                                }
                            }
                            // 这里不能使用update_entry = data['data']，因为这只会将
                            // update_entry指向的数据修改，而不会修改ng_scope.entries[updateEntryIndex]的数据值
                        }
                        toastr["success"]('保存成功');
                        //alert('保存成功');
                        $('#edit-modal').modal('hide');
                    } else {
                        var msg = data['msg'] ? data['msg'] : '保存失败';
                        toastr["error"](msg);
                    }
                }, function (data) {
                    toastr["error"]('保存失败，服务器未正确响应');
                    $btn.button('reset');
                });
            }
        }
    });
    app.getData();
})();