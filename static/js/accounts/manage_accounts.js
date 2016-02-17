/**
 * Created by restran on 2015/6/27.
 */
/**
 * Created by restran on 2015/6/27.
 */
var app = angular.module('app', []);

app.controller('appCtrl', ['$scope', '$http', appCtrl]);

function appCtrl($scope, $http) {
    //NProgress.start();

    // 由于django的csrftoken保护
    $http.defaults.xsrfCookieName = 'csrftoken';
    $http.defaults.xsrfHeaderName = 'X-CSRFToken';

    var apiUrl = '/api/accounts/';
    //$http.get(api_url).success(function(data, status, headers, config)
    $http.get(apiUrl).success(function (data) {
        if (data['success']) {
            $scope.entries = data['data'];
        }
    }).finally(function () {
        //NProgress.done();
    });


    $('form').validator().on('submit', function (e) {
        if (e.isDefaultPrevented()) {
            // handle the invalid form...
        } else {
            // everything looks good!
            $scope.save();
        }
    });


    $scope.delEntryIndex = null;
    $scope.delEntry = null;

    $scope.deleteEntry = function (entry_index) {
        $scope.delEntry = $scope.entries[entry_index];
        $scope.delEntryIndex = entry_index;
        $('#delete-modal').modal('show');
    };

    $scope.doDeleteEntry = function () {
        var btn = $('#btn-delete').button('loading');

        var post_url = '/api/accounts/delete/';
        var post_data = {'user_id': $scope.delEntry.id};
        var headers = {headers: {'Content-Type': 'application/json; charset=utf-8'}};
        $http.post(post_url, post_data, headers).success(function (data, status, headers, config) {
            if (data['success'] == true) {
                toastr["success"]('删除成功');
                // 删除 json 数组的元素
                $scope.entries.splice($scope.delEntryIndex, 1);
                $('#delete-modal').modal('hide');
            } else {
                var msg = data['msg'] ? data['msg'] : '删除失败';
                toastr["error"](msg);
            }
        }).error(function (data, status, headers, config) {
            toastr["error"]('删除失败，服务器未正确响应');
        }).finally(function () {
            btn.button('reset');
        });
    };

    var editDialog = $('#edit-modal');

    // 需要通过index来找到entries所对应的数据
    $scope.updateEntryIndex = null;
    $scope.updateEntry = null;

    $scope.editDialogMode = null;

    $scope.formData = {};

    $scope.showEditDialog = function (mode, entry_index) {
        // 还原一下
        if (mode == 'update') {
            $scope.editDialogMode = 'update';
            // 将entry的数据填充到form_data中
            $scope.updateEntry = $scope.entries[entry_index];
            $scope.updateEntryIndex = entry_index;
            $scope.formData = angular.copy($scope.updateEntry);
        } else {
            // 有些有默认值的，选择相应项
            $scope.editDialogMode = 'create';
            $scope.formData = {};
        }

        editDialog.modal('show');
    };


    // 编辑对话框保存按钮
    $scope.save = function () {
        var btn = $('#btn-save').button('loading');
        var post_url = '/api/accounts/';

        if ($scope.editDialogMode == 'create') {
            post_url += 'create/';
        } else {
            post_url += 'update/' + $scope.updateEntry.id + '/';
        }
        var postData = {'email': $scope.formData.email, 'name': $scope.formData.name};
        var headers = {headers: {'Content-Type': 'application/json; charset=utf-8'}};
        $http.post(post_url, postData, headers).success(function (data, status, headers, config) {
            if (data['success'] == true) {
                if ($scope.editDialogMode == 'create') {
                    $scope.entries.push(data['item']);
                } else {
                    $scope.entries[$scope.updateEntryIndex] = $scope.formData;
                    // 这里不能使用update_entry = data['data']，因为这只会将
                    // update_entry指向的数据修改，而不会修改ng_scope.entries[updateEntryIndex]的数据值
                }
                toastr["success"]('保存成功');
                //alert('保存成功');
                editDialog.modal('hide');
            } else {
                var msg = data['msg'] ? data['msg'] : '保存失败';
                toastr["error"](msg);
            }
        }).error(function (data, status, headers, config) {
            toastr["error"]('保存失败，服务器未正确响应');
        }).finally(function () {
            btn.button('reset');
        });
    };
}
