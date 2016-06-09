/**
 * Created by restran on 2015/6/27.
 */

(function () {
    var app = new Vue({
        el: '#app',
        data: {
            formData: {
                email: '',
                name: '',
                password: ''
            },
            createSuccess: false
        },
        computed: {},
        methods: {
            doSubmit: function ($event) {
                this.$validate(true);
                if (this.$validation.invalid) {
                    return;
                }
                if (weekPasswordDict[this.formData.password] != undefined) {
                    toastr["error"]('您的密码太弱存在被破解的风险');
                    return;
                }

                if (!(/[0-9]+/.test(this.formData.password) &&
                    /[a-zA-Z]+/.test(this.formData.password))) {
                    toastr["error"]('密码至少包含字母和数字，最短8个字符，区分大小写');
                    return;
                }

                var btn = $($event.currentTarget).button('loading');
                var apiUrl = '/api/accounts/create_admin/';
                var postData = JSON.parse(JSON.stringify(this.formData));

                var shaObj = new jsSHA("SHA-1", "TEXT");
                shaObj.update(postData['password']);
                postData['password'] = shaObj.getHash("HEX");

                var that = this;
                $request.post(apiUrl, postData, function (data) {
                    if (data['success'] == true) {
                        toastr["success"]('创建成功');
                        that.createSuccess = true;
                    } else {
                        var msg = data['msg'] ? data['msg'] : '创建失败';
                        toastr["error"](msg);
                    }
                    btn.button('reset');
                }, function (data, msg) {
                    toastr["error"]('创建失败，服务器未正确响应');
                    btn.button('reset');
                });
            }
        }
    });
})();


