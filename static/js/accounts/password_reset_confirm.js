/**
 * Created by restran on 2015/6/28.
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

    $scope.model = {new_password: ''};
    $scope.updateSuccess = false;

    $('form').validator().on('submit', function (e) {
        if (e.isDefaultPrevented()) {
            // handle the invalid form...
        } else {
            // everything looks good!
            doSubmit();
        }
    });

    function doSubmit() {
        if (weekPasswordDict[$scope.model.password] != undefined) {
            toastr["error"]('您的密码太弱存在被破解的风险');
            return;
        }

        if (!(/[0-9]+/.test($scope.model.password) &&
            /[a-zA-Z]+/.test($scope.model.password))) {
            toastr["error"]('至少包含字母和数字，最短8个字符，区分大小写');
            return;
        }

        var btn = $('#btn-submit').button('loading');
        var apiUrl = '/api/accounts/password/reset/';
        var postData = angular.copy($scope.model);
        var shaObj = new jsSHA(postData['new_password'], "TEXT");
        postData['new_password'] = shaObj.getHash("SHA-1", "HEX");
        postData['token'] = token;
        postData['user_id'] = user_id;
        var headers = {headers: {'Content-Type': 'application/json; charset=utf-8'}};
        $http.post(apiUrl, postData, headers).success(function (data, status, headers, config) {
            if (data['success'] == true) {
                toastr["success"]('密码修改成功');
                $scope.updateSuccess = true;
            } else {
                var msg = data['msg'] ? data['msg'] : '密码修改失败';
                toastr["error"](msg);
            }
        }).error(function (data, status, headers, config) {
            toastr["error"]('密码修改失败，服务器未正确响应');
        }).finally(function () {
            btn.button('reset');
        });
    }
}

// 弱口令字典
var weekPasswordDict = {
    '12345678': 0, '123456789': 0, 'a123456': 0, '123456': 0, 'a123456789': 0, '1234567890': 0,
    'qq123456': 0, 'abc123456': 0, '123456a': 0, '123456789a': 0, '147258369': 0, 'zxcvbnm': 0,
    '987654321': 0, '12345678910': 0, 'abc123': 0, 'qq123456789': 0, '123456789.': 0,
    '7708801314520': 0, 'woaini': 0, '5201314520': 0, 'q123456': 0, '123456abc': 0,
    '1233211234567': 0, '123123123': 0, '123456.': 0, '0123456789': 0, 'asd123456': 0, 'aa123456': 0,
    '135792468': 0, 'q123456789': 0, 'abcd123456': 0, '12345678900': 0, 'woaini520': 0,
    'woaini123': 0, 'zxcvbnm123': 0, '1111111111111111': 0, 'w123456': 0, 'aini1314': 0,
    'abc123456789': 0, '111111': 0, 'woaini521': 0, 'qwertyuiop': 0, '1314520520': 0, '1234567891': 0,
    'qwe123456': 0, 'asd123': 0, '000000': 0, '1472583690': 0, '1357924680': 0, '789456123': 0,
    '123456789abc': 0, 'z123456': 0, '1234567899': 0, 'aaa123456': 0, 'abcd1234': 0, 'www123456': 0,
    '123456789q': 0, '123abc': 0, 'qwe123': 0, 'w123456789': 0, '7894561230': 0, '123456qq': 0,
    'zxc123456': 0, '123456789qq': 0, '1111111111': 0, '111111111': 0, '0000000000000000': 0,
    '1234567891234567': 0, 'qazwsxedc': 0, 'qwerty': 0, '123456..': 0, 'zxc123': 0, 'asdfghjkl': 0,
    '0000000000': 0, '1234554321': 0, '123456q': 0, '123456aa': 0, '9876543210': 0, '110120119': 0,
    'qaz123456': 0, 'qq5201314': 0, '123698745': 0, '5201314': 0, '000000000': 0, 'as123456': 0,
    '123123': 0, '5841314520': 0, 'z123456789': 0, '52013145201314': 0, 'a123123': 0, 'caonima': 0,
    'a5201314': 0, 'wang123456': 0, 'abcd123': 0, '123456789..': 0, 'woaini1314520': 0,
    '123456asd': 0, 'aa123456789': 0, '741852963': 0, 'a12345678': 0, 'admin123': 0, 'admin123456': 0,
    'password': 0, 'passw0rd': 0, 'woaini1314': 0, 'password123': 0, '8888abc': 0, 'aaaaaaa1': 0,
    'aaaaaaaa1': 0, 'admin1234': 0, '12345678a': 0
};