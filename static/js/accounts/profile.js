/**
 * Created by restran on 2015/6/27.
 */
(function () {
    var app = new Vue({
        el: '#app',
        data: {
            formData: {
                old_password: '',
                new_password: ''
            },
            updateSuccess: false
        },
        computed: {},
        methods: {
            doSubmit: function ($event) {
                this.$validate(true);
                if (this.$validation.invalid) {
                    return;
                }
                if (weekPasswordDict[this.formData.new_password] != undefined) {
                    toastr["error"]('您的密码太弱存在被破解的风险');
                    return;
                }

                if (!(/[0-9]+/.test(this.formData.new_password) &&
                    /[a-zA-Z]+/.test(this.formData.new_password))) {
                    toastr["error"]('密码至少包含字母和数字，最短8个字符，区分大小写');
                    return;
                }

                var btn = $($event.currentTarget).button('loading');
                var apiUrl = '/api/accounts/password/update/';
                var postData = JSON.parse(JSON.stringify(this.formData));

                var shaObj = new jsSHA("SHA-1", "TEXT");
                shaObj.update(postData['new_password']);
                postData['new_password'] = shaObj.getHash("HEX");
                shaObj = new jsSHA("SHA-1", "TEXT");
                shaObj.update(postData['old_password']);
                postData['old_password'] = shaObj.getHash("HEX");
                var that = this;
                $request.post(apiUrl, postData, function (data) {
                    if (data['success'] == true) {
                        toastr["success"]('密码修改成功');
                        that.updateSuccess = true;
                    } else {
                        var msg = data['msg'] ? data['msg'] : '密码修改失败';
                        toastr["error"](msg);
                    }
                    btn.button('reset');
                }, function (data, msg) {
                    toastr["error"](msg);
                    btn.button('reset');
                });
            }
        }
    });

})();