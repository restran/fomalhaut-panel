/**
 * Created by restran on 2015/5/12.
 */

$.fn.serializeObject = function () {
    var o = {};
    var a = this.serializeArray();
    $.each(a, function () {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
};

// csrf token
$.ajaxSettings = $.extend($.ajaxSettings, {
    beforeSend: function (xhr, settings) {
        function getCookie(name) {
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
        }

        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});

var getUrlParam = function (name, default_value) {
    //构造一个含有目标参数的正则表达式对象
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
    // decodeURI，处理中文问题
    var url = decodeURI(window.location.search.substr(1));
    var r = url.match(reg);  //匹配目标参数
    if (r != null) return unescape(r[2]);
    return default_value; //返回参数值
};

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

var $request = {
    get: function (uri, data, successCallback, errorCallback) {
        $.ajax({
            type: 'GET',
            url: uri,
            // data to be added to query string:
            data: data,
            // type of data we are expecting in return:
            dataType: 'json',
            //timeout: 30000,
            context: $('body'),
            success: function (data) {
                console.log(data);
                try {
                    if (data['success'] == true) {
                        successCallback(data);
                    } else {
                        callErrorCallback(data, errorCallback);
                    }
                } catch (e) {
                    console.log(e);
                    callErrorCallback(data, errorCallback);
                }
            },
            error: function (xhr, type) {
                console.log('Ajax error!');
                callErrorCallback(null, errorCallback);
            }
        })
    },
    post: function (uri, data, successCallback, errorCallback) {
        $.ajax({
            type: 'POST',
            url: uri,
            // data to be added to query string:
            data: JSON.stringify(data),
            // type of data we are expecting in return:
            contentType: 'application/json; charset=utf-8',
            //timeout: 30000,
            context: $('body'),
            success: function (data) {
                console.log(data);
                try {
                    if (data['success'] == true) {
                        successCallback(data);
                    } else {
                        console.log('callErrorCallback');
                        callErrorCallback(data, errorCallback);
                    }
                } catch (e) {
                    console.log(e);
                    callErrorCallback(data, errorCallback);
                }
            },
            error: function (xhr, type) {
                console.log('Ajax error!');
                callErrorCallback(null, errorCallback);
            }
        })
    }
};

function callErrorCallback(data, callback) {
    if (callback != null && callback != undefined) {
        if (data != null && data['msg'] != '') {
            callback(data, data['msg']);
        } else {
            callback(data, '获取数据失败');
        }
    }
}

function requestGet(uri, data, successCallback, errorCallback) {
    $.ajax({
        type: 'GET',
        url: uri,
        // data to be added to query string:
        data: data,
        // type of data we are expecting in return:
        dataType: 'json',
        //timeout: 30000,
        context: $('body'),
        success: function (data) {
            console.log(data);
            try {
                if (data['success'] == true) {
                    successCallback(data);
                } else {
                    callErrorCallback(data, errorCallback);
                }
            } catch (e) {
                console.log(e);
                callErrorCallback(data, errorCallback);
            }
        },
        error: function (xhr, type) {
            console.log('Ajax error!');
            callErrorCallback(null, errorCallback);
        }
    })
}

function requestPost(uri, data, successCallback, errorCallback) {
    $.ajax({
        type: 'POST',
        url: uri,
        // data to be added to query string:
        data: JSON.stringify(data),
        // type of data we are expecting in return:
        contentType: 'application/json; charset=utf-8',
        //timeout: 30000,
        context: $('body'),
        success: function (data) {
            console.log(data);
            try {
                if (data['success'] == true) {
                    successCallback(data);
                } else {
                    console.log('callErrorCallback');
                    callErrorCallback(data, errorCallback);
                }
            } catch (e) {
                console.log(e);
                callErrorCallback(data, errorCallback);
            }
        },
        error: function (xhr, type) {
            console.log('Ajax error!');
            callErrorCallback(null, errorCallback);
        }
    })
}

(function () {
    // ie8 不支持 console
    if (!window.console) {
        window.console = (function () {
            var c = {};
            c.log = c.warn = c.debug = c.info = c.error = c.time = c.dir = c.profile
                = c.clear = c.exception = c.trace = c.assert = function () {
            };
            return c;
        })();
    }

    // ie8 不支持 getComputedStyle, bootstrap-select 会使用到
    if (!window.getComputedStyle) {
        window.getComputedStyle = function (el, pseudo) {
            this.el = el;
            this.getPropertyValue = function (prop) {
                var re = /(\-([a-z]){1})/g;
                if (prop == 'float') prop = 'styleFloat';
                if (re.test(prop)) {
                    prop = prop.replace(re, function () {
                        return arguments[2].toUpperCase();
                    });
                }
                return el.currentStyle[prop] ? el.currentStyle[prop] : null;
            };
            return this;
        }
    }

    // toastr 配置
    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": false,
        "progressBar": false,
        "positionClass": "toast-top-center",
        "preventDuplicates": true,
        "onclick": null,
        "showDuration": "300",
        "hideDuration": "1000",
        "timeOut": "3000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    }
})();

$(document).ready(function () {
    // 修复bootstrap 使用.navbar-fixed-top，且存在滚动条的情况下，
    // 打开模态对话框，导致导航栏向右偏17px的问题*/
    var oldSSB = $.fn.modal.Constructor.prototype.setScrollbar;
    $.fn.modal.Constructor.prototype.setScrollbar = function () {
        oldSSB.apply(this);
        if (this.bodyIsOverflowing && this.scrollbarWidth) {
            $('.navbar-fixed-top, .navbar-fixed-bottom').css('padding-right', this.scrollbarWidth);
        }
    };

    var oldRSB = $.fn.modal.Constructor.prototype.resetScrollbar;
    $.fn.modal.Constructor.prototype.resetScrollbar = function () {
        oldRSB.apply(this);
        $('.navbar-fixed-top, .navbar-fixed-bottom').css('padding-right', '');
    };


    // 回到顶部
    $(window).scroll(function () {
        //console.log($(window).scrollTop());
        //console.log($(window).height());
        //当滚动条的位置处于距顶部指定像素以下时，回到顶部按钮出现，否则消失
        if ($(window).scrollTop() > ($(window).height() / 2)) {
            $("#back-to-top").removeClass('hidden');
            //$("#back-to-top").fadeIn(1000);
        } else {
            $("#back-to-top").addClass('hidden');
            //$("#back-to-top").fadeOut(1000)
        }
    });

    $("#back-to-top").on('click', function (e) {
        $('html, body').animate({
            scrollTop: 0
        }, 1000);

    });

    //$('form').validator().on('submit', function (e) {
    //    if (e.isDefaultPrevented()) {
    //        // handle the invalid form...
    //    } else {
    //        // everything looks good!
    //    }
    //});

    try {
        $('form').validator({
            errors: {
                required: "这是必填项",
                match: "内容不匹配",
                minlength: "输入内容过少",
                maxlength: "输入内容过多"
            }
        });
    } catch (e) {

    }

});

(function () {
    // 使用 vue 来做导入导出
    var app = new Vue({
        el: '#nav-bar-app',
        data: {
            has_response: false,
            response: {'success': false, 'msg': '', 'errors': []},
            processDone: false,
            processMsg: '',
            processPercentage: 0,
            processInterval: null,
            realProcessPercentage: 0
        },
        methods: {
            init: function () {
                // 是否已经有回应的数据
                this.has_response = false;
                this.response = {'success': false, 'msg': '', 'errors': []};

                // 进度条
                this.processDone = false;
                this.processMsg = '';
                this.processPercentage = 0;
                this.processInterval = null;
                this.realProcessPercentage = 0;
            },
            uploadConfig: function () {
                $('#upload-config-modal').modal('show');
                app.init();
                var progressbar = $('#upload-progress-bar');
                progressbar.addClass('hidden');
            },
            closeImportModal: function () {
                // 导入成功需要刷新页面
                if (this.response['success'] == true) {
                    document.location.href = '/dashboard/config/';
                }
            }
        },
        computed: {}
    });

    app.init();

    var uploader = new plupload.Uploader({
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
                uploader.start();

                app.processDone = false;
                app.processMsg = '文件上传中...';
                app.processPercentage = 0;
                app.realProcessPercentage = 0;
                app.has_response = false;

                if (app.processInterval != null) {
                    clearInterval(app.processInterval);
                    app.processInterval = null;
                }

            },
            'UploadProgress': function (uploader, file) {
                console.log('UploadProgress');
                app.realProcessPercentage = Math.floor(file.percent * 10 / 100);
                app.processPercentage = app.realProcessPercentage;
                //var uploaded = file.loaded;
                //var size = plupload.formatSize(uploaded).toUpperCase();
                //
                //console.log(size);
                if (file.percent == 100) {
                    app.processMsg = '数据处理中...';
                    app.startProcess();
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
                app.has_response = true;
                try {
                    app.response = JSON.parse(response.response);
                } catch (err) {
                    app.response['success'] = false;
                    app.response['msg'] = '上传失败，服务器未正确响应';
                    app.response['errors'] = [];
                    app.response['success_msgs'] = [];
                }

                app.setProcessDone();
            },
            'Error': function (uploader, error) {
                app.has_response = true;
                try {
                    app.response = JSON.parse(error.response);
                } catch (err) {
                    app.response['success'] = false;
                    app.response['msg'] = '上传失败，请选择 JSON 文件';
                    app.response['errors'] = [];
                    app.response['success_msgs'] = [];
                }

                app.setProcessDone();

            }
        }
    });

    uploader.init();

    // 文件上传完成后，开始显示处理Excel的进度信息
    app.startProcess = function () {
        if (app.processInterval == null) {
            app.processInterval = setInterval(function () {
                if (app.realProcessPercentage < 50) {
                    app.realProcessPercentage += 2;
                } else if (app.realProcessPercentage < 80) {
                    app.realProcessPercentage += 1;
                } else if (app.realProcessPercentage < 90) {
                    app.realProcessPercentage += 0.5;
                } else if (app.realProcessPercentage < 95) {
                    app.realProcessPercentage += 0.1;
                } else if (app.realProcessPercentage < 99) {
                    app.realProcessPercentage += 0.01;
                } else {
                }
                app.processPercentage = Math.floor(app.realProcessPercentage);
            }, 250);
        }
    };

    app.setProcessDone = function () {
        if (app.processInterval != null) {
            clearInterval(app.processInterval);
            app.processInterval = null;
        }
        app.processPercentage = 100;
        app.processMsg = '处理完成';
    };

})();