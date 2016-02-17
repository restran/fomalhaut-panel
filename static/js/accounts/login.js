/**
 * Created by restran on 2015/6/27.
 */
/**
 * Created by restran on 2015/6/27.
 */
var app = angular.module('app', []);

app.controller('appCtrl', ['$scope', '$http', appCtrl]);

function appCtrl($scope, $http) {
    // 由于django的csrftoken保护
    $http.defaults.xsrfCookieName = 'csrftoken';
    $http.defaults.xsrfHeaderName = 'X-CSRFToken';

    $scope.model = {email: '', password: '', remember_me: false};
    $scope.loginFailed = false;

    $('form').validator().on('submit', function (e) {
        if (e.isDefaultPrevented()) {
            // handle the invalid form...
        } else {
            // everything looks good!
            doSubmit();
        }
    });

    function doSubmit() {
        var btn = $('#btn-submit').button('loading');
        var apiUrl = '/api/accounts/user_login/';
        var postData = angular.copy($scope.model);
        var shaObj = new jsSHA(postData['password'], "TEXT");
        postData['password'] = shaObj.getHash("SHA-1", "HEX");
        console.log(postData);
        var headers = {headers: {'Content-Type': 'application/json; charset=utf-8'}};
        $http.post(apiUrl, postData, headers).success(function (data, status, headers, config) {
            if (data['success'] == true) {
                toastr["success"]('登录成功');
                document.location.href = data['redirect_uri'];
            } else {
                var msg = data['msg'] ? data['msg'] : '登录失败，邮箱或密码不正确';
                $scope.loginFailed = true;
                toastr["error"](msg);
            }
        }).error(function (data, status, headers, config) {
            toastr["error"]('登录失败，服务器未正确响应');
        }).finally(function () {
            btn.button('reset');
        });
    }
}
