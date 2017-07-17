/**
 * Created by restran on 2015/6/27.
 */

(function () {
    var app = new Vue({
        el: '#app',
        data: {
            formData: {
                email: ''
            },
            success: false
        },
        computed: {},
        methods: {
            doSubmit: function ($event) {
                var btn = $($event.currentTarget).button('loading');
                var apiUrl = '/api/accounts/password/reset_request/';
                var postData = JSON.parse(JSON.stringify(this.formData));
                var that = this;
                $request.post(apiUrl, postData, function (data) {
                    if (data['success'] == true) {
                        toastr["success"]('重置请求已成功提交');
                        that.success = true;
                    } else {
                        var msg = data['msg'] ? data['msg'] : '重置失败';
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

    $('form').validator().on('submit', function (e) {
        if (e.isDefaultPrevented()) {
            // handle the invalid form...
        } else {
            // everything looks good!
            app.doSubmit(e);
        }
    });
})();