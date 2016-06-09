/**
 * Created by restran on 2015/6/27.
 */

(function () {
    var app = new Vue({
        el: '#app',
        data: {
            formData: {
                email: '',
                password: '',
                remember_me: false
            },
            loginFailed: false
        },
        computed: {},
        methods: {
            doSubmit: function ($event) {
                this.$validate(true);
                if (this.$validation.invalid) {
                    return;
                }

                var btn = $($event.currentTarget).button('loading');
                var apiUrl = '/api/accounts/user_login/';
                var postData = JSON.parse(JSON.stringify(this.formData));
                var shaObj = new jsSHA("SHA-1", "TEXT");
                shaObj.update(postData['password']);
                postData['password'] = shaObj.getHash("HEX");
                var that = this;
                $request.post(apiUrl, postData, function (data) {
                    if (data['success'] == true) {
                        toastr["success"]('登录成功');
                        document.location.href = data['redirect_uri'];
                    } else {
                        var msg = data['msg'] ? data['msg'] : '登录失败，邮箱或密码不正确';
                        that.loginFailed = true;
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

    // $('form').validator().on('submit', function (e) {
    //     if (e.isDefaultPrevented()) {
    //         // handle the invalid form...
    //     } else {
    //         // everything looks good!
    //         app.doSubmit(e);
    //     }
    // });
})();

